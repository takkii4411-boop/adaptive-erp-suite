from odoo import api, fields, models, tools, _


class BomWizard(models.Model):
    _inherit = 'bom.wizard'

    shop_drawing_nos = fields.Many2many('documents.document', string="Shop Drawing No")
    shop_drawing_nos_domain = fields.Binary(
        string="Shop Drawing No Domain",
        compute="_compute_shop_drawing_nos"
    )
    joinery_name = fields.Char(string='Joinery Name', related='estimation_line_id.product_id.name')

    @api.depends('shop_drawing_nos', 'estimation_line_id.estimation_id.project_id')
    def _compute_shop_drawing_nos(self):
        """Limit drawing_nos to documents inside 'Current Joinery Drawings' and its subfolders."""
        folder_model = self.env['documents.document']
        for rec in self:
            custom_domain = [('id', '=', 0)]
            project = rec.estimation_line_id.estimation_id.project_id

            if not project:
                rec.shop_drawing_nos_domain = custom_domain
                continue

            # Find the "Current Joinery Drawings" folder
            main_folder = folder_model.search([
                ('name', '=', 'Current Joinery Drawings'),
                ('folder_id', '=', project.documents_folder_id.id)
            ], limit=1)

            if not main_folder:
                rec.shop_drawing_nos_domain = custom_domain
                continue

            # Get all subfolder IDs (recursive)
            def get_all_subfolders(folder):
                subfolders = folder_model.search([('folder_id', '=', folder.id)])
                all_ids = subfolders.ids
                for sub in subfolders:
                    all_ids += get_all_subfolders(sub)
                return all_ids

            all_folder_ids = [main_folder.id] + get_all_subfolders(main_folder)

            # Domain to include documents from all these folders
            domain = [
                ('type', 'in', ['binary', 'url']),
                ('folder_id', 'in', all_folder_ids),
            ]
            rec.shop_drawing_nos_domain = domain