# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class HotelFloor(models.Model):
    _name = "hotel.floor"
    _description = "Floor"

    name = fields.Char('Floor Number', required=True, index=True)
    floor_number_sequence = fields.Char(string='', copy=False, readonly=True,
                                        default=lambda self: 'New')
    capacity = fields.Integer(
        string='Rooms', compute='get_capacity_room_count')
    responsible_id = fields.Many2one(
        'hr.employee', domain="[('is_staff', '=', True)]",
        string='Responsible ')
    responsible_person_id = fields.Many2one('res.users', string='Responsible')

    available_housekeeper_ids = fields.Many2many('res.users',
                                                 compute="_compute_available_housekeeper_ids")
    housekeeper_ids = fields.Many2many('res.users',
                                       'floor_housekeepers',
                                       'floor',
                                       'housekeepers',
                                       domain="[('id', 'in', available_housekeeper_ids)]")
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')

    def _compute_available_housekeeper_ids(self):
        for rec in self:
            records = self.env['res.users'].search([])
            rec.available_housekeeper_ids = records.filtered(
                lambda user: user.has_group('tk_hotel_management.hotel_housekeeper')).ids

    def get_capacity_room_count(self):
        count = self.env['hotel.room'].search_count(
            [('floor_id', '=', self.id)])
        self.capacity = count

    def total_capacity_rooms_views(self):
        return {
            'name': 'Rooms',
            'domain': [('floor_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'hotel.room',
            'view_id': False,
            'view_mode': 'list,form',
            'type': "ir.actions.act_window"
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('floor_number_sequence', 'New') == 'New':
                vals['floor_number_sequence'] = self.env[
                                                    'ir.sequence'].next_by_code(
                    'rest.floor.sequence') or 'New'
        return super(HotelFloor, self).create(vals_list)


class HotelRoomType(models.Model):
    _name = "hotel.room.type"
    _description = "Hotel Room Type"

    name = fields.Char('Room Type', required=True)
    is_seasonal_price = fields.Boolean(string='Seasonal Prices')
    seasonal_price_line_ids = fields.One2many(
        'room.season.price.lines', 'room_type_id')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    base_price = fields.Monetary(string='Base Price')
    price = fields.Monetary(string='Final Price')
    increment_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed')],
        string='Increment Type')
    increment_val = fields.Float(string='Increment Amount')
    increment_percentage = fields.Float(string='Increment Percentage')

    room_count = fields.Integer(compute="_compute_room_count", string='Rooms')

    adult_capacity = fields.Integer(string='Adults')
    child_capacity = fields.Integer(string='Children')

    charges_per_extra_adult = fields.Monetary(string='Charges / Extra Adult')
    charges_per_extra_child = fields.Monetary(string='Charges / Extra Child')

    tax_ids = fields.Many2many('account.tax', string='Taxes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'base_price' in vals:
                vals['price'] = vals['base_price']
        return super(HotelRoomType, self).create(vals_list)

    def write(self, vals):
        if 'base_price' in vals:
            self.price = vals['base_price']
        return super(HotelRoomType, self).write(vals)

    def _compute_room_count(self):
        for rec in self:
            rec.room_count = self.env['hotel.room'].search_count(
                [('room_type_id', '=', rec.id)])

    @api.constrains("seasonal_price_line_ids")
    def _check_time(self):
        for rec in self:
            for data in rec.seasonal_price_line_ids:
                records = self.env['room.season.price.lines'].search(
                    [('room_type_id', '=', rec.id), ('id', '!=', data.id)])
                for record in records:
                    if record.start_date <= data.start_date <= record.end_date or record.start_date <= data.end_date <= record.end_date:
                        raise ValidationError(
                            _("Season's time period is overlapping."))

    def action_rooms(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rooms',
            'res_model': 'hotel.room',
            'domain': [('room_type_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current'
        }

    def update_room_prices(self):
        today = fields.Date.today()
        price = self.base_price
        increment_type = False
        increment_val = 0
        increment_percentage = 0
        for data in self.seasonal_price_line_ids:
            if data.start_date <= today <= data.end_date and self.is_seasonal_price:
                if data.increment_type == 'percentage':
                    amount = (price * data.increment_val) / 100
                    price += amount
                    increment_type = 'percentage'
                    increment_val = amount
                    increment_percentage = data.increment_val
                elif data.increment_type == 'fixed':
                    price += data.increment_val
                    increment_type = 'fixed'
                    increment_val = data.increment_val
            self.price = price
            self.increment_type = increment_type
            self.increment_val = increment_val
            self.increment_percentage = increment_percentage

        records = self.env['hotel.room'].search(
            [('room_type_id', '=', self.id)])
        for rec in records:
            price = rec.base_price
            increment_type = False
            increment_val = 0
            increment_percentage = 0
            for data in rec.room_type_id.seasonal_price_line_ids:
                if data.start_date <= today <= data.end_date and rec.room_type_id.is_seasonal_price:
                    if data.increment_type == 'percentage':
                        amount = (price * data.increment_val) / 100
                        price += amount
                        increment_type = 'percentage'
                        increment_val = amount
                        increment_percentage = data.increment_val
                    elif data.increment_type == 'fixed':
                        price += data.increment_val
                        increment_type = 'fixed'
                        increment_val = data.increment_val
                rec.price = price
                rec.increment_type = increment_type
                rec.increment_val = increment_val
                rec.increment_percentage = increment_percentage


class RoomSeasonPriceLines(models.Model):
    _name = "room.season.price.lines"
    _description = 'Seasonal Pricing Lines'
    _rec_name = 'seasonal_price_id'

    seasonal_price_id = fields.Many2one('season.price', string='Season')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    increment_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed')],
        string='Increment Type')
    increment_val = fields.Float(string='Increment')
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')

    @api.onchange('seasonal_price_id')
    def _onchange_season_get_data(self):
        self.start_date = self.seasonal_price_id.start_date
        self.end_date = self.seasonal_price_id.end_date
        self.increment_type = self.seasonal_price_id.increment_type
        self.increment_val = self.seasonal_price_id.increment_val

    @api.constrains("start_date", "end_date")
    def _check_end_time(self):
        for rec in self:
            if rec.end_date < rec.start_date:
                raise ValidationError(
                    _("Season end time cannot be less than season start time."))


class HotelRoomCategory(models.Model):
    _name = "hotel.room.category"
    _description = "Hotel Room Category"

    name = fields.Char('Room Category', required=True)


class HotelRoomFacilities(models.Model):
    _name = "hotel.room.facilities"
    _description = "Facilities"

    avatar = fields.Binary()
    name = fields.Char('Facilities Name', required=True)


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _rec_name = 'display_name'

    avatar = fields.Binary()
    room_no = fields.Char(string='Room No.', required=True)
    floor_id = fields.Many2one('hotel.floor', string='Floor', required=True)
    room_type_id = fields.Many2one(
        'hotel.room.type', string='Room Type', required=True)
    room_category_id = fields.Many2one(
        'hotel.room.category', string='Room Category')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    price = fields.Monetary(string='Price')
    room_facilities_ids = fields.Many2many(
        'hotel.room.facilities', string='Facilities')
    check_in = fields.Date(string='Check-In Date')
    check_out = fields.Date(string='Check-Out Date')
    capacity = fields.Integer(string='Capacity', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    base_price = fields.Monetary(string='Base Price',
                                 related='room_type_id.base_price', store=True)
    increment_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed')],
        string='Increment Type')
    increment_percentage = fields.Float(string='Increment Percentage')
    increment_val = fields.Float(string='Increment')
    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            room_type = ''
            price = 0
            if 'room_type_id' in vals:
                room_type = self.env['hotel.room.type'].browse(
                    vals['room_type_id']).name
                price = self.env['hotel.room.type'].browse(
                    vals['room_type_id']).base_price
            data = {
                'name': f"{vals['room_no'] if 'room_no' in vals else ''}",
                'type': 'service',
                'list_price': price
            }
            if room_type:
                data['name'] = (
                    f"{vals['room_no'] if 'room_no' in vals else ''}"
                    f" - {room_type}"
                )
            product_id = self.env['product.product'].create(data)
            vals['product_id'] = product_id.id
            vals['price'] = price
            if 'room_no' in vals and 'floor_id' in vals:
                rooms = self.sudo().search([('floor_id', '=', vals['floor_id'])])
                for rec in rooms:
                    if vals['room_no'] == rec.room_no:
                        raise ValidationError(
                            _('There is already a room on the same floor with the same name.'))
        return super(HotelRoom, self).create(vals_list)

    def write(self, vals):
        if 'price' in vals:
            self.product_id.list_price = vals['price']
        if 'room_type_id' in vals:
            price = self.env['hotel.room.type'].browse(
                vals['room_type_id']).base_price
            self.price = price
        if 'room_no' in vals:
            rooms = self.sudo().search([('floor_id', '=', self.floor_id.id), ('id', '!=', self.id)])
            for rec in rooms:
                if vals['room_no'] == rec.room_no:
                    raise ValidationError(
                        _('There is already a room on the same floor with the same name.'))
        if 'floor_id' in vals:
            rooms = self.sudo().search([('floor_id', '=', vals['floor_id']), ('id', '!=', self.id)])
            for rec in rooms:
                if self.room_no == rec.room_no:
                    raise ValidationError(
                        _('On the floor you wish to switch to, there already exists a room with the same name.'))
        return super(HotelRoom, self).write(vals)

    @api.depends('room_type_id', 'room_no')
    def _compute_display_name(self):
        for rec in self:
            name = rec.room_no
            if rec.room_type_id:
                name = f"{rec.room_no} - {rec.room_type_id.name}"
            rec.display_name = name

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - %s' %
                           (rec.room_no, rec.room_type_id.name)))
        return result

    @api.model
    def seasonal_price_increment_cron(self):
        records = self.env['hotel.room'].sudo().search([])
        today = fields.Date.today()
        for rec in records:
            price = rec.base_price
            increment_type = False
            increment_val = 0
            increment_percentage = 0
            for data in rec.room_type_id.seasonal_price_line_ids:
                if data.start_date <= today <= data.end_date and rec.room_type_id.is_seasonal_price:
                    if data.increment_type == 'percentage':
                        amount = (price * data.increment_val) / 100
                        price += amount
                        increment_type = 'percentage'
                        increment_val = amount
                        increment_percentage = data.increment_val
                    elif data.increment_type == 'fixed':
                        price += data.increment_val
                        increment_type = 'fixed'
                        increment_val = data.increment_val
                rec.price = price
                rec.increment_type = increment_type
                rec.increment_val = increment_val
                rec.increment_percentage = increment_percentage
        type_records = self.env['hotel.room.type'].sudo().search([])
        for rec in type_records:
            price = rec.base_price
            increment_type = False
            increment_val = 0
            increment_percentage = 0
            for data in rec.seasonal_price_line_ids:
                if data.start_date <= today <= data.end_date and rec.is_seasonal_price:
                    if data.increment_type == 'percentage':
                        amount = (price * data.increment_val) / 100
                        price += amount
                        increment_type = 'percentage'
                        increment_val = amount
                        increment_percentage = data.increment_val
                    elif data.increment_type == 'fixed':
                        price += data.increment_val
                        increment_type = 'fixed'
                        increment_val = data.increment_val
                rec.price = price
                rec.increment_type = increment_type
                rec.increment_val = increment_val
                rec.increment_percentage = increment_percentage


class RoomProduct(models.Model):
    _inherit = 'product.product'

    def unlink(self):
        for rec in self:
            room_record = self.env['hotel.room'].sudo().search(
                [('product_id', '=', rec.id)], limit=1)
            if room_record:
                raise ValidationError(
                    _('Because this product is linked to a room, it cannot be deleted.'))
            laundry_record = self.env['laundry.service.type'].sudo().search(
                ['product_id', '=', rec.id], limit=1)
            if laundry_record:
                raise ValidationError(
                    _('Because this product is linked to a laundry service, it cannot be deleted.'))
        res = super(RoomProduct, self).unlink()
        return res


class HotelRoomBookingDetails(models.Model):
    _name = 'hotel.room.details'
    _description = 'Hotel Room Detail'
    _rec_name = 'room_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    room_sequence = fields.Char(string='', copy=False, readonly=True,
                                default=lambda self: 'New')
    room_ids = fields.Many2many(
        'hotel.room', string="Hotel Rooms", compute='compute_room_ids')
    room_id = fields.Many2one(
        'hotel.room', string='Room', required=True,
        domain="[('id','not in',room_ids)]")
    check_in = fields.Date(string='Check-In Date')
    check_out = fields.Date(string='Check-Out Date')
    days = fields.Integer(compute='day_compute_hours',
                          string='Number of Nights')
    total_price = fields.Monetary(string='Total Charges')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    price = fields.Monetary(
        string='Charge', related='room_id.price', required=True)
    capacity = fields.Integer(
        string='Capacity', related='room_id.capacity', required=True)
    booking_id = fields.Many2one('hotel.booking')
    customer_id = fields.Many2one(related='booking_id.customer_id')
    feast_id = fields.Many2one('hotel.feast')
    stages = fields.Selection(
        [('Available', "Available"), ('Booked', "Booked"),
         ('Maintenance', 'Maintenance')],
        string="Status", default='Available')
    is_invoice_created = fields.Boolean()
    charges_per_night = fields.Monetary(string='Charges')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    room_capacity = fields.Integer(compute='_compute_room_capacity')

    @api.depends('room_id')
    def _compute_room_capacity(self):
        """Get Capacity from room_type"""
        for rec in self:
            capacity = 0
            if rec.room_id and rec.room_id.room_type_id:
                capacity = (rec.room_id.room_type_id.adult_capacity
                            + rec.room_id.room_type_id.child_capacity)
            rec.room_capacity = capacity

    def unlink(self):
        for rec in self:
            if rec.stages == 'Booked':
                raise ValidationError(
                    _('You are not allowed to delete booked room records.'))
        return super(HotelRoomBookingDetails, self).unlink()

    @api.constrains("check_in", "check_out")
    def _check_dates(self):
        today = fields.Date.today()
        back_date_check_in_allowed = self.env[
            'ir.config_parameter'].sudo().get_param(
            'tk_hotel_management.back_date_check_in')
        for rec in self:
            if rec.check_in > rec.check_out:
                raise ValidationError(_(
                    "The check-in date of room booking must be earlier than the check-out date."))
            if rec.check_in < today and not back_date_check_in_allowed:
                raise ValidationError(
                    _("The date of check-in should not be outdated."))
            if rec.check_in == rec.check_out:
                raise ValidationError(
                    _("The check-in date and the check-out date cannot be the same."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('room_sequence', 'New') == 'New':
                vals['room_sequence'] = self.env['ir.sequence'].next_by_code(
                    'rest.room.sequence') or 'New'
        return super(HotelRoomBookingDetails, self).create(vals_list)

    @api.onchange('room_id')
    def _onchange_room_get_taxes(self):
        self.tax_ids = [(5, 0, 0)]
        self.tax_ids = self.room_id.room_type_id.tax_ids.ids

    @api.depends('check_in', 'check_out', 'room_id')
    def compute_room_ids(self):
        for rec in self:
            room_ids = self.env['hotel.room.details'].sudo().search(
                [('check_in', '<', rec.check_out),
                 ('check_out', '>',
                  rec.check_in),
                 ('stages', '!=', 'Available')]).mapped(
                'room_id').ids
            rec.room_ids = room_ids

    def available_to_booked(self):
        for rec in self:
            booked_id = self.env['hotel.room.details'].sudo().search(
                [('check_in', '<', rec.check_out),
                 ('check_out', '>',
                  rec.check_in),
                 ('stages', '!=', 'Available'),
                 ('room_id', '=', rec.room_id.id)], limit=1)
            if booked_id:
                raise ValidationError(
                    _("Same rooms are booked choose another room to proceed."))
            else:
                rec.booking_id.stages = "Confirm"
                rec.stages = 'Booked'

    @api.onchange('check_in', 'check_out', 'room_id')
    def _onchange_get_per_night_room_charges(self):
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

            self.charges_per_night = avg_room_price

    def booked_to_maintenance(self):
        self.stages = 'Maintenance'

    def maintenance_to_available(self):
        self.stages = 'Available'

    @api.depends('check_out', 'check_in')
    def day_compute_hours(self):
        for rec in self:
            days = 0
            if rec.check_out and rec.check_in:
                days = (rec.check_out - rec.check_in).days
            rec.days = days

    @api.onchange('days', 'charges_per_night')
    def onchange_total_price(self):
        for rec in self:
            rec.total_price = rec.days * rec.charges_per_night

    @api.model
    def hotel_room_night_invoice(self):
        today_date = fields.Date.today()
        for rec in self.env['hotel.room.details'].search(
                [('stages', '=', 'Booked'),
                 ('is_invoice_created', '=', False)]):
            if rec.booking_id.stages == "check_in":
                if rec.booking_id.invoice_payment_type == "by_night":
                    amount = rec.total_price / rec.days
                    discount_amount = 0
                    if rec.booking_id.is_any_discount:
                        discount_amount = rec.booking_id.discount_val / rec.days
                        if rec.booking_id.discount_type == 'percentage':
                            discount_amount = (
                                    (rec.charges_per_night * rec.booking_id.discount_val) / 100)

                    if rec.check_in < today_date <= rec.check_out:
                        invoice_lines = [(0, 0, {
                            'display_type': 'line_section',
                            'name': _('Room Charges Per Night')
                        })]
                        data = {
                            'product_id': rec.room_id.product_id.id,
                            'name': 'Night Invoice' + " of Room No : " + rec.room_id.room_no,
                            'quantity': 1,
                            'price_unit': rec.charges_per_night,
                            'tax_ids': rec.tax_ids.ids,
                        }
                        invoice_lines.append((0, 0, data))
                        if rec.booking_id.is_any_discount and discount_amount > 0:
                            discount_product = self.env[
                                'ir.config_parameter'].sudo().get_param(
                                'tk_hotel_management.discount_product_id')
                            invoice_lines.append((0, 0, {
                                'display_type': 'line_section',
                                'name': _('Discount on Room Charges')
                            }))
                            discount_data = {
                                'product_id': discount_product if discount_product else False,
                                'name': (_('Discount on Room Charges')),
                                'quantity': 1,
                                'price_unit': -discount_amount
                            }
                            invoice_lines.append((0, 0, discount_data))
                        record = {
                            'partner_id': rec.booking_id.customer_id.id,
                            'invoice_date': fields.Date.today(),
                            'invoice_line_ids': invoice_lines,
                            'move_type': 'out_invoice',
                        }
                        invoice_id = self.env['account.move'].create(record)
                        booking_data = {
                            'room_id': rec.room_id.id,
                            'date': fields.Date.today(),
                            'amount': rec.charges_per_night,
                            'invoice_id': invoice_id.id,
                            'booking_id': rec.booking_id.id
                        }
                        self.env['room.night.invoice'].create(booking_data)
                        rec.is_invoice_created = True

    def get_dates_between(self, start_date, end_date):
        date_list = []

        current_date = start_date

        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)

        return set(date_list)


class RoomNightInvoice(models.Model):
    _name = 'room.night.invoice'
    _description = "Room Night Invoice"

    room_id = fields.Many2one('hotel.room', string="Room")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    amount = fields.Monetary(string="Amount")
    date = fields.Date(string="Date")
    booking_id = fields.Many2one('hotel.booking', string="Booking")
    payment_state = fields.Selection(
        related='invoice_id.payment_state', string="Payment State")
    invoice_due = fields.Monetary(
        related='invoice_id.amount_residual', string="Due")
