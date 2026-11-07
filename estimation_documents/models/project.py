from odoo import models, api

FOLDER_STRUCTURE = {
    'Architectural Plans': {
        'Joinery Extract': {},
        'Specifications': {},
        'Tender Documents': {},
    },
    'Builders Timeline': {},
    'Current Joinery Drawings': {
        'MV Files': {},
        'Site Measurements': {},
        'Superseded': {},
    },
    'Contract': {
        'Quote': {},
        'SS Contract': {},
    },
    'dwg files': {},
    'Insurances': {
        'SS': {},
    },
    'ITP': {},
    'Manuals and Warranties': {},
    'Marketing Case Study': {},
    'Meetings and Emails': {},
    'Photos': {},
    'Progress Claims': {
        'SS': {},
    },
    'Safety': {},
    'Samples Submission': {},
    'Site': {},
    'Subbies and Suppliers': {
        'Supplier Quotes': {},
    },
    'Variations': {},
    'WOR and NR Reports': {},
}


class ProjectProject(models.Model):
    _inherit = "project.project"

    @api.model_create_multi
    def create(self, vals_list):
        project = super().create(vals_list)
        project._create_project_folders()
        return project

    def _create_project_folders(self):
        """Create full folder hierarchy for a project."""
        self.ensure_one()
        folder_model = self.env['documents.document']
        if not self.documents_folder_id:
            return

        parent_field = 'folder_id'

        def create_subfolders(parent_id, structure_dict):
            for folder_name, subfolders in structure_dict.items():
                values = {'name': folder_name, 'folder_id': self.documents_folder_id.id, 'type': 'folder'}
                if parent_field:
                    values[parent_field] = parent_id
                new_folder = folder_model.create(values)
                if subfolders:
                    create_subfolders(new_folder.id, subfolders)

        create_subfolders(self.documents_folder_id.id, FOLDER_STRUCTURE)