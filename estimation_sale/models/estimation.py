from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class SaleEstimation(models.Model):
    _inherit = 'sale.estimation'

    sale_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    sale_order_count = fields.Integer(
        string="Sales Order",
        compute="_compute_sale_order_count",
        store=False
    )

    @api.depends('sale_id')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = 1 if rec.sale_id else 0

    def action_open_sale_order(self):
        """Open the linked Sales Order."""
        self.ensure_one()
        if not self.sale_id:
            return False

        return {
            'name': _('Sales Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_id.id,
            'target': 'current',
        }

    def action_create_sale_order(self):
        """Create a new Sales Order from this Estimation."""
        self.ensure_one()

        winner_builder = self.builder_ids.filtered(lambda obj:obj.winner)
        if not winner_builder:
            raise ValidationError(_("Please select at least one winner from builders."))

        # Prevent duplicate sales order
        if self.sale_id:
            return {
                'name': _('Sales Order'),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': self.sale_id.id,
                'target': 'current',
            }

        # Prepare sales order lines
        order_line = [(0, 0, {
            'level_id': line.level_id.id,
            'is_not_active': line.is_not_active,
            'joinery_type': line.joinery_type,
            'joinery_no': line.joinery_no,
            'stage': line.stage,
            'room': line.room,
            'internal_notes': line.internal_notes,
            'custom_exclusion': line.custom_exclusion,
            'source_wizard_id': line.source_wizard_id.id,
            'total_cost': line.total_cost,
            'total_margin': line.total_margin,
            'name': line.description or line.product_id.name,
            'product_id': line.product_id.id,
            'product_uom_qty': line.qty,
            'price_unit': line.price_unit,
            'tax_ids': [(6, 0, line.tax_ids.ids)] if line.tax_ids else [],
        }) for line in self.estimation_line_ids]

        # Create sales order
        sale_order = self.env['sale.order'].create({
            'partner_id': winner_builder.partner_id.id,
            'estimation_id': self.id,
            'employee_id': self.employee_id.id,
            'project_id': self.project_id.id,
            'project_type_id': self.project_type_id.id,
            'joinery_type': self.joinery_type,
            'order_line': order_line,
        })

        # Link back to sale
        self.sale_id = sale_order.id

        # Open the new sales order form
        return {
            'name': _('Sales Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': sale_order.id,
            'target': 'current',
        }

    def write(self, vals):
        """Ensure sync even when updated via backend or server actions."""
        res = super(SaleEstimation, self).write(vals)
        for estimation in self:
            if estimation.sale_id:
                estimation._update_sale_from_estimation()
        return res

    def _update_sale_from_estimation(self):
        """Helper to create/update sales order data based on estimation fields."""
        self.ensure_one()
        sale_id = self.sale_id
        if not sale_id:
            return

        # === Sync Project ===
        sale_id.project_id = self.project_id.id
        # === Sync Employee ===
        sale_id.employee_id = self.employee_id.id
        # === Sync Project Type ===
        sale_id.project_type_id = self.project_type_id.id
        # === Sync Joinery Type ===
        sale_id.joinery_type = self.joinery_type
        # === Sync Opportunity ===
        sale_id.opportunity_id = self.lead_id.id