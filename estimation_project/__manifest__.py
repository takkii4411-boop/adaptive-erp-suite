# -*- coding: utf-8 -*-
{
    "name": "Estimation Project",
    "summary": "Automatically create project tasks and subtasks from approved estimations",
    "description": """
        This module integrates Estimations with Projects by automatically creating
        structured project tasks when an estimation is approved.
        
        Key Features:
        -------------
        - Automatically creates Project Tasks for each Joinery Item in an Estimation.
        - Generates a predefined set of Sub-tasks under each Joinery task to follow
          the complete project lifecycle.
        - Includes support for repeatable review tasks such as
          'Shop Drawings updated according to the latest review'.
        - Copies all Estimation attachments to the created Tasks and Sub-tasks for
          better traceability.
        - Adds a smart button on the Estimation form to quickly access the linked Project.
        - Helps Project Managers track progress, RFIs, drawings, and approvals in a
          structured and standardized workflow.
        
        This module improves project visibility, ensures process consistency,
        and reduces manual task creation after Estimation approval.
    """,
    'author': "Srinath Pal",
    'website': "https://www.nexevolve.com",
    'category': 'Project',
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "depends": [
        'sales_customization', 'sale', 'project', 'estimation_sale'
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/estimation.xml',
        'views/estimation_subtask_template.xml',
        'views/project.xml',
    ]
}