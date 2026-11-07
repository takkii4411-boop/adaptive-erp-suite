from odoo import models, fields, api, _


class SaleEstimationSubcontractor(models.Model):
    _name = "sale.estimation.subcontractor"

    name = fields.Char(string='Name', related="product_id.display_name")
    product_id = fields.Many2one("product.product", string="Description", domain="[('type', '=', 'service')]")
    subcontractor_ids = fields.Many2many('res.partner', string="Subcontractors")

    @api.model_create_multi
    def create(self, vals_list):
        """When a product is created from estimation line, create a blank BOM on that product."""
        records = super().create(vals_list)

        for rec in records:
            if rec.product_id:
                rec.product_id.type = 'service'

        return records

    def write(self, vals):
        """Also check on update — if product is newly assigned, create a BOM if none exists."""
        res = super().write(vals)

        for rec in self:
            if rec.product_id:
                if rec.product_id:
                    rec.product_id.type = 'service'
        return res