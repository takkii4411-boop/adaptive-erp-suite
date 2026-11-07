from odoo import models, fields, api, _


class JoineryName(models.Model):
    _name = "joinery.name"
    _order = 'sequence, name'

    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Name')