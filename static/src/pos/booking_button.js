/** @odoo-module */
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { SelectPartnerButton } from "@point_of_sale/app/screens/product_screen/control_buttons/select_partner_button/select_partner_button";
import { patch } from "@web/core/utils/patch";
import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { BookingScreen } from "./hotel_booking_screen";
import {
    makeAwaitable,
    ask,
    makeActionAwaitable,
} from "@point_of_sale/app/store/make_awaitable_dialog";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
        this.ui = useService('ui')
    },

    async SelectBooking(){
       const currentOrder = this.pos.get_order();

        if (!currentOrder) {
            return;
        }
        const currentBooking = currentOrder.booking_id || false;
        if (currentBooking && currentOrder.getHasRefundLines()) {
            this.dialog.add(AlertDialog, {
                title: _t("Can't change Bookings"),
                body: _t(
                    "This order already has refund lines for %s. We can't change the customer associated to it. Create a new order for the new customer.",
                    currentBooking.booking_number
                ),
            });
            return currentBooking;
        }

        const payload = await makeAwaitable(this.dialog, BookingScreen, {
                booking: currentBooking,
                getPayload: (newBooking) =>  currentOrder.set_hotelBooking(newBooking),
        });

        if (payload) {
            currentOrder.set_hotelBooking(payload)
            currentOrder.booking_id = payload;
        } else {
            currentOrder.set_hotelBooking(false)
            currentOrder.booking_id = false;
        }

        return currentBooking;

    }
 })
 patch(ControlButtons, {
    components: {
        ...ControlButtons.components,
        SelectPartnerButton,
    },
});


