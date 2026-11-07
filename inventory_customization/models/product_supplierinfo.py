from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    is_preferred = fields.Boolean(
        string="Preferred Supplier",
        default=False,
        help="Check this box to mark this vendor as the preferred supplier for this product."
    )
    min_qty = fields.Float(
        'Quantity', default=1.0, required=True, digits="Product Unit",
        help="The quantity to purchase from this vendor to benefit from the unit price. If a vendor unit is set, quantity should be specified in this unit, otherwise it should be specified in the default unit of the product.")

    def write(self, vals):
        if 'is_preferred' in vals and vals['is_preferred']:
            for supplier in self:
                if supplier.is_preferred:
                    continue
                vals['sequence'] = -999

        elif 'is_preferred' in vals:
            for supplier in self:
                if supplier.sequence < 0:
                    vals['sequence'] = 1

        return super().write(vals)

    @api.constrains('is_preferred')
    def _check_unique_preferred_supplier(self):
        for record in self.filtered('is_preferred'):
            if not record.product_tmpl_id:
                continue
            duplicates = self.search([
                ('product_tmpl_id', '=', record.product_tmpl_id.id),
                ('is_preferred', '=', True),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicates:
                raise ValidationError(
                    _("A product can have only one preferred supplier. To set a new preferred supplier, first remove the preferred flag from the existing one."
                      "Current preferred: %s") % duplicates.partner_id.display_name
                )