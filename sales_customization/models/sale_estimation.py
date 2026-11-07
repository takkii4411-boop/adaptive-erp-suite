from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
from io import BytesIO
from odoo.tools import is_html_empty
from odoo.tools.mail import html_keep_url
from odoo.tools import html2plaintext
from datetime import datetime

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class SaleEstimation(models.Model):
    _name = "sale.estimation"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _estimation_line_ids(self):
        if self:
            for rec in self:
                domain = [('estimation_id', 'in', self.ids)]
                if rec.filter_level:
                    domain.append(('level_id', '=', rec.filter_level.id))
                if rec.filter_joinery_name:
                    domain.append(('joinery_name_id', '=', rec.filter_joinery_name.id))
                if rec.filter_cl_no:
                    domain.append(('cl_no', 'ilike', rec.filter_cl_no))
                if rec.filter_description:
                    domain.append(('description', 'ilike', rec.filter_description))
                if rec.filter_stage:
                    domain.append(('stage', 'ilike', rec.filter_stage))
                if rec.filter_room:
                    domain.append(('room', 'ilike', rec.filter_room))
                if rec.filter_drawing_no:
                    domain.append(('drawing_number', 'ilike', rec.filter_drawing_no))
                if rec.filter_product_id:
                    domain.append(('product_id.name', 'ilike', rec.filter_product_id.name))
                if rec.filter_internal_notes:
                    domain.append(('internal_notes', 'ilike', rec.filter_internal_notes))
                if rec.filter_custom_exclusion:
                    domain.append(('custom_exclusion', 'ilike', rec.filter_custom_exclusion))

                if domain:
                    matching_records = self.env['sale.estimation.line'].search(domain)
                    for line in matching_records:
                        line.is_show = True
                return domain
        else:
            return []

    @api.onchange('filter_level', 'filter_product_id', 'filter_joinery_name')
    def _onchange_filters(self):
        # self.estimation_line_ids = self.env['sale.estimation.line'].search(
        #     self._estimation_line_ids()
        # )
        self._estimation_line_ids()

    # @api.constrains('filter_level', 'filter_joinery_name', 'filter_product_id')
    # def _constrain_no_save_with_filters(self):
    #     for rec in self:
    #         if (
    #                 rec.filter_level
    #                 or rec.filter_joinery_name
    #                 or rec.filter_product_id
    #         ):
    #             raise ValidationError("You cannot save while filters are applied. Please discard.")

    name = fields.Char(string='Estimation No.')
    employee_id = fields.Many2one('hr.employee', string='Assigned', copy=True, tracking=True)
    project_id = fields.Many2one('project.project', string='Project Name', copy=True, tracking=True, required=True)
    project_type_id = fields.Many2one('sale.project.type', string='Type', copy=True, tracking=True)
    builder_ids = fields.One2many('sale.builder', 'sale_id', string='Builders', copy=True)
    estimation_line_ids = fields.One2many('sale.estimation.line', 'estimation_id', string='Estimations',domain=_estimation_line_ids, copy=True)
    subcontractor_ids = fields.One2many('sale.sub.contractor', 'sale_id',string='Sub-Contractor', copy=True)
    internal_review = fields.Text(string='Internal Review', copy=True, tracking=True)
    comments = fields.Text(string='Comments', copy=True, tracking=True)
    exclusions = fields.Html(string='Standard Exclusions', compute='_compute_exclusion', copy=True)
    custom_exclusions = fields.Html(string='Custom Exclusions', copy=True)
    terms_condition = fields.Html(string='Terms & Conditions', compute='_compute_terms_condition',
        store=True, readonly=False, precompute=True)
    standard_notes = fields.Html(string='Standard Notes', copy=True)
    status = fields.Selection([('draft', 'Draft'), ('sent', 'Sent'), ('done', 'Approved'), ('cancel', 'Cancelled')], string='Status', default='draft')
    child_ids = fields.Many2many('sale.estimation', 'm1', 'm2', string='Childs')
    parent_id = fields.Many2one('sale.estimation', string='Parent')
    estimations_count = fields.Integer(string='Estimations Count', compute='_count_estimations', readonly=True)
    seq = fields.Integer(string='Seq', default=1)
    filter_level = fields.Many2one('sale.estimation.level', string='Filter Level', compute='compute_filter_level',readonly=False)
    filter_joinery_name = fields.Many2one('joinery.name', string='Filter Joinery Name', compute='compute_filter_joinery_name',readonly=False)
    filter_cl_no = fields.Char(string='Filter C/L No', compute='compute_filter_cl_no',readonly=False)
    filter_description = fields.Char(string='Filter Description', compute='compute_filter_description',readonly=False)
    filter_stage = fields.Char(string='Filter Stage', compute='compute_filter_stage',readonly=False)
    filter_drawing_no = fields.Char(string='Filter Drawing No', compute='compute_filter_drawing_no',readonly=False)
    filter_room = fields.Char(string='Filter Room', compute='compute_filter_room',readonly=False)
    filter_internal_notes = fields.Char(string='Filter Internal Notes', compute='compute_filter_internal_notes',readonly=False)
    filter_custom_exclusion = fields.Char(string='Filter Custom Exclusion', compute='compute_filter_custom_exclusion',readonly=False)
    filter_product_id = fields.Many2one('product.product', string='Filter Product', compute='compute_filter_product_id',readonly=False)
    select_all = fields.Boolean(string='Select All', default=False, copy=False)
    display_details = fields.Boolean(default=False)
    joinery_type = fields.Selection([('joinery', 'Joinery'), ('wholesale', 'Wholesale')], string='Joinery Type', default='joinery')
    custom_activity_type_id = fields.Many2one('mail.activity.type', related="activity_type_id", store=True)
    exclusion_id = fields.Many2one('estimation.exclusion', compute='_compute_exclusion')
    show_chatter = fields.Boolean(string="Show Chatter", default=True)
    material_list_id = fields.Many2one('material.list', string="Material List")

    def toggle_chatter(self):
        for record in self:
            record.show_chatter = not record.show_chatter

    @api.depends('joinery_type')
    def _compute_exclusion(self):
        for rec in self:
            if not rec.joinery_type:
                rec.exclusion_id = False
                rec.exclusions = ''
                continue
            exclusion = self.env['estimation.exclusion'].search([
                ('joinery_type', '=', rec.joinery_type)
            ], limit=1)

            if exclusion:
                rec.exclusion_id = exclusion.id
                rec.exclusions = exclusion.exclusion
            else:
                rec.exclusion_id = False
                rec.exclusions = ''

    @api.onchange('joinery_type')
    def _onchange_joinery_type(self):
        self._compute_exclusion()

    def toggle_details(self):
        for rec in self:
            rec.display_details = not rec.display_details


    def compute_filter_level(self):
        for rec in self:
            rec.filter_level = False

    def compute_filter_joinery_name(self):
        for rec in self:
            rec.filter_joinery_name = False

    def compute_filter_cl_no(self):
        for rec in self:
            rec.filter_cl_no = ''

    def compute_filter_description(self):
        for rec in self:
            rec.filter_description = ''

    def compute_filter_stage(self):
        for rec in self:
            rec.filter_stage = ''

    def compute_filter_room(self):
        for rec in self:
            rec.filter_room = ''

    def compute_filter_drawing_no(self):
        for rec in self:
            rec.filter_drawing_no = ''

    def compute_filter_internal_notes(self):
        for rec in self:
            rec.filter_internal_notes = ''

    def compute_filter_custom_exclusion(self):
        for rec in self:
            rec.filter_custom_exclusion = ''

    def compute_filter_product_id(self):
        for rec in self:
            rec.filter_product_id = False

    def action_clear_all(self):
        for rec in self:
            rec.filter_level = False
            rec.filter_cl_no = ''
            rec.filter_description = ''
            rec.filter_stage = ''
            rec.filter_room = ''
            rec.filter_internal_notes = ''
            rec.filter_custom_exclusion = ''
            rec.filter_product_id = False
            rec.filter_joinery_name = False
            rec.select_all = False
            for line in rec.estimation_line_ids:
                line.is_select = False
                line.is_show = False

    def _count_estimations(self):
        for order in self:
            order.estimations_count = len(order.child_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.estimation') or _('New')
        return super().create(vals_list)

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)

        for rec, vals in zip(self, vals_list):
            vals["name"] = rec._get_next_child_name()

        return vals_list

    def action_update(self):
        for rec in self:
            new_rec = rec.copy()  # copy_data generates correct name
            new_rec.parent_id = rec.id
            for line in new_rec.estimation_line_ids:
                line.is_existing_line = True
            rec.child_ids = [(4, new_rec.id)]

    def _get_next_child_name(self):
        """Return next child name with incrementing last number."""
        self.ensure_one()

        base_name = self.name

        if not self.child_ids:
            return f"{base_name}-1"

        suffixes = []
        for c in self.child_ids:
            if c.name.startswith(base_name + "-"):
                try:
                    number = int(c.name.replace(base_name + "-", ""))
                    suffixes.append(number)
                except ValueError:
                    pass

        next_num = max(suffixes) + 1 if suffixes else 1
        return f"{base_name}-{next_num}"

    def action_view_estimations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Linked Estimations'),
            'res_model': 'sale.estimation',
            'view_mode': 'list,form',
            'domain': [('parent_id', '=', self.id)],
        }

    @api.onchange('select_all')
    def onchange_select_all(self):
        for rec in self:
            for line in rec.estimation_line_ids:
                if rec.select_all:
                    line.is_select = True
                else:
                    line.is_select = False

    def action_open_bom_all(self):
        """Open one BOM Wizard combining all components, operations, and subcontractors from existing bom.wizard lines."""
        self.ensure_one()

        # Get selected lines
        non_filtered = self.estimation_line_ids.filtered(lambda obj: obj.is_select)
        filtered = self.estimation_line_ids.filtered(lambda obj: obj.is_select and obj.is_show)
        lines_to_process = filtered if filtered else non_filtered

        if not lines_to_process:
            raise ValidationError(_("Please select at least one line to open BOM details."))

        # Reset selection flags
        for line in non_filtered:
            line.is_select = False
            line.is_show = False
        self.select_all = False

        bom_wizards = []
        total_cost_component = 0.0
        total_cost_operation = 0.0
        total_cost_subcontractor = 0.0
        total_margin_component = 0.0
        total_margin_operation = 0.0
        total_margin_subcontractor = 0.0
        total_component = 0.0
        total_operation = 0.0
        total_subcontractor = 0.0
        currency_id = self.env.company.currency_id.id

        component_map = {}
        operation_map = {}
        subcontractor_map = {}

        all_component_margin_diffs = set()
        all_operation_margin_diffs = set()
        all_subcontractor_margin_diffs = set()

        for line in lines_to_process:
            bom_wizard = line.source_wizard_id
            if not bom_wizard:
                continue
            bom_wizards.append(bom_wizard)

            line_qty = line.qty
            # --- Components ---
            for comp in bom_wizard.component_ids:
                key = (comp.product_id.id, comp.product_categ_id.id, comp.margin)
                multiplied_qty = comp.product_uom_qty * line_qty
                if key not in component_map:
                    component_map[key] = {
                        "product_id": comp.product_id.id,
                        "product_categ_id": comp.product_categ_id.id,
                        "product_uom_qty": multiplied_qty,
                        "rate": comp.rate,
                        "product_uom": comp.product_uom.id,
                        "estimation_line_id": line.id,
                        "arch_code": comp.arch_code,
                        "margin": comp.margin,
                        "margin_diff": comp.margin_diff,
                    }
                else:
                    component_map[key]["product_uom_qty"] += multiplied_qty

            # --- Operations ---
            for op in bom_wizard.operation_ids:
                key = (op.product_id.id, op.margin)
                multiplied_qty = op.quantity * line_qty
                if key not in operation_map:
                    operation_map[key] = {
                        "name": op.name,
                        "product_id": op.product_id.id,
                        "workcenter_id": op.workcenter_id.id,
                        "duration": op.duration,
                        "quantity": multiplied_qty,
                        "rate": op.rate,
                        "estimation_line_id": line.id,
                        "margin": op.margin,
                        "margin_diff": op.margin_diff,
                    }
                else:
                    operation_map[key]["quantity"] += multiplied_qty

            # --- Subcontractors ---
            for sub in bom_wizard.subcontractor_ids:
                key = (sub.product_id.id, sub.subcontractor.id, line.product_id.id, sub.margin)
                multiplied_qty = sub.quantity * line_qty
                if key not in subcontractor_map:
                    subcontractor_map[key] = {
                        "name": line.product_id.name,
                        "product_id": sub.product_id.id,
                        "rate": sub.rate,
                        "uom": sub.uom.id,
                        "quantity": multiplied_qty,
                        "estimation_line_id": line.id,
                        "subcontractor": sub.subcontractor.id,
                        "margin": sub.margin,
                        "margin_diff": sub.margin_diff,
                    }
                else:
                    subcontractor_map[key]["quantity"] += multiplied_qty

            # --- Costs (multiplied by line_qty) ---
            total_cost_component += bom_wizard.total_cost_component * line_qty
            total_cost_operation += bom_wizard.total_cost_operation * line_qty
            total_cost_subcontractor += bom_wizard.total_cost_subcontractor * line_qty

            # --- Margins (assuming these are absolute amounts; multiply if they represent totals per unit) ---
            total_margin_component += bom_wizard.total_margin_component * line_qty
            total_margin_operation += bom_wizard.total_margin_operation * line_qty
            total_margin_subcontractor += bom_wizard.total_margin_subcontractor * line_qty

            # --- Totals (multiplied by line_qty) ---
            total_component += bom_wizard.total_component * line_qty
            total_operation += bom_wizard.total_operation * line_qty
            total_subcontractor += bom_wizard.total_subcontractor * line_qty

            all_component_margin_diffs.update(bom_wizard.component_ids.mapped('margin_diff'))
            all_operation_margin_diffs.update(bom_wizard.operation_ids.mapped('margin_diff'))
            all_subcontractor_margin_diffs.update(bom_wizard.subcontractor_ids.mapped('margin_diff'))

        # --- Convert merged maps into list of tuples ---
        component_vals = [(0, 0, val) for val in component_map.values()]
        operation_vals = [(0, 0, val) for val in operation_map.values()]
        subcontractor_vals = [(0, 0, val) for val in subcontractor_map.values()]

        # --- Create combined wizard ---
        combined_wizard = self.env["bom.wizard"].create({
            "component_ids": component_vals,
            "operation_ids": operation_vals,
            "subcontractor_ids": subcontractor_vals,
            "currency_id": currency_id,
            "estimation_id": self.id,
            "total_cost_component_all": total_cost_component,
            "total_cost_operation_all": total_cost_operation,
            "total_cost_subcontractor_all": total_cost_subcontractor,
            "total_margin_component_all": total_margin_component,
            "total_margin_operation_all": total_margin_operation,
            "total_margin_subcontractor_all": total_margin_subcontractor,
            "total_component_all": total_component,
            "total_operation_all": total_operation,
            "total_subcontractor_all": total_subcontractor,
            "margin_percent_component_diff_all": max(all_component_margin_diffs) if all_component_margin_diffs else 0.0,
            "margin_percent_operation_diff_all": max(all_operation_margin_diffs) if all_operation_margin_diffs else 0.0,
            "margin_percent_subcontractor_diff_all": max(all_subcontractor_margin_diffs) if all_subcontractor_margin_diffs else 0.0
        })

        # --- Link source ---
        for wiz in bom_wizards:
            wiz.source_wizard_id = combined_wizard.id

        # --- Open combined wizard form ---
        return {
            "name": _("Material Summary"),
            "type": "ir.actions.act_window",
            "res_model": "bom.wizard",
            "res_id": combined_wizard.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "from_product_catalog": True,
            },
        }

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id.id,
    )
    company_id = fields.Many2one(
        "res.company",
        string="company",
        default=lambda self: self.env.company.id,
    )
    amount_untaxed = fields.Monetary(string="Sub Total", compute="_compute_amount", store=True, tracking=True)
    amount_tax = fields.Monetary(string="GST Amount", compute="_compute_amount", store=True, tracking=True)
    amount_total = fields.Monetary(string="Total", compute="_compute_amount", store=True, tracking=True)
    amount_cost = fields.Monetary(string="Total Cost", compute="_compute_amount", store=True, tracking=True)
    amount_margin = fields.Monetary(string="Total Margin", compute="_compute_amount", store=True, tracking=True)

    # --- COMPUTE TOTALS ---
    @api.depends("estimation_line_ids.price_subtotal", "estimation_line_ids.price_total",
                 "estimation_line_ids.product_id", "estimation_line_ids.price_unit", "estimation_line_ids.qty",
                 "filter_level", "filter_joinery_name", "filter_cl_no", "filter_description", "filter_stage",
                 "filter_drawing_no", "filter_room", "filter_internal_notes", "filter_custom_exclusion",
                 "filter_product_id")
    def _compute_amount(self):
        for rec in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            amount_cost = 0.0
            amount_margin = 0.0

            for line in rec.estimation_line_ids.filtered(lambda l: not l.is_not_active):
                amount_untaxed += line.price_subtotal
                amount_cost += line.total_cost
                amount_margin += line.total_margin

                # Determine taxes
                taxes = line.tax_ids
                # taxes = line.product_id.taxes_id
                # if not taxes:
                #     taxes = rec.company_id.account_sale_tax_id

                if taxes:
                    tax_data = taxes.compute_all(
                        line.price_unit,
                        currency=rec.currency_id,
                        quantity=line.qty,
                        product=line.product_id,
                        partner=rec.project_id.partner_id,
                    )
                    amount_tax += sum(t['amount'] for t in tax_data.get('taxes', []))

            rec.amount_untaxed = amount_untaxed
            rec.amount_tax = amount_tax
            rec.amount_total = amount_untaxed + amount_tax
            rec.amount_cost = amount_cost
            rec.amount_margin = amount_margin

    def action_confirm(self):
        for rec in self:
            if rec.status not in ['draft', 'sent']:
                continue
            rec.status = 'done'

    def action_cancel(self):
        for rec in self:
            rec.status = 'cancel'

    def action_draft(self):
        for rec in self:
            rec.status = 'draft'

    def action_add_lines(self):
        for rec in self:
            selected_lines = rec.estimation_line_ids.filtered(lambda obj:obj.is_select)

            if not selected_lines:
                raise ValidationError(_("Please select at least one line to copy."))

            for line in selected_lines:
                line_id = line.copy()
                line_id.is_select = False
                line_id.is_copied_line = True
                rec.estimation_line_ids = [(4, line_id.id)]

    def action_estimation_send(self):
        """Send sign requests for each builder and open email wizard."""
        self.ensure_one()

        # role = self.env.ref("sign.sign_item_role_default")
        # if not role:
        #     raise ValidationError("No role is defined on the base signature template.")
        #
        # sign_requests = []
        # for builder in self.builder_ids:
        #     report = self.env.ref("sales_customization.action_report_custom_estimation")
        #     pdf_content, _ = report.with_context(builder_id=builder.id)._render_qweb_pdf(report, self.id)
        #     pdf_base64 = base64.b64encode(pdf_content)
        #
        #     attachment = self.env['ir.attachment'].create({
        #         'name': f'Estimation {self.name} - {builder.partner_id.name}.pdf',
        #         'datas': pdf_base64,
        #         'type': 'binary',
        #         'mimetype': 'application/pdf',
        #         'res_model': 'sale.estimation',
        #         'res_id': self.id
        #     })
        #
        #     sign_template = self.env['sign.template'].create({
        #         'name': f'Estimation - {self.name} - {builder.partner_id.name}',
        #     })
        #
        #     document_id = self.env['sign.document'].create({
        #         'attachment_id': attachment.id,
        #         'template_id': sign_template.id,
        #     })
        #
        #     self.env['sign.item'].create([{
        #         'document_id': document_id.id,
        #         'page': 1,  # Always first page
        #         'posX': 0.78,  # Right side
        #         'posY': 0.8,  # Bottom side
        #         'width': 0.15,  # Signature box width
        #         'height': 0.05,  # Signature box height
        #         'required': True,
        #         'type_id': self.env.ref('sign.sign_item_type_signature').id,
        #         'responsible_id': role.id,
        #     }])
        #
        #     # Create sign request for this builder
        #     sign_request = self.env['sign.request'].create({
        #         'reference': f'Estimation {self.name} - {builder.partner_id.name}',
        #         'subject': f'Estimation {self.name}',
        #         'template_id': sign_template.id,
        #         'request_item_ids': [(0, 0, {
        #             'partner_id': builder.partner_id.id,
        #             'role_id': role.id,
        #         })],
        #     })
        #     sign_requests.append(sign_request.id)

        ctx = {
            'default_model': 'sale.estimation',
            'default_res_ids': self.ids,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'email_notification_allow_footer': True,
            'proforma': self.env.context.get('proforma', False),
            # 'sign_request_ids': sign_requests,
        }

        if len(self) > 1:
            ctx['default_composition_mode'] = 'mass_mail'
        else:
            ctx.update({'force_email': True})
            if not self.env.context.get('hide_default_template'):
                mail_template = self.env.ref('sales_customization.mail_template_estimation_send')
                if mail_template:
                    client_partner_ids = self.builder_ids.filtered(lambda obj: obj.is_client)
                    ctx.update({
                        'default_template_id': mail_template.id,
                        'mark_so_as_sent': True,
                        'default_partner_ids': [(6, 0, client_partner_ids.partner_id.ids)],
                    })

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    has_selected_lines = fields.Boolean(
        string="Has Selected Lines", compute="_compute_has_selected_lines"
    )

    @api.depends('estimation_line_ids.is_select')
    def _compute_has_selected_lines(self):
        for rec in self:
            rec.has_selected_lines = any(line.is_select for line in rec.estimation_line_ids)

    def action_export_selected_xlsx(self):
        """Export selected estimation lines (is_select) to XLSX and trigger direct download."""
        self.ensure_one()
        selected_lines = self.estimation_line_ids.filtered(lambda l: l.is_select)
        if not selected_lines:
            raise ValidationError(_("Please select at least one line to export."))

        if xlsxwriter is None:
            raise ValidationError(_("The python package 'xlsxwriter' is required to export XLSX files."))

        # Prepare in-memory workbook
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # =========================================================
        # SHEET 1: JOINERY ITEMS
        # =========================================================
        worksheet = workbook.add_worksheet('Joinery Items')
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'bg_color': '#D3D3D3'
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': '#FFFFFF',
            'border': 1,
            'align': 'center'
        })

        text_format = workbook.add_format({'border': 1})
        money_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        center_format = workbook.add_format({'border': 1, 'align': 'center'})

        worksheet.merge_range(
            'A1:S1',
            f'Joinery Items - {self.name or ""}',
            title_format
        )

        worksheet.merge_range(
            'A2:S2',
            f'Date: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
            workbook.add_format({'italic': True})
        )

        headers = [
            'Inactive', 'Level', 'Joinery Type', 'Joinery No', 'Joinery Name', 'C/L No', 'Description', 'Room', 'Stage',
            'Drawing Number', 'Internal Notes', 'Custom Exclusion', 'Qty', 'Total Cost', 'Unit Price', 'Taxes',
            'Total Margin', 'Subtotal (Total)', 'Tax Incl.'
        ]

        for col, head in enumerate(headers):
            worksheet.write(2, col, head, header_format)

        row = 3

        for line in selected_lines.sorted('sequence'):
            tax_names = ', '.join(line.tax_ids.mapped('name')) if line.tax_ids else ''
            drawing_nos = ', '.join(line.drawing_nos.mapped('name')) if line.drawing_nos else ''

            description = html2plaintext(line.description)
            description = description.strip()

            worksheet.write(row, 0, 'Yes' if line.is_not_active else 'No', center_format)
            worksheet.write(row, 1, line.level_id.name or '', text_format)
            worksheet.write(row, 2, line.joinery_type or '', text_format)
            worksheet.write(row, 3, line.product_id.display_name or '', text_format)
            worksheet.write(row, 4, line.joinery_name_id.name or '', text_format)
            worksheet.write(row, 5, line.cl_no or '', text_format)
            worksheet.write(row, 6, description, text_format)
            worksheet.write(row, 7, line.room or '', text_format)
            worksheet.write(row, 8, line.stage or '', text_format)
            worksheet.write(row, 9, drawing_nos or '', text_format)
            worksheet.write(row, 10, line.internal_notes or '', text_format)
            worksheet.write(row, 11, line.custom_exclusion or '', text_format)
            worksheet.write(row, 12, line.qty or 0.0, money_format)
            worksheet.write(row, 13, line.total_cost or 0.0, money_format)
            worksheet.write(row, 14, line.price_unit or 0.0, money_format)
            worksheet.write(row, 15, tax_names, text_format)
            worksheet.write(row, 16, line.total_margin or 0.0, money_format)
            worksheet.write(row, 17, line.price_subtotal or 0.0, money_format)
            worksheet.write(row, 18, line.price_total or 0.0, money_format)

            row += 1

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:F', 18)
        worksheet.set_column('G:G', 40)
        worksheet.set_column('H:L', 18)
        worksheet.set_column('M:S', 18)

        # =========================================================
        # SHEET 2: COMPONENTS
        # =========================================================
        ws_comp = workbook.add_worksheet('Components')
        comp_headers = ['Joinery No', 'Joinery Name', 'Component', 'Arch Code', 'Qty', 'UOM', 'Margin (%)']
        for col, h in enumerate(comp_headers):
            ws_comp.write(0, col, h, header_format)

        row = 1
        for line in selected_lines.sorted('sequence'):
            wizard = line.source_wizard_id
            if not wizard:
                continue
            for comp in wizard.component_ids:
                ws_comp.write(row, 0, line.product_id.display_name or '', text_format)
                ws_comp.write(row, 1, line.joinery_name_id.name or '', text_format)
                ws_comp.write(row, 2, comp.product_id.display_name or '', text_format)
                ws_comp.write(row, 3, comp.arch_code or '', text_format)
                ws_comp.write(row, 4, comp.product_uom_qty or 0.0, money_format)
                ws_comp.write(row, 5, comp.product_id.uom_id.name or '', text_format)
                ws_comp.write(row, 6, comp.margin or 0.0, money_format)
                row += 1

        ws_comp.set_column('A:B', 22)
        ws_comp.set_column('C:C', 30)
        ws_comp.set_column('D:G', 18)

        # =========================================================
        # SHEET 3: SUBCONTRACTORS
        # =========================================================
        ws_sub = workbook.add_worksheet('Sub-Contractors')
        sub_headers = ['Joinery No', 'Joinery Name', 'Category', 'Subcontractor', 'Description', 'UOM', 'Rate', 'Qty',
                       'Margin (%)', 'Subtotal']
        for col, h in enumerate(sub_headers):
            ws_sub.write(0, col, h, header_format)

        row = 1
        for line in selected_lines.sorted('sequence'):
            wizard = line.source_wizard_id
            if not wizard:
                continue
            for sub in wizard.subcontractor_ids:
                ws_sub.write(row, 0, line.product_id.display_name or '', text_format)
                ws_sub.write(row, 1, line.joinery_name_id.name or '', text_format)
                ws_sub.write(row, 2, sub.actual_categ_id.display_name or '', text_format)
                ws_sub.write(row, 3, sub.subcontractor.name or '', text_format)
                ws_sub.write(row, 4, sub.description or '', text_format)
                ws_sub.write(row, 5, sub.uom.name or '', text_format)
                ws_sub.write(row, 6, sub.rate or 0.0, money_format)
                ws_sub.write(row, 7, sub.quantity or 0.0, money_format)
                ws_sub.write(row, 8, sub.margin or 0.0, money_format)
                ws_sub.write(row, 9, sub.subtotal or 0.0, money_format)
                row += 1

        ws_sub.set_column('A:B', 22)
        ws_sub.set_column('C:E', 25)
        ws_sub.set_column('F:J', 18)

        # =========================================================
        # SHEET 4: SHOPS  (adjust fields if your model differs)
        # =========================================================
        ws_shop = workbook.add_worksheet('Shops')
        shop_headers = ['Joinery No', 'Joinery Name', 'Shop', 'Description', 'Rate', 'Qty', 'UOM', 'Subtotal']
        for col, h in enumerate(shop_headers):
            ws_shop.write(0, col, h, header_format)

        row = 1
        for line in selected_lines.sorted('sequence'):
            wizard = line.source_wizard_id
            if not wizard or not hasattr(wizard, 'shop_ids'):
                continue
            for shop in wizard.shop_ids:
                ws_shop.write(row, 0, line.product_id.display_name or '', text_format)
                ws_shop.write(row, 1, line.joinery_name_id.name or '', text_format)
                ws_shop.write(row, 2, getattr(shop, 'name', '') or '', text_format)
                ws_shop.write(row, 3, getattr(shop, 'description', '') or '', text_format)
                ws_shop.write(row, 4, getattr(shop, 'rate', 0.0) or 0.0, money_format)
                ws_shop.write(row, 5, getattr(shop, 'quantity', 0.0) or 0.0, money_format)
                ws_shop.write(row, 6, getattr(shop, 'uom', False) and shop.uom.name or '', text_format)
                ws_shop.write(row, 7, getattr(shop, 'subtotal', 0.0) or 0.0, money_format)
                row += 1

        ws_shop.set_column('A:B', 22)
        ws_shop.set_column('C:D', 28)
        ws_shop.set_column('E:H', 18)

        workbook.close()
        output.seek(0)
        data = output.read()
        output.close()

        xlsx_base64 = base64.b64encode(data)

        attachment = self.env['ir.attachment'].create({
            'name': f'Estimation_{self.name}.xlsx',
            'datas': xlsx_base64,
            'type': 'binary',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': 'sale.estimation',
            'res_id': self.id,
        })

        # Return URL action to download the attachment directly
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }

    def action_materials_open(self):
        if not self.project_id:
            raise ValidationError(_("Please select project to show the materials."))

        existing_wizard = self.env["material.list"].search([
            ("project_id", "=", self.project_id.id),
        ], limit=1)

        if existing_wizard:
            self.material_list_id = existing_wizard.id
            return {
                "name": _("Project Material List"),
                "type": "ir.actions.act_window",
                "res_model": "material.list",
                "res_id": existing_wizard.id,
                "view_mode": "form",
                "target": "new",
                "context": {
                    "custom_estimation_id": self.id,
                    "from_product_catalog": True,
                },
            }
        return {
            "name": _("Project Material List"),
            "type": "ir.actions.act_window",
            "res_model": "material.list",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_project_id": self.project_id.id,
                "custom_estimation_id": self.id,
                "from_product_catalog": True,
            },
        }

    @api.onchange('estimation_line_ids')
    def _onchange_update_custom_exclusions(self):
        """
        Dynamically update the 'custom_exclusions' field on parent
        from child line exclusions (auto-sync both add/remove).
        """
        for rec in self:
            lines_with_exclusions = rec.estimation_line_ids.filtered(lambda l: l.custom_exclusion)

            if not lines_with_exclusions:
                rec.custom_exclusions = False
                continue

            # Build clean, styled HTML block
            html_content = "<ul style='margin-left:10px;'>"
            for line in lines_with_exclusions:
                product_name = line.product_id.display_name or "N/A"
                exclusion = line.custom_exclusion.strip()
                html_content += f"<li><b>{product_name}</b> - {exclusion}</li>"
            html_content += "</ul>"

            rec.custom_exclusions = html_content

    filter_product_domain = fields.Binary(
        string="Filter Product Domain",
        compute="_compute_filter_product_domain"
    )

    @api.depends('filter_product_id', 'estimation_line_ids.product_id')
    def _compute_filter_product_domain(self):
        """Compute JSON version of the domain for product_id."""
        for rec in self:
            custom_domain = [('id', '=', 0)]
            products = rec.estimation_line_ids.mapped('product_id')
            unique_products = {p.name: p for p in products}.values()
            if unique_products:
                domain = [('id', 'in', [p.id for p in unique_products])]
            else:
                domain = custom_domain
            rec.filter_product_domain = domain

    filter_joinery_name_domain = fields.Binary(
            string="Filter Joinery Name Domain",
            compute="_compute_filter_joinery_name_domain"
        )

    @api.depends('filter_joinery_name', 'estimation_line_ids.joinery_name_id')
    def _compute_filter_joinery_name_domain(self):
        """Compute JSON version of the domain for joinery_name_id."""
        for rec in self:
            custom_domain = [('id', '=', 0)]
            selected_products = rec.estimation_line_ids.mapped('joinery_name_id').ids
            if selected_products:
                selected_domain = ('id', 'in', selected_products)
                domain = [selected_domain]
            else:
                domain = custom_domain
            rec.filter_joinery_name_domain = domain

    @api.depends('employee_id', 'project_id', 'project_type_id', 'joinery_type', 'builder_ids')
    def _compute_terms_condition(self):
        use_invoice_terms = self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms')
        if not use_invoice_terms:
            return
        for estimation in self:
            winner_builder = estimation.builder_ids.filtered(lambda obj: obj.winner)[:1]
            estimation = estimation.with_company(estimation.company_id)
            if estimation.company_id.terms_type == 'html' and self.env.company.invoice_terms_html:
                baseurl = html_keep_url(estimation._get_note_url() + '/terms')
                context = {'lang': winner_builder.partner_id.lang or self.env.user.lang}
                estimation.terms_condition = _('Terms & Conditions: %s', baseurl)
                del context
            elif not is_html_empty(self.env.company.invoice_terms):
                if winner_builder.partner_id.lang:
                    estimation = estimation.with_context(lang=winner_builder.partner_id.lang)
                estimation.terms_condition = estimation.env.company.invoice_terms

    @api.model
    def _get_note_url(self):
        return self.env.company.get_base_url()

class SaleEstimationLine(models.Model):
    _name = "sale.estimation.line"
    _order = 'level_id, product_id, sequence, id'

    sequence = fields.Integer(string='Sequence', related="level_id.sequence", default=10)
    level_id = fields.Many2one('sale.estimation.level', string='Level', copy=True)
    joinery_no = fields.Char(string='Joinery Name')
    joinery_name_id = fields.Many2one('joinery.name', string='Joinery Name', copy=True)
    cl_no = fields.Char(string='C/L No')
    product_id = fields.Many2one('product.product', string='Joinery No', required=True)
    description = fields.Html(string="Description", translate=True)
    is_copied_line = fields.Boolean(string='Is Copied Line', default=False)
    is_not_active = fields.Boolean(string='Inactive', default=False)
    joinery_type = fields.Selection(
        [('joinery', 'Joinery'), ('wholesale', 'Wholesale')],
        string='Joinery Type',
        compute='_compute_joinery_type',
        store=True,
        readonly=False,
        force_save=True,
    )
    is_existing_line = fields.Boolean(string='Existing Line', default=False)
    parent_id = fields.Many2one('sale.estimation', string='Parent', related='estimation_id.parent_id')

    @api.depends('estimation_id.joinery_type')
    def _compute_joinery_type(self):
        for line in self:
            if not line.joinery_type:
                line.joinery_type = line.estimation_id.joinery_type or 'joinery'

    @api.onchange('joinery_type')
    def _onchange_joinery_type(self):
        for line in self:
            line.product_id = False

    def action_open_description_popup(self):
        """Open HTML description in popup"""
        self.ensure_one()
        return {
            'name': 'Description',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation.line.description.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_description': self.description,
            },
        }
    stage = fields.Char(string='Stage')
    room = fields.Char(string='Room')
    # drawing_nos = fields.Many2many('ir.attachment', string="Drawing No's")
    drawing_number = fields.Char( string="Drawing No")
    internal_notes = fields.Char(string='Internal Notes')
    custom_exclusion = fields.Char(string='Custom Exclusion')
    qty = fields.Float(string='Qty', default=1)
    estimation_id = fields.Many2one('sale.estimation', string='Estimation')
    is_select = fields.Boolean(string='Select')
    is_show = fields.Boolean(string='Show')
    price_unit = fields.Float(string="Unit Price")
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain="[('type_tax_use', '=', 'sale')]"
    )
    is_expendable = fields.Boolean(
        related='estimation_id.display_details',
        string="Expendable",
        store=True
    )

    # Computed amounts
    price_subtotal = fields.Monetary(
        string="Subtotal", compute="_compute_amount", store=True
    )
    price_tax = fields.Monetary(
        string="Tax", compute="_compute_amount", store=True
    )
    price_total = fields.Monetary(
        string="Total", compute="_compute_amount", store=True
    )
    currency_id = fields.Many2one(related="estimation_id.currency_id", store=True)
    source_wizard_id = fields.Many2one("bom.wizard", string="Source Wizard")

    total_cost = fields.Monetary(string='Cost', compute="_compute_bom_wizard_values", store=True)
    total_margin = fields.Monetary(string='Margin', compute="_compute_bom_wizard_values", store=True)

    @api.depends("price_subtotal", "price_total",
                 "product_id", "price_unit", "qty", "source_wizard_id.total_all", "source_wizard_id.total_margin_all", "source_wizard_id.total_cost_all",
                 "estimation_id.filter_level", "estimation_id.filter_joinery_name", "estimation_id.filter_cl_no", "estimation_id.filter_description", "estimation_id.filter_stage",
                 "estimation_id.filter_drawing_no", "estimation_id.filter_room", "estimation_id.filter_internal_notes", "estimation_id.filter_custom_exclusion",
                 "estimation_id.filter_product_id")
    def _compute_bom_wizard_values(self):
        for line in self:
            l_cost = 0
            l_margin = 0
            if line.source_wizard_id:
                t_cost = line.source_wizard_id.total_cost_component + line.source_wizard_id.total_cost_operation + line.source_wizard_id.total_cost_subcontractor
                t_margin = line.source_wizard_id.total_margin_component + line.source_wizard_id.total_margin_operation + line.source_wizard_id.total_margin_subcontractor

                # Multiply by line quantity
                l_cost = t_cost * line.qty
                l_margin = t_margin * line.qty
            line.total_cost = l_cost
            line.total_margin = l_margin

    @api.depends('qty', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * line.qty
            taxes = line.tax_ids.compute_all(
                line.price_unit, line.currency_id, line.qty, product=line.product_id
            )
            line.price_subtotal = taxes['total_excluded']
            line.price_tax = taxes['total_included'] - taxes['total_excluded']
            line.price_total = taxes['total_included']

    def action_open_bom(self):
        """Open BOM Wizard with existing record if available, else create new."""
        self.ensure_one()
        # Find BOM for this product
        bom = self.env["mrp.bom"]._bom_find(self.product_id)
        bom_id = bom[self.product_id]
        self.is_select = False

        if not bom_id:
            raise ValidationError(_("This joinery item doesn't have BoM."))

        existing_wizard = self.env["bom.wizard"].search([
            ("bom_id", "=", bom_id.id),
            ("estimation_line_id", "=", self.id),
        ], limit=1)
        plain_text = html2plaintext(self.description)
        plain_text = plain_text.strip()

        if existing_wizard:
            self.source_wizard_id = existing_wizard.id
            existing_wizard.filter_component_product_id = False
            existing_wizard.filter_product_id = False
            existing_wizard.filter_subcontractor_id = False
            return {
                "name": _(f"{self.product_id.display_name} - {plain_text}"),
                "type": "ir.actions.act_window",
                "res_model": "bom.wizard",
                "res_id": existing_wizard.id,
                "view_mode": "form",
                "target": "new",
                "context": {
                    "custom_estimation_id": self.estimation_id.id,
                    "from_product_catalog": True,
                },
            }

        # 🔹 Create a new wizard
        return {
            "name": _(f"{self.product_id.display_name} - {plain_text}"),
            "type": "ir.actions.act_window",
            "res_model": "bom.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_bom_id": bom_id.id,
                "default_estimation_line_id": self.id,
                "custom_estimation_id": self.estimation_id.id,
                "from_product_catalog": True,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        """When a product is created from estimation line, create a blank BOM on that product."""
        records = super().create(vals_list)
        for rec in records:
            if rec.product_id:
                rec.product_id.project_id = rec.estimation_id.project_id.id
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.product_id:
                rec.product_id.project_id = rec.estimation_id.project_id.id
        return res

    product_domain = fields.Binary(
        string="Product Domain",
        compute="_compute_product_domain"
    )

    @api.depends('product_id', 'joinery_type')
    def _compute_product_domain(self):
        """Compute JSON version of the domain for product_id."""
        for rec in self:
            if not rec.estimation_id.project_id.id:
                raise ValidationError(_("Please select project to add a line."))

            domain = []
            if rec.joinery_type == 'wholesale':
                # domain.append(('joinery_type', '=', 'wholesale'))
                domain.append(('categ_id.is_wholesale_joinery', '=', True))
            else:
                domain.append(('project_id', '=', rec.estimation_id.project_id.id))
                selected_products = rec.estimation_id.estimation_line_ids.mapped('product_id').ids
                if selected_products:
                    selected_domain = ('id', 'not in',
                                       [pid for pid in selected_products if pid != rec.product_id.id])
                    domain.append(selected_domain)

            rec.product_domain = domain

    @api.onchange('product_id')
    def _onchange_product_id_set_taxes(self):
        for line in self:
            if line.product_id:
                line.tax_ids = line.product_id.taxes_id

    def action_open_internal_notes_popup(self):
        self.ensure_one()
        return {
            'name': 'Internal Notes',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation.line.internal.notes.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_internal_notes': self.internal_notes,
            },
        }

    def action_open_custom_exclusion_popup(self):
        self.ensure_one()
        return {
            'name': 'Custom Exclusion',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation.line.custom.exclusion.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_custom_exclusion': self.custom_exclusion,
            },
        }


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        res = super().action_send_mail()
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        if active_model == 'sale.estimation' and active_id:
            record_id = self.env[active_model].browse(active_id)
            if record_id.status == 'draft':
                record_id.status = 'sent'
            mesg = record_id.message_post(
                body=f"Sale Estimation mail has been sent to {','.join([partner.name for partner in self.partner_ids])}.",
                subtype_xmlid='mail.mt_note'
            )
            client_partner_ids = record_id.builder_ids.filtered(lambda obj: obj.partner_id.id in self.partner_ids.ids)
            if client_partner_ids:
                for cp in client_partner_ids:
                    if not cp.is_mail_sent:
                        cp.is_mail_sent = True
        return res


class SaleEstimationLineDescriptionWizard(models.TransientModel):
    _name = 'sale.estimation.line.description.wizard'
    _description = 'Sale Estimation Line Description Wizard'

    line_id = fields.Many2one('sale.estimation.line', string="Line")
    description = fields.Html(string="Description", translate=True)

    def action_save_description(self):
        if self.line_id:
            self.line_id.description = self.description
        return {'type': 'ir.actions.act_window_close'}


class SaleEstimationLineInternalNotesWizard(models.TransientModel):
    _name = 'sale.estimation.line.internal.notes.wizard'
    _description = 'Internal Notes Wizard'

    line_id = fields.Many2one('sale.estimation.line', string="Line")
    internal_notes = fields.Char(string="Internal Notes")

    def action_save_internal_notes(self):
        if self.line_id:
            self.line_id.internal_notes = self.internal_notes
        return {'type': 'ir.actions.act_window_close'}

class SaleEstimationLineExclusionWizard(models.TransientModel):
    _name = 'sale.estimation.line.custom.exclusion.wizard'
    _description = 'Custom Exclusion Wizard'

    line_id = fields.Many2one('sale.estimation.line', string="Line")
    custom_exclusion = fields.Char(string="Custom Exclusion")

    def action_save_custom_exclusion(self):
        if self.line_id:
            self.line_id.custom_exclusion = self.custom_exclusion
        return {'type': 'ir.actions.act_window_close'}
