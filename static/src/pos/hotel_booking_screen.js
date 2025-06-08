/** @odoo-module */

import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";
import { Input } from "@point_of_sale/app/generic_components/inputs/input/input";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, useState, useRef } from "@odoo/owl";
import { debounce } from "@web/core/utils/timing";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class BookingScreen extends Component {
   static template = "tk_hotel_management.BookingScreen";
   static components = {Dialog, Input};
     static props = {
        booking : {
            optional: true,
        },
        getPayload: { type: Function },
        close: { type: Function },
    };


     setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.searchWordInputRef = useRef("search-word-input-booking");
        this.notification = useService("notification");
        this.ui = useService("ui");


        this.state = useState({
            query: '',
            selectedBooking: this.props.booking, // Current selected booking
            detailIsShown: this.props.editModeProps ? true : false,
            bookingList: this.getBookingList(), // Initialize booking list
        });

    }

    onClickBackButton() {
        this.props.close()
    }

    async _onPressEnterKey() {
        if (!this.state.query) {
            return;
        }
        const result = this.getFilteredBookingList();
        if (result.length > 0) {
            this.notification.add(
                _t('%s Booking(s) found for "%s".', result.length, this.state.query),
                3000
            );
        } else {
            this.notification.add(_t('No Booking found for "%s".', this.state.query), 3000);
        }
    }

     updateBookingList(event) {
        this.state.query = event.target.value.toLowerCase();
        // Update the booking list based on the query
        this.state.bookingList = this.getFilteredBookingList();
    }
    getFilteredBookingList() {
        const allBookings = this.getBookingList();
        let filteredBookings = allBookings.filter(booking =>
            booking._raw.booking_number.toLowerCase().includes(this.state.query)
        );
        return filteredBookings;
    }

     _clearSearch() {
        this.searchWordInputRef.el.value = "";
        this.state.query = "";
        this.state.bookingList = this.getBookingList(); // Reset to original list
    }

    getBookingList() {
        const currentOrder = this.pos.get_order();

        // Extract the partner name from the current order
        const partnerId = currentOrder.partner_id ? currentOrder.partner_id.id : null;
        const rawObjects = this.pos.booking
        return rawObjects.filter((booking) => {
            // Check if the booking stage is 'Confirm' or 'check_in'
            const isStageValid = booking._raw.stages === 'Confirm' || booking._raw.stages === 'check_in';
            // Check if the booking customer_id matches the partner name
            const isCustomerMatch = partnerId && booking._raw.customer_id === partnerId;
            return isStageValid && isCustomerMatch; // Return bookings that meet both conditions
        });
    }
     confirm() {
        this.props.resolve({ confirmed: true, payload: this.state.selectedPartner });
        this.pos.closeTempScreen();
    }
    onClickBooking(booking) {
        const currentOrder = this.pos.get_order();
        if (this.state.selectedBooking && this.state.selectedBooking.id == booking.id) {
            this.state.selectedBooking = null;
        } else {
            this.state.selectedBooking = booking;
        }
        this.props.getPayload(this.state.selectedBooking)
      /*  this.state.bookingList = this.getFilteredBookingList();*/
        this.props.close()
    }

}

registry.category("pos_screens").add("BookingScreen", BookingScreen);

