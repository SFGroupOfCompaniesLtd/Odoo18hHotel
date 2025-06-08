# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Location(models.Model):
    _name = 'location.detail'
    _description = 'Location details'

    name = fields.Char('Location Name', required=True)
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street-2')
    city = fields.Char(string='City')


class HotelTransportVehicle(models.Model):
    _name = 'transport.vehicle'
    _description = 'Vehicle details'

    avatar = fields.Binary()
    name = fields.Char('Vehicle Type', required=True)


class TransportVehicle(models.Model):
    _name = 'vehicle.type'
    _description = 'Vehicle details'

    avatar = fields.Binary()
    name = fields.Char('Vehicle Name', required=True)
    number = fields.Char('Vehicle Number ', required=True)
    vehicle_number = fields.Char(string='', copy=False, readonly=True,
                                 default=lambda self: 'New')
    vehicle_type_id = fields.Many2one(
        'transport.vehicle', 'Vehicle Type', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                  string='Currency')
    charges = fields.Monetary('Charge', required=True)
    capacity = fields.Integer(string='Capacity', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('vehicle_number', 'New') == 'New':
                vals['vehicle_number'] = self.env['ir.sequence'].next_by_code(
                    'rest.vehicle.sequence') or 'New'
        return super(TransportVehicle, self).create(vals_list)


class HotelTransport(models.Model):
    _name = 'hotel.transport'
    _description = 'Hotel Transport details'
    _rec_name = 'transport_type'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    transport_type = fields.Selection([('Pickup', 'Pickup'), ('Drop', 'Drop')],
                                      string=' Transport Type', required=True)
    stage = fields.Selection(
        [('pending', 'Pending'), ('complete', 'Complete'), ('cancel', 'Cancel')],
        default="pending", copy=False)
    location = fields.Char('Location Name', required=True)
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street-2')
    city = fields.Char(string='City', required=True)
    time = fields.Datetime('Start Time', required=True)
    end_time = fields.Datetime('End Time')
    charges = fields.Monetary(
        related='transport_mode_id.charges', string='Charge', required=True)
    driver_id = fields.Many2one(
        'res.partner',
        'Driver',
        domain="[('is_driver', '=', True), ('id', 'not in', unavailable_driver_ids)]",
        copy=False
    )
    transport_mode_id = fields.Many2one(
        'vehicle.type',
        'Vehicle',
        domain="[('id', 'not in', unavailable_vehicle_ids)]",
        copy=False
    )
    km = fields.Integer(string='Total KM', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                  string='Currency')
    total_charges = fields.Monetary(
        'Charge ', compute='total_charges_transport')
    booking_id = fields.Many2one('hotel.booking', required=True,
                                 domain=[('stages', 'in', ['check_in', 'Confirm'])])
    customer_id = fields.Many2one(
        related='booking_id.customer_id', string='Customer')
    transport_number = fields.Char(string='', copy=False, readonly=True,
                                   default=lambda self: 'New')
    unavailable_vehicle_ids = fields.Many2many('vehicle.type',
                                               compute='_compute_unavailable_vehicle_driver',
                                               copy=False)
    unavailable_driver_ids = fields.Many2many('res.partner',
                                              compute='_compute_unavailable_vehicle_driver',
                                              copy=False)

    @api.depends('time', 'end_time')
    def _compute_unavailable_vehicle_driver(self):
        """Not Available Vehicles and Drivers"""
        for rec in self:
            vehicle_ids = self.env['vehicle.type'].sudo().search([]).ids
            driver_ids = self.env['res.partner'].sudo().search(
                [('is_driver', '=', True)]).ids
            if rec.time and rec.end_time:
                transport_services = self.env['hotel.transport'].sudo().search(
                    [
                        ('time', '<', rec.end_time),
                        ('end_time', '>', rec.time),
                        ('stage', '=', 'pending')
                    ]
                )
                vehicle_ids = transport_services.mapped(
                    'transport_mode_id').ids
                driver_ids = transport_services.mapped('driver_id').ids
            rec.unavailable_driver_ids = driver_ids
            rec.unavailable_vehicle_ids = vehicle_ids

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('transport_number', 'New') == 'New':
                vals['transport_number'] = self.env['ir.sequence'].next_by_code(
                    'rest.transport.booking') or 'New'
        return super(HotelTransport, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.stage != 'pending':
                raise ValidationError(
                    _('Records can only be deleted during the pending stage.'))
        return super(HotelTransport, self).unlink()

    @api.constrains('time')
    def check_time_of_transport(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.time < now:
                raise ValidationError(
                    _('The start time of transportation can not be outdated.'))
            if rec.end_time and rec.end_time < rec.time:
                raise ValidationError(
                    _('The end time of the transport service can not be earlier than its start time.')
                )
            if rec.time and rec.end_time and rec.end_time == rec.time:
                raise ValidationError(
                    _('The start time and end time of transport service can not be same.')
                )
            if rec.km <= 0:
                raise ValidationError(
                    _("The total kilometer cannot be zero for transport service record."))

    @api.depends('total_charges', 'charges')
    def total_charges_transport(self):
        for rec in self:
            rec.total_charges = rec.charges * rec.km

    def action_complete(self):
        self.stage = "complete"

    def action_cancel(self):
        self.stage = "cancel"
