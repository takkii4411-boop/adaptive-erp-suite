# -*- coding: utf-8 -*-
{
    "name": "Estimation Documents",
    'summary': """
        Enhance Project and Sale Estimation with automatic document folder creation and clickable Drawing Numbers
    """,

    'description': """
        This module extends the Project and Sale Estimation functionalities by integrating
        document management automation and quick access to related drawings.
        
        Key Features
        ----------------------------------------------------
        ✅ **Automatic Folder Structure Creation**
        - When a new Project is created, a main folder is automatically generated in the Documents app.
        - Predefined subfolders and nested sub-subfolders are created under the project’s document root.
        - Maintains consistent folder hierarchy across all projects.
        
        ✅ **Clickable Drawing Numbers in Sale Estimation**
        - Extends the Sale Estimation form view (from the `sales_customization` module).
        - Drawing Number tags become clickable and open the corresponding document record.
        - Opens in a popup (modal) for seamless access without leaving the estimation screen.
        
        ✅ **Integration Highlights**
        - Fully compatible with the Odoo Documents and Project modules.
        - Non-intrusive: implemented as a lightweight extension without modifying core files.
        - Ideal for teams managing estimation, drawings, and project documentation in one flow.
    """,
    'author': "Srinath Pal",
    'website': "https://www.nexevolve.com",
    'category': 'CRM',
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "depends": [
        'sales_customization', 'documents'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/estimation.xml',
        'views/bom_wizard.xml',
        'views/documents_document_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'estimation_documents/static/src/xml/tag_list.xml',
            'estimation_documents/static/src/js/tag_list.js',
            'estimation_documents/static/src/css/style.css'
        ],
    },
}
