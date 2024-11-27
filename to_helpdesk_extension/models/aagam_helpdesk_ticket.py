# -*- coding: utf-8 -*-
from odoo import fields, models


class AagamHelpdeskTicket(models.Model):
    _inherit = "aagam.helpdesk.ticket"

    maintenance_name = fields.Char(string="Request")
    maintenance_created_by = fields.Many2one('hr.employee', string="Created by", default=lambda s: s.env.user.employee_id)
    maintenance_equipment_id = fields.Many2one('aagam.helpdesk.ticket.maintenance.equipment', string="Team")
    maintenance_category_id = fields.Many2one('aagam.helpdesk.ticket.maintenance.equipment.category', string="Category")
    maintenance_request_date = fields.Date('Request Date', tracking=True, default=fields.Date.context_today)
    maintenance_types_maintenance_id = fields.Many2one('aagam.helpdesk.ticket.types.maintenance', string="Type of maintenance")
    maintenance_user_id = fields.Many2one('res.users', string="Responsible")
    maintenance_schedule_date = fields.Datetime(string='Scheduled Date')
    maintenance_duration = fields.Float(string="Duration")
    maintenance_priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority')
    maintenance_description = fields.Html(string="Description")
    support_requests_ids = fields.One2many('helpdesk.support.requests', 'ticket_id', string="Support requests")
