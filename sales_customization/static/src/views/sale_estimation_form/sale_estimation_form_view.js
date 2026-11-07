/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { SaleEstimationFormRenderer } from "./sale_estimation_form_renderer";

export const saleEstimationFormView = {
    ...formView,
    Renderer: SaleEstimationFormRenderer,
};

registry.category("views").add("sale_estimation_form", saleEstimationFormView);