# -*- coding: utf-8 -*-
{
    "name": "Estimation Material Multi-Select",
    'summary': """
            Quickly Add Multiple Materials to Estimations in One Step.
        """,
    'description': """
            This module enhances the Sales Estimation process by introducing a 
            Material Multi-Select Wizard, allowing users to select and add multiple 
            products or materials to an estimation in a single action.
    
            Key Features:
            - Multi-select wizard to add multiple materials at once.
            - Automatically links selected products to the active material list.
            - Excludes already added materials to prevent duplicates.
            - Pre-fills product rate and related information for efficiency.
            - Reduces repetitive manual entry and improves data accuracy.
            - Seamlessly integrates with existing Estimation workflows.
    
            Use Case:
            Ideal for estimation teams who frequently add multiple products or 
            materials to projects. This feature saves time and ensures consistent 
            data handling while maintaining full control over product selection.
        """,
    'author': "Srinath Pal",
    'website': "https://www.nexevolve.com",
    'category': 'Sales/Project Estimation',
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "depends": [
        'sales_customization'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/material_list.xml',
        'views/material_wizard.xml',
        'views/bom_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'material_multiselect/static/src/css/style.css',
            'material_multiselect/static/src/xml/product_catalog.xml',
            'material_multiselect/static/src/js/product_catalog.js',
        ],
    },
}
