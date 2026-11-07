from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
from urllib.parse import urlparse


class BomWizard(models.Model):
    _name = "bom.wizard"
    _inherit = ['product.catalog.mixin']
    _description = "BOM Wizard"

    def _subcontractor_ids(self):
        domain = []
        if self:
            for rec in self:
                if rec.filter_product_id:
                    domain.append(('product_id', '=', rec.filter_product_id.id))
                if rec.filter_subcontractor_id:
                    domain.append(('subcontractor', '=', rec.filter_subcontractor_id.id))
        return domain

    def _component_ids(self):
        domain = []
        if self:
            for rec in self:
                if rec.filter_component_product_id:
                    domain.append(('product_id', '=', rec.filter_component_product_id.id))
        return domain

    bom_id = fields.Many2one("mrp.bom", string="BOM")
    bom_ids = fields.Many2many("mrp.bom", string="BOMS")
    component_ids = fields.One2many("bom.wizard.component", "wizard_id", string="Components", domain=_component_ids)
    operation_ids = fields.One2many("bom.wizard.operation", "wizard_id", string="Operations")
    subcontractor_ids = fields.One2many("bom.wizard.subcontractor", "wizard_id", string="Sub-Contractor", domain=_subcontractor_ids)

    currency_id = fields.Many2one(
        "res.currency", string="Currency",
        default=lambda self: self.env.company.currency_id.id
    )


    margin_percent_component = fields.Float(string="Component Margin (%)", default=0.0)
    margin_percent_operation = fields.Float(string="Operation Margin (%)", default=0.0)
    margin_percent_subcontractor = fields.Float(string="Subcontractor Margin (%)", default=0.0)

    is_component_margin_manual = fields.Boolean(
        string="Component Margin Manual",
        compute="_compute_is_component_margin_manual",
        store=False
    )
    is_operation_margin_manual = fields.Boolean(
        string="Operation Margin Manual",
        compute="_compute_is_operation_margin_manual",
        store=False
    )
    is_subcontractor_margin_manual = fields.Boolean(
        string="Subcontractor Margin Manual",
        compute="_compute_is_subcontractor_margin_manual",
        store=False
    )
    dummy_char = fields.Char()

    # --- Component Totals ---
    total_cost_component = fields.Monetary(string="Cost", compute="_compute_totals", store=True)
    total_margin_component = fields.Monetary(string="Margin", compute="_compute_totals", store=True)
    total_component = fields.Monetary(string="Total", compute="_compute_totals", store=True)

    # --- Operation Totals ---
    total_cost_operation = fields.Monetary(string="Cost", compute="_compute_totals", store=True)
    total_margin_operation = fields.Monetary(string="Margin", compute="_compute_totals", store=True)
    total_operation = fields.Monetary(string="Total", compute="_compute_totals", store=True)

    # --- Subcontractor Totals ---
    total_cost_subcontractor = fields.Monetary(string="Cost", compute="_compute_totals", store=True)
    total_margin_subcontractor = fields.Monetary(string="Margin", compute="_compute_totals", store=True)
    total_subcontractor = fields.Monetary(string="Total", compute="_compute_totals", store=True)

    # --- Combine Totals ---
    total_all = fields.Monetary(string="Total (All)", compute="_compute_totals", store=True)

    # --- Combine Totals Margin---
    total_margin_all = fields.Monetary(string="Total Margin (All)", compute="_compute_totals", store=True)

    # --- Combine Totals Margin---
    total_cost_all = fields.Monetary(string="Total Cost (All)", compute="_compute_totals", store=True)
    estimation_id = fields.Many2one("sale.estimation", string="Estimation")
    estimation_line_id = fields.Many2one("sale.estimation.line", string="Estimation Line")
    source_wizard_id = fields.Many2one("bom.wizard", string="Source Wizard")

    drawings_html = fields.Html( string="Drawing")
    filter_product_id = fields.Many2one('product.product', string='Description')
    filter_component_product_id = fields.Many2one('product.product', string='Description')
    filter_subcontractor_id = fields.Many2one('res.partner', string='Sub-Contractor')

    filter_product_domain = fields.Binary(
        string="Filter Product Domain",
        compute="_compute_filter_product_domain"
    )

    filter_component_product_domain = fields.Binary(
        string="Filter Product Domain",
        compute="_compute_filter_product_domain"
    )

    filter_subcontractor_domain = fields.Binary(
        string="Filter Subcontractor Domain",
        compute="_compute_filter_subcontractor_domain"
    )

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    pricelist_id = fields.Many2one('product.pricelist')
    date_order = fields.Datetime(
        string="Order Date", copy=False,
        help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.",
        default=fields.Datetime.now)
    state = fields.Selection([('draft', 'Draft'), ('sent', 'In Review'), ('done', 'Approved'), ('cancel', 'Cancelled')], string='Status', default='draft')

    # --- Component Totals All ---
    total_cost_component_all = fields.Monetary(string="Cost", store=True)
    total_margin_component_all = fields.Monetary(string="Margin", store=True)
    total_component_all = fields.Monetary(string="Total", store=True)

    # --- Operation Totals All ---
    total_cost_operation_all = fields.Monetary(string="Cost", store=True)
    total_margin_operation_all = fields.Monetary(string="Margin", store=True)
    total_operation_all = fields.Monetary(string="Total", store=True)

    # --- Subcontractor Totals All ---
    total_cost_subcontractor_all = fields.Monetary(string="Cost", store=True)
    total_margin_subcontractor_all = fields.Monetary(string="Margin", store=True)
    total_subcontractor_all = fields.Monetary(string="Total", store=True)

    margin_percent_component_all = fields.Float(string="Component Margin (%)", default=0.0, compute="_compute_margin_percent_all")
    margin_percent_operation_all = fields.Float(string="Operation Margin (%)", default=0.0, compute="_compute_margin_percent_all")
    margin_percent_subcontractor_all = fields.Float(string="Subcontractor Margin (%)", default=0.0, compute="_compute_margin_percent_all")

    margin_percent_component_diff = fields.Float(string="Total Margin", default=0.0, compute="_compute_margin_percent_diff")
    margin_percent_operation_diff = fields.Float(string="Total Margin", default=0.0, compute="_compute_margin_percent_diff")
    margin_percent_subcontractor_diff = fields.Float(string="Total Margin", default=0.0, compute="_compute_margin_percent_diff")

    margin_percent_component_diff_all = fields.Float(string="Margin Diff(%)", default=0.0)
    margin_percent_operation_diff_all = fields.Float(string="Margin Diff(%)", default=0.0)
    margin_percent_subcontractor_diff_all = fields.Float(string="Margin Diff(%)", default=0.0)

    @api.depends('filter_product_id', 'filter_component_product_id')
    def _compute_filter_product_domain(self):
        """Compute JSON version of the domain for filter_product_id."""
        for rec in self:
            domain = [('type', '=', 'service')]
            custom_domain = [('id', '=', 0)]
            selected_products = rec.subcontractor_ids.mapped('product_id').ids
            if selected_products:
                domain.append(('id', 'in', selected_products))
            else:
                domain = custom_domain
            rec.filter_product_domain = domain

            domain_comp = [('bom_ids', '=', False)]
            custom_comp = [('id', '=', 0)]

            component_products = rec.component_ids.mapped('product_id').ids
            if component_products:
                domain_comp.append(('id', 'in', component_products))
            else:
                domain_comp = custom_comp

            rec.filter_component_product_domain = domain_comp

    @api.depends('filter_subcontractor_id')
    def _compute_filter_subcontractor_domain(self):
        """Compute JSON version of the domain for filter_product_id."""
        for rec in self:
            domain = []
            custom_domain = [('id', '=', 0)]
            selected_subcontractors = rec.subcontractor_ids.mapped('subcontractor').ids
            if selected_subcontractors:
                domain.append(('id', 'in', selected_subcontractors))
            else:
                domain = custom_domain
            rec.filter_subcontractor_domain = domain

    @api.depends("component_ids.margin")
    def _compute_is_component_margin_manual(self):
        """Check if component lines have different margins from each other"""
        for rec in self:
            if not rec.component_ids:
                rec.is_component_margin_manual = False
            else:
                margins = rec.component_ids.mapped('margin')
                rec.is_component_margin_manual = len(set(margins)) > 1

    @api.depends("operation_ids.margin")
    def _compute_is_operation_margin_manual(self):
        """Check if operation lines have different margins from each other"""
        for rec in self:
            if not rec.operation_ids:
                rec.is_operation_margin_manual = False
            else:
                margins = rec.operation_ids.mapped('margin')
                rec.is_operation_margin_manual = len(set(margins)) > 1

    @api.depends("subcontractor_ids.margin")
    def _compute_is_subcontractor_margin_manual(self):
        """Check if subcontractor lines have different margins from each other"""
        for rec in self:
            if not rec.subcontractor_ids:
                rec.is_subcontractor_margin_manual = False
            else:
                # Get all unique margin values
                margins = rec.subcontractor_ids.mapped('margin')
                # If more than one unique margin value, then margins were manually edited
                rec.is_subcontractor_margin_manual = len(set(margins)) > 1

    @api.onchange("margin_percent_component")
    def _onchange_margin_percent_component(self):
        """Update subcontractor line margins based on filters."""

        # If any filter is applied → update only filtered lines
        if self.filter_component_product_id:
            for line in self.component_ids:
                if self.filter_component_product_id and line.product_id != self.filter_component_product_id:
                    continue
                line.margin = self.margin_percent_component
        else:
            # No filter → update all lines
            for line in self.component_ids:
                line.margin = self.margin_percent_component

    @api.onchange("margin_percent_operation")
    def _onchange_margin_percent_operation(self):
        """When master margin changes, update all operation line margins"""
        for line in self.operation_ids:
            line.margin = self.margin_percent_operation

    @api.onchange("margin_percent_subcontractor")
    def _onchange_margin_percent_subcontractor(self):
        """Update subcontractor line margins based on filters."""

        # If any filter is applied → update only filtered lines
        if self.filter_product_id or self.filter_subcontractor_id:
            for line in self.subcontractor_ids:
                if self.filter_product_id and line.product_id != self.filter_product_id:
                    continue
                if self.filter_subcontractor_id and line.subcontractor != self.filter_subcontractor_id:
                    continue
                line.margin = self.margin_percent_subcontractor
        else:
            # No filter → update all lines
            for line in self.subcontractor_ids:
                line.margin = self.margin_percent_subcontractor

    def action_reset_component_margins(self):
        """Reset all component line margins to the master margin percentage"""
        self.ensure_one()
        master_margin = self.margin_percent_component
        self.component_ids.write({'margin': master_margin})
        self.invalidate_recordset(['is_component_margin_manual'])
        self._compute_is_component_margin_manual()
        self.invalidate_recordset(['total_cost_component', 'total_margin_component', 'total_component', 'total_all'])
        self._compute_totals()
        return {
            'name': _(self.estimation_line_id.product_id.name if self.estimation_line_id and self.estimation_line_id.product_id else  'Material Summary'),
            'type': 'ir.actions.act_window',
            'res_model': 'bom.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_reset_operation_margins(self):
        """Reset all operation line margins to the master margin percentage"""
        self.ensure_one()
        master_margin = self.margin_percent_operation
        self.operation_ids.write({'margin': master_margin})
        self.invalidate_recordset(['is_operation_margin_manual'])
        self._compute_is_operation_margin_manual()
        self.invalidate_recordset(['total_cost_operation', 'total_margin_operation', 'total_operation', 'total_all'])
        self._compute_totals()
        return {
            'name': _(self.estimation_line_id.product_id.name if self.estimation_line_id and self.estimation_line_id.product_id else  'Material Summary'),
            'type': 'ir.actions.act_window',
            'res_model': 'bom.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_reset_subcontractor_margins(self):
        """Reset all subcontractor line margins to the master margin percentage"""
        self.ensure_one()
        master_margin = self.margin_percent_subcontractor
        self.subcontractor_ids.write({'margin': master_margin})
        self.invalidate_recordset(['is_subcontractor_margin_manual'])
        self._compute_is_subcontractor_margin_manual()
        self.invalidate_recordset(['total_cost_subcontractor', 'total_margin_subcontractor', 'total_subcontractor', 'total_all'])
        self._compute_totals()
        return {
            'name': _(self.estimation_line_id.product_id.name if self.estimation_line_id and self.estimation_line_id.product_id else  'Material Summary'),
            'type': 'ir.actions.act_window',
            'res_model': 'bom.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.depends(
        "component_ids.price_subtotal",
        "component_ids.rate",
        "component_ids.product_uom_qty",
        "component_ids.margin",
        "component_ids.margin_diff",
        "operation_ids.subtotal",
        "operation_ids.rate",
        "operation_ids.quantity",
        "operation_ids.margin",
        "operation_ids.margin_diff",
        "subcontractor_ids.subtotal",
        "subcontractor_ids.rate",
        "subcontractor_ids.quantity",
        "subcontractor_ids.margin",
        "subcontractor_ids.margin_diff",
        "margin_percent_component",
        "margin_percent_operation",
        "margin_percent_subcontractor",
    )
    def _compute_totals(self):
        for rec in self:
            # Component sums - calculate based on individual line margins
            cost_comp = sum(line.rate * line.product_uom_qty for line in rec.component_ids)
            margin_comp = sum((line.rate * line.product_uom_qty / (1 - ((line.margin + line.margin_diff) / 100)) - line.rate * line.product_uom_qty) for line in rec.component_ids)
            total_comp = sum(line.price_subtotal for line in rec.component_ids)

            # Operation sums - calculate based on individual line margins
            cost_op = sum(line.rate * line.quantity for line in rec.operation_ids)
            margin_op = sum((line.rate * line.quantity / (1 - ((line.margin + line.margin_diff) / 100)) - line.rate * line.quantity) for line in rec.operation_ids)
            total_op = sum(line.subtotal for line in rec.operation_ids)

            # Subcontractor sums - calculate based on individual line margins
            cost_sc = sum(line.rate * line.quantity for line in rec.subcontractor_ids)
            margin_sc = sum((line.rate * line.quantity / (1 - ((line.margin + line.margin_diff) / 100)) - line.rate * line.quantity) for line in rec.subcontractor_ids)
            total_sc = sum(line.subtotal for line in rec.subcontractor_ids)

            # Grand totals
            rec.total_cost_component = cost_comp
            rec.total_margin_component = margin_comp
            rec.total_component = total_comp

            rec.total_cost_operation = cost_op
            rec.total_margin_operation = margin_op
            rec.total_operation = total_op

            rec.total_cost_subcontractor = cost_sc
            rec.total_margin_subcontractor = margin_sc
            rec.total_subcontractor = total_sc

            # Combined total
            rec.total_all = total_comp + total_op + total_sc

            # Combined total margin
            rec.total_margin_all = margin_comp + margin_op + margin_sc

            # Combined total cost
            rec.total_cost_all = cost_comp + cost_op + cost_sc

            if rec.estimation_line_id:
                rec.estimation_line_id._compute_bom_wizard_values()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        margin_ids = self.env['estimation.margin'].sudo().search([])
        if margin_ids:
            materials_hardware_id = margin_ids.filtered(lambda obj: obj.name == 'materials_hardware')
            sub_contractors_id = margin_ids.filtered(lambda obj: obj.name == 'sub_contractors')
            shops_id = margin_ids.filtered(lambda obj: obj.name == 'shops')
            if materials_hardware_id or sub_contractors_id or shops_id:
                res.update({
                    "margin_percent_component": materials_hardware_id.margin if materials_hardware_id else 0,
                    "margin_percent_subcontractor": sub_contractors_id.margin if sub_contractors_id else 0,
                    "margin_percent_operation": shops_id.margin if shops_id else 0,
                })

        estimation_line_id = self._context.get("default_estimation_line_id")

        comp_vals, op_vals, sub_vals = [], [], []

        if estimation_line_id:
            line = self.env['sale.estimation.line'].browse(estimation_line_id)

            # If the estimation line already has a source wizard
            if line.source_wizard_id:
                wizard = line.source_wizard_id

                # Components
                for comp in wizard.component_ids:
                    comp_vals.append((0, 0, {
                        "product_id": comp.product_id.id,
                        "product_categ_id": comp.product_categ_id.id,
                        "name": comp.name,
                        "product_uom_qty": comp.product_uom_qty,
                        "rate": comp.rate,
                        "estimation_line_id": estimation_line_id,
                        "prod": comp.prod,
                        "sub": comp.sub,
                        "arch_code": comp.arch_code,
                    }))

                # Operations
                for op in wizard.operation_ids:
                    op_vals.append((0, 0, {
                        "name": op.name,
                        "product_id": op.product_id.id,
                        "workcenter_id": op.workcenter_id.id,
                        "duration": op.duration,
                        "rate": op.rate,
                        "quantity": op.quantity,
                        "estimation_line_id": estimation_line_id,
                    }))

                # Subcontractors
                for sub in wizard.subcontractor_ids:
                    sub_vals.append((0, 0, {
                        "name": sub.name,
                        "product_id": sub.product_id.id,
                        "rate": sub.rate,
                        "quantity": sub.quantity,
                        "uom": sub.uom.id,
                        "estimation_line_id": estimation_line_id,
                        "subcontractor": sub.subcontractor.id,
                    }))

                res.update({
                    "margin_percent_component": wizard.margin_percent_component,
                    "margin_percent_operation": wizard.margin_percent_operation,
                    "margin_percent_subcontractor": wizard.margin_percent_subcontractor,
                })
            else:
                # --- NEW: Load operations from BOM shop_ids if available ---
                bom = self.env["mrp.bom"]._bom_find(line.product_id)
                bom_id = bom[line.product_id]

                # Components from BoM
                if bom_id:
                    for comp in bom_id.bom_line_ids:
                        comp_vals.append((0, 0, {
                            "product_id": comp.product_id.id,
                            "product_categ_id": comp.product_id.categ_id.id,
                            "name": comp.product_id.display_name,
                            "product_uom_qty": comp.product_qty,
                            "rate": comp.product_id.standard_price,
                            "estimation_line_id": estimation_line_id,
                        }))
                # If no BoM exists → keep components empty (correct)

                if bom_id and bom_id.shop_ids:
                    for shop in bom_id.shop_ids:
                        op_vals.append((0, 0, {
                            "name": shop.name,
                            "product_id": shop.product_id.id,
                            "workcenter_id": False,
                            "duration": 0.0,
                            "rate": shop.rate,
                            "quantity": shop.quantity,
                            "margin": shop.margin,
                            "margin_diff": shop.margin_diff,
                            "estimation_line_id": estimation_line_id,
                        }))
                else:
                    # --- Fallback to default shops ---
                    shop_operations = self.env["sale.estimation.shop"].search([])
                    for shop in shop_operations:
                        op_vals.append((0, 0, {
                            "name": shop.name,
                            "product_id": shop.product_id.id,
                            "workcenter_id": False,
                            "duration": 0.0,
                            "rate": shop.product_id.standard_price,
                            "quantity": 0.0,
                            "estimation_line_id": estimation_line_id,
                        }))
        else:
            # Default data when no estimation_line_id in context
            shop_operations = self.env["sale.estimation.shop"].search([])
            for shop in shop_operations:
                op_vals.append((0, 0, {
                    "name": shop.name,
                    "product_id": shop.product_id.id,
                    "workcenter_id": False,
                    "duration": 0.0,
                    "rate": shop.product_id.standard_price,
                    "quantity": 0.0,
                }))

        res.update({
            "component_ids": comp_vals,
            "operation_ids": op_vals,
            "subcontractor_ids": sub_vals,
        })
        return res

    def action_save_record(self):
        """Sync current wizard data into all child wizards linked via source_wizard_id."""
        self.ensure_one()

        child_wizards = self.env["bom.wizard"].search([
            ("source_wizard_id", "=", self.id)
        ])

        # Determine filtered lines
        comp_lines = self.component_ids
        op_lines = self.operation_ids
        sub_lines = self.subcontractor_ids

        # Apply filter to Components
        if self.filter_component_product_id:
            comp_lines = comp_lines.filtered(
                lambda c: c.product_id.id == self.filter_component_product_id.id
            )

        # Apply filter to Subcontractor
        if self.filter_product_id:
            sub_lines = sub_lines.filtered(
                lambda s: s.product_id.id == self.filter_product_id.id
            )

        if self.filter_subcontractor_id:
            sub_lines = sub_lines.filtered(
                lambda s: s.subcontractor.id == self.filter_subcontractor_id.id
            )

        # Update child wizards
        for child in child_wizards:

            # Components
            for line in comp_lines:
                child_line = child.component_ids.filtered(
                    lambda l: l.product_id == line.product_id
                )
                child_line.margin_diff = self.margin_percent_component_diff_all

            # Operations (no filter)
            for line in op_lines:
                child_line = child.operation_ids.filtered(
                    lambda l: l.product_id == line.product_id
                )
                child_line.margin_diff = self.margin_percent_operation_diff_all

            # Subcontractors
            for line in sub_lines:
                child_line = child.subcontractor_ids.filtered(
                    lambda l: l.product_id == line.product_id
                              and l.subcontractor == line.subcontractor
                )
                child_line.margin_diff = self.margin_percent_subcontractor_diff_all

            child._compute_totals()

        return {'type': 'ir.actions.act_window_close'}

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._update_sale_line_price()
            rec.estimation_line_id.source_wizard_id = rec.id
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec._update_sale_line_price()
        return res

    def _update_sale_line_price(self):
        """Push wizard total to sale.estimation.line"""
        if self.estimation_line_id:
            self.estimation_line_id.price_unit = self.total_all

    @api.onchange('component_ids')
    def _onchange_component_ids(self):
        for rec in self:
            for line in rec.component_ids:
                if line.product_id:
                    project_id = rec.estimation_line_id.estimation_id.project_id.id
                    material_list_id = self.env['material.list'].search(
                        [('project_id', '=', project_id)])

                    for ml in material_list_id.order_line:
                        if ml.product_id.id == line.product_id.id:
                            line.arch_code = ml.code or ''
                            line.sequence = ml.sequence

    @api.onchange('filter_product_id', 'filter_subcontractor_id', 'filter_component_product_id',)
    def onchange_filter_product_subcontractor_id(self):
        """Dynamically update subcontractors when filters change."""
        for rec in self:
            rec._component_ids()
            rec._subcontractor_ids()
            rec._compute_totals()

    def action_apply(self):
        self._compute_totals()
        self._onchange_filter_totals()
        return {
            'name': _(self.estimation_line_id.product_id.name if self.estimation_line_id and self.estimation_line_id.product_id else  'Material Summary'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_clear_all(self):
        """Reset all filters."""
        for rec in self:
            rec.filter_product_id = False
            rec.filter_subcontractor_id = False
            rec._compute_totals()
            rec._onchange_filter_totals()

        return {
            'name': _(self.estimation_line_id.product_id.name if self.estimation_line_id and self.estimation_line_id.product_id else  'Material Summary'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_clear_all_component(self):
        """Reset all filters."""
        for rec in self:
            rec.filter_component_product_id = False
            rec._compute_totals()
            rec._onchange_filter_totals()

        return {
            'name': _(self.estimation_line_id.product_id.name if self.estimation_line_id and self.estimation_line_id.product_id else  'Material Summary'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    @api.depends('total_margin_component_all','total_margin_operation_all','total_margin_subcontractor_all',
                 'total_component_all','total_operation_all','total_subcontractor_all',)
    def _compute_margin_percent_all(self):
        for rec in self:
            rec.margin_percent_component_all = (rec.total_margin_component_all / rec.total_component_all) * 100 if rec.total_margin_component_all and rec.total_component_all else 0.0
            rec.margin_percent_operation_all = (rec.total_margin_operation_all / rec.total_operation_all) * 100 if rec.total_margin_operation_all and rec.total_operation_all else 0.0
            rec.margin_percent_subcontractor_all = (rec.total_margin_subcontractor_all / rec.total_subcontractor_all) * 100 if rec.total_margin_subcontractor_all and rec.total_subcontractor_all else 0.0

    @api.depends('total_margin_component','total_component',
                 'total_margin_operation','total_operation',
                 'total_margin_subcontractor','total_subcontractor',)
    def _compute_margin_percent_diff(self):
        for rec in self:
            rec.margin_percent_component_diff = (rec.total_margin_component / rec.total_component) * 100 if rec.total_margin_component and rec.total_component else 0.0
            rec.margin_percent_operation_diff = (rec.total_margin_operation / rec.total_operation) * 100 if rec.total_margin_operation and rec.total_operation else 0.0
            rec.margin_percent_subcontractor_diff = (rec.total_margin_subcontractor / rec.total_subcontractor) * 100 if rec.total_margin_subcontractor and rec.total_subcontractor else 0.0

    @api.onchange('filter_product_id', 'filter_subcontractor_id', 'filter_component_product_id',
                  'margin_percent_component_diff_all', 'margin_percent_operation_diff_all', 'margin_percent_subcontractor_diff_all')
    def _onchange_filter_totals(self):
        """Recalculate totals based on active filters."""

        # Default: use all lines
        comp_lines = self.component_ids
        op_lines = self.operation_ids
        sub_lines = self.subcontractor_ids

        # Apply filter to Components
        if self.filter_component_product_id:
            comp_lines = comp_lines.filtered(
                lambda c: c.product_id.id == self.filter_component_product_id.id
            )

        # Apply filter to Subcontractors
        if self.filter_product_id:
            comp_lines = comp_lines.filtered(
                lambda c: c.product_id.id == self.filter_product_id.id
            )

        if self.filter_subcontractor_id:
            sub_lines = sub_lines.filtered(
                lambda s: s.subcontractor.id == self.filter_subcontractor_id.id
            )

        # Recalculate totals
        self.total_cost_component_all = sum(l.rate * l.product_uom_qty for l in comp_lines)
        self.total_component_all = sum(l.price_subtotal for l in comp_lines)
        self.total_margin_component_all = self.total_component_all - self.total_cost_component_all

        self.total_cost_operation_all = sum(l.rate * l.quantity for l in op_lines)
        self.total_operation_all = sum(l.subtotal for l in op_lines)
        self.total_margin_operation_all = self.total_operation_all - self.total_cost_operation_all

        self.total_cost_subcontractor_all = sum(l.rate * l.quantity for l in sub_lines)
        self.total_subcontractor_all = sum(l.subtotal for l in sub_lines)
        self.total_margin_subcontractor_all = (
                self.total_subcontractor_all - self.total_cost_subcontractor_all
        )

        # Set combined totals
        self.total_all = (
                self.total_component_all
                + self.total_operation_all
                + self.total_subcontractor_all
        )

    @api.onchange("margin_percent_component_diff_all")
    def _onchange_margin_percent_component_diff_all(self):
        """Update component line margins diff."""
        for line in self.component_ids:
                line.margin_diff = self.margin_percent_component_diff_all

    @api.onchange("margin_percent_operation_diff_all")
    def _onchange_margin_percent_operation_diff_all(self):
        """Update operation line margins diff."""
        for line in self.operation_ids:
            line.margin_diff = self.margin_percent_operation_diff_all

    @api.onchange("margin_percent_subcontractor_diff_all")
    def _onchange_margin_percent_subcontractor_diff_all(self):
        """Update subcontractor line margins diff."""
        for line in self.subcontractor_ids:
            line.margin_diff = self.margin_percent_subcontractor_diff_all

    def action_go_back(self):
        estimation_id = self.env.context.get('estimation_id')
        wizard_id = self.get_wizard_id()
        bom_wizard_id = self.browse(wizard_id)
        if bom_wizard_id.exists():
            estimation_id = bom_wizard_id.estimation_id.id or bom_wizard_id.estimation_line_id.estimation_id.id
        if not estimation_id:
            return {
                'type': 'ir.actions.act_window_close',
            }

        view_id = self.env.ref('sales_customization.view_sale_estimation_type_form').id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.estimation',
            'res_id': estimation_id,
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'main',
            'context': {
                'from_product_catalog': False,
                'expand': True,
            },
        }

    def get_wizard_id(self):
        referrer = request.httprequest.referrer
        if not referrer:
            return False

        path = urlparse(referrer).path
        parts = path.strip('/').split('/')

        try:
            model = parts[1]
            record_id = int(parts[2])
            if model == 'bom.wizard':
                return record_id
        except (IndexError, ValueError):
            return False

        return False

class BomWizardComponent(models.Model):
    _name = "bom.wizard.component"
    _inherit = ['product.catalog.mixin']
    _description = "BOM Wizard Component"
    _order = "sequence, id"

    wizard_id = fields.Many2one("bom.wizard", required=True, ondelete="cascade")
    name = fields.Char(string="Component Name")
    arch_code = fields.Char(string="Arch Code")
    product_id = fields.Many2one("product.product", string="Description")
    product_categ_id = fields.Many2one("product.category", string="Category")
    rate = fields.Float(string="Rate", related='product_id.standard_price')
    product_uom = fields.Many2one('uom.uom', string="UOM", related='product_id.uom_id')
    product_uom_qty = fields.Float(string="Qty", default=1.0)
    margin = fields.Float(string="Margin (%)", default=0.0)
    price_subtotal = fields.Float(string="Sub-Total", compute='_compute_subtotal')
    prod = fields.Boolean(string='Prod', default=False)
    sub = fields.Boolean(string='Sub', default=False)
    currency_id = fields.Many2one(
        "res.currency", related='wizard_id.currency_id'
    )
    estimation_line_id = fields.Many2one("sale.estimation.line", string="Estimation Line")
    sequence = fields.Integer(string='Sequence')
    margin_diff = fields.Float(string="Margin Diff(%)", default=0.0)
    margin_all = fields.Float(string="Margin (%)", default=0.0, compute="_compute_margin_all")

    @api.depends('rate', 'product_uom_qty', 'margin', 'margin_diff')
    def _compute_subtotal(self):
        for rec in self:
            cost = rec.rate * rec.product_uom_qty
            margin = rec.margin + rec.margin_diff
            if margin >= 100:
                rec.price_subtotal = cost
            else:
                rec.price_subtotal = cost / (1 - (margin / 100))

    product_domain = fields.Binary(
        string="Product Domain",
        compute="_compute_product_domain"
    )

    @api.depends('product_categ_id', 'estimation_line_id.estimation_id.project_id')
    def _compute_product_domain(self):
        """Compute JSON version of the domain for product_id."""
        for rec in self:
            domain = [('bom_ids', '=', False)]
            custom_domain = [('id', '=', 0)]
            if rec.product_categ_id:
                domain.append(('categ_id', '=', rec.product_categ_id.id))

            estimation_id = self._context.get("custom_estimation_id")
            estimation = self.env['sale.estimation'].browse(estimation_id)
            project = estimation.project_id if estimation else False
            if project:
                existing_wizard = self.env["material.list"].search([
                    ("project_id", "=", project.id)
                ], limit=1)
                if existing_wizard:
                    prod_ids = existing_wizard.order_line.mapped('product_id').ids
                    selected_products = rec.wizard_id.component_ids.mapped('product_id').ids
                    if selected_products:
                        selected_domain = ('id', 'not in',
                                           [pid for pid in selected_products if pid != rec.product_id.id])
                        domain.append(selected_domain)

                    if prod_ids:
                        domain.append(('id', 'in', prod_ids))
                    else:
                        domain = custom_domain
                else:
                    domain = custom_domain
            else:
                domain = custom_domain

            rec.product_domain = domain

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        margin_id = self.env['estimation.margin'].sudo().search([('name', '=', 'materials_hardware')], limit=1)
        if margin_id and margin_id.margin:
            res.update({
                "margin": margin_id.margin,
            })
        return res

    @api.depends('margin', 'margin_diff')
    def _compute_margin_all(self):
        for rec in self:
            rec.margin_all = rec.margin + rec.margin_diff


class BomWizardOperation(models.Model):
    _name = "bom.wizard.operation"
    _description = "BOM Wizard Operation"

    wizard_id = fields.Many2one("bom.wizard", ondelete="cascade")
    name = fields.Char(string="Name")
    workcenter_id = fields.Many2one("mrp.workcenter", string="Work Center")
    duration = fields.Float(string="Duration (minutes)")
    rate = fields.Float(string="Rate")
    uom = fields.Many2one('uom.uom', string="UOM", default=lambda self: self.env.ref('uom.product_uom_unit').id)
    quantity = fields.Float(string="Qty")
    margin = fields.Float(string="Margin (%)", default=0.0)
    subtotal = fields.Float(string="Sub-Total", compute='_compute_subtotal')
    currency_id = fields.Many2one(
        "res.currency", related='wizard_id.currency_id'
    )
    estimation_line_id = fields.Many2one("sale.estimation.line", string="Estimation Line")
    product_id = fields.Many2one("product.product", string="Description")
    margin_diff = fields.Float(string="Margin Diff(%)", default=0.0)
    margin_all = fields.Float(string="Margin (%)", default=0.0, compute="_compute_margin_all")
    bom_id = fields.Many2one("mrp.bom", string="BoM")

    @api.depends('rate', 'quantity', 'margin', 'margin_diff')
    def _compute_subtotal(self):
        for rec in self:
            cost = rec.rate * rec.quantity
            margin = rec.margin + rec.margin_diff
            if margin >= 100:
                rec.subtotal = cost
            else:
                rec.subtotal = cost / (1 - (margin / 100))

    product_domain = fields.Binary(
        string="Product Domain",
        compute="_compute_product_domain"
    )

    @api.depends('product_id')
    def _compute_product_domain(self):
        """Compute JSON version of the domain for product_id."""
        for rec in self:
            domain = [('type', '=', 'service')]

            shop_operations = self.env["sale.estimation.shop"].search([])
            if shop_operations:
                prod_ids = shop_operations.mapped('product_id').ids
                selected_products = rec.wizard_id.operation_ids.mapped('product_id').ids
                if selected_products:
                    selected_domain = ('id', 'not in',
                                       [pid for pid in selected_products if pid != rec.product_id.id])
                    domain.append(selected_domain)
                if prod_ids:
                    domain.append(('id', 'in', prod_ids))

            rec.product_domain = domain

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.rate = rec.product_id.standard_price

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        margin_id = self.env['estimation.margin'].sudo().search([('name', '=', 'shops')], limit=1)
        if margin_id and margin_id.margin:
            res.update({
                "margin": margin_id.margin,
            })
        return res

    @api.depends('margin', 'margin_diff')
    def _compute_margin_all(self):
        for rec in self:
            rec.margin_all = rec.margin + rec.margin_diff


class BomWizardSubContractor(models.Model):
    _name = "bom.wizard.subcontractor"
    _description = "BOM Wizard Sub-Contractor"

    wizard_id = fields.Many2one("bom.wizard", required=True, ondelete="cascade")
    name = fields.Char(string="Name")
    rate = fields.Float(string="Rate")
    uom = fields.Many2one('uom.uom', string="UOM", default=lambda self: self.env.ref('uom.product_uom_unit').id)
    quantity = fields.Float(string="Qty")
    margin = fields.Float(string="Margin (%)", default=0.0)
    subcontractor = fields.Many2one('res.partner', string="Sub-Contractor")
    subtotal = fields.Float(string="Sub-Total", compute='_compute_subtotal')
    currency_id = fields.Many2one(
        "res.currency", related='wizard_id.currency_id'
    )
    estimation_line_id = fields.Many2one("sale.estimation.line", string="Estimation Line")
    product_id = fields.Many2one("product.product", string="Category")
    margin_diff = fields.Float(string="Margin Diff(%)", default=0.0)
    margin_all = fields.Float(string="Margin (%)", default=0.0, compute="_compute_margin_all")
    description = fields.Char(string="Description")
    actual_categ_id = fields.Many2one('product.category', string="Actual Category", related='product_id.categ_id')

    @api.depends('rate', 'quantity', 'margin', 'margin_diff')
    def _compute_subtotal(self):
        for rec in self:
            cost = rec.rate * rec.quantity
            margin = rec.margin + rec.margin_diff
            if margin >= 100:
                rec.subtotal = cost
            else:
                rec.subtotal = cost / (1 - (margin / 100))

    product_domain = fields.Binary(
        string="Product Domain",
        compute="_compute_product_domain"
    )

    @api.depends('product_id')
    def _compute_product_domain(self):
        """Compute JSON version of the domain for product_id."""
        for rec in self:
            domain = [('type', '=', 'service')]

            subcontractors = self.env["sale.estimation.subcontractor"].search([])
            if subcontractors:
                prod_ids = subcontractors.mapped('product_id').ids
                # selected_products = rec.wizard_id.subcontractor_ids.mapped('product_id').ids
                # if selected_products:
                #     selected_domain = ('id', 'not in',
                #                        [pid for pid in selected_products if pid != rec.product_id.id])
                #     domain.append(selected_domain)
                if prod_ids:
                    domain.append(('id', 'in', prod_ids))

            rec.product_domain = domain

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.rate = rec.product_id.standard_price

    subcontractor_domain = fields.Binary(
        string="Subcontractor Domain",
        compute="_compute_subcontractor_domain"
    )

    @api.depends('subcontractor')
    @api.onchange('product_id')
    def _compute_subcontractor_domain(self):
        """Compute JSON version of the domain for product_id."""
        for rec in self:
            domain = []
            custom_domain = [('id', '=', 0)]
            subcontractors = self.env["sale.estimation.subcontractor"].search([])
            if subcontractors:
                sub_ids = subcontractors.filtered(lambda obj:obj.product_id.id == rec.product_id.id).subcontractor_ids.ids
                selected_subcontractor = rec.wizard_id.subcontractor_ids.mapped('subcontractor').ids
                if selected_subcontractor:
                    selected_domain = ('id', 'not in',
                                       [sub for sub in selected_subcontractor if sub != rec.subcontractor.id])
                    domain.append(selected_domain)
                if sub_ids:
                    domain.append(('id', 'in', sub_ids))
                else:
                    domain = custom_domain

            rec.subcontractor_domain = domain

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        margin_id = self.env['estimation.margin'].sudo().search([('name', '=', 'sub_contractors')], limit=1)
        if margin_id and margin_id.margin:
            res.update({
                "margin": margin_id.margin,
            })
        return res

    @api.depends('margin', 'margin_diff')
    def _compute_margin_all(self):
        for rec in self:
            rec.margin_all = rec.margin + rec.margin_diff