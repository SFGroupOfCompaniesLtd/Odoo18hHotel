# -*- coding: utf-8 -*-
# Copyright 2024-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _


class ProjectTaskInherit(models.Model):
    """Project Task Inherit"""
    _inherit = 'project.task'

    start_date = fields.Datetime('Assign Date')
    room_booking_id = fields.Many2one('hotel.booking')
    hall_booking_id = fields.Many2one('hotel.feast')

    def action_view_room_booking(self):
        return {
            'name': (_('Room Booking')),
            'view_type': 'form',
            'res_model': 'hotel.booking',
            'res_id': self.room_booking_id.id,
            'view_mode': 'form',
            'type': "ir.actions.act_window"
        }

    def action_view_hall_booking(self):
        return {
            'name': (_('Hall Booking')),
            'view_type': 'form',
            'res_model': 'hotel.feast',
            'res_id': self.hall_booking_id.id,
            'view_mode': 'form',
            'type': "ir.actions.act_window"
        }
