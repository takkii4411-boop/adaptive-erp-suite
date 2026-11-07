# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import ast


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    delivery_instruction = fields.Html(string='Delivery Instructions')