from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    joinery_type = fields.Selection(
        [('material', 'Material'), ('joinery', 'Joinery'), ('wholesale', 'Wholesale')],
        string='Joinery Type',
        default='material',
        required=True
    )
    supplier_name = fields.Char(string='Supplier', compute='_compute_supplier_name')
    supplier_price = fields.Float(string='Supplier Price', compute='_compute_supplier_name')

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)

        for template in templates:
            template.product_variant_ids.write({
                "joinery_type": template.joinery_type
            })

        return templates

    def write(self, vals):
        res = super().write(vals)

        if "joinery_type" in vals:
            for template in self:
                template.product_variant_ids.write({
                    "joinery_type": template.joinery_type
                })

        return res

    @api.onchange('joinery_type')
    def _onchange_joinery_type_warning(self):
        if not self._origin:
            return

        old = self._origin.joinery_type
        new = self.joinery_type
        if old == new:
            return

        title = _("Warning")
        details = _("You changed Joinery Type from %s to %s.") % (old.upper(), new.upper())
        effect = _("\nWholesale category and shop details will be applied automatically.") if new == "wholesale" else _("\nWholesale category and shop details have been removed.")

        return {
            'warning': {
                'title': title,
                'message': details + effect,
            }
        }

    @api.depends('seller_ids')
    def _compute_supplier_name(self):
        for rec in self:
            if rec.seller_ids:
                rec.supplier_name = rec.seller_ids[0].partner_id.name
                rec.supplier_price = rec.seller_ids[0].price
            else:
                rec.supplier_name = ""
                rec.supplier_price = ""