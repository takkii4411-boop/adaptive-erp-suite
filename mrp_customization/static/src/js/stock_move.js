/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { StockMove } from "@mrp_workorder/mrp_display/mrp_record_line/stock_move";
import { LogNoteDialog } from "./log_note_dialog";

patch(StockMove.prototype, {
    get cncNo() {
        const move = this.props.record.data;
        return move.cnc_number || "" ;
    },

    get Comments() {
        const move = this.props.record.data;
        return move.comments || "" ;
    },

    async showLogNote() {
        const move = this.props.record.data;
        const note = move.log_note || "" ;
        if (!note) {
            return;
        }
        this.dialog.add(LogNoteDialog, {
            note: note,
        });
    },
});