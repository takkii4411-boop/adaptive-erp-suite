from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstimationExclusion(models.Model):
    _name = "estimation.exclusion"
    _description = "Estimation Exclusion"

    name = fields.Char(string='Name', required=True)
    joinery_type = fields.Selection([
        ('joinery', 'Joinery'),
        ('wholesale', 'Wholesale')
    ], string='Joinery Type', default='joinery', required=True)

    exclusion = fields.Html(string='Exclusion')

    @api.model
    def create(self, vals):
        joinery_type = vals[0].get('joinery_type')

        if joinery_type:
            existing = self.search([('joinery_type', '=', joinery_type)], limit=1)
            if existing:
                raise ValidationError(
                    f"An exclusion record already exists for '{dict(self._fields['joinery_type'].selection)[joinery_type]}' type. "
                    "You can only have one per type. Edit the existing one instead."
                )

        return super(EstimationExclusion, self).create(vals)

    def write(self, vals):
        if 'joinery_type' in vals:
            for rec in self:
                if rec.joinery_type != vals['joinery_type']:
                    existing = self.search([
                        ('joinery_type', '=', vals['joinery_type']),
                        ('id', '!=', rec.id)
                    ], limit=1)
                    if existing:
                        raise ValidationError(
                            f"Cannot change to '{dict(self._fields['joinery_type'].selection)[vals['joinery_type']]}' "
                            "because a record already exists for that type."
                        )
        return super().write(vals)