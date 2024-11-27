# -*- coding: utf-8 -*-
from odoo import models, fields


class AagamTelpdeskTicketMaintenanceEquipment(models.Model):
    _name = "aagam.helpdesk.ticket.maintenance.equipment"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Equipment Name', required=True, translate=True)
    category_id = fields.Many2one('aagam.helpdesk.ticket.maintenance.equipment.category', string="Equipment Category")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    color = fields.Integer(string='Color Index')
    technician_user_id = fields.Many2one('res.users', string='Technician')
    assign_date = fields.Date(string='Assigned Date', default=fields.Date.context_today)
    scrap_date = fields.Date(string='Scrap Date')
    location = fields.Char(string='Location')
    note = fields.Html(string='Note')
    partner_id = fields.Many2one('res.partner', string='Vendor', check_company=True)
    partner_ref = fields.Char(string='Vendor Reference')
    model = fields.Char('Model')
    serial_no = fields.Char(string='Serial Number', copy=False)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.context_today, required=True)
    cost = fields.Float(string='Cost')
    warranty_date = fields.Date(string='Warranty Expiration Date')
