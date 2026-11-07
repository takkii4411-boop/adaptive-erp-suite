from odoo import fields, models

class ProductColor(models.Model):
    _name = 'product.color'
    _description = 'Product Color'

    name = fields.Char('Product Color')