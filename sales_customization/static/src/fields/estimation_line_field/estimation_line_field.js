/** @odoo-module **/

import { registry } from "@web/core/registry";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { EstimationLineListRenderer } from "./estimation_line_list_renderer";

/**
 * Custom X2ManyField component for estimation_line_ids
 * that uses our custom ListRenderer with level border logic
 */
class EstimationLineField extends X2ManyField {
    static components = {
        ...X2ManyField.components,
        ListRenderer: EstimationLineListRenderer,
    };
}

export const estimationLineField = {
    ...x2ManyField,
    component: EstimationLineField,
    additionalClasses: ["o_field_one2many"],
};

registry.category("fields").add("estimation_line_x2many", estimationLineField);
