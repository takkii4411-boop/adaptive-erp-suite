from odoo import api, fields, models, tools, _


class SaleEstimation(models.Model):
    _inherit = 'sale.estimation'

    lead_id = fields.Many2one('crm.lead', string='Lead', readonly=True)
    opportunity_count = fields.Integer(
        string="Opportunities",
        compute="_compute_opportunity_count",
        store=False
    )

    @api.depends('lead_id')
    def _compute_opportunity_count(self):
        for rec in self:
            rec.opportunity_count = 1 if rec.lead_id else 0

    def action_open_opportunity(self):
        """Open the linked CRM Opportunity."""
        self.ensure_one()
        if not self.lead_id:
            return False

        return {
            'name': _('Opportunity'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.lead_id.id,
            'target': 'current',
        }
