# -*- coding: utf-8 -*-
{
    'name': "Helpdesk Extension | TO",
    'summary': """""",
    'description': """""",
    'author': "Tecnologías ORGVEN",
    'website': "https://tecnologiasorgven.com/",
    'category': 'Services/Helpdesk',
    'version': '0.0.5.8',
    'depends': [
        'base',
        'website_support_ticket_odoo_aagam',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/website_template_support.xml',
        'views/website_template_new_support.xml',
        'views/aagam_helpdesk_ticket_views.xml',
        'views/views_aagam_helpdesk_ticket_maintenance_equipment.xml',
        'views/view_aagam_helpdesk_stage.xml',
        'views/website_template_support_ticket.xml',
    ],
    'demo': [
    ],
    'assets': {
        'web.assets_frontend': [
            '/to_helpdesk_extension/static/src/css/frontend.css',
            '/to_helpdesk_extension/static/src/javascript/helpdesk_new_support.js',
            '/to_helpdesk_extension/static/src/javascript/helpdesk_ticket_support.js',
            '/to_helpdesk_extension/static/src/javascript/helpdesk_ticket.js',
        ],
    },
}
