# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SeasonPrice(models.Model):
    _name = 'season.price'
    _description = "Seasonal Prices"

    name = fields.Char(string='Title')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    increment_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed')],
        string='Increment / Decrement Type')
    increment_val = fields.Float(string='Increment / Decrement')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        ondelete='cascade')

    @api.constrains("start_date", "end_date")
    def _check_end_time(self):
        for rec in self:
            if rec.end_date < rec.start_date:
                raise ValidationError(
                    _("Season end time cannot be less than season start time."))
