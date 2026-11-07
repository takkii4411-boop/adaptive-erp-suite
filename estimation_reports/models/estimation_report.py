# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class SaleEstimationReport(models.Model):
    _name = 'sale.estimation.report'
    _description = "Sale Estimation Analysis"
    _auto = False
    _rec_name = 'estimation_id'
    _order = 'estimation_id desc'

    estimation_id = fields.Many2one('sale.estimation', string='Estimation', readonly=True)
    project_id = fields.Many2one('project.project', string='Project', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Assigned To', readonly=True)
    builder_partner_id = fields.Many2one('res.partner', string='Builder', readonly=True)
    product_id = fields.Many2one('product.product', string='Joinery No', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', readonly=True)
    product_category_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    qty = fields.Float(string="Quantity", readonly=True)
    price_unit = fields.Float(string="Unit Price", readonly=True)
    price_subtotal = fields.Monetary(string="Untaxed Amount", readonly=True)
    price_tax = fields.Monetary(string="Tax", readonly=True)
    price_total = fields.Monetary(string="Total", readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'In Review'),
        ('done', 'Approved'),
        ('cancel', 'Cancelled'),
    ], string="Status", readonly=True)

    nbr = fields.Integer(string="# of Lines", readonly=True)
    date = fields.Datetime(string="Date", related="estimation_id.create_date")
    is_client = fields.Boolean(string="Is Client")
    winner = fields.Boolean(string="Winner")
    total_margin = fields.Float(string="Margin", readonly=True)
    total_margin_per = fields.Float(string="Margin %", readonly=True)
    total_cost = fields.Float(string="Cost", readonly=True)
    subcontractor_partner_id = fields.Many2one('res.partner', string='Subcontractor', readonly=True)
    level_id = fields.Many2one('sale.estimation.level', string='Level', readonly=True)
    joinery_no = fields.Char(string='Joinery Name', readonly=True)
    component_product_id = fields.Many2one(
        'product.product',
        string='Component Product',
        readonly=True
    )

    # ---------------------------
    # QUERY PARTS
    # ---------------------------

    def _select_estimation(self):
        return """
            MIN(l.id) AS id,
            e.id AS estimation_id,
            e.project_id AS project_id,
            e.employee_id AS employee_id,
            b.partner_id AS builder_partner_id,
            s.partner_id AS subcontractor_partner_id,
            b.is_client AS is_client,
            b.winner AS winner,
            l.product_id AS product_id,
            c.product_id AS component_product_id,
            l.level_id AS level_id,
            l.joinery_no AS joinery_no,
            l.total_cost AS total_cost,
            l.total_margin AS total_margin,
            CASE 
            WHEN l.price_subtotal = 0 
                THEN 0
            ELSE (l.total_margin / l.price_subtotal) * 100
            END AS total_margin_per,
            p.product_tmpl_id AS product_tmpl_id,
            t.categ_id AS product_category_id,
            SUM(l.qty) AS qty,
            AVG(l.price_unit) AS price_unit,
            SUM(l.price_subtotal) AS price_subtotal,
            SUM(l.price_tax) AS price_tax,
            SUM(l.price_total) AS price_total,
            e.currency_id AS currency_id,
            e.company_id AS company_id,
            e.status AS status,
            COUNT(*) AS nbr
        """

    def _from_estimation(self):
        return """
            sale_estimation_line l
            LEFT JOIN sale_estimation e ON e.id = l.estimation_id
            LEFT JOIN sale_builder b ON b.sale_id = e.id
            LEFT JOIN sale_sub_contractor s ON s.sale_id = e.id
            LEFT JOIN product_product p ON p.id = l.product_id
            LEFT JOIN product_template t ON t.id = p.product_tmpl_id
            LEFT JOIN sale_estimation_level sl ON sl.id = l.level_id
            LEFT JOIN bom_wizard_component c ON c.estimation_line_id = l.id
        """

    def _where_estimation(self):
        return "l.id IS NOT NULL"

    def _group_by_estimation(self):
        return """
            e.id,
            e.project_id,
            e.employee_id,
            b.partner_id,
            b.is_client,
            b.winner,
            l.product_id,
            c.product_id,
            l.level_id,
            l.joinery_no,
            l.total_cost,
            l.total_margin,
            total_margin_per,
            s.partner_id,
            p.product_tmpl_id,
            t.categ_id,
            e.currency_id,
            e.company_id,
            e.status
        """

    def _query(self):
        return f"""
            SELECT {self._select_estimation()}
            FROM {self._from_estimation()}
            WHERE {self._where_estimation()}
            GROUP BY {self._group_by_estimation()}
        """

    @property
    def _table_query(self):
        return self._query()
