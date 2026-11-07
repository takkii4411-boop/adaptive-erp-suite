/** @odoo-module **/

import { ProductCatalogKanbanController } from "@product/product_catalog/kanban_controller";
import { patch } from "@web/core/utils/patch";
import { useSubEnv } from "@odoo/owl";

patch(ProductCatalogKanbanController.prototype, {
    setup() {
        super.setup();
        useSubEnv({
            arch_codes: this.props.context?.arch_codes || [],
        });
    }
})