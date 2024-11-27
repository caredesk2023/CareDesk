# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    helpdesk_ticket_target_closed = fields.Float(string='Target Tickets to Close', default=1)
    helpdesk_ticket_target_rating = fields.Float(string='Target Customer Rating', default=100)
    helpdesk_ticket_target_success = fields.Float(string='Target Success Rate', default=100)
    helpdesk_team_ids = fields.Many2many(
        'aagam.helpdesk.ticket.team', string="Helpdesk Team", copy=False, store=True)

    _sql_constraints = [
        ('target_ticket_closed_not_zero', 'CHECK(helpdesk_ticket_target_closed > 0)', 'You cannot have negative targets'),
        ('target_ticket_rating_not_zero', 'CHECK(helpdesk_ticket_target_rating > 0)', 'You cannot have negative targets'),
        ('target_ticket_success_not_zero', 'CHECK(helpdesk_ticket_target_success > 0)', 'You cannot have negative targets'),
    ]

    def __init__(self, pool, cr):
        init_res = super(ResUsers, self).__init__(pool, cr)
        helpdesk_fields = [
            'helpdesk_ticket_target_closed',
            'helpdesk_ticket_target_rating',
            'helpdesk_ticket_target_success',
        ]
        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend(helpdesk_fields)
        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend(helpdesk_fields)
        return init_res
