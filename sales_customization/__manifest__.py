# -*- coding: utf-8 -*-
{
    "name": "Sales Estimation Customization",
    "summary": """
        Advanced Customization for Sales Estimations with Builder, Material, and Project Integration.
    """,
    "description": """
        The *Sales Estimation Customization* module enhances Odoo's standard Sales process by adding
        a powerful estimation management system designed for project-based and construction-oriented businesses.

        Key Features:
        - Create and manage detailed sales estimations with multi-level joinery and material listings.
        - Integrated Builder, Subcontractor, and Shop management.
        - Level-based structure for precise estimation breakdowns.
        - Automatic estimation sequence generation and organized project type configuration.
        - Dynamic Bill of Materials (BoM) creation through an easy-to-use wizard.
        - Generate professional Estimation PDF reports with complete details.
        - Integrated email templates for quick estimation communication.
        - Fully compatible with Odoo Sales, MRP, and Project modules.
        - Custom form view enhancements with OWL-based UI and backend CSS styling.

        Use Case:
        This module is ideal for industries where project estimation accuracy is critical —
        such as interior design, construction, manufacturing, or custom fabrication.
        It bridges sales, production, and project operations, enabling teams to prepare,
        review, and share costed estimations efficiently within Odoo.

        """,
    "author": "Srinath Pal",
    "website": "https://www.nexevolve.com",
    "category": "Sales/Project",
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "depends": [
        'base', 'web', 'sale_management', 'mail', 'sign', 'product', 'hr', 'mrp', 'project', 'account'
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/sale_project_type_data.xml',
        'data/sale_estimation_seq.xml',
        'views/sale_estimation.xml',
        'views/sale_project_type.xml',
        'views/bom_wizard.xml',
        'views/material_list.xml',
        'views/shops.xml',
        'views/subcontractor.xml',
        'views/levels.xml',
        'views/estimation_margin.xml',
        'reports/report_custom_estimation.xml',
        'data/email_template.xml',
        'data/product_category.xml',
        'views/product_category.xml',
        'views/mrp_bom.xml',
        'views/joinery_name.xml',
        'views/product_product.xml',
        'views/product_template.xml',
        'views/estimation_exclusion_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sales_customization/static/src/css/style.css',
            'sales_customization/static/src/js/product_catalog_kanban_controller_inherit.js',
            'sales_customization/static/src/js/back_action.js',
            'sales_customization/static/src/fields/highlight_row_field/highlight_row_field.css',
            'sales_customization/static/src/views/sale_estimation_form/sale_estimation_form_renderer.js',
            'sales_customization/static/src/views/sale_estimation_form/sale_estimation_form_view.js',
            'sales_customization/static/src/fields/estimation_line_field/estimation_line_list_renderer.js',
            'sales_customization/static/src/fields/estimation_line_field/estimation_line_field.js',
            'sales_customization/static/src/fields/highlight_row_field/highlight_row_field.js',
            'sales_customization/static/src/views/wizard_form/wizard_form_renderer.js',
            'sales_customization/static/src/views/wizard_form/wizard_form_view.js',
            'sales_customization/static/src/views/product_catalog/product_catalog.xml'
        ],
    },
}
