# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError, AccessError, UserError


class HotelRestaurant(models.Model):
    _name = "hotel.restaurant"
    _description = "Reservation Details"
    _rec_name = 'reservation_number'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    reservation_number = fields.Char(string='', copy=False, readonly=True,
                                     default=lambda self: 'New')
    is_table_booking = fields.Boolean(string='Table Reservation')
    room_ids = fields.Many2many('hotel.room', string="Hotel Rooms",
                                compute="compute_hotel_rooms")
    room_id = fields.Many2one('hotel.room', string='Room',
                              domain="[('id','in',room_ids)]")
    booking_id = fields.Many2one('hotel.booking', domain=[
        ('stages', 'in', ['check_in', 'Confirm'])])
    customer_id = fields.Many2one(related='booking_id.customer_id',
                                  string='Customer')
    customer_foods_ids = fields.One2many('customer.food.order',
                                         'restaurant_id')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    total_charges = fields.Monetary(string='Total Price',
                                    compute='restaurant_food_charges')
    stages = fields.Selection(
        [('Confirm', 'Confirm'), ('Delivered', 'Delivered')],
        string='Status ', default='Confirm')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    feast_id = fields.Many2one('hotel.feast')
    # Table Details
    table_ids = fields.Many2many('table.details', compute='compute_table_ids',
                                 string="Tables")
    table_id = fields.Many2one('table.details', string="Table",
                               domain="[('id', 'not in', table_ids)]")
    table_stages = fields.Selection(related="table_id.stages")
    table_capacity = fields.Integer(related="table_id.capacity",
                                    string="Capacity")
    no_of_person = fields.Integer(string="No of People")
    res_start = fields.Datetime(string="Reservation Start")
    res_end = fields.Datetime(string="Reservation End")
    table_charges = fields.Monetary(string="Reservation Charges")

    table_booking_ids = fields.One2many('hotel.table.booking', 'restaurant_id')
    no_of_tables = fields.Integer(compute="_compute_no_of_tables")
    is_booked = fields.Boolean()
    is_free = fields.Boolean()
    total_reservation_charges = fields.Monetary(
        compute="_compute_total_reservation_charges")

    @api.depends('table_booking_ids')
    def _compute_total_reservation_charges(self):
        for rec in self:
            charges = 0
            if rec.table_booking_ids:
                for data in rec.table_booking_ids:
                    charges += data.reservation_charges
            rec.total_reservation_charges = charges

    @api.depends('table_booking_ids')
    def _compute_no_of_tables(self):
        for rec in self:
            rec.no_of_tables = len(rec.table_booking_ids.ids)

    @api.depends('customer_foods_ids', )
    def restaurant_food_charges(self):
        for rec in self:
            total_charges = 0.0
            for data in rec.customer_foods_ids:
                total_charges = total_charges + data.subtotal_amount
            if rec.is_table_booking:
                total_charges = total_charges + rec.total_reservation_charges
            rec.total_charges = total_charges

    def confirm_to_delivered(self):
        if not any(stages == 'Delivered' for stages in
                   set(self.customer_foods_ids.mapped('stages'))):
            raise ValidationError(
                _("You can not complete because food items is yet to be delivered."))
        self.stages = 'Delivered'

    # def write(self, vals):
    #     if any(stages == 'Delivered' for stages in set(self.mapped('stages'))):
    #         raise UserError(_("Because order is delivered, editing order is not allowed."))
    #     else:
    #         return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reservation_number', 'New') == 'New':
                vals['reservation_number'] = self.env[
                                                 'ir.sequence'].next_by_code(
                    'rest.restaurant.sequence') or 'New'
        return super(HotelRestaurant, self).create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.stages != 'Confirm':
                raise ValidationError(
                    _("The record of the delivered order cannot be deleted."))
        return super(HotelRestaurant, self).unlink()

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
                'room_id').mapped(
                'id')
            rec.room_ids = room_ids

    @api.depends('res_start', 'res_end', 'table_id')
    def compute_table_ids(self):
        for rec in self:
            table_ids = self.env['hotel.table.booking'].sudo().search(
                [('start_date', '<=', rec.res_end),
                 ('end_date', '>=', rec.res_start),
                 ('stage', '!=', 'a')]).mapped('table_id').ids
            rec.table_ids = table_ids

    def action_book_table(self):
        data = {
            'table_id': self.table_id.id,
            'start_date': self.res_start,
            'end_date': self.res_end,
            'stage': 'b'
        }
        table_booking = self.env['hotel.table.booking'].create(data)
        table_booking.table_id.stages = "Booked"

    def action_free_table(self):
        table_booking = self.env['hotel.table.booking'].search(
            [('table_id', '=', self.table_id.id)])
        table_booking.stage = "a"
        table_booking.table_id.stages = "Available"

    def book_tables(self):
        if self.no_of_tables <= 0:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': (_('Add tables for reservation !')),
                    'sticky': False,
                }
            }
            return message
        for rec in self.table_booking_ids:
            booked_table_id = self.env['hotel.table.booking'].sudo().search(
                [('start_date', '<=', rec.end_date),
                 ('end_date', '>=',
                  rec.start_date),
                 ('stage', '!=', 'a'),
                 ('table_id', '=', rec.table_id.id)],
                limit=1)
            if booked_table_id:
                raise ValidationError(
                    _("Same tables are booked for the same time please choose another table to proceed."))
            rec.stage = "b"
        self.is_booked = True

    def free_tables(self):
        for rec in self.table_booking_ids:
            if rec.stage == 'b':
                rec.stage = 'a'
        self.is_free = True


class RestaurantFoodCategory(models.Model):
    _name = 'food.category'
    _description = "Food Category Details"

    name = fields.Char('Food Category', required=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')


class RestaurantFood(models.Model):
    _name = 'food.item'
    _description = "Food Details"

    name = fields.Char('Food', required=True)
    food_category = fields.Many2one('food.category', required=True)
    description = fields.Text('Description')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    price = fields.Monetary(string='Price')
    food_sequence = fields.Char(string='', copy=False, readonly=True,
                                default=lambda self: 'New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('food_sequence', 'New') == 'New':
                vals['food_sequence'] = self.env['ir.sequence'].next_by_code(
                    'rest.food.sequence') or 'New'
        return super(RestaurantFood, self).create(vals_list)


class RestaurantOrder(models.Model):
    _name = 'customer.food.order'
    _description = "Customer Food Order Details"
    _rec_name = 'food_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    food_id = fields.Many2one('food.item', required=True)
    quantity = fields.Integer(string='Quantity', required=True, default=1)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    price = fields.Monetary(string='Price', related='food_id.price',
                            required=True)
    restaurant_id = fields.Many2one('hotel.restaurant')
    subtotal_amount = fields.Monetary(string='Subtotal',
                                      compute='food_order_total_amount')
    booking_id = fields.Many2one(related='restaurant_id.booking_id')
    customer_id = fields.Many2one(
        related='restaurant_id.booking_id.customer_id', string='Customer')
    stages = fields.Selection(
        [('Confirm', 'Confirm'), ('Prepared', 'Prepared'),
         ('Delivered', 'Delivered')],
        string='Status', default='Confirm')
    food_included = fields.Boolean(string="Food Included")

    def confirm_to_prepared(self):
        self.stages = 'Prepared'

    def prepared_to_delivered(self):
        self.stages = 'Delivered'

    @api.depends('quantity', 'food_id')
    def food_order_total_amount(self):
        for rec in self:
            subtotal_amount = 0.0
            if not rec.food_included:
                subtotal_amount = subtotal_amount + (rec.price * rec.quantity)
                rec.subtotal_amount = subtotal_amount
            else:
                rec.subtotal_amount = subtotal_amount


class RestaurantTableDetail(models.Model):
    _name = 'table.details'
    _description = "Table Details"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char('Table Number ', required=True)
    capacity = fields.Integer(string='Capacity', required=True)
    stages = fields.Selection(
        [('Available', "Available"), ('Booked', "Booked")],
        string='Status', default='Available')
    table_number = fields.Char(string='', copy=False, readonly=True,
                               default=lambda self: 'New')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('table_number', 'New') == 'New':
                vals['table_number'] = self.env['ir.sequence'].next_by_code(
                    'rest.table.sequence') or 'New'
        return super(RestaurantTableDetail, self).create(vals_list)

    def available_to_booked(self):
        self.stages = 'Booked'

    def booked_to_available(self):
        self.stages = 'Available'


class HotelTableBooking(models.Model):
    _name = "hotel.table.booking"
    _description = "Hotel Table Booking"
    _rec_name = "table_id"

    table_id = fields.Many2one('table.details', string="Table",
                               domain="[('id', 'not in', table_ids)]")
    stage = fields.Selection([('a', 'Available'), ('b', 'Booked')],
                             string="Status", default="a")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    restaurant_id = fields.Many2one('hotel.restaurant')
    table_ids = fields.Many2many('table.details', compute="_compute_table_ids",
                                 string='Available Tables')
    table_capacity = fields.Integer(related="table_id.capacity",
                                    string="Capacity")
    no_of_person = fields.Integer(string="No of People")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    reservation_charges = fields.Monetary('Reservation Charges')

    @api.depends('start_date', 'end_date', 'table_id')
    def _compute_table_ids(self):
        for rec in self:
            table_ids = self.env['hotel.table.booking'].sudo().search(
                [('start_date', '<=', rec.end_date),
                 ('end_date', '>=',
                  rec.start_date),
                 ('stage', '!=', 'a')]).mapped(
                'table_id').ids
            rec.table_ids = table_ids

    @api.constrains('start_date', 'end_date')
    def check_table_reservation_dates(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.start_date >= rec.end_date:
                raise ValidationError(_(
                    "The start date of table reservation must be earlier than the end date."))
            if rec.start_date < now:
                raise ValidationError(
                    _("The start date and time of table reservation should not be outdated."))
