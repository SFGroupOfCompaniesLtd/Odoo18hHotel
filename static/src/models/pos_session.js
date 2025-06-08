/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async processServerData() {
        await super.processServerData();
         this.booking = this.models["hotel.booking"].getAll()
    }

});

