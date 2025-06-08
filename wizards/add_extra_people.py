from odoo import fields, models, api, _


class AddExtraPeopleWizard(models.TransientModel):
    _name = 'extra.people.wizard'
    _description = 'Model for adding extra person in booking'

    booking_id = fields.Many2one('hotel.booking', string='Booking Ref')
    adult_quantity = fields.Integer(string='Extra Adults')
    child_quantity = fields.Integer(string='Extra Children')
    room_detail_id = fields.Many2one('hotel.room.details', string='Room ')
    room_id = fields.Many2one(related='room_detail_id.room_id')
    number_of_days = fields.Integer(related='room_detail_id.days')
    per_adult_extra_charges = fields.Monetary(
        related='room_id.room_type_id.charges_per_extra_adult')
    per_child_extra_charges = fields.Monetary(
        related='room_id.room_type_id.charges_per_extra_child')
    charges = fields.Monetary(string='Total Charges')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company, ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')

    def default_get(self, fields_list):
        res = super(AddExtraPeopleWizard, self).default_get(fields_list)
        active_id = self._context.get('active_id')
        res['booking_id'] = active_id
        return res

    @api.onchange('adult_quantity', 'child_quantity', 'room_detail_id')
    def onchange_quantity_and_room(self):
        adult_charges = 0.0
        child_charges = 0.0
        if self.adult_quantity > 0:
            adult_charges = self.adult_quantity * \
                            self.number_of_days * self.per_adult_extra_charges
        if self.child_quantity > 0:
            child_charges = self.child_quantity * \
                            self.number_of_days * self.per_child_extra_charges
        self.charges = adult_charges + child_charges

    def add_extra_service_charges(self):
        data = {
            'product_id': self.env.ref('tk_hotel_management.hotel_extra_services_charge').id,
            'service': f"Extra person charges for {self.number_of_days} days and for room no {self.room_id.room_no}",
            'quantity': 1,
            'amount': self.charges,
            'booking_id': self.booking_id.id
        }
        self.env['hotel.extra.services'].create(data)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': _('Extra-person charges were added.'),
                'type': 'rainbow_man',
            }
        }
