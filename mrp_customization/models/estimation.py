from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class SaleEstimation(models.Model):
    _inherit = 'sale.estimation'

    mrp_ids = fields.Many2many('mrp.production', string='Manufacturing')
    mrp_order_count = fields.Integer(
        string="Manufacturing",
        compute="_compute_mrp_order_count",
        store=False
    )

    @api.depends('mrp_ids')
    def _compute_mrp_order_count(self):
        for rec in self:
            sale_mrp_count = len(rec.sale_id.mrp_production_ids)
            project_mrp_count = self.env['mrp.production'].search_count([('project_id', '=', self.project_id.id), ('id', 'not in', rec.mrp_ids.ids)])
            rec.mrp_order_count = len(rec.mrp_ids) + sale_mrp_count + project_mrp_count if rec.mrp_ids else 0

    def action_open_mrp_order(self):
        """Open the linked Manufacturing Order."""
        self.ensure_one()
        if not self.mrp_ids:
            return False

        return {
            'name': _('Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': ['|', ('id', 'in', self.mrp_ids.ids + self.sale_id.mrp_production_ids.ids), ('project_id', '=', self.project_id.id)],
            'target': 'current',
        }

    def action_create_manufacturing_order(self):
        """Create Manufacturing Orders and auto-create KIT BOM if not exists."""
        self.ensure_one()

        selected_lines = self.estimation_line_ids.filtered(lambda obj: obj.is_select)

        if not selected_lines:
            raise ValidationError(_("Please select at least one line to create manufacturing order."))

        mrp_obj = self.env['mrp.production']
        bom_obj = self.env['mrp.bom']

        for line in selected_lines:
            # 🔹 Check if MO already exists for this estimation line
            existing_mo = mrp_obj.search([
                ('estimation_id', '=', self.id),
                ('estimation_line_id', '=', line.id),
                ('product_id', '=', line.product_id.id),
            ], limit=1)

            if existing_mo:
                continue

            product = line.product_id

            bom = bom_obj.search([
                ('product_id', '=', product.id),
                ('type', '=', 'phantom')
            ], limit=1)

            if not bom:
                bom = bom_obj.create({
                    'product_id': product.id,
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'type': 'phantom',  # KIT BOM
                    'product_qty': 1,
                    'bom_line_ids': []
                })

            mrp_order = mrp_obj.create({
                'product_id': product.id,
                'estimation_id': self.id,
                'estimation_line_id': line.id,
                'project_id': self.project_id.id,
                'bom_id': bom.id,
            })

            # Link back to sale
            self.mrp_ids = [(4, mrp_order.id)]

        return {
            'name': _('Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': ['|', ('id', 'in', self.mrp_ids.ids + self.sale_id.mrp_production_ids.ids), ('project_id', '=', self.project_id.id)],
            'target': 'current',
        }