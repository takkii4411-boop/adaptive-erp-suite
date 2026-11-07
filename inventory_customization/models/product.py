from odoo import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_color_id = fields.Many2one('product.color', string='Colour')
    product_finish_id = fields.Many2one('product.finish', string='finish')
    website_char = fields.Char('Website')
    length = fields.Char('Length')
    width = fields.Char('Width')
    thickness = fields.Char('Thickness')

    def _compute_cost_price(self):
        for product in self:
            preferred_supplier = None
            for supplier in product.seller_ids:
                if supplier.is_preferred:
                    preferred_supplier = supplier
                    break
            if not preferred_supplier and product.seller_ids:
                preferred_supplier = product.seller_ids.sorted('sequence')[0]
            if preferred_supplier and preferred_supplier.min_qty > 0:
                cost = preferred_supplier.price / preferred_supplier.min_qty
            else:
                cost = 0.0
            product.standard_price = cost

    def write(self, vals):
        res = super().write(vals)
        if 'seller_ids' in vals:
            self._compute_cost_price()
        return res
