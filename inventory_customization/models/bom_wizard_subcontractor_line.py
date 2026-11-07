from odoo import api, models, fields


class BomWizardSubContractorLine(models.Model):
    _name = "bom.wizard.subcontractor.line"

    hardware_id = fields.Many2one('material.hardware.details')
    name = fields.Char(string="Name")
    rate = fields.Float(string="Rate")
    uom = fields.Many2one('uom.uom', string="UOM", default=lambda self: self.env.ref('uom.product_uom_unit').id)
    quantity = fields.Float(string="Qty")
    margin = fields.Float(string="Margin (%)", default=0.0)
    subcontractor = fields.Many2one('res.partner', string="Sub-Contractor")
    subtotal = fields.Float(string="Sub-Total", compute='_compute_subtotal')
    currency_id = fields.Many2one(
        "res.currency", related='hardware_id.currency_id'
    )
    estimation_line_id = fields.Many2one("sale.estimation.line", string="Estimation Line")
    product_id = fields.Many2one("product.product", string="Category")
    margin_diff = fields.Float(string="Margin Diff(%)", default=0.0)
    margin_all = fields.Float(string="Margin (%)", default=0.0, compute="_compute_margin_all")
    description = fields.Char(string="Description")

    @api.depends('rate', 'quantity', 'margin', 'margin_diff')
    def _compute_subtotal(self):
        for rec in self:
            cost = rec.rate * rec.quantity
            margin = rec.margin + rec.margin_diff
            if margin >= 100:
                rec.subtotal = cost
            else:
                rec.subtotal = cost / (1 - (margin / 100))

    @api.depends('margin', 'margin_diff')
    def _compute_margin_all(self):
        for rec in self:
            rec.margin_all = rec.margin + rec.margin_diff