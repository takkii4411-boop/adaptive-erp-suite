import re
from odoo import models, fields, api


class ResUser(models.Model):
    _inherit = 'res.users'

    def remove_html_tags(self, text):
        """Remove all HTML tags from the given text string."""
        if not text:
            return ''
        if 'img' in text:
            return 'img'
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)