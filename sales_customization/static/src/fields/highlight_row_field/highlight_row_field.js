/** @odoo-module **/

import { registry } from "@web/core/registry";
import { booleanField } from "@web/views/fields/boolean/boolean_field";
import { Component, onMounted, onWillUnmount, onPatched } from "@odoo/owl";

export class HighlightRowField extends booleanField.component {
    setup() {
        super.setup();

        onMounted(() => {
            this.updateRowHighlight();
        });

        onPatched(() => {
            this.updateRowHighlight();
        });

        onWillUnmount(() => {
            this.removeRowHighlight();
        });
    }

    /**
     * Find the table row (tr) element containing this field
     */
    getTableRow() {
        // Try multiple ways to access the root element
        let element = null;

        // Method 1: Check __owl__ refs
        if (this.__owl__ && this.__owl__.refs && this.__owl__.refs.root) {
            element = this.__owl__.refs.root.el;
        }

        // Method 2: Direct el property
        if (!element && this.el) {
            element = this.el;
        }

        // Method 3: Access through __owl__.bdom
        if (!element && this.__owl__ && this.__owl__.bdom) {
            element = this.__owl__.bdom.bdom.el;
        }

        if (!element) {
            console.warn('HighlightRowField: Could not find element', this);
            return null;
        }

        // Traverse up the DOM to find the <tr> element
        let currentElement = element;
        while (currentElement && currentElement.tagName !== 'TR') {
            currentElement = currentElement.parentElement;
            if (!currentElement || currentElement === document.body) {
                console.warn('HighlightRowField: Could not find TR element');
                return null;
            }
        }
        return currentElement;
    }

    /**
     * Update the row highlight based on field conditions
     */
    updateRowHighlight() {
        const row = this.getTableRow();
        if (!row) return;

        // Get the current record's values
        const record = this.props.record;
        const isCopiedLine = record.data.is_copied_line;
        const isExistingLine = record.data.is_existing_line;
        const levelId = record.data.level_id;
        const parentId = record.data.parent_id;

        // Condition: is_copied_line == true && level_id == false
        const shouldHighlight = isCopiedLine === true && !levelId;
        const shouldHighlightExisting = isExistingLine === false && parentId;

        if (shouldHighlight) {
            // Add highlight class
            row.classList.add('o_row_highlight_warning');
        } else {
            // Remove highlight
            row.classList.remove('o_row_highlight_warning');
        }

        if (shouldHighlightExisting) {
            // Add highlight class
            row.classList.add('o_row_highlight_warning_ext');
        } else {
            // Remove highlight
            row.classList.remove('o_row_highlight_warning_ext');
        }
    }

    /**
     * Remove highlight when component is unmounted
     */
    removeRowHighlight() {
        const row = this.getTableRow();
        if (!row) return;

        row.classList.remove('o_row_highlight_warning');
        row.style.backgroundColor = '';
    }
}

export const highlightRowBoolean = {
    ...booleanField,
    component: HighlightRowField,
};

registry.category("fields").add("highlight_row_boolean", highlightRowBoolean);
