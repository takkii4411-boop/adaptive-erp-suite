from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    sale_chatter_position = fields.Selection(
        [
            ("auto", "Responsive"),
            ("bottom", "Bottom"),
            ("sided", "Sided"),
        ],
        default="bottom",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["sale_chatter_position"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["sale_chatter_position"]