# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo Website Helpdesk Support Ticket Management Module, Issue Management for Customers, Helpdesk with Ticket Support System',
    'version': '15.0.0.6',
    'category': 'Services/Helpdesk',
    'sequence': 110,
    'summary': 'Odoo website helpdesk Ticket Support management Issue management for customer support with dashboard in ticket helpdesk module, ticket portal, ticket management, customer helpdesk, help desk ticket, manage your customer help desk support ticket, billing for support, timesheets, website support ticket, website help desk support online ticketing system for customer support service, helpdesk module, customizable helpdesk app, Service Desk, Helpdesk with Stages, support ticket by team, custoker support module manage customer support ticket help desk app Help Desk Ticket Management odoo online customer support',

    'depends': ['base_setup','mail','utm','rating','web_tour','resource','portal','project','website','hr_timesheet','web','board','account','contacts','product'],
    'description': """Odoo website helpdesk Ticket management odoo module with version 15,14,13,12 and dashboard for your customer support ticket helpdesk module, ticket portal, ticket management, customer helpdesk, helpdesk ticket manage your customer help desk support ticket, billing for support, timesheets, website support ticket, website help desk support online ticketing system
    

Odoo Helpdesk Ticket Management App odoo 15, 14, 13, 12
================================

Features:

    - Process of customer tickets through different stages to solve them.
    - Add priorities, types, descriptions and tags to define your tickets.
    - Use the chatter to communicate additional information and ping co-workers on helpdesk tickets.
    - Enjoy the use of an adapted dashboard, and an easy-to-use kanban view to handle your ticket portal.
    - Make an in-depth analysis of your tickets through the pivot view in the reports menu.
    - Create a team and define its members, use an automatic assignment method if you wish.
    - Use a mail alias to automatically create tickets and communicate with your customers.
    - Add Service Level Agreement deadlines automatically to your Odoo website helpdesk Tickets.
    - Get customer feedback by using ratings.
    - Install additional features easily using your team form view.
    - Interactive Dashboard, Ticket filters

    """,
    "data": [
        "security/helpdesk_security.xml",
        "security/ir.model.access.csv",

        "data/helpdesk_ticket_sequence_number.xml",
        "data/helpdesk_ticket_mail_template.xml",
        "data/aagam_helpdesk_ticket_mail_template.xml",
        "data/aagam_helpdesk_ticket_data.xml",

        # "views/asset.xml",
        "views/helpdesk_menu.xml",
        "views/view_aagam_helpdesk_ticket_type.xml",
        "views/view_aagam_helpdesk_ticket_team.xml",
        "views/view_aagam_helpdesk_stage.xml",
        "views/view_aagam_helpdesk_ticket.xml",
        "views/view_aagam_helpdesk_ticket_category.xml",
        "views/view_aagam_helpdesk_channel.xml",
        "views/view_aagam_helpdesk_ticket_tag.xml",
        "views/view_aagam_helpdesk_ticket_sla_policy.xml",
        "views/view_portal_create_helpdesk_ticket.xml",
        "views/portal_template_helpdesk_ticket.xml",
        "views/helpdesk_ticket_search.xml",
        "views/view_inherit_res_config.xml",

        # 'data/to_heldesk_data.xml',

	"report/report.xml",
        "report/ticket_report.xml",

    ],
"demo":["data/aagam_helpdesk_ticket_data.xml"],
    'assets': {
            'web._assets_primary_variables': [
                '/website_support_ticket_odoo_aagam/static/src/scss/style.scss',
            ],
            'web.assets_qweb': [
                'website_support_ticket_odoo_aagam/static/src/xml/**/*',
            ],
            'web.assets_backend': [

                '/website_support_ticket_odoo_aagam/static/src/js/helpdesk_ticket_dashboard.js',
                '/website_support_ticket_odoo_aagam/static/src/js/helpdesk_ticket_filter_stage_dashboard.js',
                '/website_support_ticket_odoo_aagam/static/src/js/Chart.js',
                '/website_support_ticket_odoo_aagam/static/src/css/style.css',
            ],
            'web.assets_frontend': [
                '/website_support_ticket_odoo_aagam/static/src/scss/style.scss',
                '/website_support_ticket_odoo_aagam/static/src/js/portal.js',

            ],
        },
     'price': 76.00,
    'currency': 'USD',
    'support': ': business@aagaminfotech.com',
    'author': 'Aagam Infotech',
    'website': 'http://aagaminfotech.com',
    'installable': True,
    'license': 'OPL-1',
    'images': ['static/description/images/Banner-Img.png'],
    'application': True,
}
