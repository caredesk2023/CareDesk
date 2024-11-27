# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    is_attachment = fields.Boolean('Allow Attachment', default=False, config_parameter='website_support_ticket_odoo_aagam.is_attachment')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id, readonly=True)
