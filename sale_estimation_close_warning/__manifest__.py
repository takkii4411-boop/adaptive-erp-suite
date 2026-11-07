# -*- coding: utf-8 -*-
{
    'name': 'Sale Estimation Wizard Close Warning',
    'category': 'Sales',
    'summary': 'Show warning when closing wizard for Sale Estimation',
    'depends': ['base', 'web', 'sale_management', 'sales_customization'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'sale_estimation_close_warning/static/src/js/close_warning.js',
        ],
    },
    'installable': True,
    'application': False,
    "license": "Other proprietary",
}