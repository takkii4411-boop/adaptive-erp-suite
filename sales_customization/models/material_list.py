from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.http import request
from urllib.parse import urlparse


class MaterialList(models.Model):
    _name = "material.list"
    _inherit = ['product.catalog.mixin']

    order_line = fields.One2many('material.list.line', 'material_list_id', string='Material Line')
    estimation_id = fields.Many2one("sale.estimation", string="Estimation")
    project_id = fields.Many2one("project.project", string="Project")
    state = fields.Selection([('draft', 'Draft'), ('sent', 'In Review'), ('done', 'Approved'), ('cancel', 'Cancelled')], string='Status', default='draft')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    pricelist_id = fields.Many2one('product.pricelist')
    date_order = fields.Datetime(
        string="Order Date", copy=False,
        help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.",
        default=fields.Datetime.now)

    def action_save_material_record(self):
        """On save, sync all material lines with their linked BOM components."""
        for line in self.order_line:
            line._sync_bom_components()
        return {'type': 'ir.actions.act_window_close'}

    def action_go_back(self):
        estimation_id = self.env.context.get('estimation_id')
        material_id = self.get_material_id()
        bom_material_id = self.browse(material_id)
        if bom_material_id.exists():
            estimation = self.env["sale.estimation"].search([
                ("material_list_id", "=", self.id),
            ], limit=1)
            estimation_id = bom_material_id.estimation_id.id or estimation.id
        if not estimation_id:
            return {
                'type': 'ir.actions.act_window_close',
            }

        view_id = self.env.ref('sales_customization.view_sale_estimation_type_form').id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation',
            'res_id': estimation_id,
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'main',
            'context': {
                'from_product_catalog': False,
                'expand': True,
            },
        }

    def get_material_id(self):
        referrer = request.httprequest.referrer
        if not referrer:
            return False

        path = urlparse(referrer).path
        parts = path.strip('/').split('/')

        try:
            model = parts[1]
            record_id = int(parts[2])
            if model == 'material.list':
                return record_id
        except (IndexError, ValueError):
            return False

        return False


class MaterialListLine(models.Model):
    _name = "material.list.line"
    _inherit = ['product.catalog.mixin']
    _order = "sequence, id"

    material_list_id = fields.Many2one("material.list", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Material Name")
    old_product_id = fields.Many2one("product.product", string="Old Material Name")
    code = fields.Char(string="Material Code")
    rate = fields.Float(string="Rate", related='product_id.standard_price')
    product_uom_qty = fields.Float()
    price_unit = fields.Float(compute='_compute_price_unit')
    name = fields.Char(related='product_id.name', string='Description')
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', related='product_id.uom_id')
    price_subtotal = fields.Float(string="Subtotal", compute='_compute_amount', store=True)
    sequence = fields.Integer(string='No.')
    product_domain = fields.Binary(
        string="Product Domain",
        compute="_compute_product_domain"
    )

    @api.depends('product_id', 'material_list_id.order_line.product_id')
    def _compute_product_domain(self):
        """Hide already-selected products from dropdown in the same material list."""
        for rec in self:
            domain = [('bom_ids', '=', False),('type', '!=', 'service')]

            if rec.material_list_id:
                selected_products = rec.material_list_id.order_line.mapped('product_id').ids
                if selected_products:
                    selected_domain = ('id', 'not in', [pid for pid in selected_products if pid != rec.product_id.id])
                    domain.append(selected_domain)

            rec.product_domain = domain

    def _sync_bom_components(self):
        """Sync all material lines with corresponding BOM wizard components."""
        for rec in self:
            estimation_id = rec._context.get("custom_estimation_id")
            estimation = self.env['sale.estimation'].browse(estimation_id)
            if not estimation:
                continue

            estimation_lines = estimation.estimation_line_ids.filtered(lambda l: l.source_wizard_id)

            for est_line in estimation_lines:
                bom_wizard = est_line.source_wizard_id
                if not bom_wizard:
                    continue

                # Find matching component in this BoM wizard
                component = bom_wizard.component_ids.filtered(
                    lambda c: c.product_id.id in [rec.old_product_id.id, rec.product_id.id]
                )

                if component:
                    component = component[0]
                    component.product_id = rec.product_id.id
                    component.arch_code = rec.code or ''
                    component.sequence = rec.sequence

    @api.onchange('product_id', 'code')
    def _onchange_product_and_code(self):
        for rec in self:
            rec._sync_bom_components()

    @api.model_create_multi
    def create(self, vals_list):
        rec = super().create(vals_list)
        for line in rec:
            line.old_product_id = line.product_id
            line._sync_bom_components()
        return rec

    def write(self, vals):
        for rec in self:
            if 'product_id' in vals:
                rec.old_product_id = rec.product_id
        res = super().write(vals)
        self._sync_bom_components()
        return res

    def unlink(self):
        for rec in self:
            estimation_id = rec._context.get("custom_estimation_id")
            estimation = self.env['sale.estimation'].browse(estimation_id)
            if not estimation:
                continue

            estimation_lines = estimation.estimation_line_ids.filtered(lambda l: l.source_wizard_id)

            for est_line in estimation_lines:
                bom_wizard = est_line.source_wizard_id
                if not bom_wizard:
                    continue

                # Find matching component in this BoM wizard
                component = bom_wizard.component_ids.filtered(
                    lambda c: c.product_id.id in [rec.old_product_id.id, rec.product_id.id]
                )
                if component:
                    raise ValidationError(
                        "You cannot delete this line because the product "
                        f"'{rec.product_id.display_name}' used in the BOM of joinery items."
                    )

        return super().unlink()
