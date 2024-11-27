# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast
from odoo import api, fields, models
import datetime
from dateutil import relativedelta
from ast import literal_eval
from odoo.osv import expression
from datetime import date
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import  ValidationError


class aagamHelpdeskTeam(models.Model):
    _name = "aagam.helpdesk.ticket.team"
    _description = "Helpdesk Team"
    _inherit = ["mail.thread", "mail.alias.mixin"]

    def _default_domain_member_ids(self):
        return [('groups_id', 'in', self.env.ref('website_support_ticket_odoo_aagam.group_helpdesk_ticket_users').id)]

    def _default_stage_ids(self):
        pass


    name = fields.Char(string="Name",required=1)
    member_ids = fields.Many2many("res.users",string="Team Members", domain=[('id','!=',2)])
    use_alias = fields.Boolean('Email alias', default=True)
    email_alias_id = fields.Many2one("mail.alias",string="Email Alias",ondelete="restrict")
    # alias_user_id = fields.Many2many('res.users', 'Owner')
    team_leader_id = fields.Many2one("res.users",string="Team Leader")
    allow_timesheet = fields.Boolean(string="Allow Timesheet")
    use_sla = fields.Boolean(string="Use SLA")
    company_id = fields.Many2one(comodel_name="res.company",string="Company",default=lambda self: self.env.company)
    calendar_id = fields.Many2one("resource.calendar",string="Working Hours",domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    project_id = fields.Many2one("project.project",string="Default Project")
    helpdesk_type_ids = fields.Many2many("aagam.helpdesk.ticket.type",string="Ticket Type")
    helpdesk_ticket_ids = fields.One2many("aagam.helpdesk.ticket","helpdesk_team_id",string="Tickets")
    assigning_method = fields.Selection([
        ('manual', 'Manually'),
        ('randomly', 'Random'),
        ('balanced', 'Balanced')], string='Ticket Assigment Method',
        default='manual', required=True,compute='_compute_assign_method', store=True, readonly=False)
    visibility_member_ids = fields.Many2many('res.users', 'helpdesk_visibility_team', string='Team Visibility',
                                             domain=lambda self: self._default_domain_member_ids(), required=1)
    helpdesk_category_ids = fields.Many2many("aagam.helpdesk.ticket.category", string="Category")
    active = fields.Boolean(default=True)
    # use_sla = fields.Boolean(string="Use SLA")
    resource_calendar_id = fields.Many2one("resource.calendar","Working Hours",default=lambda self: self.env.company.resource_calendar_id,domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    color = fields.Integer(string="Color Index", default=0)
    upcoming_sla_fail_tickets = fields.Integer(string='Upcoming SLA Fail Tickets', compute='_compute_fail_sla_tickets')
    use_rating = fields.Boolean('Ratings on tickets')
    portal_rating_url = fields.Char('URL to Submit an Issue', readonly=True, compute='_compute_portal_rating_url')
    portal_show_rating = fields.Boolean(
        'Display Rating on Customer Portal', compute='_compute_portal_show_rating', store=True,
        readonly=False)
    allow_portal_ticket_closing = fields.Boolean('Ticket closing', help="Allow customers to close their tickets")
    stage_ids = fields.Many2many(
        'aagam.helpdesk.stage', relation='team_stage_rel', string='Stages',
        default=_default_stage_ids,
        help="Stages the team will use. This team's tickets will only be able to be in these stages.")

    def _get_closing_stage(self):
        """
            Return the first closing kanban stage or the last stage of the pipe if none
        """
        closed_stage = self.stage_ids.filtered(lambda stage: stage.is_close)
        if not closed_stage:
            closed_stage = self.stage_ids[-1]
        return closed_stage


    @api.onchange('member_ids')
    def _onchange_member_ids(self):
        team_id = self.env['aagam.helpdesk.ticket.team'].search([])
        user_ids = self.env['res.users'].search([('id','!=',2)])
        lst = []
        for team in team_id:
            for user in user_ids:
                if user.has_group('website_support_ticket_odoo_aagam.group_helpdesk_ticket_users') or user.has_group(
                        'website_support_ticket_odoo_aagam.group_helpdesk_ticket_manager'):
                    user_manager = self.env['res.users'].search([('id', '=', user.id)])
                    for manager in user_manager:
                        for member in team.member_ids.ids:
                            if manager.id == member:
                                lst.append(team.id)
                        manager.write({'helpdesk_team_ids': [(6, 0, lst)]})

    @api.depends('member_ids', 'visibility_member_ids')
    def _compute_assign_method(self):
        with_manual = self.filtered(lambda t: not t.member_ids and not t.visibility_member_ids)
        with_manual.update({'assigning_method': 'manual'})

    @api.constrains('assigning_method', 'member_ids', 'visibility_member_ids')
    def _check_member_assignation(self):
        if not self.member_ids and not self.visibility_member_ids and self.assigning_method != 'manual':
            raise ValidationError(_("You must have team members assigned to change the assignment method."))

    def _determine_stage(self):
        """ Get a dict with the stage (per team) that should be set as first to a created ticket
            :returns a mapping of team identifier with the stage (maybe an empty record).
            :rtype : dict (key=team_id, value=record of helpdesk.stage)
        """
        result = dict.fromkeys(self.ids, self.env['aagam.helpdesk.stage'])
        for team in self:
            result[team.id] = self.env['aagam.helpdesk.stage'].search([('team_ids', 'in', team.id)], order='sequence',
                                                                limit=1)
        return result

    def _determine_user_to_assign(self):
        """ Get a dict with the user (per team) that should be assign to the nearly created ticket according to the team policy
            :returns a mapping of team identifier with the "to assign" user (maybe an empty record).
            :rtype : dict (key=team_id, value=record of res.users)
        """
        result = dict.fromkeys(self.ids, self.env['res.users'])
        for team in self:
            member_ids = sorted(team.member_ids.ids) if team.member_ids else sorted(team.visibility_member_ids.ids)
            if member_ids:
                if team.assigning_method == 'randomly':  # randomly means new tickets get uniformly distributed
                    last_assigned_user = self.env['aagam.helpdesk.ticket'].search([('helpdesk_team_id', '=', team.id)],
                                                                            order='create_date desc, id desc',
                                                                            limit=1).res_user_id
                    index = 0
                    if last_assigned_user and last_assigned_user.id in member_ids:
                        previous_index = member_ids.index(last_assigned_user.id)
                        index = (previous_index + 1) % len(member_ids)
                    result[team.id] = self.env['res.users'].browse(member_ids[index])
                elif team.assigning_method == 'balanced':  # find the member with the least open ticket
                    ticket_count_data = self.env['aagam.helpdesk.ticket'].read_group(
                        [('helpdesk_stage_id.is_close', '=', False), ('res_user_id', 'in', member_ids), ('helpdesk_team_id', '=', team.id)],
                        ['res_user_id'], ['res_user_id'])
                    open_ticket_per_user_map = dict.fromkeys(member_ids, 0)  # dict: user_id -> open ticket count
                    open_ticket_per_user_map.update(
                        (item['res_user_id'][0], item['user_id_count']) for item in ticket_count_data)
                    result[team.id] = self.env['res.users'].browse(
                        min(open_ticket_per_user_map, key=open_ticket_per_user_map.get))
        return result

    @api.depends('use_rating')
    def _compute_portal_show_rating(self):
        without_rating = self.filtered(lambda t: not t.use_rating)
        without_rating.update({'portal_show_rating': False})

    @api.depends('name', 'portal_show_rating')
    def _compute_portal_rating_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for team in self:
            if team.name and team.portal_show_rating and team.id:
                team.portal_rating_url = '%s/helpdesk/rating/%s' % (base_url, slug(team))
            else:
                team.portal_rating_url = False

    def _alias_get_creation_values(self):
        values = super(aagamHelpdeskTeam, self)._alias_get_creation_values()
        values['alias_model_id'] = self.env['ir.model']._get('aagam.helpdesk.ticket').id
        if self.id:
            values['alias_defaults'] = defaults = ast.literal_eval(self.alias_defaults or "{}")
            defaults['team_id'] = self.id
        return values

    @api.onchange('use_alias', 'name')
    def _onchange_use_alias(self):
        if not self.use_alias:
            self.alias_name = False

    def _compute_fail_sla_tickets(self):
        ticket_id = self.env['aagam.helpdesk.ticket'].read_group([
            ('helpdesk_team_id', 'in', self.ids),
            ('sla_deadline', '!=', False),
            ('sla_deadline', '<=', fields.Datetime.to_string((datetime.date.today() + relativedelta.relativedelta(days=1)))),
        ], ['helpdesk_team_id'], ['helpdesk_team_id'])
        data = dict((data['helpdesk_team_id'][0], data['helpdesk_team_id_count']) for data in ticket_id)
        for team in self:
            team.upcoming_sla_fail_tickets = data.get(team.id, 0)

    def stage_set(self):
        result = dict.fromkeys(self.ids, self.env['aagam.helpdesk.stage'])
        for team in self:
            result[team.id] = self.env['aagam.helpdesk.stage'].search([('team_ids', 'in', team.id)],
                                                                            order='sequence', limit=1)
        return result
    def assign_user_to_team(self):
        result = dict.fromkeys(self.ids, self.env['res.users'])
        for team in self:
            member_ids = sorted(team.member_ids.ids)
            if member_ids:
                if team.assigning_method == 'randomly':  # randomly means new tickets get uniformly distributed
                    last_assigned_user = self.env['aagam.helpdesk.ticket'].search([('team_id', '=', team.id)], order='create_date desc, id desc', limit=1).res_user_id
                    index = 0
                    if last_assigned_user and last_assigned_user.id in member_ids:
                        previous_index = member_ids.index(last_assigned_user.id)
                        index = (previous_index + 1) % len(member_ids)
                    result[team.id] = self.env['res.users'].browse(member_ids[index])
                elif team.assigning_method == 'balanced':  # find the member with the least open ticket
                    ticket_count_data = self.env['aagam.helpdesk.ticket'].read_group([('helpdesk_stage_id.is_close', '=', False), ('res_user_id', 'in', member_ids)], ['res_user_id'], ['res_user_id'])
                    open_ticket_per_user_map = dict.fromkeys(member_ids, 0)  # dict: user_id -> open ticket count
                    open_ticket_per_user_map.update((item['res_user_id'][0], item['user_id_count']) for item in ticket_count_data)
                    result[team.id] = self.env['res.users'].browse(min(open_ticket_per_user_map, key=open_ticket_per_user_map.get))
        return result

    @api.model
    def retrieve_dashboard(self):
        domain = [('res_user_id', '=', self.env.uid)]
        group_fields = ['priority', 'create_date', 'helpdesk_stage_id', 'closed_hours']
        list_fields = ['priority', 'create_date', 'helpdesk_stage_id', 'closed_hours']
        user_uses_sla = self.user_has_groups('helpdesk.group_use_sla') and \
                        bool(self.env['aagam.helpdesk.ticket.team'].search(
                            [('use_sla', '=', True), '|', ('member_ids', 'in', self._uid), ('member_ids', '=', False)]))
        user_id = self.env['res.users'].search_read([])

        team_id = self.env['aagam.helpdesk.ticket.team'].search_read()

        ticket_new = self.env['aagam.helpdesk.ticket'].search_read(domain=[('helpdesk_stage_id', '=', 'New')])
        ticket_in_progress = self.env['aagam.helpdesk.ticket'].search_read(domain=[('helpdesk_stage_id', '=', 'In Progress')])
        ticket_solved = self.env['aagam.helpdesk.ticket'].search_read(domain=[('helpdesk_stage_id', '=', 'Solved')])
        ticket_cancelled = self.env['aagam.helpdesk.ticket'].search_read(domain=[('helpdesk_stage_id', '=', 'Cancelled')])
        ticket_others = self.env['aagam.helpdesk.ticket'].search_read(
            domain=[('helpdesk_stage_id', '!=', 'In Progress'), ('helpdesk_stage_id', '!=', 'New'), ('helpdesk_stage_id', '!=', 'Solved'),
                    ('helpdesk_stage_id', '!=', 'Cancelled')])
        user_id_serach = user_id
        assingUser_id = user_id

        team_data = self.env['aagam.helpdesk.ticket'].search([('res_user_id', '=', 8), ('helpdesk_team_id', '=', 2)])
        if self.env['ir.config_parameter'].sudo().get_param('stage_ids'):
            stage_ids = literal_eval(self.env['ir.config_parameter'].sudo().get_param('stage_ids'))
            stage_ids = self.env['aagam.helpdesk.stage'].browse(stage_ids)
        else:
            stage_ids = []
        if self.env['ir.config_parameter'].sudo().get_param('filter_ids'):
            filter_ids = literal_eval(self.env['ir.config_parameter'].sudo().get_param('filter_ids'))
            filter_ids = self.env['aagam.helpdesk.stage'].browse(filter_ids)
        else:
            filter_ids = []
        stage_dict = {}
        filter_dict = {}
        for i in stage_ids:
            stage_dict[i.id] = i.name
        for i in filter_ids:
            filter_dict[i.id] = i.name
        if user_uses_sla:
            group_fields.insert(1, 'sla_deadline:year')
            group_fields.insert(2, 'sla_deadline:hour')
            group_fields.insert(3, 'sla_reached_late')
            list_fields.insert(1, 'sla_deadline')
            list_fields.insert(2, 'sla_reached_late')

        HelpdeskTicket = self.env['aagam.helpdesk.ticket']
        tickets = HelpdeskTicket.search_read(expression.AND([domain, [('helpdesk_stage_id.closed', '=', False)]]),
                                             ['sla_deadline', 'closed_hours', 'sla_reached_late', 'priority'])
        all_tickets = HelpdeskTicket.search_read(expression.AND([domain, [('name', '!=', False)]]),
                                                 ['sla_deadline', 'closed_hours', 'sla_reached_late', 'priority'])
        closed_tickets = HelpdeskTicket.search_read(expression.AND([domain, [('helpdesk_stage_id.closed', '=', True)]]),
                                                    ['sla_deadline', 'closed_hours', 'sla_reached_late', 'priority'])
        result = {
            'user_id': user_id,
            'team_id': team_id,
            'assingUser_id': assingUser_id,

            'ticket_new': ticket_new,
            'ticket_new_length': len(ticket_new),

            'ticket_in_progress': ticket_in_progress,
            'ticket_in_progress_length': len(ticket_in_progress),

            'ticket_solved': ticket_solved,
            'ticket_solved_length': len(ticket_solved),

            'ticket_cancelled': ticket_cancelled,
            'ticket_cancelled_length': len(ticket_cancelled),

            'ticket_others': ticket_others,
            'ticket_others_length': len(ticket_others),

            'user_id_serach': user_id_serach,
            'stage_dict': stage_dict,
            'helpdesk_target_closed': self.env.user.helpdesk_ticket_target_closed,
            'helpdesk_target_rating': self.env.user.helpdesk_ticket_target_rating,
            'helpdesk_target_success': self.env.user.helpdesk_ticket_target_success,
            'today': {'count': 0, 'rating': 0, 'success': 0},
            'yesterday': {'count': 0, 'rating': 0, 'success': 0},
            '7days': {'count': 0, 'rating': 0, 'success': 0},
            'month': {'count': 0, 'rating': 0, 'success': 0},
            'year': {'count': 0, 'rating': 0, 'success': 0},
            'my_all': {'count': 0, 'hours': 0, 'failed': 0},
            'my_all_tickets': {'count': 0, 'hours': 0, 'failed': 0},
            'my_closed_tickets': {'count': 0, 'hours': 0, 'failed': 0},
            'my_high': {'count': 0, 'hours': 0, 'failed': 0},
            'my_low': {'count': 0, 'hours': 0, 'failed': 0},
            'my_medium': {'count': 0, 'hours': 0, 'failed': 0},
            'my_urgent': {'count': 0, 'hours': 0, 'failed': 0},
            'show_demo': not bool(HelpdeskTicket.search([], limit=1)),
            'rating_enable': False,
            'success_rate_enable': user_uses_sla,
            'cuurent_date': date.today()
        }

        def failed_sla_ticket(data):
            deadline = data.get('sla_deadline')
            sla_deadline = fields.Datetime.now() > deadline if deadline else False
            return sla_deadline or data.get('sla_reached_late')

        def ticket_to_add(ticket, key="my_all"):
            result[key]['count'] += 1
            result[key]['hours'] += ticket['closed_hours']
            if failed_sla_ticket(ticket):
                result[key]['failed'] += 1

        def all_add_to(ticket, key="my_all_tickets"):
            result[key]['count'] += 1
            result[key]['hours'] += ticket['closed_hours']
            if failed_sla_ticket(ticket):
                result[key]['failed'] += 1

        def close_to(ticket, key="my_closed_tickets"):
            result[key]['count'] += 1
            result[key]['hours'] += ticket['closed_hours']
            if failed_sla_ticket(ticket):
                result[key]['failed'] += 1

        for ticket in closed_tickets:
            close_to(ticket, 'my_closed_tickets')

        for ticket in all_tickets:
            all_add_to(ticket, 'my_all_tickets')

        for ticket in tickets:
            all_add_to(ticket, 'my_all')
            if ticket['priority'] == '2':
                all_add_to(ticket, 'my_high')
            if ticket['priority'] == '1':
                all_add_to(ticket, 'my_medium')
            if ticket['priority'] == '3':
                all_add_to(ticket, 'my_urgent')
            if ticket['priority'] == '0':
                all_add_to(ticket, 'my_low')

        dt = fields.Date.today()
        tickets = HelpdeskTicket.read_group(domain + [('helpdesk_stage_id.closed', '=', True), ('closed_date', '>=', dt)],
                                            list_fields, group_fields, lazy=False)
        for ticket in tickets:
            result['today']['count'] += ticket['__count']
            if not failed_sla_ticket(ticket):
                result['today']['success'] += ticket['__count']

        dt = fields.Datetime.to_string((datetime.date.today() - relativedelta.relativedelta(days=6)))
        tickets = HelpdeskTicket.read_group(domain + [('helpdesk_stage_id.closed', '=', True), ('closed_date', '>=', dt)],
                                            list_fields, group_fields, lazy=False)
        for ticket in tickets:
            result['7days']['count'] += ticket['__count']
            if not failed_sla_ticket(ticket):
                result['7days']['success'] += ticket['__count']

        today = datetime.date.today()
        dt = today.replace(day=1)
        tickets = HelpdeskTicket.read_group(
            domain + [('helpdesk_stage_id.closed', '=', True), ('closed_date', '>=', dt)],
            list_fields, group_fields, lazy=False)
        for ticket in tickets:
            result['month']['count'] += ticket['__count']
            if not failed_sla_ticket(ticket):
                result['month']['success'] += ticket['__count']

        today = datetime.date.today()
        dt = today.replace(month=1, day=1)
        tickets = HelpdeskTicket.read_group(
            domain + [('helpdesk_stage_id.closed', '=', True), ('closed_date', '>=', dt)],
            list_fields, group_fields, lazy=False)
        for ticket in tickets:
            result['year']['count'] += ticket['__count']
            if not failed_sla_ticket(ticket):
                result['year']['success'] += ticket['__count']

        result['today']['success'] = (result['today']['success'] * 100) / (result['today']['count'] or 1)
        result['my_all_tickets']['hours'] = round(
            result['my_all_tickets']['hours'] / (result['my_all_tickets']['count'] or 1), 2)
        result['yesterday']['success'] = (result['yesterday']['success'] * 100) / (result['yesterday']['count'] or 1)
        result['7days']['success'] = (result['7days']['success'] * 100) / (result['7days']['count'] or 1)
        result['month']['success'] = (result['month']['success'] * 100) / (result['month']['count'] or 1)
        result['year']['success'] = (result['year']['success'] * 100) / (result['year']['count'] or 1)
        result['my_closed_tickets']['hours'] = round(
            result['my_closed_tickets']['hours'] / (result['my_closed_tickets']['count'] or 1), 2)

        result['my_all']['hours'] = round(result['my_all']['hours'] / (result['my_all']['count'] or 1), 2)
        result['my_medium']['hours'] = round(result['my_medium']['hours'] / (result['my_medium']['count'] or 1), 2)
        result['my_low']['hours'] = round(result['my_low']['hours'] / (result['my_low']['count'] or 1), 2)
        result['my_urgent']['hours'] = round(result['my_urgent']['hours'] / (result['my_urgent']['count'] or 1), 2)

        if self.env['aagam.helpdesk.ticket.team'].search(
                [('use_rating', '=', True), '|', ('member_ids', 'in', self._uid), ('member_ids', '=', False)]):
            result['rating_enable'] = True
            # rating of today
            domain = [('res_user_id', '=', self.env.uid)]
            dt = fields.Date.today()
            tickets = self.env['aagam.helpdesk.ticket'].search(
                domain + [('helpdesk_stage_id.closed', '=', True), ('closed_date', '>=', dt)])
            activity = tickets.rating_get_grades()
            total_rating = self.average_avtivity(activity)
            total_activity_values = sum(activity.values())
            team_satisfaction = round((total_rating / total_activity_values if total_activity_values else 0), 2) * 10
            if team_satisfaction:
                result['today']['rating'] = team_satisfaction

            # rating of last 7 days (6 days + today)
            dt = fields.Datetime.to_string((datetime.date.today() - relativedelta.relativedelta(days=6)))
            tickets = self.env['aagam.helpdesk.ticket'].search(
                domain + [('helpdesk_stage_id.closed', '=', True), ('closed_date', '>=', dt)])
            activity = tickets.rating_get_grades()
            total_rating = self.average_avtivity(activity)
            total_activity_values = sum(activity.values())
            team_satisfaction_7days = round((total_rating / total_activity_values if total_activity_values else 0),
                                            2) * 10
            if team_satisfaction_7days:
                result['7days']['rating'] = team_satisfaction_7days
        return result
