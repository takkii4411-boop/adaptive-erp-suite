from odoo import models, fields, api, _
from odoo.fields import Command, Domain
from collections import defaultdict

class MaterialList(models.Model):
    _inherit = "material.list"

    def _default_order_line_values(self, child_field=False):
        default_data = super()._default_order_line_values(child_field=child_field)
        new_default_data = self.env['material.list.line']._get_product_catalog_lines_data()
        return {**default_data, **new_default_data}

    def _get_action_add_from_catalog_extra_context(self):
        return {
            **super()._get_action_add_from_catalog_extra_context(),
            'product_catalog_currency_id': self.currency_id.id,
            'product_catalog_digits': self.order_line._fields['price_unit'].get_digits(self.env),
        }

    def _get_product_catalog_domain(self):
        return super()._get_product_catalog_domain() & Domain('bom_ids', '=', False) & Domain('type', '!=', 'service')

    def _get_product_catalog_order_data(self, products, **kwargs):
        pricelist = self.pricelist_id._get_products_price(
            quantity=1.0,
            products=products,
            currency=self.currency_id,
            date=self.date_order,
            **kwargs,
        )
        return {product_id: {'price': price} for product_id, price in pricelist.items()}

    def _get_product_catalog_record_lines(self, product_ids, *, child_field=False, **kwargs):
        grouped_lines = defaultdict(lambda: self.env['material.list.line'])
        for line in self.order_line:
            if line.product_id.id not in product_ids:
                continue
            grouped_lines[line.product_id] |= line
        return grouped_lines

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        """Update or remove material list line based on catalog changes."""
        self.ensure_one()
        line = self.order_line.filtered(lambda l: l.product_id.id == product_id)

        if line:
            if quantity > 0:
                line.product_uom_qty = quantity
            else:
                line.unlink()
                return 0.0
        else:
            if quantity > 0:
                line = self.env['material.list.line'].sudo().create({
                    'material_list_id': self.id,
                    'product_id': product_id,
                    'product_uom_qty': quantity,
                })
                self.env.cr.commit()

        return line.price_unit if line else 0.0

    def _is_readonly(self):
        self.ensure_one()
        return False

    def action_handle_new_product_from_catalog(self):
        self.ensure_one()

        return self.with_context(custom_estimation_id = self.env.context.get('custom_estimation_id')).action_add_from_catalog()



class MaterialListLine(models.Model):
    _inherit = "material.list.line"

    currency_id = fields.Many2one(related="material_list_id.currency_id", store=True)

    def action_add_material_from_catalog(self):
        order = self.env['material.list'].browse(self.env.context.get('order_id'))
        return order.action_add_from_catalog()

    def _get_product_catalog_lines_data(self, default=False, **kwargs):
        """ Override of `sale` to add the delivered quantity.

        :rtype: dict
        :return: A dict with the following structure:
            {
                'deliveredQty': float,
                'quantity': float,
                'price': float,
                'readOnly': bool,
            }
        """
        if len(self) == 1:
            return {
                'quantity': self.product_uom_qty,
                'price': self.price_unit,
                'readOnly': self.material_list_id._is_readonly(),
                'uomDisplayName': self.product_uom.display_name,
                'productType': self.product_id.type,
            }
        elif self:
            self.product_id.ensure_one()
            order_line = self[0]
            order = order_line.material_list_id
            return {
                'readOnly': True,
                'uomDisplayName': self.product_id.uom_id.display_name,
                'productType': self.product_id.type,
                'price': order.pricelist_id._get_product_price(
                    product=order_line.product_id,
                    quantity=1.0,
                    currency=order.currency_id,
                    date=order.date_order,
                    **kwargs,
                ),
                'quantity': sum(
                    self.mapped(
                        lambda line: line.product_uom._compute_quantity(
                            qty=line.product_uom_qty,
                            to_unit=line.product_id.uom_id,
                        )
                    )
                ),
            }
        else:
            return {
                'price': 0,
                'quantity': 0,
                'uomDisplayName': '',
                'productType': '',
            }

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            if not line.product_uom or not line.product_id:
                line.price_unit = 0.0
            else:
                price = line.material_list_id.pricelist_id._get_product_price(
                    product=line.product_id,
                    quantity=1.0,
                    currency=line.material_list_id.currency_id,
                    date=line.material_list_id.date_order,
                ),
                line.price_unit = price[0]

    @api.depends('product_id', 'product_uom_qty', 'price_unit')
    def _compute_amount(self):
        """
        Compute the amounts of the CLL line.
        """
        for line in self:
            if not line.price_unit or not line.product_id or not line.product_uom_qty:
                line.price_subtotal = 0.0
            else:
                price_subtotal = line.price_unit * line.product_uom_qty
                line.price_subtotal = price_subtotal
