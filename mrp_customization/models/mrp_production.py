from odoo import models, api, fields
from odoo.fields import Command
from ast import literal_eval


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    _order = 'workorder_no asc, name asc'

    @api.depends('bom_id', 'product_id', 'product_qty', 'product_uom_id', 'never_product_template_attribute_value_ids', 'move_raw_ids', 'move_raw_ids.operation_id',)
    def _compute_workorder_ids(self):
        for production in self:
            if production.state != 'draft':
                continue

            manual_ops = production.move_raw_ids.filtered(lambda m: m.operation_id)
            if not manual_ops:
                super(MrpProduction, production)._compute_workorder_ids()
                continue

            cmds = []

            # UNIQUE operations only
            operations = manual_ops.mapped('operation_id')

            # Existing workorders mapped by operation
            existing_wo_map = {
                wo.operation_id.id: wo
                for wo in production.workorder_ids
                if wo.operation_id
            }

            # Create or update (NO duplicates)
            for operation in operations:
                values = {
                    'name': operation.name,
                    'production_id': production.id,
                    'workcenter_id': operation.workcenter_id.id,
                    'product_uom_id': production.product_uom_id.id,
                    'operation_id': operation.id,
                    'state': 'ready',
                }
                if operation.id in existing_wo_map:
                    cmds.append(
                        Command.update(existing_wo_map[operation.id].id, values)
                    )
                else:
                    cmds.append(Command.create(values))

            # Delete obsolete workorders
            valid_operation_ids = operations.ids
            obsolete_wos = production.workorder_ids.filtered(
                lambda wo: wo.operation_id and wo.operation_id.id not in valid_operation_ids
            )
            cmds += [Command.delete(wo.id) for wo in obsolete_wos]

            production.workorder_ids = cmds

    @api.onchange('move_raw_ids.operation_id')
    def _onchange_move_raw_ids_operation(self):
        if self.state == 'draft':
            self._compute_workorder_ids()


    workorder_no = fields.Char(string="Work Order No",copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        mos = super().create(vals_list)

        for mo in mos:
            # If WO not set and this MO is created from another MO
            if not mo.workorder_no:
                parent_mo = mo._get_parent_mo()
                if parent_mo and parent_mo.workorder_no:
                    mo.workorder_no = parent_mo.workorder_no

        return mos

    def write(self, vals):
        res = super().write(vals)

        if 'workorder_no' in vals:
            for mo in self:
                mo._propagate_workorder_no(vals.get('workorder_no'))

        return res

    def _get_parent_mo(self):
        self.ensure_one()
        move = self.move_dest_ids[:1]
        return move.production_id if move else False

    def _propagate_workorder_no(self, workorder_no, visited=None):
        if not visited:
            visited = self.env['mrp.production']

        visited |= self

        # Auto-created child MOs
        for move in self.move_raw_ids:
            child_mo = move.created_production_id
            if child_mo and child_mo not in visited:
                child_mo.workorder_no = workorder_no
                child_mo._propagate_workorder_no(workorder_no, visited)

        # Existing MOs with same product
        component_products = self.move_raw_ids.mapped('product_id')

        child_mos = self.env['mrp.production'].search([
            ('product_id', 'in', component_products.ids),
            ('id', 'not in', visited.ids),
        ])

        for child_mo in child_mos:
            child_mo.workorder_no = workorder_no
            child_mo._propagate_workorder_no(workorder_no, visited)

    def action_open_shop_floor(self):
        """ Opens shop floor on Overview workcenter with a filter for current MO """
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('mrp_workorder.action_mrp_display')
        action['context'] = literal_eval(action['context']) | {
            'search_default_workorder_no': self.workorder_no,
            'workcenter_id': 0,  # Sets active WC to Overview
            'search_default_blocked': True,
            'shouldHideNewWorkcenterButton': True,
        }

        del action['context']['search_default_filter_ready']
        del action['context']['search_default_filter_workorder_no']
        return action

    @api.model
    def action_open_csv_import_wizard(self):

        view_id = self.env.ref('mrp_customization.mrp_csv_import_wizard_form').id

        return {
            'name': 'Import Components from CSV',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.csv.import.wizard',
            'view_mode': 'form',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
        }

    nesting_report = fields.Binary(string="Nesting Report", attachment=True)
    nesting_report_filename = fields.Char()
    nesting_report_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Nesting Report Attachment",
        compute="_compute_nesting_report_attachment",
        store=True,
        readonly=True
    )

    @api.depends("nesting_report")
    def _compute_nesting_report_attachment(self):
        for rec in self:
            if not rec.nesting_report:
                rec.nesting_report_attachment_id = False
                continue

            if not isinstance(rec.nesting_report, (bytes, bytearray)):
                rec.nesting_report_attachment_id = False
                continue

            attachment_vals = {
                "name": rec.nesting_report_filename,
                "type": "binary",
                "datas": rec.nesting_report,
                "res_model": rec._name,
                "res_id": rec.id,
                "mimetype": "application/pdf",
                "public": True,
            }

            if rec.nesting_report_attachment_id:
                rec.nesting_report_attachment_id.write(attachment_vals)
                attachment = rec.nesting_report_attachment_id
            else:
                attachment = rec.env["ir.attachment"].create(attachment_vals)

            rec.nesting_report_attachment_id = attachment.id

    def action_preview_nesting_report(self):
        self.ensure_one()
        attachment = self.nesting_report_attachment_id
        if not attachment:
            return False

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}/{self.nesting_report_filename}?download=false",
            "target": "new",
        }

    project_count = fields.Integer(string='Number of Projects', compute='_compute_project_count')

    def _compute_project_count(self):
        for rec in self:
            rec.project_count = len(rec.project_id)

    def action_view_projects(self):
        kanban_view_id = self.env.ref('project.view_project_kanban').id
        result = {
            "type": "ir.actions.act_window",
            "res_model": "project.project",
            "views": [[kanban_view_id, "kanban"], [False, "form"]],
            "context": {"create": False},
            "name": "Project",
        }
        if len(self.project_id) == 1:
            result['views'] = [(False, "form")]
            result['res_id'] = self.project_id.id
        return result

    estimation_id = fields.Many2one('sale.estimation', string='Estimation', readonly=True)
    estimation_line_id = fields.Many2one('sale.estimation.line', string='Estimation Line', readonly=True)
    custom_sale_order_id = fields.Many2one('sale.order', string="Sales Order", related='estimation_id.sale_id')

    def action_open_estimation_bom(self):
        """Open the linked Estimation BoM Wizard."""
        self.ensure_one()
        if not self.estimation_line_id:
            return False

        return {
            'name': (self.estimation_line_id.product_id.name if self.estimation_line_id and self.estimation_line_id.product_id else 'Material Summary'),
            'type': 'ir.actions.act_window',
            'res_model': 'bom.wizard',
            'res_id': self.estimation_line_id.source_wizard_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    length = fields.Float(
        string='Length',
        help='Length of the component'
    )
    width = fields.Float(
        string='Width',
        help='Width of the component'
    )
    comment = fields.Char(string='Comment')