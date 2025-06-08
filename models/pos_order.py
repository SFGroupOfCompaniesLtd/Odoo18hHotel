# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError, UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    booking_id = fields.Many2one('hotel.booking', string='Booking', readonly=True)











