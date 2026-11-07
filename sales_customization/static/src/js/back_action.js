/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("actions").add("go_back_action", async function () {
    window.history.back();
});