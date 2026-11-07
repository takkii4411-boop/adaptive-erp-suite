from odoo import models, fields, api, _


class SaleSubContractor(models.Model):
    _name = "sale.sub.contractor"

    partner_id = fields.Many2one('res.partner', string='Name')
    sale_id = fields.Many2one('sale.estimation', string='Estimation')
    status = fields.Selection([('win', 'Win'), ('on_hold', 'On Hold'), ('loss', 'Loss')], string='Status')
    winner = fields.Boolean(string='Winner')