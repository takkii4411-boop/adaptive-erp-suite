{
    "name": "Sale Chatter Position",
    "summary": "Add an option to change the chatter position in Sales Order",
    "author": "Srinath Pal",
    "website": "https://www.nexevolve.com",
    "category": "Sales Extra Tools",
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "depends": ["web", "mail", "hr"],
    "data": [
        "views/res_users.xml",
        "views/web.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "sale_chatter_position/static/src/**/*.js",
            "sale_chatter_position/static/src/**/*.scss",
        ],
    },
}