# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    estimation_id = fields.Many2one('sale.estimation', string='Estimation', readonly=True)
    builder_ids = fields.Many2many('res.partner', string='Builders', copy=False)
    employee_id = fields.Many2one('hr.employee', string='Estimator', copy=True, tracking=True)
    project_id = fields.Many2one('project.project', string='Project Name', copy=True, tracking=True)
    estimation_count = fields.Integer(string="Estimations", compute="_compute_estimation_count")
    estimation_revenue = fields.Monetary(string="Estimation Revenue",currency_field='company_currency',
                                                 compute="_compute_estimation_revenue", store=True, readonly=False)
    location_qus_id = fields.Many2one('location.qus', string='Location')
    size_qus_id = fields.Many2one('size.qus', string='Size')
    complexity_qus_id = fields.Many2one('complexity.qus', string='Complexity')
    builder_qus_id = fields.Many2one('builder.qus', string='Builder')
    type_qus_id = fields.Many2one('type.qus', string='Type')
    likelihood_qus_id = fields.Many2one('likelihood.qus', string='Likelihood')
    project_criteria_per = fields.Monetary(string="Project Criteria", currency_field='company_currency',
                                         compute="_compute_project_criteria_per", store=True, readonly=False)
    remark = fields.Text(string='Remark')
    lead_type = fields.Selection([
        ('joinery', 'Joinery'),
        ('wholesale', 'Wholesale'),
    ], default='joinery', string="Lead Type")
    opportunity_received_date = fields.Date(string="Opportunity Received Date:")
    proposal_due_date = fields.Date(string="Due Date:")
    expected_project_award_date = fields.Date(string="Expected Project Award Date:")
    expected_project_duration = fields.Integer(string="Expected Project Duration")

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        ctx = dict(self.env.context)

        stage_id = ctx.get("default_stage_id")
        if stage_id:
            stage = self.env["project.project.stage"].browse(stage_id)
            if not stage.exists():
                fallback_stage = self.env.ref(
                    "project.project_project_stage_0", raise_if_not_found=False
                )
                if fallback_stage:
                    ctx["default_stage_id"] = fallback_stage.id

        project_env = self.env["project.project"].with_context(ctx)

        for lead in leads.filtered("name"):
            project = project_env.create({
                "name": lead.name,
                "partner_id": lead.partner_id.id or False,
                "user_id": lead.user_id.id or False,
            })
            lead.project_id = project.id

        return leads

    @api.depends('estimation_id.amount_total')
    def _compute_estimation_revenue(self):
        for lead in self:
            if lead.estimation_id:
                lead.estimation_revenue = lead.estimation_id.amount_total


    @api.depends('estimation_id')
    def _compute_estimation_count(self):
        Estimation = self.env['sale.estimation']
        for lead in self:
            lead.estimation_count = Estimation.search_count(['|',('lead_id', '=', lead._origin.id),('parent_id', '=', self.estimation_id.id)])

    def action_create_estimation(self):
        """Create a new Sale Estimation from this CRM Lead."""
        self.ensure_one()

        # Prevent duplicate estimations
        if self.estimation_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.estimation',
                'view_mode': 'form',
                'res_id': self.estimation_id.id,
                'target': 'current',
            }

        # Prepare builder lines
        builder_lines = [(0, 0, {
            'partner_id': builder.id,
        }) for builder in self.builder_ids]

        # Create estimation
        estimation = self.env['sale.estimation'].create({
            'builder_ids': builder_lines,
            'company_id': self.company_id.id,
            'lead_id': self.id,
            'employee_id': self.employee_id.id,
            'project_id': self.project_id.id,
        })

        # Link back to lead
        self.estimation_id = estimation.id

        # Open the new estimation form
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation',
            'view_mode': 'form',
            'res_id': estimation.id,
            'target': 'current',
        }

    def action_open_estimation(self):
        """Open linked Sale Estimation(s)."""
        self.ensure_one()

        Estimation = self.env['sale.estimation']
        estimations = Estimation.search(['|', ('lead_id', '=', self.id),('parent_id', '=', self.estimation_id.id)])

        if not estimations:
            return False

        action = {
            'name': _('Estimation'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation',
            'target': 'current',
            'context': {'default_lead_id': self.id},
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

    def write(self, vals):
        """Ensure sync even when updated via backend or server actions."""
        res = super(CRMLead, self).write(vals)
        for lead in self:
            if lead.estimation_id:
                lead._update_estimation_from_lead()
        return res

    def _update_estimation_from_lead(self):
        """Helper to create/update estimation data based on lead fields."""
        self.ensure_one()
        estimation = self.estimation_id
        if not estimation:
            return

        # === Sync Project ===
        estimation.project_id = self.project_id.id

        # === Sync Employee ===
        estimation.employee_id = self.employee_id.id

        # === Sync Builders ===
        existing_partner_ids = estimation.builder_ids.mapped('partner_id').ids
        new_partner_ids = self.builder_ids.ids

        # Delete builders that are no longer selected
        to_remove = estimation.builder_ids.filtered(lambda b: b.partner_id.id not in new_partner_ids)
        to_remove.unlink()

        # Create new builder lines for new partners
        for partner in self.builder_ids:
            if partner.id not in existing_partner_ids:
                self.env['sale.builder'].create({
                    'partner_id': partner.id,
                    'sale_id': estimation.id,
                })

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        for rec in self:
            if rec.stage_id:
                rec.probability = rec.stage_id.probability

    @api.depends(
        'location_qus_id.score',
        'size_qus_id.score',
        'complexity_qus_id.score',
        'builder_qus_id.score',
        'type_qus_id.score',
        'likelihood_qus_id.score'
    )
    def _compute_project_criteria_per(self):
        for lead in self:
            total_score = sum([
                lead.location_qus_id.score or 0,
                lead.size_qus_id.score or 0,
                lead.complexity_qus_id.score or 0,
                lead.builder_qus_id.score or 0,
                lead.type_qus_id.score or 0,
                lead.likelihood_qus_id.score or 0,
            ])
            lead.project_criteria_per = (total_score / 60.0) * 100 if total_score else 0.0

class CrmLead2opportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        self.ensure_one()
        if self.lead_id and not self.lead_id.remark and self.lead_id.project_criteria_per < 80:
            raise ValidationError(_('Please select remark to create opportunity.'))
        return super().action_apply()