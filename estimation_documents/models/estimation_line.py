from odoo import api, fields, models, tools, _


class SaleEstimation(models.Model):
    _inherit = 'sale.estimation'

    def action_open_project_documents(self):
        """Open related project documents in list view."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'documents.document',
            'name': _('Documents'),
            'view_mode': 'kanban,list,form',
            'domain': [
                '|',
                ('type', 'in', ['folder','binary', 'url']),
                '&',
                ('res_model', '=', 'project.project'),
                ('folder_id', '=', self.project_id.documents_folder_id.id),
            ],
            'context': {
                'searchpanel_default_user_folder_id': self.project_id.documents_folder_id.id,
                'default_folder_id': self.project_id.documents_folder_id.id,
                'default_res_model': 'project.project',
                'default_res_id': self.project_id.id,
            },
        }

class SaleEstimationLine(models.Model):
    _inherit = 'sale.estimation.line'

    drawing_nos = fields.Many2many('documents.document', string="Arch Drawing No")
    drawing_nos_domain = fields.Binary(
        string="Drawing No Domain",
        compute="_compute_drawing_nos"
    )

    def _get_tender_documents_folder(self, project):
        """Return the 'Tender Documents' folder under the given project's main folder."""
        if not project or not project.documents_folder_id:
            return False

        document = self.env['documents.document']
        architectural_plans_document_id = document.search([
            ('name', '=', 'Architectural Plans'),
            ('folder_id', '=', project.documents_folder_id.id)
        ], limit=1)

        return document.search([
            ('name', '=', 'Tender Documents'),
            ('folder_id', '=', architectural_plans_document_id.id)
        ], limit=1)

    @api.depends('drawing_nos', 'estimation_id.project_id')
    def _compute_drawing_nos(self):
        """Limit drawing_nos to documents inside the 'Tender Documents' subfolder."""
        for rec in self:
            custom_domain = [('id', '=', 0)]
            project = rec.estimation_id.project_id

            if project:
                tender_folder = rec._get_tender_documents_folder(project)
                if tender_folder:
                    domain = [('folder_id', '=', tender_folder.id)]
                else:
                    domain = custom_domain
            else:
                domain = custom_domain

            rec.drawing_nos_domain = domain

    drawing_nos_limited = fields.Many2many(
        'documents.document',
        string="Arch Drawings (Preview)",
        compute="_compute_drawing_nos_limited",
        store=False,
        readonly=True,
    )

    @api.depends('drawing_nos')
    def _compute_drawing_nos_limited(self):
        for rec in self:
            sorted_drawings = rec.drawing_nos.sorted('name')
            rec.drawing_nos_limited = sorted_drawings[:2]

    def action_edit_drawing_nos(self):
        self.ensure_one()
        domain = self.drawing_nos_domain
        return {
            'name': _('Architectural Drawings'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation.line.drawing.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'drawing_nos_domain': domain,
                'default_order_documents_document': 'create_date DESC',
            },
        }

class SaleEstimationLineDrawingWizard(models.TransientModel):
    _name = 'sale.estimation.line.drawing.wizard'
    _description = 'Select Architectural Drawings'

    line_id = fields.Many2one('sale.estimation.line', required=True, ondelete='cascade')
    drawing_nos = fields.Many2many(
        'documents.document',
        string='Arch Drawing No',
    )
    drawing_nos_domain = fields.Char('Drawing Nos Domain')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        line_id = self.env.context.get('default_line_id')
        domain_from_context = self.env.context.get('drawing_nos_domain', [])
        res['drawing_nos_domain'] = domain_from_context
        if line_id:
            line = self.env['sale.estimation.line'].browse(line_id)
            res['line_id'] = line_id
            if 'drawing_nos' in fields:
                res['drawing_nos'] = [(6, 0, line.drawing_nos.ids)]
        return res

    def action_apply(self):
        self.ensure_one()
        self.line_id.write({'drawing_nos': [(6, 0, self.drawing_nos.ids)]})
        return {'type': 'ir.actions.act_window_close'}
