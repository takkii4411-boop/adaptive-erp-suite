from odoo import models, fields, api, _
from odoo.exceptions import UserError
import ast


class SaleEstimation(models.Model):
    _inherit = "sale.estimation"

    project_id = fields.Many2one("project.project", string="Project")
    project_task_count = fields.Integer(
        string="Tasks",
        compute="_compute_project_task_count"
    )
    project_count = fields.Integer(
        string="Projects",
        compute="_compute_project_task_count"
    )

    def _compute_project_task_count(self):
        Task = self.env["project.task"]
        for rec in self:
            rec.project_task_count = Task.search_count([
                ("project_id", "=", rec.project_id.id)
            ]) if rec.project_id else 0
            rec.project_count = len(rec.project_id) if rec.project_id else 0

    def _get_estimation_hierarchy(self):
        self.ensure_one()
        records = self

        parent = self.parent_id
        while parent:
            records |= parent
            parent = parent.parent_id

        def _get_children(rec):
            result = rec.child_ids
            for child in rec.child_ids:
                result |= _get_children(child)
            return result

        records |= _get_children(self)
        return records

    def action_confirm(self):
        for rec in self:
            if not rec.estimation_line_ids:
                raise UserError(_(
                    "Please add at least one joinery item line to confirm."
                ))
            hierarchy = rec._get_estimation_hierarchy()

            if hierarchy.filtered(lambda r: r.status == "done"):
                raise UserError(_(
                    "You cannot confirm this estimation because one or more related estimations "
                    "in its hierarchy are already approved."
                ))

        res = super().action_confirm()

        for rec in self:
            rec._create_project_tasks()
            if rec.project_id:
                rec.project_id.project_number = rec.name.replace("E", "P")

        return res

    def _create_project_tasks(self):
        Task = self.env["project.task"]
        Attachment = self.env["ir.attachment"]
        SubtaskTemplate = self.env["estimation.subtask.template"]

        templates = SubtaskTemplate.search([("active", "=", True)], order="sequence")

        for estimation in self:
            if not estimation.project_id:
                raise UserError(_("Please assign a Project before approving the Estimation."))

            attachments = Attachment.search([
                ("res_model", "=", estimation._name),
                ("res_id", "=", estimation.id),
            ])

            for line in estimation.estimation_line_ids:
                # MAIN TASK
                main_task = Task.create({
                    "name": line.product_id.name,
                    "project_id": estimation.project_id.id,
                    "description": _("Auto-created from Estimation %s") % estimation.name,
                })

                estimation._copy_attachments(attachments, main_task)

                for template in templates:
                    subtask = Task.create({
                        "name": f"{template.name} (Sub Task)",
                        "project_id": estimation.project_id.id,
                        "parent_id": main_task.id,
                    })

                    estimation._copy_attachments(attachments, subtask)

    def _copy_attachments(self, attachments, task):
        for att in attachments:
            att.copy({
                "res_model": "project.task",
                "res_id": task.id,
            })

    def action_open_project(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].with_context(active_id=self.project_id.id)._for_xml_id('project.act_project_project_2_project_task_all')
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
            action['views'] = [(view_id, view_type) for view_id, view_type in action['views'] if view_type not in ('pivot', 'graph')]
        return action

    def action_update(self):
        for rec in self:
            hierarchy = rec._get_estimation_hierarchy()

            if hierarchy.filtered(lambda r: r.status == "done"):
                raise UserError(_(
                    "You cannot update this estimation because one or more related estimations "
                    "in its hierarchy are already approved."
                ))

        return super().action_update()

    def _update_sale_from_estimation(self):
        res = super()._update_sale_from_estimation()
        for rec in self:
            if rec.sale_id and rec.project_id:
                rec.project_id.custom_sale_order_id = rec.sale_id.id
        return res