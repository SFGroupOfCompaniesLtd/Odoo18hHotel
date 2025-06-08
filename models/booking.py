# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import calendar
import datetime
from odoo import models, fields, api, _
from datetime import timedelta, datetime
from datetime import date
from odoo.exceptions import ValidationError, AccessError, UserError


class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _description = "Hotel Bookings"
    _rec_name = 'booking_number'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    booking_number = fields.Char(string='', copy=False, readonly=True,
                                 default=lambda self: 'New')
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True)
    adults = fields.Integer(string='Adults', required=True, default=1)
    children = fields.Integer(string='Children')
    responsible = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string='Responsible',
        required=True)
    no_of_room = fields.Integer(string='No of Rooms', compute='room_count')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    stages = fields.Selection(
        [('Draft', 'Draft'), ('Confirm', 'Confirmed'),
         ('check_in', 'Check-in'), ('Complete', 'Check-out'),
         ('Cancel', 'Cancel')],
        string='Status', default='Draft', copy=False)
    is_any_agent = fields.Boolean(string="Any Agent")
    agent_id = fields.Many2one(
        'res.partner', domain="[('is_agent','=',True)]", string="Agent")
    agent_commission = fields.Monetary(string="Commission")
    agent_percentage_commission = fields.Monetary(
        string="Commission ", compute="_compute_percentage_commission")
    percentage = fields.Float(string="Percentage")
    agent_bill_id = fields.Many2one('account.move', string="Agent Bill", copy=False)
    agent_commission_type = fields.Selection(
        [('fix', 'Fix'), ('percentage', 'Percentage')], default="fix",
        string="Commission Type")
    agent_payment_state = fields.Selection(
        related="agent_bill_id.payment_state", string="Payment Status ")

    # Breakfast, Dinner and Lunch
    is_breakfast_included = fields.Boolean(string="Breakfast")
    breakfast_charge = fields.Monetary(string="Breakfast Charges")
    is_dinner_included = fields.Boolean(string="Dinner")
    dinner_charge = fields.Monetary(string="Dinner Charges")
    is_lunch_included = fields.Boolean(string="Lunch")
    lunch_charge = fields.Monetary(string="Lunch Charges")

    # Invoices
    room_total_charges = fields.Monetary(
        string='Room Charges', compute='room_charges')
    transport_total_charges = fields.Monetary(
        string='Transport Charges', compute='transport_charges')
    laundry_total_charges = fields.Monetary(
        string='Laundry Charges', compute='laundry_charges')
    restaurant_services_charges = fields.Monetary(
        string='Restaurant Charges', compute='restaurant_charges')
    all_service_amount = fields.Monetary(
        string='Amount Due', compute='total_service_amount')
    total_amount = fields.Monetary(
        string='Total Amount', compute='compute_total_amount', store=True)
    invoice_id = fields.Many2one('account.move', string="Invoice ", copy=False)
    payment_state = fields.Selection(
        related='invoice_id.payment_state', string="Payment Status")
    invoice_due = fields.Monetary(
        related='invoice_id.amount_residual', string="Due", store=True)
    payable_due = fields.Monetary(
        string="Payable Due", compute="_compute_payable_due_charges")
    invoice_payment_type = fields.Selection(
        [('once', 'Once'), ('by_night', 'Invoice Posted by Night')],
        default="once",
        string="Invoice Payment")
    room_night_invoice_ids = fields.One2many(
        'room.night.invoice', 'booking_id', string="Room Night Invoice")
    total_night_invoice = fields.Monetary(
        string="Room Charges Payable", compute="_compute_total_due_invoice")
    total_night_invoice_due = fields.Monetary(
        string="Room Charges Due", compute="_compute_total_due_invoice")

    # Advance
    is_advance = fields.Boolean(string='Advance', copy=False)
    advance_amount = fields.Monetary(string='Advance Amount', copy=False)
    journal_id = fields.Many2one(
        'account.journal', string="Journal",
        domain="[('type','in',['bank','cash'])]", copy=False)

    # One2Many
    service_ids = fields.One2many(
        'hotel.extra.services', 'booking_id', string='Services')
    room_ids = fields.One2many(
        'hotel.room.details', 'booking_id', string='Rooms')
    transport_ids = fields.One2many('hotel.transport', 'booking_id')
    laundry_ids = fields.One2many('laundry.service', 'booking_id')
    restaurant_ids = fields.One2many('hotel.restaurant', 'booking_id')
    proof_ids = fields.One2many(
        'proof.details', 'booking_id', string='Proof Details')

    # Cancel Booking
    cancels_invoice_id = fields.Many2one(
        'account.move', string="Invoice", readonly=True, copy=False)
    cancellation_reason = fields.Text(string="Cancellation Reason")
    cancellation_charge = fields.Monetary(string='Cancellation Charges')
    is_cancellation_charge = fields.Boolean(string="Cancellation Charge")

    is_any_discount = fields.Boolean("Any Discount")
    discount_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed')])
    discount_val = fields.Float('Discount')

    discount_amount = fields.Monetary(compute="_compute_discount_amount")

    # others
    is_manual = fields.Boolean("Is Manual")

    order_count = fields.Integer(string='Order Count', compute='_compute_order_count', store=True)
    order_ids = fields.One2many('pos.order', 'booking_id', string='Orders')

    # Housekeeping Tasks
    housekeeping_task_count = fields.Integer(compute='_compute_housekeeping_task_count')

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['id', 'booking_number', 'customer_id', 'stages']

    def _load_pos_data(self, data):
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        bookings = self.search([])
        bookings = bookings.read(fields, load=False)
        return {
            'data': bookings,
            'fields': fields,
        }

    @api.depends('order_ids')
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = self.env['pos.order'].search_count([('booking_id', '=', rec.id)])

    def action_view_order(self):
        return {
            'name': _('Orders'),
            'res_model': 'pos.order',
            'view_mode': 'list,form',
            'context': {'default_booking_id': self.id},
            'domain': [('booking_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    @api.depends('housekeeping_task_count')
    def _compute_housekeeping_task_count(self):
        for rec in self:
            rec.housekeeping_task_count = self.env['project.task'].sudo().search_count(
                [('room_booking_id', '=', rec.id)])

    def action_view_housekeeping_tasks(self):
        return {
            'name': _('Tasks'),
            'res_model': 'project.task',
            'view_mode': 'kanban,list,form',
            'context': {'create': False},
            'domain': [('room_booking_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    @api.depends('is_any_discount', 'discount_type', 'discount_val',
                 'room_total_charges')
    def _compute_discount_amount(self):
        for rec in self:
            amount = 0
            if rec.is_any_discount:
                amount = rec.discount_val
                if rec.discount_type == 'percentage':
                    amount = round(
                        (rec.discount_val * rec.room_total_charges) / 100, 2)
            rec.discount_amount = amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('booking_number', 'New') == 'New':
                vals['booking_number'] = self.env['ir.sequence'].next_by_code(
                    'rest.room.booking') or 'New'
        rec = super(HotelBooking, self).create(vals_list)
        return rec

    def unlink(self):
        for rec in self:
            if rec.stages != 'Draft':
                raise ValidationError(
                    _('Records can only be deleted during the draft stage.'))
        return super(HotelBooking, self).unlink()

    @api.constrains('room_ids')
    def dates_same_check(self):
        if self.room_ids:
            for rec in self.room_ids:
                records = self.env['hotel.room.details'].search(
                    [('booking_id', '=', self.id), ('id', '!=', rec.id)])
                if records:
                    for record in records:
                        if record.check_in != rec.check_in or record.check_out != rec.check_out:
                            raise ValidationError(
                                _("The check-in and check-out dates for rooms under one booking cannot be different."))

    @api.onchange('discount_type')
    def _onchange_discount_type(self):
        """Onchange discount do discount val field 0"""
        self.discount_val = 0

    # Stages
    def draft_to_confirm(self):
        self.dates_same_check()
        if self.no_of_room <= 0:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': (_('Add rooms to confirm booking !')),
                    'sticky': False,
                }
            }
            return message

        for rec in self.room_ids:
            rooms = self.env['hotel.room.details'].sudo().search(
                [('id', '!=', rec.id), ('booking_id', '=', self.id)])
            for data in rooms:
                if data.room_id.id == rec.room_id.id:
                    raise ValidationError(
                        _('Please select different rooms for your booking; you cannot select the same room more than once.'))
            # booked_id = self.env['hotel.room.details'].sudo().search([('check_in', '<', rec.check_out),
            #                                                           ('check_out', '>',
            #                                                            rec.check_in),
            #                                                           ('stages', '!=', 'Available'),
            #                                                           ('room_id', '=', rec.room_id.id)], limit=1)
            # if booked_id:
            #     raise ValidationError(_("Same rooms are booked choose another room to proceed."))
        for rec in self.room_ids:
            if rec.booking_id.id == self.id:
                rec.available_to_booked()
        self.stages = 'Confirm'
        if not self.invoice_id:
            if self.is_breakfast_included:
                breakfast_product_id = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'tk_hotel_management.breakfast_product')
                self.create_extra_service_data(name="Breakfast Charges",
                                               amount=self.breakfast_charge,
                                               product_id=breakfast_product_id)
            if self.is_dinner_included:
                dinner_product_id = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'tk_hotel_management.dinner_product')
                self.create_extra_service_data(name="Dinner Charges",
                                               amount=self.dinner_charge,
                                               product_id=dinner_product_id)
            if self.is_lunch_included:
                lunch_product_id = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'tk_hotel_management.lunch_product')
                self.create_extra_service_data(name="Lunch Charges",
                                               amount=self.lunch_charge,
                                               product_id=lunch_product_id)
        if self.invoice_id:
            for data in self.service_ids:
                if data.is_meal_charges:
                    data.unlink()
            if self.is_breakfast_included:
                breakfast_product_id = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'tk_hotel_management.breakfast_product')
                self.create_extra_service_data(name="Breakfast Charges",
                                               amount=self.breakfast_charge,
                                               product_id=breakfast_product_id)
            if self.is_lunch_included:
                lunch_product_id = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'tk_hotel_management.lunch_product')
                self.create_extra_service_data(name="Lunch Charges",
                                               amount=self.lunch_charge,
                                               product_id=lunch_product_id)
            if self.is_dinner_included:
                dinner_product_id = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'tk_hotel_management.dinner_product')
                self.create_extra_service_data(name="Dinner Charges",
                                               amount=self.dinner_charge,
                                               product_id=dinner_product_id)

    def confirm_to_done(self):
        self.stages = 'Complete'
        for rec in self.room_ids:
            if rec.booking_id.id == self.id:
                rec.maintenance_to_available()
                data = {
                    'is_room': True,
                    'housekeeping_type': 'Cleaning',
                    'room_id': rec.room_id.id,
                    'desc': 'New Request for Housekeeping for Room',
                    'start_datetime': rec.check_out
                }
                self.env['hotel.housekeeping'].create(data)

    def create_extra_service_data(self, name, amount, product_id):
        data = {
            'product_id': product_id if product_id else self.env.ref(
                'tk_hotel_management.hotel_extra_services_charge').id,
            'service': name,
            'quantity': 1,
            'amount': amount,
            'booking_id': self.id,
            'is_meal_charges': True
        }
        self.env['hotel.extra.services'].create(data)

    def confirm_to_cancel(self):
        for rec in self.room_ids:
            if rec.booking_id.id == self.id:
                rec.maintenance_to_available()
        self.stages = 'Cancel'

    def action_check_in(self):
        self.stages = "check_in"
        project_id = self.env['ir.config_parameter'].sudo().get_param(
            'tk_hotel_management.housekeeping_project_id')
        housekeeping_project = self.env['project.project'].sudo().browse(int(project_id))
        for rec in self.room_ids:
            data = {
                'name': f'Housekeeping Room No:{rec.room_id.display_name}',
                'project_id': housekeeping_project.id if housekeeping_project else self.env.ref(
                    'tk_hotel_management.house_keeping_project').id,
                'user_ids': rec.room_id.floor_id.housekeeper_ids.ids,
                'start_date': rec.check_out,
                'room_booking_id': self.id,
                'company_id': self.company_id.id
            }
            task_id = self.env['project.task'].sudo().create(data)

    def action_draft(self):
        self.stages = 'Draft'

    # Compute Amount
    @api.depends('room_ids', 'is_breakfast_included', 'breakfast_charge',
                 'is_dinner_included', 'dinner_charge',
                 'is_lunch_included', 'lunch_charge', 'total_night_invoice',
                 'total_night_invoice_due')
    def room_charges(self):
        for rec in self:
            room_total_charges = 0.0
            if rec.invoice_payment_type == "by_night":
                rec.room_total_charges = rec.total_night_invoice
            else:
                for data in rec.room_ids:
                    room_total_charges = room_total_charges + data.total_price
                rec.room_total_charges = room_total_charges

    @api.depends('transport_ids')
    def transport_charges(self):
        for rec in self:
            transport_total_charges = 0.0
            for data in rec.transport_ids:
                if data.stage == "complete":
                    transport_total_charges = transport_total_charges + data.total_charges
            rec.transport_total_charges = transport_total_charges

    @api.depends('laundry_ids', )
    def laundry_charges(self):
        for rec in self:
            laundry_total_charges = 0.0
            for data in rec.laundry_ids:
                laundry_total_charges = laundry_total_charges + data.total_charges
            rec.laundry_total_charges = laundry_total_charges

    @api.depends('restaurant_ids')
    def restaurant_charges(self):
        for rec in self:
            restaurant_services_charges = 0.0
            for data in rec.restaurant_ids:
                restaurant_services_charges = restaurant_services_charges + data.total_charges
            rec.restaurant_services_charges = restaurant_services_charges

    @api.depends('service_ids')
    def total_service_amount(self):
        for rec in self:
            all_service_amount = 0.0
            for data in rec.service_ids:
                all_service_amount = all_service_amount + data.all_amount
            rec.all_service_amount = all_service_amount

    @api.depends('room_total_charges', 'transport_total_charges',
                 'laundry_total_charges',
                 'restaurant_services_charges', 'all_service_amount',
                 'invoice_payment_type', 'discount_amount')
    def compute_total_amount(self):
        for rec in self:
            total_amount = rec.room_total_charges + rec.transport_total_charges + rec.laundry_total_charges + \
                           rec.restaurant_services_charges + rec.all_service_amount - rec.discount_amount
            rec.total_amount = total_amount

    @api.depends('agent_commission_type', 'percentage', 'total_amount')
    def _compute_percentage_commission(self):
        for rec in self:
            if rec.agent_commission_type == "percentage":
                rec.agent_percentage_commission = (
                                                          rec.percentage * rec.total_amount) / 100
            else:
                rec.agent_percentage_commission = 0.0

    @api.depends('room_night_invoice_ids', 'invoice_payment_type')
    def _compute_total_due_invoice(self):
        for rec in self:
            total = 0.0
            total_due = 0.0
            for data in rec.room_night_invoice_ids:
                total = total + data.amount
                total_due = total_due + data.invoice_due
            rec.total_night_invoice = total
            rec.total_night_invoice_due = total_due

    @api.depends('total_night_invoice_due', 'invoice_id',
                 'invoice_payment_type', 'invoice_due',
                 'room_night_invoice_ids.invoice_id.amount_residual',
                 'room_night_invoice_ids.invoice_due')
    def _compute_payable_due_charges(self):
        for rec in self:
            if rec.invoice_payment_type == "by_night":
                rec.payable_due = rec.invoice_due + rec.total_night_invoice_due
            else:
                rec.payable_due = rec.invoice_due

    # Count
    def room_count(self):
        for order in self:
            count = 0
            for line in order.room_ids:
                count += 1
            order.update({
                'no_of_room': count,
            })

    @api.model
    def get_hotel_stats(self):
        today_date = fields.Date.today()
        active_booking_count = self.env['hotel.booking'].sudo().search_count(
            ['|', ('stages', '=', 'check_in'), ('stages', '=', 'Confirm')])
        hall_count = self.env['hotel.feast'].sudo(
        ).search_count([('stages', '=', 'Confirm')])
        today_check_in_count = self.env[
            'hotel.room.details'].sudo().search_count(
            [('stages', '=', 'Booked'), ('check_in', '=', today_date)])
        today_check_out_count = self.env[
            'hotel.room.details'].sudo().search_count(
            [('stages', '=', 'Booked'), ('check_out', '=', today_date)])
        food_count = self.env['hotel.restaurant'].sudo(
        ).search_count([('stages', '=', 'Confirm')])
        transports_count = self.env['hotel.transport'].sudo(
        ).search_count([('stage', '=', 'pending')])
        d_booking = self.env['hotel.booking'].search_count(
            [('stages', '=', 'Draft')])
        c_booking = self.env['hotel.booking'].search_count(
            [('stages', '=', 'Confirm')])
        check_in_booking = self.env['hotel.booking'].search_count(
            [('stages', '=', 'check_in')])
        check_out_booking = self.env['hotel.booking'].search_count(
            [('stages', '=', 'Complete')])
        cancel_booking = self.env['hotel.booking'].search_count(
            [('stages', '=', 'Cancel')])
        data = {
            'active_booking_count': active_booking_count,
            'hall_count': hall_count,
            'today_check_in': today_check_in_count,
            'today_check_out': today_check_out_count,
            'food_count': food_count,
            'transports_count': transports_count,
            'top_customer': self.get_top_customer(),
            'get_cat_room': self.get_cat_room(),
            'booking_month': self.booking_month(),
            'booking_day': self.booking_day(),

            'room': [['Draft', 'Confirm', 'Check In', 'Check Out', 'Cancel'],
                     [d_booking, c_booking, check_in_booking,
                      check_out_booking, cancel_booking]]
        }
        return data

    def get_top_customer(self):
        partner, amount, data = [], [], []
        customer = self.env['res.partner'].search(
            [('is_agent', '=', False)]).mapped('id')
        for group in self.env['account.move'].read_group(
                [('partner_id', 'in', customer)],
                ['amount_total',
                 'partner_id'],
                ['partner_id'],
                orderby="amount_total DESC", limit=5):
            if group['partner_id']:
                name = self.env['res.partner'].sudo().browse(
                    int(group['partner_id'][0])).name
                partner.append(name)
                amount.append(group['amount_total'])

        data = [partner, amount]

        return data

    def get_cat_room(self):
        stages, room_counts, data_cat = [], [], []
        room_cat_ids = self.env['hotel.room.category'].search([])
        if not room_cat_ids:
            data_cat = [[], []]
        for stg in room_cat_ids:
            room_data = self.env['hotel.room'].search_count(
                [('room_category_id', '=', stg.id)])
            room_counts.append(room_data)
            stages.append(stg.name)
        data_cat = [stages, room_counts]
        return data_cat

    def booking_month(self):
        year = fields.Date.today().year
        year_str = str(year)
        data_dict = {
            '01/' + year_str: 0,
            '02/' + year_str: 0,
            '03/' + year_str: 0,
            '04/' + year_str: 0,
            '05/' + year_str: 0,
            '06/' + year_str: 0,
            '07/' + year_str: 0,
            '08/' + year_str: 0,
            '09/' + year_str: 0,
            '10/' + year_str: 0,
            '11/' + year_str: 0,
            '12/' + year_str: 0,
        }
        booking = self.env['hotel.booking'].search(
            [('stages', 'in', ['Confirm', 'check_in', 'Complete'])])
        for data in booking:
            if data.create_date.year == year:
                month_year = data.create_date.strftime("%m/%Y")
                data_dict[month_year] += 1
        return [list(data_dict.keys()), list(data_dict.values())]

    def booking_day(self):
        day_dict = self.get_current_month_days()
        confirm_dict = self.get_current_month_days()
        check_in_dict = self.get_current_month_days()
        check_out_dict = self.get_current_month_days()
        cancel_dict = self.get_current_month_days()
        year = fields.date.today().year
        month = fields.date.today().month
        confirm_booking = self.env['hotel.booking'].search(
            [('stages', '=', 'Confirm')])
        check_in_booking = self.env['hotel.booking'].search(
            [('stages', '=', 'check_in')])
        check_out_booking = self.env['hotel.booking'].search(
            [('stages', '=', 'Complete')])
        cancel_booking = self.env['hotel.booking'].search(
            [('stages', '=', 'Cancel')])
        for data in confirm_booking:
            if data.create_date.year == year and month == data.create_date.month:
                booking_time = data.create_date.strftime(
                    '%d') + " " + data.create_date.strftime('%h')
                confirm_dict[booking_time] = confirm_dict[booking_time] + 1
        for data in check_in_booking:
            if data.create_date.year == year and month == data.create_date.month:
                booking_time = data.create_date.strftime(
                    '%d') + " " + data.create_date.strftime('%h')
                check_in_dict[booking_time] = check_in_dict[booking_time] + 1
        for data in check_out_booking:
            if data.create_date.year == year and month == data.create_date.month:
                booking_time = data.create_date.strftime(
                    '%d') + " " + data.create_date.strftime('%h')
                check_out_dict[booking_time] = check_out_dict[booking_time] + 1
        for data in cancel_booking:
            if data.create_date.year == year and month == data.create_date.month:
                booking_time = data.create_date.strftime(
                    '%d') + " " + data.create_date.strftime('%h')
                cancel_dict[booking_time] = cancel_dict[booking_time] + 1
        return [list(day_dict.keys()), list(confirm_dict.values()),
                list(check_in_dict.values()),
                list(check_out_dict.values()), list(cancel_dict.values())]

    def get_current_month_days(self):
        day_dict = {}
        year = fields.date.today().year
        month = fields.date.today().month
        num_days = calendar.monthrange(year, month)[1]
        days = [date(year, month, day) for day in range(1, num_days + 1)]
        for data in days:
            day_dict[data.strftime('%d') + " " + data.strftime('%h')] = 0
        return day_dict


class HotelBookingProofDetails(models.Model):
    _name = 'proof.details'
    _description = "Proof Details"
    _rec_name = 'booking_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    id_number = fields.Char('Document Number', required=True)
    id_name = fields.Char('Document Name', required=True)
    person_Id = fields.Char('Full Name', required=True)
    document = fields.Binary(string='Document', required=True)
    file_name = fields.Char()
    booking_id = fields.Many2one('hotel.booking', required=True)
    customer_id = fields.Many2one(
        related='booking_id.customer_id', string='Customer')
    proof_number = fields.Char(string='', copy=False, readonly=True,
                               default=lambda self: 'New')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')


class HotelExtraServices(models.Model):
    _name = 'hotel.extra.services'
    _description = "Hotel Extra Service"
    _rec_name = 'service'

    service = fields.Char('Service Description', required=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    amount = fields.Monetary(string='Amount')
    quantity = fields.Integer(string='Quantity', required=True, default=1)
    booking_id = fields.Many2one('hotel.booking')
    all_amount = fields.Monetary(
        string='Total Amount', compute='total_all_amount_charges')

    product_id = fields.Many2one('product.product',
                                 domain=[('type', '=', 'service')],
                                 string='Service Product')
    is_meal_charges = fields.Boolean()

    @api.depends('amount', 'quantity')
    def total_all_amount_charges(self):
        for rec in self:
            rec.all_amount = rec.amount * rec.quantity

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            amount = 0
            service = ''
            if rec.product_id:
                amount = rec.product_id.lst_price
                service = rec.product_id.name
            rec.amount = amount
            rec.service = service
