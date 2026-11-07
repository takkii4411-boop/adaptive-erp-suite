/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class LogNoteDialog extends Component {
    static template = "mrp_customization.LogNoteDialog";
    static components = { Dialog };

    static props = {
        note: String,   // HTML
        close: Function,
    };
}
