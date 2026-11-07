from odoo import _, api, Command, fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material',
        index=True, ondelete='cascade', required=False, check_company=True) # required=True removed for our custom requirement.
    company_id = fields.Many2one('res.company', 'Company', related='workcenter_id.company_id') #related='bom_id.company_id' change for our custom requirement.