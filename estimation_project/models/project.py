from odoo import models, api, fields, _


class ProjectProject(models.Model):
    _inherit = "project.project"

    project_number = fields.Char(string="Project Number")
    custom_sale_order_id = fields.Many2one('sale.order', string="Sales Order")
    custom_mrp_ids = fields.Many2many('mrp.production', string="Manufacturing",
                                      compute="_compute_custom_mrp_ids", )
    mrp_count = fields.Integer(
        string="Manufacturing",
        compute="_compute_custom_mrp_ids",
        store=False
    )
    custom_estimation_ids = fields.Many2many('sale.estimation', string="Estimations",
                                      compute="_compute_custom_estimation_ids", )
    estimation_count = fields.Integer(
        string="Estimations",
        compute="_compute_custom_estimation_ids",
        store=False
    )
    delivery_ids = fields.Many2many(
        'stock.picking',
        string="Deliveries",
        compute="_compute_transfer_counts"
    )

    receipt_ids = fields.Many2many(
        'stock.picking',
        string="Receipts",
        compute="_compute_transfer_counts"
    )

    delivery_count = fields.Integer(
        string="Deliveries",
        compute="_compute_transfer_counts"
    )

    receipt_count = fields.Integer(
        string="Receipts",
        compute="_compute_transfer_counts"
    )
    sale_order_count = fields.Integer(
        string="Sales Order",
        compute="_compute_sale_order_count",
        store=False
    )

    @api.depends('custom_sale_order_id')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = 1 if rec.custom_sale_order_id else 0

    @api.depends('project_number')
    def _compute_custom_mrp_ids(self):
        for rec in self:
            if rec.project_number:
                mrp_orders = self.env['mrp.production'].search(
                    [('project_id', '=', rec.id)])
                rec.custom_mrp_ids = [(6, 0, mrp_orders.ids)]
                rec.mrp_count = len(rec.custom_mrp_ids) if rec.custom_mrp_ids else 0
            else:
                rec.custom_mrp_ids = []
                rec.mrp_count = 0

    def action_open_mrp(self):
        self.ensure_one()
        if not self.custom_mrp_ids:
            return False

        return {
            'name': _('Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.custom_mrp_ids.ids)],
            'target': 'current',
        }

    @api.depends('project_number')
    def _compute_custom_estimation_ids(self):
        for rec in self:
            if rec.project_number:
                mrp_orders = self.env['sale.estimation'].search(
                    [('project_id', '=', rec.id)])
                rec.custom_estimation_ids = [(6, 0, mrp_orders.ids)]
                rec.estimation_count = len(rec.custom_estimation_ids) if rec.custom_estimation_ids else 0
            else:
                rec.custom_estimation_ids = []
                rec.estimation_count = 0

    def action_open_estimations(self):
        self.ensure_one()
        if not self.custom_estimation_ids:
            return False

        return {
            'name': _('Estimations'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.custom_estimation_ids.ids)],
            'target': 'current',
        }

    @api.depends('project_number')
    def _compute_transfer_counts(self):
        for rec in self:
            deliveries = self.env['stock.picking'].search([
                ('project_id', '=', rec.id),
                ('picking_type_id.code', '=', 'outgoing')
            ])

            receipts = self.env['stock.picking'].search([
                ('project_id', '=', rec.id),
                ('picking_type_id.code', '=', 'incoming')
            ])

            rec.delivery_ids = [(6, 0, deliveries.ids)]
            rec.receipt_ids = [(6, 0, receipts.ids)]
            rec.delivery_count = len(deliveries) + len(rec.custom_sale_order_id.picking_ids - deliveries)
            rec.receipt_count = len(receipts)

    def action_open_deliveries(self):
        self.ensure_one()
        return {
            'name': _('Deliveries'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.delivery_ids.ids + self.custom_sale_order_id.picking_ids.ids)],
            'target': 'current',
        }

    def action_open_receipts(self):
        self.ensure_one()
        return {
            'name': _('Receipts'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.receipt_ids.ids)],
            'target': 'current',
        }

    def action_open_sale_order(self):
        """Open the linked Sales Order."""
        self.ensure_one()
        if not self.custom_sale_order_id:
            return False

        return {
            'name': _('Sales Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.custom_sale_order_id.id,
            'target': 'current',
        }