# -*- coding: utf-8 -*-
from odoo import models, fields


class AagamHelpdeskTicketMaintenanceEquipmentCategory(models.Model):
    _name = "aagam.helpdesk.ticket.maintenance.equipment.category"

    name = fields.Char(string="Name category")
