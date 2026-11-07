from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstimationMargin(models.Model):
    _name = "estimation.margin"

    name = fields.Selection(
        [('materials_hardware', 'Materials & hardware'), ('sub_contractors', 'Sub-contractors'), ('shops', 'Shops')],
        string='Name')
    margin = fields.Float(string='Margin')

    @api.model_create_multi
    def create(self, vals_list):
        margin_ids = self.env['estimation.margin'].sudo().search([])
        existing_margins = margin_ids.mapped('name') if margin_ids else False
        if existing_margins and vals_list[0]['name'] in existing_margins:
            raise ValidationError(f'This name is already exist!')
        return super().create(vals_list)