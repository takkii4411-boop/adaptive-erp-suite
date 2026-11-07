from odoo import fields, models, api, _
from odoo.exceptions import UserError
import base64
import logging
from collections import defaultdict

_logger = logging.getLogger(__name__)


class MrpCsvImportWizard(models.TransientModel):
    _name = 'mrp.csv.import.wizard'
    _description = 'Import Joinery Assemblies + Components from CSV'

    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', readonly=True)
    csv_file = fields.Binary(string='CSV File', required=True)
    file_name = fields.Char(string='File Name')

    def action_import(self):
        self.ensure_one()
        if not self.csv_file:
            raise UserError(_("Please upload a CSV file."))

        ImportLog = self.env['mrp.import.log']
        project_id = False

        try:
            content = self._decode_csv_content()
            sections = self._parse_sections(content)

            if not sections.get('PRODUCTS'):
                raise UserError(_("No PRODUCTS section found or no valid rows."))

            if not sections.get('PARTS'):
                raise UserError(_("No PARTS section found."))

            joinery_data = self._extract_joinery_cabinet_quantities(sections['PRODUCTS'])
            project = joinery_data.get('project')
            project_id = self.env['project.project'].search([('name', '=', project)])
            parts_by_joinery_and_cabinet = self._extract_parts_by_joinery_and_cabinet(sections['PARTS'])
            sheet_materials = self._extract_unique_sheet_materials(sections.get('SHEETS', []))
            sheet_nc_codes = self._extract_sheet_nc_codes(sections.get('SHEETS', []))

            # Validate all products exist before proceeding
            self._validate_all_products(joinery_data, parts_by_joinery_and_cabinet)

            self._ensure_sheet_products(sheet_materials)

            # Create empty BOMs for all manufactured levels
            self._create_or_update_cabinet_boms(joinery_data, parts_by_joinery_and_cabinet)
            self._create_or_update_part_boms(parts_by_joinery_and_cabinet)

            # Create MOs + manual raw moves for components at each level
            created_mos = self._create_all_manufacturing_orders(joinery_data, parts_by_joinery_and_cabinet, sheet_nc_codes, project_id)

            count = len(created_mos)
            if not count:
                raise UserError(_("No valid manufacturing orders were created."))

            joineries = ", ".join(set(mo.product_id.name for mo in created_mos if mo.origin and 'Joinery' in (mo.origin or '')))
            message = f"Created {count} manufacturing order(s).\nJoineries processed: {joineries or 'N/A'}"

            # Log success
            ImportLog.sudo().create({
                'file_name': self.file_name or 'Unknown',
                'status': 'success',
                'message': message,
                'mo_count': count,
                'project_id': project_id.id if project_id else False,
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'soft_reload',
                'params': {
                    'title': _('Import Completed'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

        except Exception as e:
            # Log failure using a new cursor so it persists even if the main transaction rolls back
            try:
                with self.pool.cursor() as new_cr:
                    new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                    new_env['mrp.import.log'].create({
                        'file_name': self.file_name or 'Unknown',
                        'status': 'fail',
                        'message': str(e),
                        'mo_count': 0,
                        'project_id': project_id.id if project_id else False,
                    })
            except Exception:
                _logger.exception("Failed to create import failure log")
            raise

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _decode_csv_content(self):
        raw = base64.b64decode(self.csv_file)
        for encoding in ['utf-8-sig', 'utf-8', 'windows-1252', 'iso-8859-1']:
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise UserError(_("Cannot decode CSV. Please save as UTF-8 and retry."))

    def _parse_sections(self, text):
        lines = text.splitlines()
        sections = defaultdict(list)
        current_section = None
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('HEADER:'):
                current_section = stripped.replace('HEADER:', '').strip()
                continue
            if current_section:
                sections[current_section].append(stripped)
        return sections

    def _extract_joinery_cabinet_quantities(self, product_lines):
        result = defaultdict(lambda: defaultdict(float))
        metadata = defaultdict(dict)
        project = ''
        for line in product_lines:
            fields = [f.strip() for f in line.split(';')]
            if len(fields) < 7:
                continue
            project, joinery, _, cab_num, cab_name, qty_str, wo_name = fields[:7]
            comment = fields[7].strip() if len(fields) > 7 else ''
            try:
                qty = float(qty_str.replace(',', '.'))
                if qty <= 0:
                    continue
            except:
                continue
            if not joinery or not cab_name:
                continue
            result[joinery][cab_name] += qty
            if cab_name not in metadata[joinery]:
                metadata[joinery][cab_name] = {
                    'cab_num': cab_num,
                    'comment': comment,
                    'wo_name': wo_name,
                }
        if not result:
            raise UserError(_("No valid joinery + cabinet combinations found."))
        return {'quantities': result, 'metadata': metadata, 'project': project}

    def _extract_parts_by_joinery_and_cabinet(self, part_lines):
        mapping = defaultdict(lambda: defaultdict(list))
        for line in part_lines:
            fields = [f.strip() for f in line.split(';')]
            if len(fields) < 6:
                continue
            try:
                joinery = fields[0]
                cabinet_no = fields[1]
                part_name = fields[2]
                length = float(fields[3]) if fields[3] else 0.0
                width = float(fields[4]) if fields[4] else 0.0
                material = fields[5]
                product_comment = fields[6].strip() if len(fields) > 6 else ''
                part_comment = fields[7].strip() if len(fields) > 7 else ''
                cnc_number = fields[8].strip() if len(fields) > 8 else ''
            except:
                continue
            mapping[joinery][cabinet_no].append({
                'name': part_name,
                'length': length,
                'width': width,
                'material': material,
                'comment': part_comment or product_comment,
                'cabinet_no': cabinet_no,
                'cnc_number': cnc_number,
            })
        return mapping

    def _extract_unique_sheet_materials(self, sheet_lines):
        materials = set()
        for line in sheet_lines:
            if not line.strip():
                continue
            fields = [f.strip() for f in line.split(';')]
            if fields and fields[0]:
                name = fields[0].split('(')[0].strip()
                if name:
                    materials.add(name)
        return materials

    def _extract_sheet_nc_codes(self, sheet_lines):
        nc_map = {}
        for line in sheet_lines:
            stripped = line.strip()
            if not stripped:
                continue
            fields = [f.strip() for f in stripped.split(';')]
            if len(fields) >= 3:
                sheet_name = fields[0].split('(')[0].strip()
                nc_code = fields[2].strip()
                if sheet_name and nc_code:
                    nc_map[sheet_name] = nc_code
        return nc_map

    def _ensure_sheet_products(self, material_names):
        Product = self.env['product.product']
        uom_unit = self.env.ref('uom.product_uom_unit')
        for name in material_names:
            if not Product.search([('name', '=', name)], limit=1):
                Product.create({
                    'name': name,
                    'type': 'consu',
                    'uom_id': uom_unit.id,
                    'tracking': 'lot',
                    'is_storable': True
                })

    # ── Empty BOM Creation for all manufactured levels ──────────────────────

    def _create_or_update_part_boms(self, parts_map):
        Product = self.env['product.product']
        Bom = self.env['mrp.bom']
        uom_unit = self.env.ref('uom.product_uom_unit')

        processed = set()

        for joinery, cabinet_dict in parts_map.items():
            for cabinet_no, parts in cabinet_dict.items():
                for part in parts:
                    part_name = part['name']
                    if part_name in processed:
                        continue

                    part_product = Product.search([('name', '=', part_name)], limit=1) or \
                        Product.create({
                            'name': part_name,
                            'type': 'consu',
                            'uom_id': uom_unit.id,
                            'tracking': 'lot',
                            'is_storable': True
                        })

                    if not Bom.search([('product_id', '=', part_product.id), ('type', '=', 'normal')], limit=1):
                        Bom.create({
                            'product_tmpl_id': part_product.product_tmpl_id.id,
                            'product_id': part_product.id,
                            'product_qty': 1.0,
                            'type': 'normal',
                        })

                    processed.add(part_name)

    def _create_or_update_cabinet_boms(self, joinery_data, parts_map):
        Product = self.env['product.product']
        Bom = self.env['mrp.bom']
        uom_unit = self.env.ref('uom.product_uom_unit')

        quantities = joinery_data['quantities']
        metadata = joinery_data['metadata']

        cabinet_names = set()

        for joinery, cab_dict in parts_map.items():
            for cab_no, _ in cab_dict.items():
                cab_name = cab_no
                for j, cabs in quantities.items():
                    for name, _ in cabs.items():
                        if metadata.get(j, {}).get(name, {}).get('cab_num') == cab_no:
                            cab_name = name
                            break
                cabinet_names.add(cab_name)

        for cab_name in cabinet_names:
            cab_product = Product.search([('name', '=', cab_name)], limit=1) or \
                Product.create({
                    'name': cab_name,
                    'type': 'consu',
                    'uom_id': uom_unit.id,
                    'tracking': 'lot',
                    'is_storable': True
                })

            if not Bom.search([('product_id', '=', cab_product.id), ('type', '=', 'normal')], limit=1):
                Bom.create({
                    'product_tmpl_id': cab_product.product_tmpl_id.id,
                    'product_id': cab_product.id,
                    'product_qty': 1.0,
                    'type': 'normal',
                })


    # ── Product Validation ────────────────────────────────────────────────────

    def _validate_all_products(self, joinery_data, parts_map):
        """Validate that all products at every level exist before creating MOs."""
        Product = self.env['product.product']
        missing = {}

        quantities = joinery_data['quantities']

        # Level 1: Joinery products
        missing_joinery = []
        for joinery_name in quantities:
            if not Product.search([('name', '=', joinery_name)], limit=1):
                missing_joinery.append(joinery_name)
        if missing_joinery:
            missing['Joinery'] = missing_joinery

        # Level 2: Cabinet products
        missing_cabinet = []
        for cabinet_dict in quantities.values():
            for cab_name in cabinet_dict:
                if not Product.search([('name', '=', cab_name)], limit=1):
                    if cab_name not in missing_cabinet:
                        missing_cabinet.append(cab_name)
        if missing_cabinet:
            missing['Cabinet'] = missing_cabinet

        # Level 3: Part products
        missing_parts = []
        for cabinet_dict in parts_map.values():
            for parts in cabinet_dict.values():
                for part in parts:
                    if not Product.search([('name', '=', part['name'])], limit=1):
                        if part['name'] not in missing_parts:
                            missing_parts.append(part['name'])
        if missing_parts:
            missing['Part'] = missing_parts

        # Level 4: Sheet / Material products
        missing_sheets = []
        for cabinet_dict in parts_map.values():
            for parts in cabinet_dict.values():
                for part in parts:
                    if not Product.search([('name', '=', part['material'])], limit=1):
                        if part['material'] not in missing_sheets:
                            missing_sheets.append(part['material'])
        if missing_sheets:
            missing['Sheet Material'] = missing_sheets

        if missing:
            lines = []
            for level, names in missing.items():
                lines.append(f"\n{level}:")
                for name in names:
                    lines.append(f"  - {name}")
            raise UserError(_(
                "The following products are missing in the system. "
                "Please create them before importing:%s"
            ) % ''.join(lines))

    # ── MO Creation + Manual Raw Moves for all levels ────────────────────────

    def _create_all_manufacturing_orders(self, joinery_data, parts_map, sheet_nc_codes, project_id):
        Product = self.env['product.product']
        StockMove = self.env['stock.move']
        uom_unit = self.env.ref('uom.product_uom_unit')

        created_mos = []

        quantities = joinery_data['quantities']
        metadata = joinery_data['metadata']

        if not project_id:
            raise UserError(_("Project not found."))

        if len(project_id) > 1:
            raise UserError(_("Multiple projects found."))

        # ─────────────────────────────────────────────
        # 1️⃣ JOINERY MO → CABINET COMPONENTS
        # ─────────────────────────────────────────────
        for joinery_name, cabinet_dict in quantities.items():
            joinery_product = Product.search([('name', '=', joinery_name)], limit=1)
            if not joinery_product:
                raise UserError(_("Product not found."))

            joinery_mo = self.env['mrp.production'].search([('product_id', '=', joinery_product.id),('project_id', '=', project_id.id)])
            if not joinery_mo:
                continue

            created_mos.append(joinery_mo)

            for cab_name, cab_qty in cabinet_dict.items():
                cab_num = metadata[joinery_name][cab_name]['cab_num']
                cab_product = Product.search([('name', '=', cab_name)], limit=1)
                if not cab_product:
                    continue

                StockMove.create({
                    'product_id': cab_product.id,
                    'product_uom_qty': cab_qty,
                    'product_uom': uom_unit.id,
                    'location_id': joinery_mo.location_src_id.id,
                    'location_dest_id': joinery_mo.location_dest_id.id,
                    'raw_material_production_id': joinery_mo.id,
                    'cabinet_no': cab_num,
                })

        # ─────────────────────────────────────────────
        # 2️⃣ CABINET MO → PART COMPONENTS
        # ─────────────────────────────────────────────
        for joinery_name, cabinet_dict in quantities.items():
            for cab_name, cab_qty in cabinet_dict.items():
                cab_num = metadata[joinery_name][cab_name]['cab_num']
                cab_product = Product.search([('name', '=', cab_name)], limit=1)
                if not cab_product:
                    continue

                cab_mo = self.env['mrp.production'].create({
                    'product_id': cab_product.id,
                    'product_qty': cab_qty,
                    'product_uom_id': uom_unit.id,
                    'origin': f"CSV Import - Cabinet {cab_name}",
                    'project_id': project_id.id,
                })
                created_mos.append(cab_mo)

                # ✅ CORRECT part source
                parts = parts_map.get(joinery_name, {}).get(cab_num, [])

                for part in parts:
                    part_product = Product.search([('name', '=', part['name'])], limit=1)
                    if not part_product:
                        continue

                    StockMove.create({
                        'product_id': part_product.id,
                        'product_uom_qty': 1.0,
                        'product_uom': uom_unit.id,
                        'location_id': cab_mo.location_src_id.id,
                        'location_dest_id': cab_mo.location_dest_id.id,
                        'raw_material_production_id': cab_mo.id,
                        'cabinet_no': cab_num,
                        'comments': part['comment'],
                    })

        # ─────────────────────────────────────────────
        # 3️⃣ PART MO → SHEET COMPONENTS
        # ─────────────────────────────────────────────
        processed_parts = set()

        for joinery_name, cabinet_dict in parts_map.items():
            for cab_num, parts in cabinet_dict.items():
                for part in parts:
                    part_key = (part['name'], cab_num)
                    if part_key in processed_parts:
                        continue
                    processed_parts.add(part_key)

                    part_product = Product.search([('name', '=', part['name'])], limit=1)
                    sheet_product = Product.search([('name', '=', part['material'])], limit=1)
                    if not part_product or not sheet_product:
                        continue

                    part_mo = self.env['mrp.production'].create({
                        'product_id': part_product.id,
                        'product_qty': 1.0,
                        'product_uom_id': uom_unit.id,
                        'origin': f"CSV Import - Part {part['name']} ({cab_num})",
                        'project_id': project_id.id,
                    })
                    created_mos.append(part_mo)

                    StockMove.create({
                        'product_id': sheet_product.id,
                        'product_uom_qty': 1.0,
                        'product_uom': uom_unit.id,
                        'location_id': part_mo.location_src_id.id,
                        'location_dest_id': part_mo.location_dest_id.id,
                        'raw_material_production_id': part_mo.id,
                        'cabinet_no': cab_num,
                        'cnc_number': part['cnc_number'],
                        'comments': part['comment'],
                    })

        return created_mos
