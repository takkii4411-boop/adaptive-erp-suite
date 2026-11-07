# Adaptive ERP Suite — Odoo 19

![Odoo](https://img.shields.io/badge/Odoo-19.0-purple) ![Modules](https://img.shields.io/badge/Custom%20Modules-12-blue) ![License](https://img.shields.io/badge/License-LGPL--3-green)

A **sales-estimation centric ERP suite** for Odoo 19 — a full **Estimation module family** (CRM, Sale, Project, Documents, Reports) plus targeted customizations in **MRP, Inventory, Purchase and Sales**, developed as client-required features on Odoo 19 core flows. **My role in this suite: small enhancements, fixes & debugging (MRP/inventory tweaks, chatter positioning, wizard close-warning, report adjustments)** — the suite belongs to a team build; bundled here as context of the delivery.

```
adaptive-erp-suite/
├── estimation_crm/                  # Estimations linked to CRM leads/opportunities
├── estimation_sale/                 # Estimations → Sale Orders conversion (models + flows)
├── estimation_project/              # Estimations linked to Projects/Tasks
├── estimation_documents/            # Attach documents to estimations
├── estimation_reports/              # Estimation PDF/QWeb reports
├── sale_estimation_close_warning/   # Confirmation warning when closing estimation wizards
├── mrp_customization/               # Manufacturing customizations
├── inventory_customization/         # Inventory customizations
├── material_multiselect/            # Multi-select for materials on operations
├── purchase_report/                 # Custom purchase order report
├── sales_customization/             # Sales flow customizations
└── sale_chatter_position/           # Rearranges chatter (right/left) on sale views
```

## Highlights

- **Estimation lifecycle** — create an Estimation, link it to CRM lead, convert to **Sale Order**, attach documents, and print estimation reports — forming a complete pre-sales estimation pipeline.
- **Sale Order integration** — `estimation.py`, `sale_order.py`, `sale_order_line.py` models extend interactive estimation→SO conversion.
- **Wizard close warning** — employees get a confirmation warning (instead of a silent data loss) when closing estimation wizards.
- **MRP/Inventory tweaks** — material multi-select and manufacturing/inventory process adjustments for factory workflows.
- **Purchase & Sales reports** — custom PO reports and sales customizations aligned to client reporting formats.

## Dependencies

`crm, sale_management, project, documents, mrp, stock, purchase, mail, web` (per-module)

## License

LGPL-3 (as declared in module manifests).
