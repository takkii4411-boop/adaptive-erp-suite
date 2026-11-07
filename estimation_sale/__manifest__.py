# -*- coding: utf-8 -*-
{
    "name": "Estimation Sale",
    'summary': """
        Seamless Integration Between Sales Estimations and Sales Orders.
    """,
    'description': """
        The *Estimation Sale* module connects Sales Estimations with Sales Orders, creating 
        a smooth and controlled workflow from cost estimation to final quotation or job order.

        Key Features:
        - Create Sales Orders directly from Sales Estimations with a single click.
        - Automatic linking between estimations and their generated Sales Orders.
        - Smart button on Estimations to open the related Sales Order.
        - Smart button on Sales Orders to view all linked Estimations.
        - Prevents accidental creation of duplicate Sales Orders from the same Estimation.
        - Transfers estimation details (levels, joinery info, cost, margin, rooms, notes, etc.)  
          into Sales Order Lines automatically.
        - Sales Orders inherit estimator, project, project type, and joinery type information.
        - Displays a count of linked estimations or sales orders for quick navigation.
        
        Use Case:
        Ideal for businesses that rely on project- or estimation-driven sales workflows.  
        This module ensures a fluid transition from the estimation phase to the sales order, 
        while maintaining full traceability between the two documents. Users can quickly 
        navigate between estimations and their corresponding sales orders, ensuring  
        clarity and reducing manual data duplication.
    """,
    'author': "Srinath Pal",
    'website': "https://www.nexevolve.com",
    'category': 'Sales',
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "depends": [
        'sales_customization', 'sale', 'sale_chatter_position'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/estimation.xml',
        'views/sale_order.xml',
    ]
}
