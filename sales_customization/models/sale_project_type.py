from odoo import models, fields, api, _


class SaleProjectType(models.Model):
    _name = "sale.project.type"

    name = fields.Char(string='Name')