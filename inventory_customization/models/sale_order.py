from odoo import api, fields, models, tools, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self.picking_ids:
            if self.project_id:
                rec.project_id = self.project_id.id
        return res