from datetime import timedelta
from odoo import fields, api, models


class RoomChange(models.TransientModel):
    _name = 'room.change'
    _description = 'Room Change'
    _rec_name = 'room_id'

    old_room_ids = fields.Many2many('hotel.room.details', string="Old Rooms",
                                    compute="compute_old_room")
    old_room_id = fields.Many2one('hotel.room.details',
                                  string="Room To Change",
                                  domain="[('id','in',old_room_ids)]")
    room_ids = fields.Many2many('hotel.room', string="New Hotel Rooms",
                                compute='compute_hotel_rooms')
    room_id = fields.Many2one('hotel.room', string="Room",
                              domain="[('id','not in',room_ids)]")
    booking_id = fields.Many2one('hotel.booking', string="Booking")
    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")
    is_room_change_charges = fields.Boolean(string="Is Charges")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    charges = fields.Monetary(string="Room Change Charges")
    room_adult_capacity = fields.Integer(
        related="room_id.room_type_id.adult_capacity")
    room_child_capacity = fields.Integer(
        related="room_id.room_type_id.child_capacity")

    @api.model
    def default_get(self, fields):
        res = super(RoomChange, self).default_get(fields)
        active_id = self._context.get('active_id')
        res['booking_id'] = active_id
        return res

    @api.depends('check_in', 'check_out', 'room_id')
    def compute_hotel_rooms(self):
        for rec in self:
            room_ids = self.env['hotel.room.details'].sudo().search(
                [('check_in', '<=', rec.check_out),
                 ('check_out', '>=', rec.check_in),
                 ('stages', '!=', 'Available')]).mapped(
                'room_id').ids
            rec.room_ids = room_ids

    @api.depends('old_room_id', 'booking_id')
    def compute_old_room(self):
        for rec in self:
            ids = []
            for data in rec.booking_id.room_ids:
                if data.stages == "Booked":
                    ids.append(data.id)
            rec.old_room_ids = ids

    @api.onchange('old_room_id')
    def _onchange_old_room_check_in_check_out(self):
        for rec in self:
            if rec.old_room_id:
                rec.check_in = rec.old_room_id.check_in
                rec.check_out = rec.old_room_id.check_out

    def get_dates_between(self, start_date, end_date):
        date_list = []

        current_date = start_date

        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)

        return set(date_list)

    def action_room_change(self):
        if self.is_room_change_charges:
            data = {
                'service': 'Room Change : ' + self.old_room_id.room_id.room_no + " to " + self.room_id.room_no,
                'quantity': 1,
                'amount': self.charges,
                'booking_id': self.booking_id.id
            }
            self.env['hotel.extra.services'].create(data)
        if self.check_out and self.check_in and self.room_id:
            booking_dates = self.get_dates_between(start_date=self.check_in,
                                                   end_date=self.check_out)
            base_price = self.room_id.room_type_id.base_price
            charges = []
            if self.room_id.room_type_id.is_seasonal_price and self.room_id.room_type_id.seasonal_price_line_ids:
                for rec in self.room_id.room_type_id.seasonal_price_line_ids:
                    season_dates = self.get_dates_between(
                        start_date=rec.start_date, end_date=rec.end_date)
                    if booking_dates.intersection(season_dates):
                        if rec.increment_type == 'percentage':
                            amount = (base_price * rec.increment_val) / 100
                            charges.append(amount)
                        if rec.increment_type == 'fixed':
                            charges.append(rec.increment_val)

            if len(charges) > 0:
                avg_room_price = base_price + sum(charges) / len(charges)
            else:
                avg_room_price = base_price
            self.old_room_id.charges_per_night = avg_room_price
        self.old_room_id.room_id = self.room_id.id
        self.old_room_id.tax_ids = [(5, 0, 0)]
        self.old_room_id.tax_ids = self.room_id.room_type_id.tax_ids.ids
        self.old_room_id.onchange_total_price()
        self.booking_id.compute_total_amount()
