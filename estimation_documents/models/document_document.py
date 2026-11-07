from odoo import models
from urllib.parse import quote


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    _order = 'create_date DESC, id DESC, name ASC'

    def action_preview_drawing_nos(self):
        self.ensure_one()
        document = self
        if not document:
            return False

        return {
            "type": "ir.actions.act_url",
            "url": f"/odoo/documents/{quote(document.access_token, safe="")}",
            "target": "new",
        }