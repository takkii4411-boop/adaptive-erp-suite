from odoo import models, fields

class EstimationSubtaskTemplate(models.Model):
    _name = "estimation.subtask.template"
    _description = "Estimation Project Subtask Template"
    _order = "sequence, id"

    name = fields.Char(
        string="Subtask Name",
        required=True
    )

    sequence = fields.Integer(
        default=10,
        help="Controls the order of subtask creation"
    )

    active = fields.Boolean(
        default=True
    )