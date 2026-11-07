/** @odoo-module **/

import { ProductCatalogKanbanController } from "@product/product_catalog/kanban_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ProductCatalogKanbanController.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");

    },

    async backToQuotation() {
        const activeModel = this.props.context?.active_model;
        if (!["sale.estimation", "sale.estimation.line"].includes(activeModel)) {
            return await super.backToQuotation();
        }
        await this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: this.orderResModel,
            views: [[false, "form"]],
            view_mode: "form",
            res_id: this.orderId,
            target: "main",
            context: {
                from_product_catalog: false,
                estimation_id: this.props?.context.custom_estimation_id
            },
        }, {clearBreadcrumbs: true, stackPosition: "replaceCurrentAction"});
    },

    async createProduct() {
        await this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "product.product",
            views: [[false, "form"]],
            view_mode: "form",
            target: "new",
            name: "Create Product",
            context: {
                default_name: "",
                is_created_from_catalog: true,
                custom_estimation_id: this.props?.context.custom_estimation_id,
                order_id: this.props?.context.order_id,
                res_model: this.orderResModel
            }

        },
        {
            onClose: async () => {
                const wizardId = this.props.context?.order_id;
                try {
                   const result = await this.orm.call(
                        this.orderResModel,
                        "action_handle_new_product_from_catalog",
                        [[wizardId]],
                        {context: {'custom_estimation_id': this.props.context?.custom_estimation_id}}
                    );
                } catch(err) {
                    console.error("Failed to call wizard method:", error.data);
                }


            }
        }
        );
    }
});
