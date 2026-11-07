from odoo import models, api
from odoo.exceptions import ValidationError


class SaleEstimation(models.Model):
    _inherit = "sale.estimation"

    def action_open_material_hardware_details(self):
        self.ensure_one()

        if not self.project_id:
            raise ValidationError("Please select a project to view material & hardware details.")

        mat_hard_details = self.env['material.hardware.details'].search([
            ('estimation_id', '=', self.id)
        ], limit=1)

        if not mat_hard_details:
            mat_hard_details = self.env['material.hardware.details'].create({
                'estimation_id': self.id,
            })

        arch_map = {}
        qty_map = {}
        margin_map = {}
        sub_con_map = {}

        for est_line in self.estimation_line_ids:
            wizard = est_line.source_wizard_id
            if not wizard:
                continue

            sub_by_categ = {
                sub.actual_categ_id.id: sub.subcontractor.name
                for sub in wizard.subcontractor_ids
                if sub.actual_categ_id
            }
            for comp in est_line.source_wizard_id.component_ids:
                product = comp.product_id
                pid = product.id
                arch_map[pid] = comp.arch_code
                qty_map[pid] = qty_map.get(pid, 0) + (comp.product_uom_qty * est_line.qty)
                margin_map[pid] = comp.margin
                categ_id = product.categ_id.id if product.categ_id else False
                if categ_id in sub_by_categ:
                    sub_con_map[pid] = sub_by_categ[categ_id]

        material_lists = self.env['material.list'].search([
            ('project_id', '=', self.project_id.id)
        ])

        existing_product_ids = set()

        for mat_list in material_lists:
            for line in mat_list.order_line:
                product = line.product_id
                seller = product.seller_ids[:1]

                vals = {
                    'product_id': product.id,
                    'categ_id': product.categ_id.id,
                    'sort_no': line.sequence,
                    'product_color_id': product.product_color_id.id or False,
                    'product_finish_id': product.product_finish_id.id or False,
                    'supplier_id': seller.partner_id.id if seller else False,
                    'arch_code': arch_map.get(product.id),
                    'uom_id': product.uom_id.id,
                    'rate': line.rate,
                    'qty': qty_map.get(product.id, 0),
                    'sub_total': qty_map.get(product.id, 0) * line.rate,
                    'margin': margin_map.get(product.id, 0),
                    'sub_con': sub_con_map.get(product.id),
                }

                existing_line = mat_hard_details.line_ids.filtered(
                    lambda l: l.product_id.id == product.id
                )

                if existing_line:
                    if existing_line.comments:
                        vals['comments'] = existing_line.comments
                    if existing_line.sub_con:
                        vals['sub_con'] = existing_line.sub_con

                    existing_line.write(vals)
                    existing_product_ids.add(product.id)
                else:
                    mat_hard_details.write({'line_ids': [(0, 0, vals)]})
                    existing_product_ids.add(product.id)

            mat_hard_details.sub_contractor_bom_line_ids.unlink()

            sub_vals = []
            sub_map = {}

            for est_line in self.estimation_line_ids:
                wizard = est_line.source_wizard_id
                if not wizard:
                    continue

                for sub in wizard.subcontractor_ids:
                    key = (sub.product_id.id, sub.subcontractor.id, est_line.product_id.id, sub.margin)
                    multiplied_qty = sub.quantity * est_line.qty
                    if key not in sub_map:
                        sub_map[key] = {
                            'hardware_id': mat_hard_details.id,
                            'estimation_line_id': est_line.id,
                            'name': sub.name,
                            'product_id': sub.product_id.id,
                            'subcontractor': sub.subcontractor.id,
                            'rate': sub.rate,
                            'quantity': multiplied_qty,
                            'margin': sub.margin,
                            'margin_diff': sub.margin_diff,
                            'description': sub.description,
                            'uom': sub.uom.id,
                        }
                    else:
                        sub_map[key]["quantity"] += multiplied_qty
                sub_vals = [(0, 0, val) for val in sub_map.values()]

            if sub_vals:
                mat_hard_details.write({
                    'sub_contractor_bom_line_ids': sub_vals
                })

        return {
            'type': 'ir.actions.act_window',
            'name': f'Material & Hardware - {self.project_id.name}',
            'res_model': 'material.hardware.details',
            'res_id': mat_hard_details.id,
            'view_mode': 'form',
            'target': 'new',
        }