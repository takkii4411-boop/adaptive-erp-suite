# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    level_id = fields.Many2one('sale.estimation.level', string='Level')
    joinery_no = fields.Char(string='Joinery Name')
    is_not_active = fields.Boolean(string='Inactive', default=False)
    joinery_type = fields.Selection([('joinery', 'Joinery'), ('wholesale', 'Wholesale')],string='Joinery Type',)
    stage = fields.Char(string='Stage')
    room = fields.Char(string='Room')
    internal_notes = fields.Char(string='Internal Notes')
    custom_exclusion = fields.Char(string='Custom Exclusion')
    source_wizard_id = fields.Many2one("bom.wizard", string="Source Wizard")
    total_cost = fields.Monetary(string='Cost')
    total_margin = fields.Monetary(string='Margin')