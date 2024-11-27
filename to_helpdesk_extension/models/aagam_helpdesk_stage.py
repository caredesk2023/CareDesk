# -*- coding: utf-8 -*-

from odoo import fields, models


class aagamHelpdeskStage(models.Model):
    _inherit = "aagam.helpdesk.stage"

    color = fields.Integer(string='Color', default=4)
