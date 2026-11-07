from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    supplier_code = fields.Char(
        string="Supplier Code"
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    supplier_code = fields.Char(
        string="Supplier Code",
        related="product_tmpl_id.supplier_code",
        store=True,
        readonly=False
    )