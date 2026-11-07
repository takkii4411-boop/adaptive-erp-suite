/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer";
import { onMounted, onPatched, useEffect, useRef } from "@odoo/owl";

export class SaleEstimationFormRenderer extends FormRenderer {
    setup() {
        super.setup();
        this.rootRef = useRef("compiled_view_root");

        // Align filters after component is mounted and patched
        onMounted(() => {
            this.alignFiltersWithColumns();
        });

        onPatched(() => {
            this.alignFiltersWithColumns();
        });
    }

    /**
     * Dynamically align filter fields with table columns
     * by reading actual column widths from the rendered table
     */
    alignFiltersWithColumns() {
        // Small delay to ensure table is fully rendered
        setTimeout(() => {
            const table = this.rootRef.el?.querySelector('div[name="estimation_line_ids"] table.o_list_table');
            const filterWrapper = this.rootRef.el?.querySelector('.estimation_filter_wrapper');

            if (!table || !filterWrapper) {
                console.log("Table or filter wrapper not found");
                return;
            }

            // Get all table header cells
            const headerCells = table.querySelectorAll('thead tr:first-child th');
            const filterCells = filterWrapper.querySelectorAll('.filter-cell');

            console.log("Found table headers:", headerCells.length);
            console.log("Found filter cells:", filterCells.length);

            // Map column names to filter cells for alignment
            const columnMap = {
                'is_select': 0,      // Checkbox
                'action_button': 1,  // BOM button
                'level_id': 2,
                'product_id': 3,
                'joinery_no': 4,
                'description': 5,
                'desc_button': 6,
                'room': 7,
                'drawing_number': 8,
                'internal_notes': 9,
                'custom_exclusion': 10,
                'qty': 11,
                'price_unit': 12,
                'price_total': 13,
                'is_copied_line': 14,
            };

            // Apply widths from table columns to filter cells
            headerCells.forEach((th, index) => {
                const width = th.offsetWidth;
                if (filterCells[index]) {
                    filterCells[index].style.width = width + 'px';
                    filterCells[index].style.minWidth = width + 'px';
                    filterCells[index].style.maxWidth = width + 'px';
                }
            });

            console.log("Filter alignment completed");
        }, 100);
    }
}