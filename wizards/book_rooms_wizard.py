# -*- coding: utf-8 -*-
# Copyright 2024-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class BookRoomWizard(models.TransientModel):
    """Wizard to book rooms"""
    _name = 'book.room.wizard'
    _description = __doc__

    check_in_date = fields.Date('Check-in Date')
    check_out_date = fields.Date('Check-out Date')
    room_type_ids = fields.Many2many('hotel.room.type', string='Room Types')
    booked_room_ids = fields.Many2many(
        'hotel.room', column1='booked_room', column2='rooms',
        relation='booked_room_rel',
        compute='_compute_booked_room_ids')
    room_ids = fields.Many2many(
        'hotel.room', column1='book_room',
        column2='room_booking',
        relation='book_available_room_rel',
        domain="[('id', 'not in', booked_room_ids), "
               "('room_type_id', 'in', room_type_ids)]", string='Rooms')
    adults_count = fields.Integer('Adults')
    children_count = fields.Integer('Children')
    alert_message = fields.Char(compute="_compute_alert_message")
    hotel_booking_id = fields.Many2one('hotel.booking')
    room_adult_capacity = fields.Integer(
        compute="_compute_room_adult_capacity")
    room_child_capacity = fields.Integer(
        compute="_compute_room_child_capacity")

    def default_get(self, fields_list):
        res = super(BookRoomWizard, self).default_get(fields_list)
        active_id = self._context.get('active_id')
        booking_id = self.env['hotel.booking'].sudo().browse(active_id)
        res['hotel_booking_id'] = booking_id.id
        res['adults_count'] = booking_id.adults
        res['children_count'] = booking_id.children
        return res

    @api.depends('room_ids')
    def _compute_room_adult_capacity(self):
        for rec in self:
            adults = 0
            if rec.room_ids:
                for data in rec.room_ids:
                    adults += data.room_type_id.adult_capacity
            rec.room_adult_capacity = adults

    @api.depends('room_ids')
    def _compute_room_child_capacity(self):
        for rec in self:
            children = 0
            if rec.room_ids:
                for data in rec.room_ids:
                    children += data.room_type_id.child_capacity
            rec.room_child_capacity = children

    @api.depends('check_in_date', 'check_out_date')
    def _compute_booked_room_ids(self):
        """Find Booked Rooms"""
        for rec in self:
            booked_rooms = self.env['hotel.room.details'].sudo().search(
                [
                    ('check_in', '<', rec.check_out_date),
                    ('check_out', '>',
                     rec.check_in_date),
                    ('stages', '!=', 'Available')]).mapped(
                'room_id').ids
            rec.booked_room_ids = booked_rooms

    @api.depends('check_in_date', 'check_out_date')
    def _compute_alert_message(self):
        """Date Validation Alert Message"""
        message = ""
        today = fields.Date.today()
        back_date_check_in_allowed = self.env[
            'ir.config_parameter'].sudo().get_param(
            'tk_hotel_management.back_date_check_in')
        if self.check_in_date and self.check_out_date:
            if self.check_in_date > self.check_out_date:
                message = ("The check-in date of room booking must be earlier "
                           "than the check-out date.")
            if self.check_in_date == self.check_out_date:
                message = ("The check-in date and the check-out date cannot "
                           "be the same.")
        if (self.check_in_date and self.check_in_date < today and
                not back_date_check_in_allowed):
            message = "The date of check-in should not be outdated."
        self.alert_message = message

    @api.onchange('room_type_ids')
    def _onchange_room_type_ids(self):
        self.room_ids = [(5, 0, 0)]

    def action_create_hotel_room_bookings(self):
        """Validate dates and capacity and after that create bookings"""
        today = fields.Date.today()
        back_date_check_in_allowed = self.env[
            'ir.config_parameter'].sudo().get_param(
            'tk_hotel_management.back_date_check_in')
        for rec in self:
            # Date Validations
            if rec.check_in_date > rec.check_out_date:
                raise ValidationError(_(
                    "The check-in date of room booking must be earlier "
                    "than the check-out date."))
            if rec.check_in_date < today and not back_date_check_in_allowed:
                raise ValidationError(
                    _("The date of check-in should not be outdated."))
            if rec.check_in_date == rec.check_out_date:
                raise ValidationError(
                    _("The check-in date and the check-out date cannot be "
                      "the same."))
            # Capacity Validation
            if rec.room_adult_capacity < rec.adults_count:
                raise ValidationError(_("The adult's capacity exceeded"))
            extra_children = rec.children_count - rec.room_child_capacity
            adults = rec.adults_count
            total = extra_children + adults
            if (rec.room_child_capacity < rec.children_count
                    and rec.adults_count <= rec.room_adult_capacity < total):
                raise ValidationError(_("The children's capacity exceeded"))

            # Add Rooms
            if rec.room_ids:
                for data in rec.room_ids:
                    line_data = {
                        'check_in': rec.check_in_date,
                        'check_out': rec.check_out_date,
                        'room_id': data.id,
                        'booking_id': rec.hotel_booking_id.id,
                    }
                    room_line_id = self.env[
                        'hotel.room.details'].sudo().create(line_data)
                    room_line_id._onchange_room_get_taxes()
                    room_line_id._onchange_get_per_night_room_charges()
                    room_line_id.onchange_total_price()
