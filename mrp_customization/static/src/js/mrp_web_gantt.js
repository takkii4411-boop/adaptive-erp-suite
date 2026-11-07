/** @odoo-module **/

import { GanttRenderer } from "@web_gantt/gantt_renderer";
import { ganttView } from "@web_gantt/gantt_view";
import { registry } from "@web/core/registry";
const viewRegistry = registry.category("views");

export class MrpGanttRenderer extends GanttRenderer {
    static pillTemplate = "mrp_customization.GanttRenderer.Pill";
    static components = {...GanttRenderer.components,};

    getRowTypeHeight(type) {
        return { t0: 24, t1: 50, t2: 10 }[type];
    }

    getGridStyle() {
        const rowsTemplate = this.computeRowsTemplate();
        const colsTemplate = this.computeColsTemplate();
        const style = {
            "--Gantt__RowHeader-width": `${this.rowHeaderWidth}px`,
            "--Gantt__Pill-height": "50px",
            "--Gantt__Thumbnail-max-height": "16px",
            "--Gantt__GridRows-grid-template-rows": rowsTemplate,
            "--Gantt__GridColumns-grid-template-columns": colsTemplate,
        };
        if (this.totalWidth !== null) {
            style.width = `${this.totalWidth}px`;
        }
        return Object.entries(style)
            .map((entry) => entry.join(":"))
            .join(";");
    }
}

export const MrpGanttView = {
    ...ganttView,
    Renderer: MrpGanttRenderer,
};

viewRegistry.add("mrp_gantt", MrpGanttView);