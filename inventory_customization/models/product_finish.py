from odoo import fields, models

class ProductFinish(models.Model):
    _name = 'product.finish'
    _description = 'Product Finish'

    name = fields.Char('Product Finish')