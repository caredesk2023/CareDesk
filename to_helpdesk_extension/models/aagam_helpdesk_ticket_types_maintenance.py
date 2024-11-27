# -*- coding: utf-8 -*-
from odoo import fields, models


class AagamHelpdeskTicketTypesMaintenance(models.Model):
    _name = "aagam.helpdesk.ticket.types.maintenance"

    types_maintenance_name = fields.Char(string="Type of maintenance")
