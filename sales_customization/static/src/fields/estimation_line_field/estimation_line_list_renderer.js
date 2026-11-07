/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { onMounted, onPatched } from "@odoo/owl";

export class EstimationLineListRenderer extends ListRenderer {
    setup() {
        super.setup();

        onMounted(() => {
            this.addLevelBorders();
        });

        onPatched(() => {
            this.addLevelBorders();
        });
    }

    /**
     * Add border-top to rows where level_id changes from previous row
     */
    addLevelBorders() {
        const rows = this.tableRef?.el?.querySelectorAll('tbody tr.o_data_row');
        if (!rows || rows.length === 0) return;

        let previousLevelId = null;

        rows.forEach((row, index) => {
            // Get the record ID from the row
            const recordId = row.dataset.id;
            const record = this.props.list.records.find(r => r.id == recordId);

            if (!record) {
                // Remove border if no record found
                row.classList.remove('o_level_change_border');
                return;
            }

            // Get the level_id from the record data
            // level_id is a Many2one field, stored as [id, display_name] or false
            const currentLevelId = record.data.level_id ?
                (Array.isArray(record.data.level_id) ? record.data.level_id[0] : record.data.level_id) :
                null;

            // Add border if:
            // 1. Not the first row (index > 0)
            // 2. Current level is not null
            // 3. Current level is different from previous level
            if (index > 0 && currentLevelId !== null && currentLevelId?.id !== previousLevelId?.id) {
                row.classList.add('o_level_change_border');
            } else {
                row.classList.remove('o_level_change_border');
            }

            // Update previous level for next iteration
            previousLevelId = currentLevelId;
        });
    }
}
