# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class HotelHall(models.Model):
    _name = 'hotel.hall'
    _description = 'Hotel hall'
    _rec_name = 'hall_no'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    avatar = fields.Binary()
    hall_no = fields.Char(string='Hall No.', required=True)
    floor_id = fields.Many2one('hotel.floor', string='Floor', required=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    price = fields.Monetary(string='Price', required=True)
    hall_facilities_ids = fields.Many2many('hotel.room.facilities',
                                           string='Facilities')
    capacity = fields.Integer(string='Capacity', required=True)


class HotelFeast(models.Model):
    _name = "hotel.feast"
    _description = "Hotel Hall Booking"
    _rec_name = 'booking_number'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    booking_number = fields.Char(string='', copy=False, readonly=True,
                                 default=lambda self: 'New')
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  required=True)
    responsible = fields.Many2one('res.users',
                                  default=lambda self: self.env.user,
                                  string='Responsible', required=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    stages = fields.Selection([('Draft', 'Draft'), ('Confirm', 'Confirm'),
                               ('Complete', 'Complete'), ('Cancel', 'Cancel')],
                              string='Status ', default='Draft', copy=False)
    total_all_amount = fields.Monetary(string='Total Charges',
                                       compute="_compute_total_amount")
    cancellation_charge = fields.Monetary(string='Cancels Charges')
    cancels_invoice_id = fields.Many2one('account.move', string="Invoice ",
                                         readonly=True, copy=False)
    cancellation_reason = fields.Text(string="Cancellation Reason")
    is_cancellation_charge = fields.Boolean(string="Cancellation Charge")
    start_date = fields.Datetime(string="Event Start")
    end_date = fields.Datetime(string="Event End")

    # Hall Details
    hall_ids = fields.Many2many('hotel.hall', string="Hotel Halls",
                                compute='compute_hotel_hall_ids', copy=False)
    hall_id = fields.Many2one('hotel.hall', string="Hall",
                              domain="[('id','not in',hall_ids)]", copy=False)
    floor_id = fields.Many2one(related="hall_id.floor_id", string='Location')
    price = fields.Monetary(string='Price / Hour', related="hall_id.price",
                            store=True)
    capacity = fields.Integer(related="hall_id.capacity", string="Capacity")
    hours = fields.Float(string="Total Hours", compute="_compute_no_of_days",
                         store=True)

    # Deposit Amount
    is_deposit = fields.Boolean(string='Any Deposit')
    deposit_amount = fields.Monetary(string='Deposit Amount')
    feast_invoice_id = fields.Many2one('account.move', string="Invoice",
                                       readonly=True, copy=False)
    journal_id = fields.Many2one('account.journal', string="Journal",
                                 domain="[('type','in',['bank','cash'])]", copy=False)
    payment_state = fields.Selection(related="feast_invoice_id.payment_state")

    # Extra Services
    extra_service_ids = fields.One2many('hall.extra.service',
                                        'hall_booking_id')
    total_service_charges = fields.Monetary(
        compute='_compute_total_service_charges')

    def feast_invoice(self):
        invoice_line = []
        self.stages = 'Complete'
        hall_booking = self.env['hotel.hall.booking'].search(
            [('hall_id', '=', self.hall_id.id), ('start_date', '=', self.start_date),
             ('end_date', '=', self.end_date), ('stage', '=', 'b')], limit=1)
        hall_booking.stage = "a"
        data = {
            'is_hall': True,
            'housekeeping_type': 'Cleaning',
            'hall_id': self.hall_id.id,
            'desc': "New House Keeping request for Hall",
            'start_datetime': self.end_date
        }
        self.env['hotel.housekeeping'].create(data)
        if self.is_deposit:
            deposit = {
                'payment_type': 'inbound',
                'partner_id': self.customer_id.id,
                'amount': self.deposit_amount,
                'journal_id': self.journal_id.id
            }
            payment_id = self.env['account.payment'].create(deposit)
            payment_id.action_post()
        data = {
            'product_id': self.env.ref(
                'tk_hotel_management.hotel_feast_charges').id,
            'name': 'Hall Booking ',
            'quantity': 1,
            'price_unit': self.total_all_amount,
        }
        invoice_line.append((0, 0, {
            'display_type': 'line_section',
            'name': _('Hall Booking Charges')
        }))
        invoice_line.append((0, 0, data))
        if self.total_service_charges > 0:
            invoice_line.append((0, 0, {
                'display_type': 'line_section',
                'name': _('Extra Services Charges')
            }))
            for data in self.extra_service_ids:
                record = {
                    'product_id': data.product_id.id,
                    'name': data.service_description,
                    'quantity': data.quantity,
                    'price_unit': data.amount,
                }
                invoice_line.append((0, 0, record))
        record = {
            'partner_id': self.customer_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_line,
            'move_type': 'out_invoice'
        }
        feast_invoice_id = self.env['account.move'].sudo().create(record)
        self.feast_invoice_id = feast_invoice_id.id

    def draft_to_confirm(self):
        if self.hall_id:
            booked_id = self.env['hotel.hall.booking'].sudo().search(
                [('hall_id', '=', self.hall_id.id), ('start_date', '<', self.end_date),
                 ('end_date', '>', self.start_date), ('stage', '=', 'b')], limit=1)
            if booked_id:
                raise ValidationError(
                    _("Same hall is booked choose another hall to proceed."))
            self.env['hotel.hall.booking'].create({
                'hall_id': self.hall_id.id,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'stage': 'b'
            })
            project_id = self.env['ir.config_parameter'].sudo().get_param(
                'tk_hotel_management.housekeeping_project_id')
            housekeeping_project = self.env['project.project'].sudo().browse(int(project_id))
            data = {
                'name': f'Housekeeping Hall : {self.hall_id.hall_no}',
                'project_id': housekeeping_project.id if housekeeping_project else self.env.ref(
                    'tk_hotel_management.house_keeping_project').id,
                'user_ids': self.hall_id.floor_id.housekeeper_ids.ids,
                'start_date': self.end_date,
                'hall_booking_id': self.id,
                'company_id': self.company_id.id
            }
            task_id = self.env['project.task'].sudo().create(data)
            self.stages = 'Confirm'

    def confirm_to_cancel(self):
        self.stages = 'Cancel'
        hall_booking = self.env['hotel.hall.booking'].search(
            [('hall_id', '=', self.hall_id.id), ('start_date', '=', self.start_date),
             ('end_date', '=', self.end_date), ('stage', '=', 'b')], limit=1)
        hall_booking.stage = "a"

    @api.constrains('start_date', 'end_date')
    def check_hall_booking_timing(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.start_date < now:
                raise ValidationError(
                    _('The event start time cannot be outdated.'))
            if rec.start_date >= rec.end_date:
                raise ValidationError(
                    _('The event start date of hall booking must be earlier than the event end date.'))

    @api.depends('start_date', 'end_date')
    def _compute_no_of_days(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                duration = rec.end_date - rec.start_date
                duration_in_s = duration.total_seconds()
                hours = duration_in_s / 3600
                if hours >= 1:
                    rec.hours = hours
                else:
                    rec.hours = 0.0

    @api.depends('hours', 'price')
    def _compute_total_amount(self):
        for rec in self:
            if rec.hours and rec.price:
                rec.total_all_amount = rec.hours * rec.price
            else:
                rec.total_all_amount = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('booking_number', 'New') == 'New':
                vals['booking_number'] = self.env['ir.sequence'].next_by_code(
                    'rest.feast.booking') or 'New'
        return super(HotelFeast, self).create(vals_list)

    @api.depends('start_date', 'end_date', 'hall_id')
    def compute_hotel_hall_ids(self):
        for rec in self:
            hall_ids = []
            if rec.start_date and rec.end_date:
                hall_ids = self.env['hotel.hall.booking'].sudo().search(
                    [('start_date', '<=', rec.end_date),
                     ('end_date', '>=', rec.start_date),
                     ('stage', '!=', 'a')]).mapped('hall_id').ids
            rec.hall_ids = hall_ids

    @api.depends('extra_service_ids')
    def _compute_total_service_charges(self):
        for rec in self:
            amount = 0
            for data in rec.extra_service_ids:
                amount += data.total_amount
            rec.total_service_charges = amount


class HotelHallBooking(models.Model):
    _name = "hotel.hall.booking"
    _description = "Hotel Hall Booking"
    _rec_name = "hall_id"

    hall_id = fields.Many2one('hotel.hall', string="Hall")
    stage = fields.Selection(
        [('a', 'Available'), ('b', 'Booked'), ('m', 'Maintenance')],
        string="Status")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')


class HallExtraService(models.Model):
    _name = 'hall.extra.service'
    _description = 'Extra services for hall booking'

    product_id = fields.Many2one('product.product', string='Service Product',
                                 domain=[('type', '=', 'service')])
    service_description = fields.Char(string='Service Description')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    amount = fields.Monetary(string='Amount')
    quantity = fields.Integer(string='Quantity', default=1)
    hall_booking_id = fields.Many2one('hotel.feast', string='Hall')
    total_amount = fields.Monetary(compute='_compute_total_amount',
                                   string='Total Amount')

    @api.depends('amount', 'quantity')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.amount * rec.quantity

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            amount = 0
            if rec.product_id:
                amount = rec.product_id.lst_price
            rec.amount = amount
