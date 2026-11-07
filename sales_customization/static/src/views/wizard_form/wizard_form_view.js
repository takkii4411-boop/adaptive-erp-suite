/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { WizardFormRenderer } from "./wizard_form_renderer";

export const WizardFormView = {
    ...formView,
    Renderer: WizardFormRenderer,
};

registry.category("views").add("wizard_form", WizardFormView);