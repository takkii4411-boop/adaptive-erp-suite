/** @odoo-module **/

import { TagsList } from "@web/core/tags_list/tags_list";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(TagsList.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
    },

    async onDrawingTagClick(ev, self) {
        ev.stopPropagation();
        ev.preventDefault();
        const tagEl = ev.currentTarget;
        const tagAtt = tagEl.parentElement.parentElement;
        const tagField = tagAtt.getAttribute('name');
        const drawingId = tagEl?.dataset?.id;
        if (tagAtt && tagField != 'drawing_nos_limited') return;
        if (!drawingId) return;

        const docs = await self.orm.searchRead(
            "documents.document",
            [["id", "=", drawingId]],
            ["access_token"]
        );
        if (docs.length) {
            window.open(`/odoo/documents/${docs[0].access_token}`, "_blank");
        }
    },
});