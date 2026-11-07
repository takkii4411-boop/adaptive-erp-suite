from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleBuilder(models.Model):
    _name = "sale.builder"

    partner_id = fields.Many2one('res.partner', string='Name')
    sale_id = fields.Many2one('sale.estimation', string='Estimation')
    status = fields.Selection([('win', 'Win'), ('on_hold', 'On Hold'), ('loss', 'Loss')], string='Status')
    winner = fields.Boolean(string='Winner')
    is_client = fields.Boolean(string='Is Client', default=False)
    is_mail_sent = fields.Boolean(string='Is Mail sent', default=False)

    partner_domain = fields.Binary(
        string="Subcontractor Domain",
        compute="_compute_partner_id_domain"
    )

    @api.depends('partner_id')
    def _compute_partner_id_domain(self):
        """Compute JSON version of the domain for product_id."""
        for rec in self:
            domain = []
            selected_products = rec.sale_id.builder_ids.mapped('partner_id').ids
            if selected_products:
                selected_domain = ('id', 'not in',
                                   [pid for pid in selected_products if pid != rec.partner_id.id])
                domain.append(selected_domain)

            rec.partner_domain = domain

    @api.onchange('is_client')
    def _onchange_is_client(self):
        """Allow only one builder as Client (live effect in O2M)."""
        for rec in self:
            if rec.is_client and rec._origin:
                all_builders = rec._origin.sale_id.builder_ids if rec._origin.sale_id else rec.sale_id.builder_ids
                for builder in all_builders:
                    if builder != rec:
                        builder.is_client = False

    @api.onchange('winner')
    def _onchange_winner(self):
        """Allow only one builder as Winner (live effect in O2M)."""
        for rec in self:
            if rec.winner and rec._origin:
                all_builders = rec._origin.sale_id.builder_ids if rec._origin.sale_id else rec.sale_id.builder_ids
                for builder in all_builders:
                    if builder != rec:
                        builder.winner = False

    @api.constrains('is_client', 'sale_id')
    def _check_single_client(self):
        for rec in self:
            if rec.is_client:
                duplicates = self.search([
                    ('sale_id', '=', rec.sale_id.id),
                    ('is_client', '=', True),
                    ('id', '!=', rec.id)
                ])
                if duplicates:
                    raise ValidationError(_("Only one builder can be selected as Client."))

    @api.constrains('winner', 'sale_id')
    def _check_single_winner(self):
        for rec in self:
            if rec.winner:
                duplicates = self.search([
                    ('sale_id', '=', rec.sale_id.id),
                    ('winner', '=', True),
                    ('id', '!=', rec.id)
                ])
                if duplicates:
                    raise ValidationError(_("Only one builder can be selected as Winner."))