# -*- coding: utf-8 -*-
from odoo import fields, models


class HelpdeskSupportRequests(models.Model):
    _name = "helpdesk.support.requests"
    _description = "Helpdesk Support Requests"

    ticket_id = fields.Many2one('aagam.helpdesk.ticket', string='Ticket ID')
    description = fields.Html('Description')
