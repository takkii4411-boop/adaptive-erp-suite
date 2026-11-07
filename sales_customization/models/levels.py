from odoo import models, fields, api, _


class SaleEstimationLevel(models.Model):
    _name = "sale.estimation.level"
    _order = 'sequence, name'

    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Name')