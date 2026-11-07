from odoo import models, fields, api, _

class ProductCategory(models.Model):
    _inherit = "product.category"

    is_wholesale_joinery = fields.Boolean(string='Is a Wholesale type Joinery', default=False)