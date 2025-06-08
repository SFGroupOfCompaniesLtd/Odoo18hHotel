import { registry } from "@web/core/registry";
import { Base } from "@point_of_sale/app/models/related_models";

export class HotelBooking extends Base {
    static pythonModel = "hotel.booking";

    setup(vals) {
        super.setup(vals);
        this.booking_number = vals.booking_number || 0;
        this.uiState = {
            initialPosition: {},
        };
    }


}
registry.category("pos_available_models").add(HotelBooking.pythonModel, HotelBooking);





