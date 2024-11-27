# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class aagamTicketType(models.Model):
    _name = "aagam.helpdesk.ticket.type"
    _description = "Helpdesk Ticket Type"

    name = fields.Char(string="Name",required=1)
    team_ids = fields.Many2many("aagam.helpdesk.ticket.team",string="Helpdesk Teams")
