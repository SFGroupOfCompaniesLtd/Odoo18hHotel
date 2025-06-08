from odoo import fields, models


class ResConfigSettingInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    dinner_product = fields.Many2one(
        'product.product', string='Dinner',
        domain=[
            ('type', '=', 'service')],
        default=lambda self: self.env.ref('tk_hotel_management.room_dinner',
                                          raise_if_not_found=False),
        config_parameter='tk_hotel_management.dinner_product',
    )
    lunch_product = fields.Many2one(
        'product.product', string='Lunch',
        domain=[('type', '=', 'service')],
        default=lambda self: self.env.ref('tk_hotel_management.room_lunch',
                                          raise_if_not_found=False),
        config_parameter='tk_hotel_management.lunch_product')
    breakfast_product = fields.Many2one(
        'product.product', string='Breakfast',
        domain=[
            ('type', '=', 'service')],
        default=lambda self: self.env.ref('tk_hotel_management.room_breakfast',
                                          raise_if_not_found=False),
        config_parameter='tk_hotel_management.breakfast_product')

    back_date_check_in = fields.Boolean(
        string='Back Date Check-in',
        config_parameter='tk_hotel_management.back_date_check_in')

    discount_product_id = fields.Many2one(
        'product.product',
        default=lambda self: self.env.ref('tk_hotel_management.room_charges_discount',
                                          raise_if_not_found=False),
        config_parameter='tk_hotel_management.discount_product_id'
    )

    housekeeping_project_id = fields.Many2one(
        'project.project',
        default=lambda self: self.env.ref('tk_hotel_management.house_keeping_project',
                                          raise_if_not_found=False),
        config_parameter='tk_hotel_management.housekeeping_project_id'
    )
