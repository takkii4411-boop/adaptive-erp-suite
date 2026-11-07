from odoo import _, api, Command, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    operation_id = fields.Many2one(
        'mrp.routing.workcenter', 'Operation To Consume', check_company=True,
        domain="[]") # ('id', 'in', allowed_operation_ids) removed for our custom requirement.

    cnc_number = fields.Char(string='CNC Part No')
    log_note = fields.Html(string='Log Note')
    cabinet_no = fields.Char(string="Cabinet No")
    comments = fields.Text(string="Comments")
    worker = fields.Char(string="Worker")
    product_name = fields.Char(string="Product Name", related='product_id.name', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'cnc_number' in vals:
                vals['cnc_number'] = vals['cnc_number'] or False
            if 'log_note' in vals:
                vals['log_note'] = vals['log_note'] or False
        return super().create(vals_list)

    def write(self, vals):
        if 'cnc_number' in vals:
            vals['cnc_number'] = vals['cnc_number'] or False
        if 'log_note' in vals:
            vals['log_note'] = vals['log_note'] or False
        return super().write(vals)

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append('cnc_number')
        distinct_fields.append('log_note')
        distinct_fields.append('comments')
        return distinct_fields

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    cnc_number = fields.Char(string='CNC Part No', related='move_id.cnc_number')
    log_note = fields.Html(string='Log Note', related='move_id.log_note')