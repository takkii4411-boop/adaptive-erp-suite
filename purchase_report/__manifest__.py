{
    "name": "Custom Purchase Order Report",
    'summary': 'Custom Purchase Order Report',
    "author": "Srinath Pal",
    "website": "https://www.nexevolve.com",
    "category": "Purchase",
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "depends": ["purchase"],
    "data": [
        "views/purchase_order.xml",
        "reports/report_paperformat.xml",
        "reports/report_action.xml",
        "reports/report_footer_header.xml",
        "reports/report_body.xml",
    ],
}