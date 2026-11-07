/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

const originalSetup = Dialog.prototype.setup;
const originalDismiss = Dialog.prototype.dismiss;

patch(Dialog.prototype, {
    setup() {
        originalSetup.call(this, ...arguments);
        this.dialogService = useService("dialog");
        this.actionService = useService("action");
    },

    async dismiss() {
        const currentProps = this.props.actionProps;
        if (currentProps?.context?.active_model === 'sale.estimation.line'|| currentProps?.context?.active_model === 'sale.estimation'){
            const confirmed = await new Promise((resolve) => {
                this.dialogService.add(ConfirmationDialog, {
                    title: "Warning",
                    body: "Are you sure you want to discard the changes?",
                    confirmLabel: "Ok",
                    cancelLabel: "Cancel",
                    confirm: () => resolve(true),
                    cancel: () => resolve(false),
                });
            });

            if (!confirmed) {
                return;
            }
        }
        return originalDismiss.call(this, ...arguments);
    },
});