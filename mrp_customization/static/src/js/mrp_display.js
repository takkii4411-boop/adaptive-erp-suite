import { patch } from "@web/core/utils/patch";
import { MrpDisplayAction } from "@mrp_workorder/mrp_display/mrp_display_action";

patch(MrpDisplayAction.prototype, {
    get fieldsStructure() {
        let res = super.fieldsStructure;
        res['stock.move'].push('cnc_number');
        res['stock.move'].push('log_note');
        res['stock.move'].push('comments');
        res['stock.move.line'].push('cnc_number');
        res['stock.move.line'].push('log_note');
        res['mrp.production'].push('nesting_report_filename');
        res['mrp.production'].push('nesting_report_attachment_id');
        return res;
    }
})