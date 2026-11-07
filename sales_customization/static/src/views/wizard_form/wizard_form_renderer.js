/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer";
import { onMounted, onPatched, useEffect, useRef } from "@odoo/owl";

export class WizardFormRenderer extends FormRenderer {
    setup() {
        super.setup();
        this.rootRef = useRef("compiled_view_root");

        onMounted(() => {
            this._applySaleEstimationModalStyle();
        });

    }

     /**
     * Apply full-width modal style for Sale Estimation form
     */
    _applySaleEstimationModalStyle() {
        const dialog = this.rootRef.el?.closest(".modal-dialog");
        if (dialog) {
            dialog.classList.add("sale-estimation-dialog");
        }
    }
}