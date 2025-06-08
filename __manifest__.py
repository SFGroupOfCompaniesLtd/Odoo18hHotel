# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

{
    'name': "Advance Hotel Management | Hotel Reservation Management",
    'summary': """This module allow you to manage Hotel, Room Booking, Hall Booking, Restaurant, Laundry, Housekeeping & etc..""",
    'description': """
        Hotel  Management
        Hotel Room Management
        Hall Booking
        Restaurant Services
        Housekeeping Services
        Laundry Services
        Transport Services
        Reservation Services
    """,
    'category': 'Industry',
    'version': '2.2',
    'author': 'TechKhedut Inc.',
    'company': 'TechKhedut Inc.',
    'maintainer': 'TechKhedut Inc.',
    'website': "https://www.techkhedut.com",
    'depends': [
        'contacts',
        'account',
        'hr',
        'mail',
        'product',
        'project',
        'point_of_sale',
        'pos_restaurant',
    ],
    'data': [
        # Security
        'security/groups.xml',
        'security/ir.model.access.csv',
        # Data
        'data/ir_cron.xml',
        'data/sequence.xml',
        'data/data.xml',
        # Report
        'reports/booking_report.xml',
        # Wizards
        'wizards/booking_report.xml',
        'wizards/booking_invoice_view.xml',
        'wizards/room_cancellation_view.xml',
        'wizards/room_change_view.xml',
        'wizards/add_extra_people_wizard_view.xml',
        'wizards/book_rooms_wizard.xml',
        # Views
        'views/hotel_room_views.xml',
        'views/hotel_floor_views.xml',
        'views/hotel_room_type_views.xml',
        'views/hotel_room_category_views.xml',
        'views/hotel_customer_details_views.xml',
        'views/hotel_room_details_views.xml',
        'views/hotel_booking_views.xml',
        'views/hotel_booking_proof_details_views.xml',
        'views/hotel_room_facilities_views.xml',
        'views/hotel_transport_driver_views.xml',
        'views/hotel_transport_vehicle_views.xml',
        'views/hotel_transport_vehicle_type_views.xml',
        'views/hotel_transport_location_views.xml',
        'views/hotel_transport_views.xml',
        'views/hotel_laundry_service_type_views.xml',
        'views/hotel_laundry_service_details_views.xml',
        'views/hotel_housekeeping_views.xml',
        'views/hotel_staff_views.xml',
        'views/hotel_restaurant_views.xml',
        'views/hotel_restaurant_food_item_views.xml',
        'views/hotel_restaurant_customer_food_order_views.xml',
        'views/hotel_laundry_item_views.xml',
        'views/hotel_restaurant_food_category_views.xml',
        'views/hotel_restaurant_table_details_views.xml',
        'views/hotel_hall_booking_views.xml',
        'views/hotel_hall_views.xml',
        'views/hotel_extra_services_views.xml',
        'views/hotel_seasonal_price_views.xml',
        'views/hotel_res_config_settings_inherit_view.xml',
        'views/assets.xml',
        'views/project_task_inherit.xml',
        'views/pos_order_inherite_view.xml',
        # Menus
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tk_hotel_management/static/src/js/lib/moment.min.js',
            'tk_hotel_management/static/src/js/lib/apexcharts.js',
            'tk_hotel_management/static/src/js/lib/Animated.js',
            'tk_hotel_management/static/src/js/lib/index.js',
            'tk_hotel_management/static/src/js/lib/xy.js',
            'tk_hotel_management/static/src/js/lib/percent.js',
            'tk_hotel_management/static/src/js/dashboard.js',
            'tk_hotel_management/static/src/js/hotel.js',
            'tk_hotel_management/static/src/css/lib/dashboard.css',
            'tk_hotel_management/static/src/css/lib/style.css',
            'tk_hotel_management/static/src/css/style.scss',
            'tk_hotel_management/static/src/scss/dash_style.scss',
            'tk_hotel_management/static/src/xml/dashboard.xml',
        ],
'point_of_sale._assets_pos': [
            'tk_hotel_management/static/src/models/pos_session.js',
            'tk_hotel_management/static/src/models/hotel_booking.js',
            'tk_hotel_management/static/src/pos/hotel_booking_screen.js',
            'tk_hotel_management/static/src/pos/hotel_booking_screen.css',
            'tk_hotel_management/static/src/pos/hotel_booking_screen.xml',
            'tk_hotel_management/static/src/pos/booking_button.js',
            'tk_hotel_management/static/src/pos/booking_button.xml',
            'tk_hotel_management/static/src/models/order.js',

        ],
    },
    'images': ['static/description/banner.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'price': 199,
    'currency': 'USD',
    'license': 'OPL-1',
}
