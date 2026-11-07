# -*- coding: utf-8 -*-
{
    "name": "Estimation Reports",
    'summary': """
        Advanced Sales Estimation Reporting with Pivot, Graph, and List Analysis.
    """,
    'description': """
        This module provides a powerful reporting dashboard for Sales Estimations, 
        allowing users to analyze estimation performance, builder contributions, 
        and product-wise breakdowns using Pivot, Graph, and List views.

        Key Features:
        - Comprehensive reporting for Sales Estimations.
        - Analyze data by Builder, Customer, Product, or Salesperson.
        - Interactive filters and dynamic group-by options.
        - Default grouping by Estimation for quick insights.
        - Fully compatible with Pivot, Graph, and List views.
        - Supports drill-down to estimation records for detailed review.
        - Simplifies decision-making for project cost and sales analysis.

        Use Case:
        Ideal for organizations managing multiple project estimations who need 
        a clear visual and analytical overview of their sales pipeline, builder 
        performance, and estimation profitability — all in one place.
    """,
    'author': "Srinath Pal",
    'website': "https://www.nexevolve.com",
    'category': 'Sales/Reporting',
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "depends": [
        'sales_customization'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/estimation_report.xml',
    ]
}
