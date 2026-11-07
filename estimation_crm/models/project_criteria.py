from odoo import api, fields, models, tools, _


class QuestionBase(models.Model):
    _name = 'question.base'
    _description = 'Base model for all question models'

    name = fields.Char(string='Question')
    model = fields.Char(string='Model')

    def action_open_view(self):
        self.ensure_one()
        action = {
            'name': _(self.name),
            'type': 'ir.actions.act_window',
            'res_model': self.model,
            'view_mode': 'list,form',
            'views': [(False, 'list'),(False, 'form')],
            'target': 'current',
        }
        return action

class LocationQus(models.Model):
    _name = 'location.qus'

    name = fields.Char(string='Description', required=True)
    score = fields.Integer(string='Score')
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('name', 'score')
    def _compute_display_name(self):
        for record in self:
            display_name = f"{record.name} = {record.score}"
            record.display_name = display_name


class SizeQus(models.Model):
    _name = 'size.qus'

    name = fields.Char(string='Description', required=True)
    score = fields.Integer(string='Score')
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('name', 'score')
    def _compute_display_name(self):
        for record in self:
            display_name = f"{record.name} = {record.score}"
            record.display_name = display_name

class ComplexityQus(models.Model):
    _name = 'complexity.qus'

    name = fields.Char(string='Description', required=True)
    score = fields.Integer(string='Score')
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('name', 'score')
    def _compute_display_name(self):
        for record in self:
            display_name = f"{record.name} = {record.score}"
            record.display_name = display_name

class BuilderQus(models.Model):
    _name = 'builder.qus'

    name = fields.Char(string='Description', required=True)
    score = fields.Integer(string='Score')
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('name', 'score')
    def _compute_display_name(self):
        for record in self:
            display_name = f"{record.name} = {record.score}"
            record.display_name = display_name

class TypeQus(models.Model):
    _name = 'type.qus'

    name = fields.Char(string='Description', required=True)
    score = fields.Integer(string='Score')
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('name', 'score')
    def _compute_display_name(self):
        for record in self:
            display_name = f"{record.name} = {record.score}"
            record.display_name = display_name

class LikelihoodQus(models.Model):
    _name = 'likelihood.qus'

    name = fields.Char(string='Description', required=True)
    score = fields.Integer(string='Score')
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('name', 'score')
    def _compute_display_name(self):
        for record in self:
            display_name = f"{record.name} = {record.score}"
            record.display_name = display_name