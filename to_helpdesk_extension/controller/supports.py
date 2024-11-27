# -*- coding: utf-8 -*-

import re
import math

from odoo import http
from odoo.http import request


class Supports(http.Controller):

    @http.route(['/support/tickets'], type='http', auth="user", website=True)
    def support_tickets(self, **post):
        return request.render("to_helpdesk_extension.website_template_support")

    @http.route(['/ticket/list'], type='json', auth="user", website=True)
    def to_helpdesk_helpdesk_form(self, **post):
        website_input_page = post.get('website_input_page')
        website_input_search = post.get('website_input_search')
        website_input_stage = post.get('website_input_stage')
        ticket_section = request.env['aagam.helpdesk.ticket']
        stages = request.env['aagam.helpdesk.stage'].search([], order='sequence ASC')
        stages_result = []

        # FILTRAR SOLO LOS REGISTROS CREADOS POR EL USUARIO.
        domain = [('create_uid', '=', request.env.user.id)]

        if website_input_search:
            domain = domain + ['|', ('name', 'ilike', website_input_search), ('number', 'ilike', website_input_search)]
        for stage in stages:
            stages_result.append(stage.name.strip() if stage.name.strip() else "")

        # FILTRAR LOS REGISTROS POR ETAPA
        if website_input_stage:
            if website_input_stage == 'All tickets':
                pass
            else:
                selected_stage = stages.filtered(lambda s: s.name.strip() == website_input_stage.strip() if website_input_stage else "")
                domain = domain + [('helpdesk_stage_id', '=', selected_stage.id)]
        else:
            website_input_stage = 'All tickets'

        # SE BUSCAN TODOS LOS REGISTROS QUE COINCIDAN CON EL DOMAIN
        total_tickets = request.env['aagam.helpdesk.ticket'].search(domain, order='id DESC')
        # SE DETERMINA EL NUMERO DE PAGINAS DE LA PAGINACIÓN
        number_pages = 0
        if total_tickets:
            if len(total_tickets) > 5:
                number_pages = math.ceil(len(total_tickets) / 5)

        # SE ENCARGA DE INCREMENTAR LA NUMERACIÓN DE LA PAGINACIÓN
        if website_input_page:
            if website_input_page == 'default':
                if number_pages:
                    website_input_page = 1
            else:
                website_input_page = int(website_input_page)
                if number_pages >= website_input_page + 1:
                    website_input_page = website_input_page
            if website_input_page != 'default':
                website_input_page = int(website_input_page)

        if total_tickets:
            if not number_pages:
                ticket_section = total_tickets[0:5]
            else:
                if not website_input_page:
                    website_input_page = 1
                start = (website_input_page * 5) - 5
                end = website_input_page * 5
                ticket_section = total_tickets[start:end]

        open_tickets = []
        # RECORRE Y GUARDA ENA LISTA TODOS LOS REGISTROS CONSEGUIDOS
        for ticket in ticket_section:
            color = {
                0: "darkgreen;",
                1: "#F06050",
                2: "#F4A460",
                3: "#F7CD1F",
                4: "#6CC1ED",
                5: "#814968",
                6: "#EB7E7F",
                7: "#2C8397",
                8: "#475577",
                9: "#D6145F",
                10: "#30C381",
                11: "#9365B8",
            }
            stage = ""
            website_context = request.env.context
            if not ticket.sudo().helpdesk_stage_id:
                if website_context["lang"] == "es_ES" or website_context["lang"] == "es_VE":
                    stage = "En evaluación"
                else:
                    stage = "Under evaluation"
            else:
                stage = ticket.sudo().helpdesk_stage_id.name.strip() if ticket.sudo().helpdesk_stage_id.name else False


            open_tickets.append(
                {
                    'number': ticket.number,
                    'name': ticket.name,
                    'helpdesk_stage_id': stage,
                    'stage_color': color[ticket.helpdesk_stage_id.color],
                    'description': re.sub("<.*?>", "", ticket.sudo().support_requests_ids[0].description if ticket.sudo().support_requests_ids else ""),
                })

        tickets = request.env['aagam.helpdesk.ticket'].sudo().search([('create_uid', '=', request.env.user.id)])
        tickets_ids = tickets.ids

        retrieved_messages = request.env['mail.message'].sudo().search([('res_id', 'in', tickets_ids), ('message_type', '=', 'comment')], order='id DESC', limit=10)

        messages = []
        for message in retrieved_messages:
            messages_date = message.create_date.strftime('%d-%m-%Y %H:%M')
            messages.append(
                {'body': re.sub("<.*?>", "", message.body),
                 'subject': message.record_name,
                 'res_id': message.res_id,
                 'create_date': messages_date,
                 }
            )

        if open_tickets and not number_pages:
            number_pages = 1
        result = {
            'number_pages': number_pages,
            'open_tickets': open_tickets,
            'stages_result': stages_result,
            'website_input_stage': website_input_stage.strip() if website_input_stage else "",
            'messages': messages,
            'messages_account': len(messages),
            'ticket_account': len(open_tickets),
        }

        return result

    @http.route(['/support/ticket/new'], type='http', auth="user", website=True)
    def _new_support_ticket(self, **kw):
        priorities = dict(request.env['aagam.helpdesk.ticket']._fields['priority'].selection)
        support_type = request.env['aagam.helpdesk.ticket.type'].sudo().search([])
        return request.render("to_helpdesk_extension.new_support_ticket", {
            'priorities': priorities,
            'support_type': support_type,
        })

    @http.route(['/ticket/save'], type='json', auth="user", website=True)
    def _save_ticket(self, **kw):
        title = kw.get('title')
        description = kw.get('description')
        priority = kw.get('priority')
        type = kw.get('type')
        request.env['aagam.helpdesk.ticket'].sudo().create({
            'name': title,
            'description': "<p><b>%s</b></p>" % description,
            'priority': priority,
            'helpdesk_ticket_type_id': type,
            'support_requests_ids': [(0, 0, {
                'description': description
            })],
        })
        return {}

    @http.route(['/ticket/additional/incident'], type='json', auth="user", website=True)
    def _save_additional_incident(self, **kw):
        additional_incident = kw.get('additional_incident')
        ticket_number = kw.get('ticket_number')
        ticket = request.env['aagam.helpdesk.ticket'].search([('number', '=', ticket_number)])
        ticket.sudo().write({
            'support_requests_ids': [(0, 0, {
                'description': additional_incident
            })],
        })
        return {}

    @http.route(["/support/ticket/<string:ticket_number>"], type='http', auth='user', website=True)
    def _render_template_support_ticket(self, ticket_number):
        ticket = request.env['aagam.helpdesk.ticket'].sudo().search([('number','=',ticket_number)])
        priority_dict = dict(ticket._fields['priority'].selection)
        priority = priority_dict.get(ticket.priority)
        return request.render("to_helpdesk_extension.support_ticket", {
            'ticket': ticket,
            'ticket_priority': priority,
        })
