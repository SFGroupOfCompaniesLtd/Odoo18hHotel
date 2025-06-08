# -*- coding: utf-8 -*-

import logging
from datetime import date, timedelta, datetime

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def get_room_status(today, last_day):
    timeline, room_status = [], []
    room_ids = request.env['hotel.room'].sudo().search([])

    for x in range((last_day - today).days + 1):
        current_date = today + timedelta(days=x)
        day_name = current_date.strftime("%A")[:3]
        date_entry = day_name + ' ' + str(current_date.day) + '/' + str(
            current_date.month)
        timeline.append(date_entry)
    for room in room_ids:
        rooms = []
        booking_numbers = []
        for x in range((last_day - today).days + 1):
            current_date = today + timedelta(days=x)
            book_id = request.env['hotel.room.details'].sudo().search(
                [('room_id', '=', room.id),
                 ('stages', '!=', 'Available'),
                 ('check_in', '<=', current_date),
                 ('check_out', '>', current_date)])

            booked = False
            booking_num = False
            if book_id:
                booked = book_id.id
                booking_num = book_id.booking_id.booking_number
            rooms.append(booked)
            booking_numbers.append(booking_num)

        room_details = room.room_no + (
            " - " + room.room_type_id.name if room.room_type_id else '')
        room_status.append((room_details, rooms, booking_numbers))
    return [timeline, room_status]


class RoomDashboard(http.Controller):

    @http.route('/get/rooms/status', type='json', auth='user')
    def get_statistics(self):
        today = date.today()
        last_day = today + timedelta(days=31)
        room_status = get_room_status(today, last_day)
        return room_status

    @http.route('/get/rooms/status/by/date', type='json', auth='user')
    def get_room_stats_by_date(self, **kw):
        if not kw.get('start_date') and not kw.get('end_date'):
            return
        today = datetime.strptime(kw.get('start_date'), '%Y-%m-%d').date()
        last_day = datetime.strptime(kw.get('end_date'), '%Y-%m-%d').date()
        room_status = get_room_status(today, last_day)
        return room_status
