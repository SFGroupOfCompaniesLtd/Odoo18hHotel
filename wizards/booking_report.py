# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, api, models
import xlwt
import base64
from io import BytesIO


class BookingExcelReport(models.TransientModel):
    _name = 'booking.excel.report'
    _description = "Booking Excel report"

    check_in = fields.Date(string="Check In Date", required=True)
    check_out = fields.Date(string="Check Out Date", required=True)

    def booking_excel_report(self):
        check_in = self.check_in
        check_out = self.check_out
        customer_ids = self.env['hotel.room.details'].search(
            [('check_in', '>=', check_in),
             ('check_out', '<=', check_out)])

        filename = 'Customer Details.pdf'
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet1 = workbook.add_sheet('Customer', cell_overwrite_ok=True)
        sheet1.show_grid = False
        format1 = xlwt.easyxf()
        xlwt.add_palette_colour("custom_light_green", 0x21)
        workbook.set_colour_RGB(0x21, 247, 255, 250)
        xlwt.add_palette_colour("custom_normal_red", 0x22)
        workbook.set_colour_RGB(0x22, 250, 234, 232)
        xlwt.add_palette_colour("custom_normal_green", 0x23)
        workbook.set_colour_RGB(0x23, 235, 255, 242)
        border_square = xlwt.Borders()
        border_square.top = xlwt.Borders.HAIR
        border_square.left = xlwt.Borders.HAIR
        border_square.right = xlwt.Borders.HAIR
        border_square.bottom = xlwt.Borders.HAIR
        border_square.top_colour = xlwt.Style.colour_map["gray50"]
        border_square.bottom_colour = xlwt.Style.colour_map["gray50"]
        border_square.right_colour = xlwt.Style.colour_map["gray50"]
        border_square.left_colour = xlwt.Style.colour_map["gray50"]
        al = xlwt.Alignment()
        al.horz = xlwt.Alignment.HORZ_CENTER
        al.vert = xlwt.Alignment.VERT_CENTER
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'
        date_format.font.name = "Century Gothic"
        date_format.borders = border_square
        date_format.alignment = al
        title = xlwt.easyxf(
            "font: height 350, name Century Gothic, bold on, color_index blue_gray;"
            " align: vert center, horz center;"
            "border: bottom thick, bottom_color sea_green;"
            "pattern: pattern solid, fore_colour custom_light_green;")
        sub_title = xlwt.easyxf(
            "font: height 215, name Century Gothic, bold on, color_index gray80; "
            "align: vert center, horz center; "
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")
        sub_title_right = xlwt.easyxf(
            "font: height 185, name Century Gothic, bold on, color_index gray80; "
            "align: vert center, horz right; "
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")
        border_all_right = xlwt.easyxf(
            "align:horz right, vert center;"
            "font:name Century Gothic;"
            "border:  top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")
        border_all_center = xlwt.easyxf(
            "align:horz center, vert center;"
            "font:name Century Gothic;"
            "border:  top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

        sheet1.col(0).width = 7000
        sheet1.col(1).width = 5000
        sheet1.col(2).width = 6000
        sheet1.col(3).width = 6000
        sheet1.col(4).width = 6000
        sheet1.col(5).width = 6000
        sheet1.col(6).width = 6000
        sheet1.row(0).height = 1000
        sheet1.row(1).height = 600
        sheet1.write_merge(0, 0, 0, 6, "Booking Details", title)
        sheet1.write(1, 0, 'Booking Ref.', sub_title)
        sheet1.write(1, 1, 'Customer', sub_title)
        sheet1.write(1, 2, 'Room', sub_title)
        sheet1.write(1, 3, 'Check-In Date', sub_title)
        sheet1.write(1, 4, 'Check-Out Date', sub_title)
        sheet1.write(1, 5, 'Number Of Nights', sub_title_right)
        sheet1.write(1, 6, 'Total Charges', sub_title_right)
        row = 2
        for customer in customer_ids:
            sheet1.row(row).height = 400
            sheet1.write(row, 0, customer.booking_id.booking_number, border_all_center)
            sheet1.write(row, 1, customer.booking_id.customer_id.name, border_all_center)
            sheet1.write(row, 2, customer.room_id.room_no, border_all_center)
            sheet1.write(row, 3, customer.check_in, date_format)
            sheet1.write(row, 4, customer.check_out, date_format)
            sheet1.write(row, 5, customer.days, border_all_right)
            sheet1.write(row, 6, f"{customer.currency_id.symbol} {customer.total_price}", border_all_right)
            row += 1

        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())

        attachment = self.env['ir.attachment'].sudo()
        filename = 'Customer Details' + ".xlsx"
        attachment_id = attachment.create(
            {'name': filename,
             'type': 'binary',
             'public': False,
             'datas': out})
        if attachment_id:
            report = {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % (attachment_id.id),
                'target': 'self',
            }
            return report
