# -*- coding: utf-8 -*-
{
    "name": "Estimation CRM",
    'summary': """
        Seamless Integration Between CRM Opportunities and Sales Estimations.
    """,
    'description': """
        The *Estimation CRM* module connects CRM Opportunities with the Sales Estimation process,
        creating a smooth workflow from lead qualification to estimation generation.

        Key Features:
        - Create Sales Estimations directly from CRM Opportunities.
        - Automatically link estimations to their originating opportunities.
        - Smart Button on CRM Opportunities to view related Estimations (form or list view based on count).
        - Smart Button on Sales Estimations to open the linked CRM Opportunity.
        - Builder selection in Opportunities automatically transferred to new Estimations.
        - Estimation count displayed on Opportunities for quick access and visibility.
        - Streamlined bid management process for construction, service, or custom project sales.

        Use Case:
        Ideal for businesses that rely on project-based or quotation-driven sales,
        this module ensures efficient collaboration between sales and estimation teams.
        Users can track all estimations linked to a CRM lead and quickly navigate between
        opportunities and their corresponding estimation records.
    """,
    'author': "Srinath Pal",
    'website': "https://www.nexevolve.com",
    'category': 'CRM',
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "depends": [
        'sales_customization', 'crm'
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/crm_lead.xml',
        'views/estimation.xml',
        'views/crm_stage.xml',
        'views/project_criteria.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'estimation_crm/static/src/css/style.css'
        ]
    },
}
