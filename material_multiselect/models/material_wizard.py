from odoo import models, fields, api

class MaterialMultiSelectWizard(models.TransientModel):
    _name = 'material.multiselect.wizard'
    _description = 'Select Multiple Materials'

    material_list_id = fields.Many2one('material.list', string='Material List')
    product_ids = fields.Many2many(
        'product.product',
        string='Materials',
    )

    product_domain = fields.Binary(
        string="Product Domain",
        compute="_compute_product_domain"
    )

    @api.depends('material_list_id')
    @api.onchange('material_list_id')
    def _compute_product_domain(self):
        """Exclude already-selected products from the same material list."""
        for rec in self:
            domain = []
            if rec.material_list_id:
                selected_product_ids = rec.material_list_id.material_line_ids.mapped('product_id').ids
                if selected_product_ids:
                    domain = [('id', 'not in', selected_product_ids)]
            rec.product_domain = domain

    def action_add_materials(self):
        """Create material lines for selected products"""
        self.ensure_one()
        if not self.material_list_id:
            return

        MaterialLine = self.env['material.list.line']
        for product in self.product_ids:
            MaterialLine.create({
                'material_list_id': self.material_list_id.id,
                'product_id': product.id,
                'old_product_id': product.id,
                'rate': product.standard_price or 0.0,
            })
