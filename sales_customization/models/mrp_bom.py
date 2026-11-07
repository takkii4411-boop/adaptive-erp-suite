from odoo import models, fields, api, _

class MrpBom(models.Model):
    _inherit = "mrp.bom"

    shop_ids = fields.One2many('bom.wizard.operation', 'bom_id', string='Shops')