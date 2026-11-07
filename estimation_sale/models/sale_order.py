# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
import ast


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    estimation_id = fields.Many2one('sale.estimation', string='Estimation', readonly=True)
    estimation_count = fields.Integer(string="Estimations", compute="_compute_estimation_count")
    employee_id = fields.Many2one('hr.employee', string='Estimator', copy=True, tracking=True)
    project_id = fields.Many2one('project.project', string='Project Name', copy=True, tracking=True, required=True)
    project_type_id = fields.Many2one('sale.project.type', string='Type', copy=True, tracking=True)
    joinery_type = fields.Selection([('joinery', 'Joinery'), ('wholesale', 'Wholesale')], string='Joinery Type')
    custom_project_task_count = fields.Integer(
        string="Tasks",
        compute="_compute_project_task_count"
    )
    custom_project_count = fields.Integer(
        string="Projects",
        compute="_compute_project_task_count"
    )
    opportunity_count = fields.Integer(
        string="Opportunities",
        compute="_compute_opportunity_count",
        store=False
    )
    custom_mrp_ids = fields.Many2many('mrp.production', string="Manufacturing", compute="_compute_custom_mrp_ids",)
    mrp_count = fields.Integer(
        string="Manufacturing",
        compute="_compute_custom_mrp_ids",
        store=False
    )

    @api.depends('estimation_id')
    def _compute_estimation_count(self):
        Estimation = self.env['sale.estimation']
        for order in self:
            order.estimation_count = Estimation.search_count(['|',('sale_id', '=', order.id),('parent_id', '=', self.estimation_id.id)])

    def action_open_estimation(self):
        """Open linked Sale Estimation(s)."""
        self.ensure_one()

        Estimation = self.env['sale.estimation']
        estimations = Estimation.search(['|', ('sale_id', '=', self.id),('parent_id', '=', self.estimation_id.id)])

        if not estimations:
            return False

        action = {
            'name': _('Estimation'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation',
            'target': 'current',
            'context': {'default_sale_id': self.id},
        }

        if len(estimations) == 1:
            # Open single estimation in form view
            action.update({
                'view_mode': 'form',
                'res_id': estimations.id,
            })
        else:
            # Open multiple estimations in tree + form view
            action.update({
                'view_mode': 'list,form',
                'views': [(False, 'list'),(False, 'form')],
                'domain': [('id', 'in', estimations.ids)],
            })

        return action

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

    @api.depends('opportunity_id')
    def _compute_opportunity_count(self):
        for rec in self:
            rec.opportunity_count = 1 if rec.opportunity_id else 0

    def action_open_opportunity(self):
        """Open the linked CRM Opportunity."""
        self.ensure_one()
        if not self.opportunity_id:
            return False

        return {
            'name': _('Opportunity'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.opportunity_id.id,
            'target': 'current',
        }

    @api.depends('project_id')
    def _compute_custom_mrp_ids(self):
        for rec in self:
            if rec.project_id:
                mrp_orders = self.env['mrp.production'].search(['|', ('project_id', '=', rec.project_id.id), ('custom_sale_order_id', '=', rec.id)])
                rec.custom_mrp_ids = [(6, 0, mrp_orders.ids)]
                rec.mrp_count = len(rec.custom_mrp_ids) + len(rec.mrp_production_ids) if rec.custom_mrp_ids else 0
            else:
                rec.custom_mrp_ids = []
                rec.mrp_count = 0

    def action_open_mrp(self):
        """Open the linked CRM Opportunity."""
        self.ensure_one()
        if not self.custom_mrp_ids:
            return False

        return {
            'name': _('Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': ['|', ('id', 'in', self.custom_mrp_ids.ids + self.mrp_production_ids.ids), ('custom_sale_order_id', '=', self.id)],
            'target': 'current',
        }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self.mrp_production_ids:
            if self.project_id:
                rec.project_id = self.project_id.id
        return res