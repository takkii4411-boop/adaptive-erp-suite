from odoo import models, fields, api, _
import ast


class StockPicking(models.Model):
    _inherit = "stock.picking"

    custom_project_task_count = fields.Integer(
        string="Tasks",
        compute="_compute_project_task_count"
    )
    custom_project_count = fields.Integer(
        string="Projects",
        compute="_compute_project_task_count"
    )
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")

    def _compute_project_task_count(self):
        Task = self.env["project.task"]
        for rec in self:
            rec.custom_project_task_count = Task.search_count([
                ("project_id", "=", rec.project_id.id)
            ]) if rec.project_id else 0
            rec.custom_project_count = len(rec.project_id) if rec.project_id else 0

    def action_custom_view_project_ids(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].with_context(active_id=self.project_id.id)._for_xml_id(
            'project.act_project_project_2_project_task_all')
        action['display_name'] = self.project_id.name
        context = action['context'].replace('active_id', str(self.project_id.id))
        context = ast.literal_eval(context)
        context.update({
            'create': False,
            'active_test': self.project_id.active,
            'active_id': self.project_id.id,
            'allow_milestones': self.project_id.allow_milestones,
            'allow_task_dependencies': self.project_id.allow_task_dependencies,
        })
        action['context'] = context
        if self.project_id.is_template:
            action['context'].update({'template_project': True})
            action['views'] = [(view_id, view_type) for view_id, view_type in action['views'] if
                               view_type not in ('pivot', 'graph')]
        return action
