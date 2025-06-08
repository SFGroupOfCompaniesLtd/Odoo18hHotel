# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelCustomerBooking(models.Model):
    _inherit = 'res.partner'

    is_agent = fields.Boolean(string="Agent")
    is_driver = fields.Boolean(string='Driver')

    def unlink(self):
        for rec in self:
            booking = self.env['hotel.booking'].search([('customer_id', '=', rec.id)], limit=1)
            if booking:
                raise ValidationError(
                    _('Because this record is associated with a room booking record, you are not permitted to delete it.'))

            hall = self.env['hotel.feast'].search([('customer_id', '=', rec.id)], limit=1)
            if hall:
                raise ValidationError(
                    _("Because this record is associated with a hall booking record, you are not permitted to delete it."))

            agent = self.env['hotel.booking'].search([('agent_id', '=', rec.id)], limit=1)
            if agent:
                raise ValidationError(
                    _('Because this agent record is associated with a room booking record, you are not permitted to delete it.'))

            transport = self.env['hotel.transport'].search([('driver_id', '=', rec.id)], limit=1)
            if transport:
                raise ValidationError(
                    _('Because this record is associated with a transport service record as a driver, you are not permitted to delete it.'))
        return super(HotelCustomerBooking, self).unlink()
