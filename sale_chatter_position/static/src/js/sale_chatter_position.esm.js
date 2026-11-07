import {FormCompiler} from "@web/views/form/form_compiler";
import {patch} from "@web/core/utils/patch";
import {append, setAttributes} from "@web/core/utils/xml";
import {SIZES} from "@web/core/ui/ui_service";

patch(FormCompiler.prototype, {
    /**
     * @override
     */
    compile(node, params) {
        const res = super.compile(node, params);
        const webClientViewAttachmentViewHookXml = res.querySelector(
            ".o_attachment_preview"
        );
        const chatterContainerHookXml = res.querySelector(
            ".o-mail-Form-chatter:not(.o-isInFormSheetBg)"
        );
        if (!chatterContainerHookXml) {
            // No chatter, keep the result as it is
            return res;
        }
        const chatterContainerXml = chatterContainerHookXml.querySelector(
            "t[t-component='__comp__.mailComponents.Chatter']"
        );
        // Const chatterParent = chatterContainerXml.parentNode;
        const formSheetBgXml = res.querySelector(".o_form_sheet_bg");
        const parentXml = formSheetBgXml && formSheetBgXml.parentNode;
        if (!parentXml) {
            // Miss-config: a sheet-bg is required for the rest
            return res;
        }
        // Restrict only for sales order
        const FormClassName = this.templates.FormRenderer.className;
        const SaleFormClassName = 'o_sale_order';

        // Don't patch anything if the setting is "auto": this is the core behaviour
        if (odoo.sale_chatter_position === "auto" && FormClassName == SaleFormClassName) {
            return res;
            // For "sided", we have to remote the bottom chatter
            // (except if there is an attachment viewer, as we have to force bottom)
        } else if (odoo.sale_chatter_position === "sided" && FormClassName == SaleFormClassName) {
            setAttributes(chatterContainerXml, {
                isInFormSheetBg: `__comp__.uiService.size < ${SIZES.XXL}`,
                isChatterAside: `__comp__.uiService.size >= ${SIZES.XXL}`,
            });
            setAttributes(chatterContainerHookXml, {
                class: "o-aside",
            });
            // For "bottom", we keep the chatter in the form sheet
            // (the one used for the attachment viewer case)
            // If it's not there, we create it.
        } else if (odoo.sale_chatter_position === "bottom" && FormClassName == SaleFormClassName) {
            if (webClientViewAttachmentViewHookXml) {
                const sheetBgChatterContainerHookXml = res.querySelector(
                    ".o-mail-Form-chatter.o-isInFormSheetBg"
                );
                setAttributes(sheetBgChatterContainerHookXml, {
                    "t-if": "true",
                });
                setAttributes(chatterContainerHookXml, {
                    "t-if": "false",
                });
            } else {
                const sheetBgChatterContainerHookXml =
                    chatterContainerHookXml.cloneNode(true);
                sheetBgChatterContainerHookXml.classList.add("o-isInFormSheetBg");
                setAttributes(sheetBgChatterContainerHookXml, {
                    "t-if": "true",
                    "t-attf-class": `{{ (__comp__.uiService.size >= ${SIZES.XXL} && ${
                        odoo.sale_chatter_position !== "bottom"
                    }) ? "o-aside" : "mt-4 mt-md-0" }}`,
                });
                append(formSheetBgXml, sheetBgChatterContainerHookXml);
                const sheetBgChatterContainerXml =
                    sheetBgChatterContainerHookXml.querySelector(
                        "t[t-component='__comp__.mailComponents.Chatter']"
                    );

                setAttributes(sheetBgChatterContainerXml, {
                    isInFormSheetBg: "true",
                });
                setAttributes(chatterContainerHookXml, {
                    "t-if": "false",
                });
            }
        }
        return res;
    },
    compileForm(el, params) {
        const form = super.compileForm(el, params);
        const sheet = form.querySelector(".o_form_sheet_bg");
        if (sheet && odoo.sale_chatter_position === "sided") {
            setAttributes(form, {
                "t-attf-class": "",
                class: "d-flex d-print-block flex-nowrap h-100",
            });
        }
        return form;
    },
});