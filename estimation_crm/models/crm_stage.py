# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _


class CRMStage(models.Model):
    _inherit = 'crm.stage'

    probability = fields.Float('Probability', aggregator="avg", copy=False)