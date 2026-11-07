from odoo import api, fields, models, tools, _


class BomWizardContractor(models.Model):
    _inherit = 'bom.wizard.subcontractor'

    sub_contractor_id = fields.Many2one(
        'sale.sub.contractor',
        string="Related Sub Contractor",
        ondelete='set null'
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            estimation_id = rec.wizard_id._context.get("custom_estimation_id")
            if estimation_id and rec.subcontractor:
                existing_sub = rec.env['sale.sub.contractor'].search([('partner_id', '=', rec.subcontractor.id),('sale_id', '=', estimation_id)])
                if not existing_sub:
                    sub = rec.env['sale.sub.contractor'].create({
                        'partner_id': rec.subcontractor.id,
                        'sale_id': estimation_id,
                    })
                    rec.sub_contractor_id = sub.id

        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            sub = rec.sub_contractor_id
            if not sub:
                continue

            update_vals = {}
            if 'subcontractor' in vals:
                update_vals['partner_id'] = rec.subcontractor.id

            if update_vals:
                sub.write(update_vals)
        return res

    def unlink(self):
        for rec in self:
            if rec.sub_contractor_id:
                rec.sub_contractor_id.unlink()
        return super().unlink()