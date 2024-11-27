# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
import calendar as cal
from datetime import timedelta
import datetime
from datetime import date
from email.utils import formataddr

TICKET_PRIORITY = [
    ('0', 'All'),
    ('1', 'Low priority'),
    ('2', 'High priority'),
    ('3', 'Urgent'),
    ('4', 'High'),
]

class HelpdeskTicketInvoice(models.Model):
    _name = 'helpdesk.ticket.invoice'
    _description = "Helpdesk Ticket Invoice"

    product_id = fields.Many2one('product.product', 'Product',required=True)
    name = fields.Char(related='product_id.name',string='Lable',required=True)
    tax = fields.Char(string='Tax')
    quantity = fields.Float('Quantity')
    price_unit = fields.Float(compute='_compute_abcd',string='Price',store=True)
    ticket_id = fields.Many2one('aagam.helpdesk.ticket', 'First')

    @api.depends('quantity')
    def _compute_abcd(self):
        for record in self:
            search = record.env['product.product'].sudo().search([('name','=',record.product_id.name)])
            for rec in search:
                record.price_unit = record.quantity * rec.list_price

    @api.onchange('product_id')
    def _onchange_tax(self):
        for record in self:
            search = record.env['product.product'].sudo().search([('name','=',record.product_id.name)])
            for rec in search:
                record.tax =search.taxes_id.name



class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    ticket_id = fields.Many2one('aagam.helpdesk.ticket', 'Ticket')

class aagamHelpdeskTicket(models.Model):
    _name = "aagam.helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _rec_name = "number"
    _inherit = ["mail.thread.cc", "mail.activity.mixin", "portal.mixin"]

    def _default_helpdesk_stage_id(self):
        return [(0, 0, {'name': 'New', 'sequence': 0,
                        'template_id': self.env.ref('website_support_ticket_odoo_aagam.aagam_helpdesk_ticket_new_create',
                                                    raise_if_not_found=False) or None})]

    @api.model
    def group_helpdesk_stage_ids(self, stages, domain, order):
        helpdesk_stage_ids = self.env["aagam.helpdesk.stage"].search([])
        return helpdesk_stage_ids

    name = fields.Char(string="Name",required=1)
    number = fields.Char(string="Ticket number", default="/", readonly=True)
    helpdesk_team_id = fields.Many2one("aagam.helpdesk.ticket.team",string="Helpdesk Team")
    helpdesk_stage_id = fields.Many2one("aagam.helpdesk.stage",string="Stage",group_expand="group_helpdesk_stage_ids",default=_default_helpdesk_stage_id,
        track_visibility="onchange",ondelete="restrict",index=True,copy=False,)
    helpdesk_ticket_type_id = fields.Many2one('aagam.helpdesk.ticket.type', string="Ticket Type")
    res_user_id = fields.Many2one("res.users", string="Assigned user", tracking=True, index=True)
    not_start = fields.Boolean(related="helpdesk_stage_id.not_start", store=True)
    priority = fields.Selection([("0", ("Low")),("1", ("Medium")),("2", ("High")),("3", ("Very High"))],string="Priority",default="1")
    partner_id = fields.Many2one("res.partner", string="Contact")
    partner_name = fields.Char(string="Partner",readonly=1,force_save=1)
    partner_email = fields.Char(string="Email",readonly=1,force_save=1)
    last_stage_update = fields.Datetime(string="Last Stage Update", default=fields.Datetime.now)
    active = fields.Boolean(default=True)
    user_ids = fields.Many2many("res.users", related="helpdesk_team_id.member_ids", string="Users")
    company_id = fields.Many2one("res.company",string="Company",required=True,default=lambda self: self.env.company)
    description = fields.Html(required=True, sanitize_style=True)
    assigned_date = fields.Datetime(string="Assigned Date")
    create_date = fields.Datetime(string="Create Date")
    closed_date = fields.Datetime(string="Closed Date")
    closed = fields.Boolean(related="helpdesk_stage_id.closed")
    team_sla = fields.Boolean(string="Team SLA", compute="_compute_team_sla")
    sla_ids = fields.Many2many('aagam.helpdesk.ticket.sla.policy', 'helpdesk_sla_policy', 'ticket_id', 'sla_policy_id', string="SLAs", copy=False)
    sla_expired = fields.Boolean(string="SLA expired")
    sla_deadline = fields.Datetime(string="SLA deadline")
    sla_reached_late = fields.Boolean("Has SLA reached late", compute='_compute_sla_reached_late', compute_sudo=True,
                                      store=True)
    sla_status_ids = fields.One2many('helpdesk.sla.status', 'ticket_id', string="SLA Status")
    channel_id = fields.Many2one("aagam.helpdesk.channel",string="Channel")
    date = fields.Date('Created on', default=fields.Date.today())
    closed_hours = fields.Integer("Time to close (hours)", compute='_compute_close_hours', store=True)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string="Number of Attachments")
    is_task = fields.Boolean()
    is_task_button = fields.Boolean()
    timesheet_ids = fields.One2many('account.analytic.line','ticket_id','Timesheet')
    ticket_invoice_ids = fields.One2many('helpdesk.ticket.invoice', 'ticket_id', 'Ticket Invoice')
    priority_new = fields.Selection(TICKET_PRIORITY, string='Customer Rating', default='0')
    comment = fields.Text(string='Comment')
    create_new_bool = fields.Boolean(string='Create New Ticket ?')
    assign_date = fields.Datetime("First assignation date")
    assign_hours = fields.Integer("Time to first assignation (hours)", compute='_compute_assign_hours', store=True)
    date_last_stage_update = fields.Datetime("Last Stage Update", copy=False, readonly=True)
    project_project_id = fields.Many2one('project.project', string="Project")
    tag_ids = fields.Many2many('aagam.helpdesk.ticket.tag', string='Tags')
    closed_by_partner = fields.Boolean('Closed by Partner')
    attachment_ids = fields.Many2many('ir.attachment', 'attachment_id', 'helpdesk_res_id',
                                      string="Attachment",
                                      help='You can attach the copy of your document', copy=False)
    is_ticket_closed = fields.Boolean(string='Is Ticket Closed')
    close_ticket_date = fields.Datetime(string='Close Ticket')
    is_customer_replied = fields.Boolean(string='Is Customer Replied')
    sla_fail = fields.Boolean("Failed SLA Policy", compute='_compute_sla_fail', search='_search_sla_fail')
    sla_success = fields.Boolean("Success SLA Policy", compute='_compute_sla_success', search='_search_sla_success')
    color = fields.Integer('Color Index', default=1)
    kanban_state = fields.Selection([
        ('normal', 'Grey'),
        ('done', 'Green'),
        ('blocked', 'Red')], string='Kanban State',
        default='normal', required=True)
    kanban_state_label = fields.Char(compute='_compute_kanban_state_label', string='Column Status', tracking=True)

    legend_blocked = fields.Char(
        'Red Kanban Label', default=lambda s: _('Blocked'), translate=True, required=True)
    legend_done = fields.Char(
        'Green Kanban Label', default=lambda s: _('Ready'), translate=True, required=True)
    legend_normal = fields.Char(
        'Grey Kanban Label', default=lambda s: _('In Progress'), translate=True, required=True)
    is_invoice = fields.Boolean()
    # ticket_invoice_ids = fields.One2many('helpdesk.ticket.invoice', 'ticket_id', 'Ticket Invoice')
    is_invoice_button = fields.Boolean()
    invoice_number = fields.Char(string="Invoice Number")
    account_detail = fields.Many2one('account.move', string='Account', track_visibility='onchange')
    account_total_data = fields.Float(string='Invoice Amount')

    def create_invoice(self):
        self.is_invoice = True
        if self.ticket_invoice_ids:
            move = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.partner_id.id,
                'date': datetime.datetime.now(),
                'invoice_date': datetime.datetime.now(),

            })

            for product in self.ticket_invoice_ids:
                move.write({
                    'invoice_line_ids': [
                        (0, 0, {
                            'product_id': product.product_id,
                            'product_uom_id': False,
                            'quantity': product.quantity,
                            'price_unit': product.product_id.list_price,
                            'price_subtotal': product.price_unit,
                            'tax_ids': product.product_id.taxes_id,
                        }),
                    ]
                })
            move.action_post()
            self.write({
                'is_invoice': True,
                'invoice_number': move.id,
            })

    def invoice_action(self):
        self.is_invoice_button = True
        search_invoice = self.env['account.move'].search([('partner_id', '=', self.partner_id.id),
                                                          ('id', '=', self.invoice_number)])

        self.account_detail = search_invoice.id
        self.account_total_data = search_invoice.amount_residual

        return {
            'name': _('Create Invoice'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': search_invoice.id,
            'type': 'ir.actions.act_window',
        }

    @api.depends('helpdesk_stage_id', 'kanban_state')
    def _compute_kanban_state_label(self):
        for task in self:
            if task.kanban_state == 'normal':
                task.kanban_state_label = task.legend_normal
            elif task.kanban_state == 'blocked':
                task.kanban_state_label = task.legend_blocked
            else:
                task.kanban_state_label = task.legend_done

    @api.depends('sla_deadline', 'sla_reached_late')
    def _compute_sla_fail(self):
        now = fields.Datetime.now()
        for ticket in self:
            if ticket.sla_deadline:
                ticket.sla_fail = (ticket.sla_deadline < now) or ticket.sla_reached_late
            else:
                ticket.sla_fail = ticket.sla_reached_late

    @api.depends('sla_deadline', 'sla_reached_late')
    def _compute_sla_success(self):
        now = fields.Datetime.now()
        for ticket in self:
            ticket.sla_success = (ticket.sla_deadline and ticket.sla_deadline > now)

    def _sla_assigning_rxeach(self):
        """ Flag the SLA status of current ticket for the given stage_id as reached, and even the unreached SLA applied
            on stage having a sequence lower than the given one.
        """
        self.env['helpdesk.sla.status'].search([
            ('ticket_id', 'in', self.ids),
            ('reached_datetime', '=', False),
            ('deadline', '!=', False),
            ('target_type', '=', 'assigning')
        ]).write({'reached_datetime': fields.Datetime.now()})


    def close_action(self):
        self.is_ticket_closed = True
        self.closed_by_partner = True
        self.close_ticket_date = datetime.date.today()

    def _sla_apply(self, keep_reached=False):
        sla_per_tickets = self._sla_find()

        sla_status_value_list = []
        for tickets, slas in sla_per_tickets.items():
            sla_status_value_list += tickets._sla_generate_status_values(slas, keep_reached=keep_reached)

        sla_status_to_remove = self.mapped('sla_status_ids')
        if keep_reached:
            sla_status_to_remove = sla_status_to_remove.filtered(lambda status: not status.reached_datetime)

        if sla_status_value_list:
            sla_status_to_remove.with_context(norecompute=True)

        sla_status_to_remove.unlink()
        return self.env['helpdesk.sla.status'].create(sla_status_value_list)

    def _sla_find(self):
        tickets_map = {}
        sla_domain_map = {}

        def _generate_key(ticket):
            fields_list = self._sla_reset_trigger()
            key = list()
            for field_name in fields_list:
                if ticket._fields[field_name].type == 'many2one':
                    key.append(ticket[field_name].id)
                else:
                    key.append(ticket[field_name])
            return tuple(key)

        for ticket in self:
            if ticket.helpdesk_team_id.use_sla:  # limit to the team using SLA
                key = _generate_key(ticket)
                # group the ticket per key
                tickets_map.setdefault(key, self.env['aagam.helpdesk.ticket'])
                tickets_map[key] |= ticket
                # group the SLA to apply, by key
                if key not in sla_domain_map:
                    sla_domain_map[key] = [('team_id', '=', ticket.helpdesk_team_id.id), ('priority', '<=', ticket.priority),
                                           ('helpdesk_stage_id.sequence', '>=', ticket.helpdesk_stage_id.sequence), '|',
                                           ('ticket_type_id', '=', ticket.helpdesk_ticket_type_id.id), ('ticket_type_id', '=', False)]

        result = {}
        for key, tickets in tickets_map.items():  # only one search per ticket group
            domain = sla_domain_map[key]
            slas = self.env['aagam.helpdesk.ticket.sla.policy'].search(domain)
            result[tickets] = slas.filtered(lambda s: s.tag_ids <= tickets.tag_ids)  # SLA to apply on ticket subset

        return result
    def _sla_assigning_reach(self):
        """ Flag the SLA status of current ticket for the given stage_id as reached, and even the unreached SLA applied
            on stage having a sequence lower than the given one.
        """
        self.env['helpdesk.sla.status'].search([
            ('ticket_id', 'in', self.ids),
            ('reached_datetime', '=', False),
            ('deadline', '!=', False),
            ('target_type', '=', 'assigning')
        ]).write({'reached_datetime': fields.Datetime.now()})


    def _sla_generate_status_values(self, slas, keep_reached=False):
        status_to_keep = dict.fromkeys(self.ids, list())

        if keep_reached:
            for ticket in self:
                for status in ticket.sla_status_ids:
                    if status.reached_datetime:
                        status_to_keep[ticket.id].append(status.sla_id.id)

        result = []
        for ticket in self:
            for sla in slas:
                if not (keep_reached and sla.id in status_to_keep[ticket.id]):
                    result.append({
                        'ticket_id': ticket.id,
                        'sla_id': sla.id,
                        'reached_datetime': fields.Datetime.now() if ticket.helpdesk_stage_id == sla.helpdesk_stage_id else False
                    })

        return result

    @api.depends('assign_date')
    def _compute_assign_hours(self):
        for ticket in self:
            create_date = fields.Datetime.from_string(ticket.create_date)
            if create_date and ticket.assign_date:
                duration_data = ticket.helpdesk_team_id.resource_calendar_id.get_work_duration_data(create_date,
                                                                                           fields.Datetime.from_string(
                                                                                               ticket.assign_date),
                                                                                           compute_leaves=True)
                ticket.assign_hours = duration_data['hours']
            else:
                ticket.assign_hours = False

    @api.onchange('partner_id')
    def _onchange_partner(self):
        for ticket in self:
            if ticket.partner_id:
                ticket.partner_name = ticket.partner_id.name
                ticket.partner_email = ticket.partner_id.email

    def create_task(self):
        self.is_task= True
        task_id = self.env['project.task'].create({
                'name': self.name,
                'project_id': self.project_project_id.id,
                'partner_id' : self.partner_id.id,
                'description': self.description,
                })

    def task_action(self):
        self.is_task_button = True
        search_record = self.env['project.task'].search([('name','=',self.name),('description','=',self.description),('project_id','=',self.project_project_id.id)])
        if search_record:
            return {
                'name': _('Create Task'),
                'view_mode': 'form',
                'res_model': 'project.task',
                'res_id': search_record.id,
                'type': 'ir.actions.act_window',
                }

    def action_get_attachment_tree_view(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        return action


    def _compute_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'aagam.helpdesk.ticket'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])
        attach_data = { res['res_id']: res['res_id_count'] for res in read_group_res }
        for record in self:
            record.attachment_number = attach_data.get(record.id, 0)

    @api.depends('sla_status_ids.deadline', 'sla_status_ids.reached_datetime')
    def _compute_sla_reached_late(self):
        mapping = {}
        if self.ids:
            self.env.cr.execute("""
                    SELECT ticket_id, COUNT(id) AS reached_late_count
                    FROM helpdesk_sla_status
                    WHERE ticket_id IN %s AND deadline < reached_datetime
                    GROUP BY ticket_id
                """, (tuple(self.ids),))
            mapping = dict(self.env.cr.fetchall())

        for ticket in self:
            ticket.sla_reached_late = mapping.get(ticket.id, 0) > 0

    @api.onchange('helpdesk_team_id', 'helpdesk_ticket_type_id')
    def _default_sla_policy(self):
        for ticket in self:
            lst = []
            sla_ids = self.env['aagam.helpdesk.ticket.sla.policy'].search(
                [('team_id', '=', ticket.helpdesk_team_id.id), ('ticket_type_id', '=', ticket.helpdesk_ticket_type_id.id)])
            if sla_ids:
                for sla in sla_ids:
                    lst.append(sla.id)
            ticket.write({'sla_ids': [(6, 0, lst)]})
            for policy in ticket.sla_ids:
                if policy.days or policy.hours or policy.time_minutes:
                    deadline = ticket.date + timedelta(days=policy.days, hours=policy.hours,
                                                       minutes=policy.time_minutes)
                    ticket.write({'sla_deadline': deadline})

    @api.depends('create_date', 'closed_date')
    def _compute_close_hours(self):
        for ticket in self:
            create_date = fields.Datetime.from_string(ticket.create_date)
            if create_date and ticket.closed_date:
                """SECCIÓN DE CÓDIGO COMENTADA POR GENERAR ERROR SINGLETON, REVISAR - TO/DEBUG 20/15/2023"""
                # duration_data = ticket.helpdesk_team_id.resource_calendar_id.get_work_duration_data(create_date,
                #                                                                            fields.Datetime.from_string(
                #                                                                                ticket.closed_date),
                #                                                                            compute_leaves=True)
                # print(duration_data,'408')
                # ticket.closed_hours = duration_data['hours']
            else:
                ticket.closed_hours = False

    def _compute_team_sla(self):
        for rec in self:
            rec.team_sla = rec.helpdesk_team_id.use_sla

    def assign_to_me(self):
        self.write({"res_user_id": self.env.user.id})

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec.number + " - " + rec.name))
        return res

    @api.model
    def _sla_reset_trigger(self):
        return ['helpdesk_team_id', 'priority', 'helpdesk_ticket_type_id','tag_ids']

    @api.model_create_multi
    def create(self, list_value):
        now = fields.Datetime.now()
        teams = self.env['aagam.helpdesk.ticket.team'].browse(
            [vals['helpdesk_team_id'] for vals in list_value if vals.get('helpdesk_team_id')])
        team_default_map = dict.fromkeys(teams.ids, dict())
        for team in teams:
            team_default_map[team.id] = {
                'stage_id': team._determine_stage()[team.id].id,
                'user_id': team._determine_user_to_assign()[team.id].id
            }

        for vals in list_value:
            vals['number'] = self.env['ir.sequence'].next_by_code('helpdesk.ticket.sequence')
        for vals in list_value:
            if 'partner_name' in vals and 'partner_email' in vals and 'partner_id' not in vals:
                try:
                    vals['partner_id'] = self.env['res.partner'].find_or_create(
                        tools.formataddr((vals['partner_name'], vals['partner_email']))
                    ).id
                except UnicodeEncodeError:
                    # 'formataddr' doesn't support non-ascii characters in email. Therefore, we fall
                    # back on a simple partner creation.
                    vals['partner_id'] = self.env['res.partner'].create({
                        'name': vals['partner_name'],
                        'email': vals['partner_email'],
                    }).id

        # determine partner email for ticket with partner but no email given
        partners = self.env['res.partner'].browse([vals['partner_id'] for vals in list_value if
                                                   'partner_id' in vals and vals.get(
                                                       'partner_id') and 'partner_email' not in vals])
        partner_email_map = {partner.id: partner.email for partner in partners}
        partner_name_map = {partner.id: partner.name for partner in partners}

        for vals in list_value:
            if vals.get('helpdesk_team_id'):
                team_default = team_default_map[vals['helpdesk_team_id']]
                if 'helpdesk_stage_id' not in vals:
                    vals['helpdesk_stage_id'] = team_default['helpdesk_stage_id']
                if 'res_user_id' not in vals:
                    vals['res_user_id'] = team_default['res_user_id']
                if vals.get(
                        'res_user_id'):  # if a user is finally assigned, force ticket assign_date and reset assign_hours
                    vals['assign_date'] = fields.Datetime.now()
                    vals['assign_hours'] = 0

            # set partner email if in map of not given
            if vals.get('partner_id') in partner_email_map:
                vals['partner_email'] = partner_email_map.get(vals['partner_id'])
            # set partner name if in map of not given
            if vals.get('partner_id') in partner_name_map:
                vals['partner_name'] = partner_name_map.get(vals['partner_id'])

            if vals.get('stage_id'):
                vals['date_last_stage_update'] = now

        # new_list_value = []
        # for list_val in list_value:
        #     new_list_value.append({
        #         'helpdesk_ticket_type_id': list_val['helpdesk_ticket_type_id'],
        #         'name': list_val['name'],
        #         'partner_name': list_val['partner_name'],
        #         'partner_email': list_val['partner_email'],
        #         'priority': list_val['priority'],
        #         'description': list_val['description'],
        #         'number': list_val['number'],
        #         'partner_id': partner_name_id
        #     })
        tickets = super(aagamHelpdeskTicket, self).create(list_value)
        template = self.env.ref('website_support_ticket_odoo_aagam.aagam_helpdesk_ticket_new_create')
        mail = template.send_mail(tickets.id, force_send=True)

        for ticket in tickets:
            if ticket.partner_id:
                ticket.message_subscribe(partner_ids=ticket.partner_id.ids)

        tickets.sudo()._sla_apply()

        return tickets

    def _sla_reach(self, stage_id):
        """ Flag the SLA status of current ticket for the given stage_id as reached, and even the unreached SLA applied
            on stage having a sequence lower than the given one.
        """
        stage = self.env['aagam.helpdesk.stage'].browse(stage_id)
        stages = self.env['aagam.helpdesk.stage'].search([('sequence', '<=', stage.sequence), (
        'team_ids', 'in', self.mapped('helpdesk_team_id').ids)])  # take previous stages
        self.env['helpdesk.sla.status'].search([
            ('ticket_id', 'in', self.ids),
            ('sla_stage_id', 'in', stages.ids),
            ('reached_datetime', '=', False),
            ('target_type', '=', 'stage')
        ]).write({'reached_datetime': fields.Datetime.now()})

        # For all SLA of type assigning, we compute deadline if they are not succeded (is succeded = has a reach_datetime)
        # and if they are linked to a specific stage.
        self.env['helpdesk.sla.status'].search([
            ('ticket_id', 'in', self.ids),
            ('sla_stage_id', '!=', False),
            ('reached_datetime', '=', False),
            ('target_type', '=', 'assigning')
        ])._compute_deadline()

    def write(self, vals):
        assigned_tickets = closed_tickets = self.browse()
        if vals.get('res_user_id'):
            assigned_tickets = self.filtered(lambda ticket: not ticket.assign_date)

        if vals.get('helpdesk_stage_id'):
            if self.env['aagam.helpdesk.stage'].browse(vals.get('helpdesk_stage_id')).is_close:
                closed_tickets = self.filtered(lambda ticket: not ticket.closed_date)
            else:  # auto reset the 'closed_by_partner' flag
                vals['closed_by_partner'] = False

        now = fields.Datetime.now()

        # update last stage date when changing stage
        if 'helpdesk_stage_id' in vals:
            vals['date_last_stage_update'] = now

        res = super(aagamHelpdeskTicket, self - assigned_tickets - closed_tickets).write(vals)
        res &= super(aagamHelpdeskTicket, assigned_tickets - closed_tickets).write(dict(vals, **{
            'assign_date': now,
        }))
        res &= super(aagamHelpdeskTicket, closed_tickets - assigned_tickets).write(dict(vals, **{
            'closed_date': now,
        }))
        res &= super(aagamHelpdeskTicket, assigned_tickets & closed_tickets).write(dict(vals, **{
            'assign_date': now,
            'closed_date': now,
        }))

        if vals.get('partner_id'):
            self.message_subscribe([vals['partner_id']])

        # SLA business
        sla_triggers = self._sla_reset_trigger()
        if any(field_name in sla_triggers for field_name in vals.keys()):
            self.sudo()._sla_apply(keep_reached=True)
        if 'helpdesk_stage_id' in vals:
            self.sudo()._sla_reach(vals['helpdesk_stage_id'])

        if 'helpdesk_stage_id' in vals or 'res_user_id' in vals:
            self.filtered(lambda ticket: ticket.res_user_id).sudo()._sla_assigning_reach()

        return res

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_ticket_number(default)
        res = super().copy(default)
        return res

    def _prepare_ticket_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_context(force_company=values["company_id"])
        return seq.next_by_code("helpdesk.ticket.sequence") or "/"


    @api.model
    def get_helpdesk_ticket_month_wise(self):
        cr = self._cr

        query = """SELECT date FROM aagam_helpdesk_ticket"""
        cr.execute(query)
        partner_data = cr.dictfetchall()
        data_dict = {}
        lst_val = []
        dict = {}

        for data in partner_data:
            if data['date']:
                mydate = data['date'].month
                for month_idx in range(0, 13):
                    if mydate == month_idx:
                        value = cal.month_name[month_idx]
                        lst_val.append(value)
                        lst_val = list(set(lst_val))
                        for record in lst_val:
                            count = 0
                            for rec in lst_val:
                                if rec == record:
                                    count = count + 1
                                dict.update({record: count})
                        keys, values = zip(*dict.items())
                        data_dict.update({"data": dict})

        return data_dict

    @api.model
    def get_helpdesk_ticket_week_wise(self):
        cr = self._cr
        query = """SELECT date FROM aagam_helpdesk_ticket"""
        cr.execute(query)
        partner_data = cr.dictfetchall()
        data_dic = {}
        lst_val = []
        dict = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"]
        for data in partner_data:
            if data['date']:
                mydate = data['date'].weekday()
                if mydate >= 0:
                    value = days[mydate]
                    lst_val.append(value)

                    lst_data_val = list(set(lst_val))

                    for record in lst_data_val:
                        count = 0
                        for rec in lst_val:
                            if rec == record:
                                count = count + 1
                            dict.update({record: count})
                        keys, values = zip(*dict.items())
                        data_dic.update({"data": dict})
        return data_dic

    @api.model
    def get_helpdesk_ticket_all(self):
        today = date.today()
        lst_date = []
        lst_last_month = []
        last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
        start_day_of_prev_month = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month.day)

        sdate = start_day_of_prev_month  # start date
        edate = last_day_of_prev_month  # end date

        delta = edate - sdate  # as timedelta
        for i in range(delta.days + 1):
            day = sdate + timedelta(days=i)
            lst_last_month.append(day)

        last_month_ticket_id = self.env['aagam.helpdesk.ticket'].sudo().search_count([('date', 'in', lst_last_month)])
        for i in range(7, 14):
            last_week_date = today - timedelta(days=i)
            lst_date.append(last_week_date)
        last_week_ticket = self.env['aagam.helpdesk.ticket'].sudo().search_count([('date', 'in', lst_date)])

        total_ticket = self.env['aagam.helpdesk.ticket'].sudo().search_count([])
        today_ticket = self.env['aagam.helpdesk.ticket'].sudo().search_count([('date', '=', fields.Date.today())])

        return {
            'total_ticket': total_ticket,
            'today_ticket': today_ticket,
            'last_week_ticket': last_week_ticket,
            'last_month_ticket': last_month_ticket_id,

        }
    @api.onchange('helpdesk_ticket_type_id','helpdesk_team_id')
    def _onchange_team(self):
        res = {}
        lst = []

        helpdesk_team_id = self.env['aagam.helpdesk.ticket.team'].search([('name', '=', self.helpdesk_team_id.name)])
        if helpdesk_team_id.member_ids:
            for team_member in helpdesk_team_id.member_ids:
                lst.append(team_member.id)
            res['domain'] = {'res_user_id': [('id', 'in', lst)]}
            return res
