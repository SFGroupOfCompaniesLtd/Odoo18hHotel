/** @odoo-module */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.booking_id = this.booking_id || 0 ;
    },
   set_hotelBooking(booking) {
        this.assert_editable();
        this.update({ booking_id: booking });
        this.updatePricelistAndFiscalPosition(booking);
    },
    get_hotelBooking() {
        return this.booking_id;
    },
});

