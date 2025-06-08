# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LaundryItem(models.Model):
    _name = "laundry.item"
    _description = "Laundry item"

    name = fields.Char(string='Laundry Items')
    color = fields.Integer(string='Color')


class HotelLaundry(models.Model):
    _name = "laundry.service.type"
    _description = "Laundry Service Type"
    _rec_name = 'service_name'

    service_name = fields.Char('Service Name', required=True, )
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    charges = fields.Monetary(string='Price', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    laundry_service_type_number = fields.Char(string='', copy=False,
                                              readonly=True,
                                              default=lambda self: 'New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('laundry_service_type_number', 'New') == 'New':
                vals['laundry_service_type_number'] = self.env[
                                                          'ir.sequence'].next_by_code(
                    'rest.laundry.sequence') or 'New'
        return super(HotelLaundry, self).create(vals_list)

    @api.onchange('product_id')
    def onchange_product_set_charges(self):
        self.charges = self.product_id.list_price


class HotelLaundryDetails(models.Model):
    _name = "laundry.service"
    _description = "Laundry Service Details"
    _rec_name = 'service_name_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    laundry_service_number = fields.Char(string='', copy=False, readonly=True,
                                         default=lambda self: 'New')
    service_name_id = fields.Many2one('laundry.service.type',
                                      string='Service Name', required=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    charges = fields.Monetary(string='Charge',
                              related='service_name_id.charges', required=True)
    room_ids = fields.Many2many('hotel.room', string="Hotel Rooms",
                                compute="compute_hotel_rooms")
    room_id = fields.Many2one('hotel.room', string='Room', required=True,
                              domain="[('id','in',room_ids)]")
    responsible_id = fields.Many2one('hr.employee',
                                     domain="[('is_staff', '=', True)]",
                                     string='Responsible',
                                     required=True)
    deadline_date = fields.Datetime(string='Deadline')
    booking_id = fields.Many2one('hotel.booking', required=True, domain=[
        ('stages', 'in', ['check_in', 'Confirm'])])
    customer_id = fields.Many2one(related='booking_id.customer_id',
                                  string='Customer')
    laundry_item_ids = fields.Many2many('laundry.item', string='Laundry Items',
                                        required=True)
    color = fields.Integer(string='Color')
    quantity = fields.Integer(string='Quantity', required=True)
    total_charges = fields.Monetary(string='Total Charges',
                                    compute='laundry_charges')
    stages = fields.Selection(
        [('Request', 'Request'), ('In Progress', 'In Progress'),
         ('Completed', 'Completed')],
        string='Status', default='Request')

    def unlink(self):
        for rec in self:
            if rec.stages != 'Request':
                raise ValidationError(
                    _('Records can only be deleted during the request stage.'))
        return super(HotelLaundryDetails, self).unlink()

    def confirm_to_send_laundry(self):
        self.stages = 'In Progress'

    def laundry_to_done(self):
        self.stages = 'Completed'

    @api.depends('charges', 'quantity')
    def laundry_charges(self):
        for rec in self:
            total_charges = rec.total_charges + (rec.charges * rec.quantity)
            rec.total_charges = total_charges

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('laundry_service_number', 'New') == 'New':
                vals['laundry_service_number'] = self.env[
                                                     'ir.sequence'].next_by_code(
                    'rest.laundry.sequence') or 'New'
        return super(HotelLaundryDetails, self).create(vals_list)

    @api.depends('booking_id', 'room_id')
    def compute_hotel_rooms(self):
        for rec in self:
            id = self._context.get('booking_id')
            booking_id = False
            if id:
                booking_id = id
            elif not id:
                booking_id = rec.booking_id.id
            room_ids = self.env['hotel.room.details'].sudo().search(
                [('booking_id', '=', booking_id)]).mapped(
                'room_id').mapped('id')
            rec.room_ids = room_ids

    @api.constrains('deadline_date')
    def check_deadline_date(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.deadline_date:
                if rec.deadline_date <= now:
                    raise ValidationError(
                        _('The deadline cannot be from the past.'))
