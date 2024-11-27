# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
import base64
import io
from werkzeug.utils import redirect
from datetime import datetime, date, timedelta
import calendar
import datetime
from odoo import http
from odoo.http import request
from odoo.osv.expression import AND, OR
import dateutil.relativedelta
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.tools import groupby as groupbyelem
from operator import itemgetter


@http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
def helpdesk_ticket_view(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content', **kw):
    values = self._prepare_portal_layout_values()
    user = request.env.user
    domain = []

    searchbar_sortings = {
        'date': {'label': _('Newest'), 'order': 'create_date desc'},
        'name': {'label': _('Subject'), 'order': 'name'},
    }
    searchbar_inputs = {
        'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
        'message': {'input': 'message', 'label': _('Search in Messages')},
        'customer': {'input': 'customer', 'label': _('Search in Customer')},
        'id': {'input': 'id', 'label': _('Search ID')},
        'number': {'input': 'number', 'label': _('Search Ticket No.')},
        'all': {'input': 'all', 'label': _('Search in All')},
    }

    # default sort by value
    if not sortby:
        sortby = 'date'
    order = searchbar_sortings[sortby]['order']

    # archive groups - Default Group By 'create_date'
    archive_groups = self._get_archive_groups('aagam.helpdesk.ticket', domain)
    if date_begin and date_end:
        domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

    # search
    if search and search_in:
        search_domain = []
        if search_in in ('id', 'all'):
            search_domain = OR([search_domain, [('id', 'ilike', search)]])
        if search_in in ('content', 'all'):
            search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
        if search_in in ('customer', 'all'):
            search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
        if search_in in ('message', 'all'):
            search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
        if search_in in ('number', 'all'):
            search_domain = OR([search_domain, [('number', 'ilike', search)]])
        domain += search_domain

    # pager
    tickets_count = request.env['aagam.helpdesk.ticket'].search_count(domain)
    pager = portal_pager(
        url="/my/tickets",
        url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
        total=tickets_count,
        page=page,
        step=self._items_per_page
    )

    tickets = request.env['aagam.helpdesk.ticket'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
    request.session['my_tickets_history'] = tickets.ids[:100]

    values.update({
        'date': date_begin,
        'tickets': tickets,
        'page_name': 'ticket',
        'default_url': '/my/tickets',
        'pager': pager,
        'archive_groups': archive_groups,
        'searchbar_sortings': searchbar_sortings,
        'searchbar_inputs': searchbar_inputs,
        'sortby': sortby,
        'search_in': search_in,
        'search': search,
    })
    return request.render("website_support_ticket_odoo_aagam.view_helpdesk_ticket_portal", values)


@http.route('/search_helpdesk_tickets', type='http', auth='user', website=True)
def search_helpdesk_tickets(self, **kwargs):
    ticket_ids = request.env['aagam.helpdesk.ticket'].sudo().search([])
    return request.render('website_support_ticket_odoo_aagam.helpdesk_ticket_search', {'ticket': ticket_ids})


class CustomerPortalAa(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortalAa, self)._prepare_portal_layout_values()
        if values.get('sales_user', False):
            values['title'] = _("Salesperson")
        return values

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'ticket_count' in counters:
            values['ticket_count'] = request.env['aagam.helpdesk.ticket'].search_count([])
        return values

    def _ticket_get_page_view_values(self, ticket, access_token, **kwargs):
        values = {
            'page_name': 'ticket',
            'ticket': ticket,
        }
        return self._get_page_view_values(ticket, access_token, values, 'my_tickets_history', False, **kwargs)

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def my_helpdesk_tickets(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all', search=None, groupby='none',
                            search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
            'reference': {'label': _('Reference'), 'order': 'id'},
            'update': {'label': _('Last Stage Update'), 'order': 'date_last_stage_update desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'assigned': {'label': _('Assigned'), 'domain': [('user_id', '!=', False)]},
            'unassigned': {'label': _('Unassigned'), 'domain': [('user_id', '=', False)]},
            'open': {'label': _('Open'), 'domain': [('close_date', '=', False)]},
            'closed': {'label': _('Closed'), 'domain': [('close_date', '!=', False)]},
            'last_message_sup': {'label': _('Last message is from support')},
            'last_message_cust': {'label': _('Last message is from customer')},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'id': {'input': 'id', 'label': _('Search in Reference')},
            'status': {'input': 'status', 'label': _('Search in Stage')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'stage': {'input': 'stage_id', 'label': _('Stage')},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if filterby in ['last_message_sup', 'last_message_cust']:
            discussion_subtype_id = request.env.ref('mail.mt_comment').id
            messages = request.env['mail.message'].search_read([('model', '=', 'aagam.helpdesk.ticket'), ('subtype_id', '=', discussion_subtype_id)],
                                                               fields=['res_id', 'author_id'], order='date desc')
            last_author_dict = {}
            for message in messages:
                if message['res_id'] not in last_author_dict:
                    last_author_dict[message['res_id']] = message['author_id'][0]

            ticket_author_list = request.env['aagam.helpdesk.ticket'].search_read(fields=['id', 'partner_id'])
            ticket_author_dict = dict(
                [(ticket_author['id'], ticket_author['partner_id'][0] if ticket_author['partner_id'] else False) for ticket_author in
                 ticket_author_list])

            last_message_cust = []
            last_message_sup = []
            for ticket_id in last_author_dict.keys():
                if last_author_dict[ticket_id] == ticket_author_dict[ticket_id]:
                    last_message_cust.append(ticket_id)
                else:
                    last_message_sup.append(ticket_id)

            if filterby == 'last_message_cust':
                domain = [('id', 'in', last_message_cust)]
            else:
                domain = [('id', 'in', last_message_sup)]

        else:
            domain = searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('id', 'all'):
                search_domain = OR([search_domain, [('id', 'ilike', search)]])
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                discussion_subtype_id = request.env.ref('mail.mt_comment').id
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search), ('message_ids.subtype_id', '=', discussion_subtype_id)]])
            if search_in in ('status', 'all'):
                search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            domain += search_domain

        # pager
        tickets_count = len(request.env['aagam.helpdesk.ticket'].search(domain))
        pager = portal_pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in, 'search': search},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )

        tickets = request.env['aagam.helpdesk.ticket'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_tickets_history'] = tickets.ids[:100]

        if groupby == 'stage':
            grouped_tickets = [request.env['aagam.helpdesk.ticket'].concat(*g) for k, g in groupbyelem(tickets, itemgetter('stage_id'))]
        else:
            grouped_tickets = [tickets]
        values.update({
            'date': date_begin,
            'grouped_tickets': grouped_tickets,
            'tickets': tickets,
            'page_name': 'ticket',
            'default_url': '/my/tickets',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
        })
        return request.render("website_support_ticket_odoo_aagam.view_helpdesk_ticket_portal", values)

    # @http.route([
    #     '/my/ticket/close/<int:ticket_id>',
    #     '/my/ticket/close/<int:ticket_id>/<access_token>',
    # ], type='http', auth="public", website=True)
    # def ticket_close(self, ticket_id=None, access_token=None, **kw):
    #
    #     current_date = datetime.datetime.now()
    #     try:
    #         ticket_sudo = self._document_check_access('aagam.helpdesk.ticket', ticket_id, access_token)
    #     except (AccessError, MissingError):
    #         return request.redirect('/my')
    #
    #     if not ticket_sudo.helpdesk_team_id.allow_portal_ticket_closing:
    #         raise UserError(_("The team does not allow ticket closing through portal"))
    #
    #     if not ticket_sudo.closed_by_partner:
    #         closing_stage = ticket_sudo.helpdesk_team_id._get_closing_stage()
    #         if ticket_sudo.helpdesk_stage_id != closing_stage:
    #
    #             ticket_sudo.write({'helpdesk_stage_id': closing_stage[0].id,
    #                                'closed_by_partner': True,
    #                                'close_ticket_date': current_date})
    #         else:
    #             ticket_sudo.write({'closed_by_partner': True, 'close_ticket_date': current_date})
    #         body = _('Ticket closed by the customer')
    #         ticket_sudo.with_context(mail_create_nosubscribe=True).message_post(body=body, message_type='comment', subtype_xmlid='mail.mt_note')
    #     return request.redirect('/my/ticket/%s/%s' % (ticket_id, access_token or ''))

    @http.route(['/helpdesk/rating/submit'], type='http', auth="public", website=True)
    def index_submit(self, access_token=None, **post):
        ticket = request.env['aagam.helpdesk.ticket'].sudo().search([('id', '=', post.get('id'))])
        if post.get('rating') == 'poor':
            ticket.priority_new = '1'
        if post.get('rating') == 'average':
            ticket.priority_new = '2'
        if post.get('rating') == 'good':
            ticket.priority_new = '3'
        if post.get('rating') == 'excellent':
            ticket.priority_new = '4'
        if post.get('comment'):
            ticket.write({'comment': post.get('comment')})
        return request.render('website_support_ticket_odoo_aagam.rating_submit')


class aagamHelpdeskTicket(http.Controller):

    @http.route('/getData', type='json', auth='public', website=True)
    def getData(self, **kwargs):
        domain = []
        if kwargs.get('teamLead_id'):
            teamlead_id = int(kwargs.get('teamLead_id'))
            domain.append(('res_user_id', '=', teamlead_id))
        if kwargs.get('team_id'):
            team_id = int(kwargs.get('team_id'))
            domain.append(('helpdesk_team_id', '=', team_id))
        if kwargs.get('ticket_type_id'):
            ticket_type_id = int(kwargs.get('ticket_type_id'))
            domain.append(('ticket_type_id', '=', ticket_type_id))
        if kwargs.get('assignUser_id'):
            assignUser_id = int(kwargs.get('assignUser_id'))
            domain.append(('res_user_id', '=', assignUser_id))

        if kwargs.get('custome_date_id'):
            custome_date_id = kwargs.get('custome_date_id')
            if custome_date_id:
                date_str = custome_date_id
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                today = date.today()
                start_date = date_obj
                end_date = datetime(today.year, today.month, today.day, 23, 59, 59)
                domain.append(('create_date', '>=', start_date))
                domain.append(('create_date', '<=', end_date))

        if kwargs.get('date_id'):
            date_id = int(kwargs.get('date_id'))
            if date_id == 1:
                today = date.today()
                start_date = datetime(today.year, today.month, today.day)
                end_date = datetime(today.year, today.month, today.day, 23, 59, 59)
                domain.append(('create_date', '>=', start_date))
                domain.append(('create_date', '<=', end_date))
            if date_id == 2:
                today = date.today()
                yesterday = today - timedelta(days=1)
                start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
                end_date = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
                domain.append(('create_date', '>=', start_date))
                domain.append(('create_date', '<=', end_date))
            if date_id == 3:
                date_obj = datetime.today()
                start_of_week = date_obj - timedelta(days=date_obj.weekday())  # Monday
                end_of_week = start_of_week + timedelta(days=6)  # Sunday
                domain.append(('create_date', '>=', start_of_week))
                domain.append(('create_date', '<=', end_of_week))

            if date_id == 4:
                date_obj = datetime.today()
                start_of_week = date_obj + timedelta(days=-date_obj.weekday(), weeks=-1)  # Monday
                end_of_week = date_obj + timedelta(-date_obj.weekday() - 1)  # Sunday

                domain.append(('create_date', '>=', start_of_week))
                domain.append(('create_date', '<=', end_of_week))
            if date_id == 5:
                date_obj = datetime.today()
                start_of_month = date_obj.replace(day=1)
                end_of_month = date_obj.replace(day=calendar.monthrange(date_obj.year, date_obj.month)[1])
                domain.append(('create_date', '>=', start_of_month))
                domain.append(('create_date', '<=', end_of_month))

            if date_id == 6:
                date_obj = datetime.today()
                date_obj = date_obj + dateutil.relativedelta.relativedelta(months=-1)
                start_of_month = date_obj.replace(day=1)
                end_of_month = date_obj.replace(day=calendar.monthrange(date_obj.year, date_obj.month)[1])
                domain.append(('create_date', '>=', start_of_month))
                domain.append(('create_date', '<=', end_of_month))

            if date_id == 7:
                date_obj = datetime.today()
                x = ('%s-01-01' % (date_obj.year))
                y = ('%s-12-31' % (date_obj.year))
                start_of_year = datetime.strptime(x, '%Y-%m-%d')
                end_of_year = datetime.strptime(y, '%Y-%m-%d')
                domain.append(('create_date', '>=', start_of_year))
                domain.append(('create_date', '<=', end_of_year))

            if date_id == 8:
                date_obj = datetime.today()
                x = ('%s-01-01' % (date_obj.year - 1))
                y = ('%s-12-31' % (date_obj.year - 1))
                start_of_year = datetime.strptime(x, '%Y-%m-%d')
                end_of_year = datetime.strptime(y, '%Y-%m-%d')
                domain.append(('create_date', '>=', start_of_year))
                domain.append(('create_date', '<=', end_of_year))

            if date_id == 9:
                date_str = '2021-07-06'
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                start_of_week = date_obj - timedelta(days=date_obj.weekday())  # Monday

        ticket_ids_filter = request.env['aagam.helpdesk.ticket'].sudo().search(domain)
        teamdata_new = {}
        teamdata_inprogress = {}
        teamdata_solved = {}
        teamdata_cancelled = {}
        teamdata_others = {}
        for data in ticket_ids_filter:
            dict = {}
            if data.helpdesk_stage_id.name == 'New':
                dict['number'] = data.number
                dict['customer'] = data.partner_id.name
                dict['create_date'] = data.create_date
                dict['write_date'] = data.write_date
                dict['assign_user'] = data.res_user_id.name
                dict['stage'] = data.helpdesk_stage_id.name
                teamdata_new[data.id] = dict
            if data.helpdesk_stage_id.name == 'In Progress':
                dict['number'] = data.number
                dict['customer'] = data.partner_id.name
                dict['create_date'] = data.create_date
                dict['write_date'] = data.write_date
                dict['assign_user'] = data.res_user_id.name
                dict['stage'] = data.helpdesk_stage_id.name
                teamdata_inprogress[data.id] = dict
            if data.helpdesk_stage_id.name == 'Solved':
                dict['number'] = data.number
                dict['customer'] = data.partner_id.name
                dict['create_date'] = data.create_date
                dict['write_date'] = data.write_date
                dict['assign_user'] = data.res_user_id.name
                dict['stage'] = data.helpdesk_stage_id.name
                teamdata_solved[data.id] = dict
            if data.helpdesk_stage_id.name == 'Cancelled':
                dict['number'] = data.number
                dict['customer'] = data.partner_id.name
                dict['create_date'] = data.create_date
                dict['write_date'] = data.write_date
                dict['assign_user'] = data.res_user_id.name
                dict['stage'] = data.helpdesk_stage_id.name
                teamdata_cancelled[data.id] = dict
            if data.helpdesk_stage_id.name not in ['New', 'In Progress', 'Solved', 'Cancelled']:
                dict['number'] = data.number
                dict['customer'] = data.partner_id.name
                dict['create_date'] = data.create_date
                dict['write_date'] = data.write_date
                dict['assign_user'] = data.res_user_id.name
                dict['stage'] = data.helpdesk_stage_id.name
                teamdata_others[data.id] = dict
        len_teamdata_new = len(teamdata_new)
        len_teamdata_inprogress = len(teamdata_inprogress)
        len_teamdata_solved = len(teamdata_solved)
        len_teamdata_cancelled = len(teamdata_cancelled)
        len_teamdata_others = len(teamdata_others)
        result = {
            'teamdata_new': teamdata_new,
            'teamdata_inprogress': teamdata_inprogress,
            'teamdata_solved': teamdata_solved,
            'teamdata_cancelled': teamdata_cancelled,
            'teamdata_others': teamdata_others,
            'len_teamdata_new': len_teamdata_new,
            'len_teamdata_inprogress': len_teamdata_inprogress,
            'len_teamdata_solved': len_teamdata_solved,
            'len_teamdata_cancelled': len_teamdata_cancelled,
            'len_teamdata_others': len_teamdata_others,
        }
        return result

    @http.route('/search_helpdesk_tickets', type='http', auth='user', website=True)
    def search_create_helpdesk_tickets_details(self, **kwargs):
        helpdesk_tickets = request.env['aagam.helpdesk.ticket'].sudo().search([])
        return request.render('website_support_ticket_odoo_aagam.helpdesk_ticket_search', {'ticket': helpdesk_tickets})

    @http.route(['/helpdesk/search/ticket'], type='http', methods=['POST'], auth='user', website=True, csrf=False)
    def helpdesk_search_ticket(self, **kwargs):
        ticket_id = request.env['aagam.helpdesk.ticket'].search([('number', '=', kwargs.get('search'))])
        if ticket_id:
            return request.redirect('/aagam/helpdesk/ticket/%s' % (ticket_id.id))
        else:
            return request.render('website_support_ticket_odoo_aagam.helpdesk_error_message', {'error_message': ticket_id})

    # @http.route([
    #     "/aagam/helpdesk/ticket/<int:ticket_id>",
    #     "/aagam/helpdesk/ticket/<int:ticket_id>/<access_token>",
    #     '/my/ticket/<int:ticket_id>',
    #     '/my/ticket/<int:ticket_id>/<access_token>'
    # ], type='http', auth="public", website=True)
    # def tickets_followup(self, ticket_id=None, access_token=None, **kw):
    #     try:
    #         ticket_sudo = self._document_check_access('aagam.helpdesk.ticket', ticket_id, access_token)
    #     except (AccessError, MissingError):
    #         return request.redirect('/my')
    #
    #     values = self._ticket_get_page_view_values(ticket_sudo, access_token, **kw)
    #     return request.render("website_support_ticket_odoo_aagam.tickets_followup", values)

    @http.route(['/helpdesk/form'], type='http', auth="public", website=True)
    def helpdesk_form(self, **post):
        helpdesk_tickets = request.env['aagam.helpdesk.ticket'].sudo().search([])
        helpdesk_tickets_type = request.env['aagam.helpdesk.ticket.type'].sudo().search([])
        res_config_param = request.env['res.config.settings'].sudo().search([])
        if res_config_param:
            res_config = request.env['res.config.settings'].sudo().search([])[-1]
        else:
            res_config = res_config_param

        partner_name = ""
        partner_email = ""
        return request.render("website_support_ticket_odoo_aagam.helpdesk_create_ticket_from_front_end",
                              {'my_tickets': helpdesk_tickets,
                               'ticket_types': helpdesk_tickets_type,
                               'partner_name': partner_name,
                               'partner_email': partner_email,
                               'is_attachment': res_config.is_attachment})

    @http.route(['/helpdesk/form/submit'], type='http', auth="public", website=True)
    def helpdesk_form_submit(self, **post):
        ticket = request.env['aagam.helpdesk.ticket'].sudo().create({
            'helpdesk_ticket_type_id': post.get('helpdesk_ticket_type_id'),
            'name': post.get('name'),
            'partner_name': post.get('partner_name'),
            'partner_email': post.get('partner_email'),
            'priority': post.get('priority'),
            'description': post.get('description'),
        })
        if post.get('attachment'):
            file = post.get('attachment')
            name = post.get('attachment').filename
            attachment_id = request.env['ir.attachment'].sudo().create({
                'name': name,
                'res_name': name,
                'type': 'binary',
                'datas': base64.b64encode(file.read()),
                'res_model': 'aagam.helpdesk.ticket',
                'res_id': ticket.id
            })

            ticket.sudo().write({'attachment_ids': [(6, 0, attachment_id.ids)]})

        vals = {
            'ticket': ticket,
        }
        return request.render("website_support_ticket_odoo_aagam.view_helpdesk_ticket_success", vals)

    @http.route(['/ticket/attachment/download/<int:attachment_id>'], type='http', auth="user", website=True)
    def download_attcahment_tickets(self, attachment_id=None, **post):
        attachment = request.env['ir.attachment'].sudo().search_read(
            [('id', '=', int(attachment_id))],
            ["name", "datas", "type", "res_model", "res_id", "type", "url"]
        )
        if attachment:
            attachment = attachment[0]
        else:
            return redirect('//ticket/attachment/download/%s' % attachment_id)

        if attachment["type"] == "url":
            if attachment["url"]:
                return redirect(attachment["url"])
            else:
                return request.not_found()
        elif attachment["datas"]:
            data = io.BytesIO(base64.standard_b64decode(attachment["datas"]))
            return http.send_file(data, filename=attachment['name'], as_attachment=True)
        else:
            return request.not_found()

    @http.route(['/portal/get_id'], type='json', auth="user", website=True, csrf=False)
    def get_ticket_id(self, **post):
        base_value = request.params['id']
        send_data = request.env['aagam.helpdesk.ticket'].sudo().search([('id', '=', base_value)])
        if request.env.is_admin():
            send_data.is_customer_replied = False
        else:
            send_data.is_customer_replied = True


class TicketRating(http.Controller):

    @http.route(['/helpdesk/rating', '/helpdesk/rating/<model("aagam.helpdesk.ticket.team"):team>'], type='http', auth="public", website=True,
                sitemap=True)
    def page(self, team=False, **kw):
        user = request.env.user
        team_domain = [('id', '=', team.id)] if team else []
        if user.has_group('website_support_ticket_odoo_aagam.group_helpdesk_ticket_manager'):
            domain = AND([[('use_rating', '=', True)], team_domain])
        else:
            domain = AND([[('use_rating', '=', True), ('portal_show_rating', '=', True)], team_domain])
        teams = request.env['aagam.helpdesk.ticket.team'].search(domain)
        team_values = []
        for team in teams:
            tickets = request.env['aagam.helpdesk.ticket'].sudo().search([('team_id', '=', team.id)])
            domain = [
                ('res_model', '=', 'aagam.helpdesk.ticket'), ('res_id', 'in', tickets.ids),
                ('consumed', '=', True), ('rating', '>=', 1),
            ]
            ratings = request.env['rating.rating'].sudo().search(domain, order="id desc", limit=100)

            yesterday = (datetime.date.today() - datetime.timedelta(days=-1)).strftime('%Y-%m-%d 23:59:59')
            stats = {}
            any_rating = False
            for x in (7, 30, 90):
                todate = (datetime.date.today() - datetime.timedelta(days=x)).strftime('%Y-%m-%d 00:00:00')
                domdate = domain + [('create_date', '<=', yesterday), ('create_date', '>=', todate)]
                stats[x] = {1: 0, 3: 0, 5: 0}
                rating_stats = request.env['rating.rating'].sudo().read_group(domdate, [], ['rating'])
                total = sum(st['rating_count'] for st in rating_stats)
                for rate in rating_stats:
                    any_rating = True
                    stats[x][rate['rating']] = (rate['rating_count'] * 100) / total
            values = {
                'team': team,
                'ratings': ratings if any_rating else False,
                'stats': stats,
            }
            team_values.append(values)
        return request.render('website_support_ticket_odoo_aagam.view_helpdesk_ticket_rating', {'page_name': 'rating', 'teams': team_values})
