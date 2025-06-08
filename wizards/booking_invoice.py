# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, api, models, _


class HotelBookingInvoice(models.TransientModel):
    _name = "hotel.booking.invoice"
    _description = "Hotel Booking Invoice Details"
    _rec_name = 'booking_id'

    booking_id = fields.Many2one('hotel.booking', string="Booking")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 ondelete='cascade')
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    room_total_charges = fields.Monetary(string="Room Charged",
                                         related='booking_id.room_total_charges',
                                         store=True)
    transportation_charges = fields.Monetary(string="Transportation Charges",
                                             related='booking_id.transport_total_charges',
                                             store=True)
    advance_amount = fields.Monetary(string="Advance Amount",
                                     related='booking_id.advance_amount')
    laundry_charges = fields.Monetary(string="Laundry Charges",
                                      related='booking_id.laundry_total_charges',
                                      store=True)
    restaurant_charges = fields.Monetary(string="Restaurant Charges",
                                         related='booking_id.restaurant_services_charges',
                                         store=True)
    extra_service_charges = fields.Monetary(string="Extra Service Charges",
                                            related='booking_id.all_service_amount',
                                            store=True)
    room_charges_desc = fields.Text(string="Room Charges Desc",
                                    compute="_compute_room_charge_desc")
    transport_charges_desc = fields.Text(string="Transport Charges Desc",
                                         compute="_compute_transport_charge_desc")
    laundry_charges_desc = fields.Text(string="Laundry Charges Desc",
                                       compute="_compute_laundry_charge_desc")
    restaurant_charges_desc = fields.Text(string="Restaurant Charges Desc",
                                          compute="_compute_restaurant_charge_desc")
    extra_charges_desc = fields.Text(string="Extra Service Charges Desc",
                                     compute="_compute_extra_charge_desc")
    total_amount = fields.Monetary(string="Total Amount",
                                   compute="_compute_payable_amount")
    payable_amount = fields.Monetary(string="Payable Amount",
                                     compute="_compute_payable_amount")
    agent_commission = fields.Monetary(string="Agent Commission",
                                       compute="_compute_agent_commission")
    invoice_payment_type = fields.Selection(
        related="booking_id.invoice_payment_type", string="Invoice Payment")

    discount_amount = fields.Monetary(compute="_compute_discount_amount")
    discount_desc = fields.Char(compute="_compute_discount_desc")

    @api.model
    def default_get(self, fields):
        res = super(HotelBookingInvoice, self).default_get(fields)
        active_id = self._context.get('active_id')
        res['booking_id'] = active_id
        return res

    @api.depends('booking_id')
    def _compute_discount_amount(self):
        for rec in self:
            amount = 0
            if rec.booking_id.is_any_discount:
                amount = rec.booking_id.discount_val
                if rec.booking_id.discount_type == 'percentage':
                    amount = (rec.booking_id.room_total_charges
                              * rec.booking_id.discount_val) / 100
            rec.discount_amount = amount

    @api.depends('booking_id')
    def _compute_discount_desc(self):
        for rec in self:
            desc = ""
            if rec.booking_id.is_any_discount:
                desc = f"Discount on Room charges - Booking ({rec.booking_id.booking_number})"
            rec.discount_desc = desc

    @api.depends('booking_id')
    def _compute_room_charge_desc(self):
        for rec in self:
            room = ""
            if rec.booking_id.invoice_payment_type == "by_night":
                room = room + " -No Invoice Generated of Room Charges Because Invoice Posted by Every Night- " + "\n"
            for data in rec.booking_id.room_ids:
                room = room + " " + str((
                        data.room_id.room_no + " - " + data.room_id.room_type_id.name)) + " - " + str(
                    data.total_price) + rec.currency_id.symbol + "\n"
            rec.room_charges_desc = room

    @api.depends('booking_id')
    def _compute_transport_charge_desc(self):
        for rec in self:
            transport = ""
            for data in rec.booking_id.transport_ids:
                transport = transport + " " + str(
                    data.transport_type) + " - " + str(
                    data.km) + " KM" + " - " + str(
                    data.total_charges) + rec.currency_id.symbol + "\n"
            rec.transport_charges_desc = transport

    @api.depends('booking_id')
    def _compute_laundry_charge_desc(self):
        for rec in self:
            laundry = ""
            for data in rec.booking_id.laundry_ids:
                laundry = laundry + " " + str(
                    data.service_name_id.service_name) + " - " + str(
                    data.quantity) + " Item" + " - " + str(
                    data.total_charges) + rec.currency_id.symbol + "\n"
            rec.laundry_charges_desc = laundry

    @api.depends('booking_id')
    def _compute_restaurant_charge_desc(self):
        for rec in self:
            restaurant = ""
            for data in rec.booking_id.restaurant_ids:
                restaurant = restaurant + " " + str(
                    data.reservation_number) + " - " + str(
                    data.total_charges) + rec.currency_id.symbol + "\n"
            rec.restaurant_charges_desc = restaurant

    @api.depends('booking_id')
    def _compute_extra_charge_desc(self):
        for rec in self:
            extra = ""
            for data in rec.booking_id.service_ids:
                extra = extra + " " + \
                        str(data.service) + " - " + str(data.all_amount) + \
                        rec.currency_id.symbol + "\n"
            rec.extra_charges_desc = extra

    @api.depends('room_total_charges', 'transportation_charges',
                 'laundry_charges',
                 'restaurant_charges', 'extra_service_charges', 'booking_id',
                 'discount_amount')
    def _compute_payable_amount(self):
        for rec in self:
            total_amount = 0.0
            if rec.booking_id.invoice_payment_type == "by_night":
                room_charges = 0
            else:
                room_charges = rec.room_total_charges
            total_amount = room_charges + rec.transportation_charges + \
                           rec.laundry_charges + rec.restaurant_charges + \
                           rec.extra_service_charges - rec.discount_amount
            rec.total_amount = total_amount
            rec.payable_amount = total_amount

    @api.depends('booking_id')
    def _compute_agent_commission(self):
        for rec in self:
            if rec.booking_id:
                if rec.booking_id.is_any_agent:
                    if rec.booking_id.agent_commission_type == "fix":
                        rec.agent_commission = rec.booking_id.agent_commission
                    else:
                        rec.agent_commission = rec.booking_id.agent_percentage_commission
                else:
                    rec.agent_commission = 0.0
            else:
                rec.agent_commission = 0.0

    def action_create_booking_invoice(self):
        if self.booking_id.is_advance:
            deposit = {
                'payment_type': 'inbound',
                'partner_id': self.booking_id.customer_id.id,
                'amount': self.advance_amount,
                'journal_id': self.booking_id.journal_id.id
            }
            if not self.booking_id.invoice_id:
                payment_id = self.env['account.payment'].create(deposit)
                payment_id.action_post()
        self.booking_id.confirm_to_done()
        invoice_lines = []
        if self.booking_id.invoice_payment_type == 'once':
            invoice_lines.append((0, 0, {
                'display_type': 'line_section',
                'name': _('Room Charges')
            }))
            for rec in self.booking_id.room_ids:
                room_data = {
                    'product_id': rec.room_id.product_id.id,
                    'name': f"{rec.room_id.product_id.name} - {rec.charges_per_night}{rec.currency_id.symbol}",
                    'quantity': rec.days,
                    'tax_ids': rec.tax_ids.ids,
                    'price_unit': rec.charges_per_night,
                }
                invoice_lines.append((0, 0, room_data))
        if self.transportation_charges > 0:
            invoice_lines.append((0, 0, {
                'display_type': 'line_section',
                'name': _('Transportation Charges')
            }))
            transportation_data = {
                'product_id': self.env.ref(
                    'tk_hotel_management.hotel_transportation_charge').id,
                'name': self.transport_charges_desc,
                'quantity': 1,
                'price_unit': self.transportation_charges,
            }
            invoice_lines.append((0, 0, transportation_data))
        if self.restaurant_charges > 0:
            invoice_lines.append((0, 0, {
                'display_type': 'line_section',
                'name': _('Restaurant Charges')
            }))
            restaurant_data = {
                'product_id': self.env.ref(
                    'tk_hotel_management.hotel_restaurant_charge').id,
                'name': self.restaurant_charges_desc,
                'quantity': 1,
                'price_unit': self.restaurant_charges,
            }
            invoice_lines.append((0, 0, restaurant_data))
        if self.laundry_charges > 0:
            invoice_lines.append((0, 0, {
                'display_type': 'line_section',
                'name': _('Laundry Charges')
            }))
            for rec in self.booking_id.laundry_ids:
                laundry_data = {
                    'product_id': rec.service_name_id.product_id.id,
                    'name': f"{rec.service_name_id.service_name} - {rec.quantity} Item - {rec.total_charges}{rec.currency_id.symbol}",
                    'quantity': rec.quantity,
                    'price_unit': rec.charges,
                }
                invoice_lines.append((0, 0, laundry_data))
        if self.extra_service_charges > 0:
            invoice_lines.append((0, 0, {
                'display_type': 'line_section',
                'name': _('Extra Service Charges')
            }))
            for rec in self.booking_id.service_ids:
                extra_service_data = {
                    'product_id': rec.product_id.id if rec.product_id else self.env.ref(
                        'tk_hotel_management.hotel_extra_services_charge').id,
                    'name': rec.service,
                    'quantity': rec.quantity,
                    'price_unit': rec.amount,
                }
                invoice_lines.append((0, 0, extra_service_data))
        if self.booking_id.is_any_discount:
            discount_product = self.env[
                'ir.config_parameter'].sudo().get_param(
                'tk_hotel_management.discount_product_id')
            invoice_lines.append((0, 0, {
                'display_type': 'line_section',
                'name': _('Discount on Room Charges')
            }))
            discount_data = {
                'product_id': discount_product if discount_product else False,
                'name': self.discount_desc,
                'quantity': 1,
                'price_unit': -self.discount_amount
            }
            invoice_lines.append((0, 0, discount_data))
        record = {
            'partner_id': self.booking_id.customer_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'move_type': 'out_invoice',
        }

        if not self.booking_id.invoice_id and invoice_lines:
            invoice_id = self.env['account.move'].sudo().create(record)
            self.booking_id.invoice_id = invoice_id.id
        if self.booking_id.invoice_id:
            if self.booking_id.invoice_id.state == 'draft':
                self.booking_id.invoice_id.invoice_line_ids = [(5, 0, 0)]
                self.booking_id.invoice_id.invoice_line_ids = invoice_lines
            if self.booking_id.invoice_id.state == 'posted':
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'title': (
                            _('Invoice is posted you cannot make any changes.')),
                        'sticky': False,
                    }
                }
                return message

        if self.booking_id.is_any_agent:
            price = self.booking_id.agent_commission
            if self.booking_id.agent_commission_type == 'percentage':
                price = self.booking_id.agent_percentage_commission
            data = {
                'product_id': self.env.ref(
                    'tk_hotel_management.agent_invoice').id,
                'name': 'Commission of ' + self.booking_id.booking_number + " Booking",
                'quantity': 1,
                'price_unit': price,
            }
            agent_bill_line = [(0, 0, data)]
            agent = {
                'partner_id': self.booking_id.agent_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': agent_bill_line,
                'move_type': 'in_invoice',
            }
            if not self.booking_id.agent_bill_id:
                bill_id = self.env['account.move'].sudo().create(agent)
                self.booking_id.agent_bill_id = bill_id.id
            if self.booking_id.agent_bill_id:
                if self.booking_id.agent_bill_id.state == 'draft':
                    self.booking_id.agent_bill_id.invoice_line_ids = [
                        (5, 0, 0)]
                    self.booking_id.agent_bill_id.invoice_line_ids = agent_bill_line
                if self.booking_id.agent_bill_id.state == 'posted':
                    message = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'warning',
                            'title': (
                                _('Agent bill invoice is posted you cannot make any changes.')),
                            'sticky': False,
                        }
                    }
                    return message
