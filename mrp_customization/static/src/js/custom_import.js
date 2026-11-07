/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
export class MrpProductionListController extends ListController {
  setup() {
      super.setup();
  }
  async onClickUploadCSV() {
        try {
            const action = await this.orm.call(
                "mrp.production",
                "action_open_csv_import_wizard",
                [],
                {}
            );

            await this.actionService.doAction(action);
        } catch (error) {
            console.error("Error opening CSV wizard:", error);
            this.env.services.notification.add("Failed to open import wizard", { type: "danger" });
        }
    }
}
MrpProductionListController.template = "mrp_customization.MrpListView.Buttons";
export const mrpProductionCustomView = {
   ...listView,
   Controller: MrpProductionListController,
};
registry.category("views").add("button_in_tree", mrpProductionCustomView);
