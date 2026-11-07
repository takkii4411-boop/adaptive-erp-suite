from odoo import api, fields, models, _


class MrpImportLog(models.Model):
    _name = 'mrp.import.log'
    _description = 'MRP CSV Import Log'
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    file_name = fields.Char(string='File Name', readonly=True)
    status = fields.Selection(
        [('success', 'Success'), ('fail', 'Failed')],
        string='Status',
        required=True,
        readonly=True,
    )
    message = fields.Text(string='Message', readonly=True)
    mo_count = fields.Integer(string='MOs Created', readonly=True, default=0)
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('mrp.import.log') or _('New')
        return super().create(vals_list)