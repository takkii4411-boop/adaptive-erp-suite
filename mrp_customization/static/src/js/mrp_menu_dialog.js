import { patch } from "@web/core/utils/patch";
import { MrpMenuDialog } from "@mrp_workorder/mrp_display/dialog/mrp_menu_dialog";

patch(MrpMenuDialog.prototype, {
    async previewNR() {
        let attId = null;
        let filename = null;

        if (this.props.record.resModel === "mrp.production") {
            const attachment = this.props.record.data.nesting_report_attachment_id;
            attId = attachment ? attachment.id : null;
            filename = this.props.record.data.nesting_report_filename;
        }

        if (!attId) {
            return;
        }

        const url = `/web/content/${attId}/${filename}?download=false`;

        await this.action.doAction({
            type: "ir.actions.act_url",
            target: "new",
            url: url,
        });
    }

})