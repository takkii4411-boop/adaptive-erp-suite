from odoo import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = "product.product"

    project_id = fields.Many2one('project.project', string='Project Name', copy=False)
    joinery_type = fields.Selection([('material', 'Material'), ('joinery', 'Joinery'), ('wholesale', 'Wholesale')], string='Joinery Type', default='material', required=True)
    supplier_name = fields.Char(string='Supplier', compute='_compute_supplier_name')
    supplier_price = fields.Float(string='Supplier Price', compute='_compute_supplier_name')

    @api.model_create_multi
    def create(self, vals_list):
        res_list = super(ProductProduct, self).create(vals_list)
        material_list = False
        res_model = self.env.context.get('res_model')
        order_id = self.env.context.get('order_id')
        custom_estimation_id = self.env.context.get('custom_estimation_id')
        is_created_from_catalog = self.env.context.get('is_created_from_catalog')
        if is_created_from_catalog:
            estimation = self.env['sale.estimation'].browse(custom_estimation_id)
            if estimation:
                material_list = self.env['material.list'].search([("project_id", "=", estimation.project_id.id)])
                if res_model == 'material.list':
                    if material_list:
                        material_list._update_order_line_info(res_list.id, 1)
                if res_model == 'bom.wizard':
                    bom_wizard = self.env['bom.wizard'].browse(order_id)
                    if bom_wizard:
                        bom_wizard._update_order_line_info(res_list.id, 1)
        for product in res_list:
            if res_model == 'bom.wizard' and material_list:
                self.env['material.list.line'].sudo().create({
                    'material_list_id': material_list.id,
                    'product_id': product.id,
                    'product_uom_qty': 0.0,
                })
            self._set_category(product)
            self._ensure_bom(product)
            self._ensure_shop_ids(product)

        return res_list

    def write(self, vals):
        res = super().write(vals)

        if "joinery_type" in vals:
            for product in self:
                template = product.product_tmpl_id
                if template.joinery_type != product.joinery_type:
                    template.write({"joinery_type": product.joinery_type})

                self._set_category(product)
                self._ensure_bom(product)
                self._ensure_shop_ids(product)
                bom = self.env["mrp.bom"]._bom_find(product)
                bom_id = bom[product]
                if bom_id:
                    if product.joinery_type != "wholesale":
                        bom_id.write({"shop_ids": [(5, 0, 0)]})
                    if product.joinery_type == "material":
                        bom_id.unlink()

        return res

    def _set_category(self, product):
        """Set wholesale category if wholesale. Remove if not."""
        categ = self.env.ref('sales_customization.categ_wholesale', raise_if_not_found=False)

        if product.joinery_type == "wholesale":
            if categ and product.categ_id != categ:
                product.categ_id = categ.id
        else:
            # If not wholesale → remove category
            if product.categ_id:
                product.categ_id = False

    def _ensure_bom(self, product):
        """BoM must exist for ALL types."""
        if product.joinery_type == "material":
            return

        Bom = self.env["mrp.bom"]
        bom = Bom._bom_find(product)
        if bom:
            return bom

        bom = Bom.create({
            "product_tmpl_id": product.product_tmpl_id.id,
            "product_id": product.id,
            "type": "normal",
            "bom_line_ids": [],
            "operation_ids": [],
            "shop_ids": [],
        })
        return bom

    def _ensure_shop_ids(self, product):
        """Add shop lines ONLY for wholesale, and only if empty."""
        if product.joinery_type != "wholesale":
            return

        Bom = self.env["mrp.bom"]
        bom = Bom._bom_find(product)
        bom_id = bom[product]
        if not bom_id:
            return

        if bom_id.shop_ids:
            return

        bom_id.write({"shop_ids": self._generate_shop_ids()})

    def _generate_shop_ids(self):
        """Generate shop_ids lines."""
        Shop = self.env["sale.estimation.shop"]
        shops = Shop.search([])
        result = []

        for shop in shops:
            result.append((
                0, 0, {
                "name": shop.name,
                "product_id": shop.product_id.id,
                "workcenter_id": False,
                "duration": 0.0,
                "rate": shop.product_id.standard_price,
                "quantity": 0.0,
            }
            ))
        return result

    def get_formview_action(self, access_uid=None):
        res = super().get_formview_action(access_uid=access_uid)
        if self.bom_ids:
            res_id = self.bom_ids.filtered(lambda obj: obj.product_tmpl_id.id == self.product_tmpl_id.id)
            res.update({
                'name': self.name,
                'res_model': 'mrp.bom',
                'view_mode': 'form',
                'views': [(False, 'form')],
                'res_id': res_id[0].id,
            })
        return res

    @api.depends('seller_ids')
    def _compute_supplier_name(self):
        for rec in self:
            if rec.seller_ids:
                rec.supplier_name = rec.seller_ids[0].partner_id.name
                rec.supplier_price = rec.seller_ids[0].price
            else:
                rec.supplier_name = ""
                rec.supplier_price = ""

    @api.onchange('joinery_type')
    def _onchange_joinery_type_warning(self):
        if not self._origin:
            return

        old = self._origin.joinery_type
        new = self.joinery_type

        if old == new:
            return

        title = _("Warning")
        details = _(
            "You changed Joinery Type from %s to %s."
        ) % (old.upper(), new.upper())

        if new == "wholesale":
            effect = _("\nWholesale category and shop details will be applied automatically.")
        else:
            effect = _("\nWholesale category and shop details have been removed.")

        message = details + effect

        return {
            'warning': {
                'title': title,
                'message': message,
            }
        }