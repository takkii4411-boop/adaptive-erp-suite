{
    'name': 'Inventory Customization',
    'category': 'Inventory/Inventory',
    'summary': 'Inventory Customization',

    'depends': ['base', 'web', 'stock', 'product', 'purchase', 'sales_customization', 'material_multiselect', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/product_supplierinfo_views.xml',
        'views/sale_estimation_inherit.xml',
        'views/material_hardware_details_views.xml',
        'views/product_color_views.xml',
        'views/product_finish_views.xml',
        'views/stock_picking.xml',
        'views/purchase_order.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_customization/static/src/css/style.css'
        ]
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}