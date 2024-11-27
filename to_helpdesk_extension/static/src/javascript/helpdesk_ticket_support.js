odoo.define('to_helpdesk_extension.HelpdeskTicketSupport', function (require) {
    "use strict";

    var core = require('web.core');
    var animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var qweb = core.qweb;

    animation.registry.HelpdeskTicketSupportAnimation = animation.Class.extend({
        selector: '#to_helpdesk_ticket_support',
        events: {
            'input #search_ticket': '_search_ticket_name',
            'click #btn_save_ticket': '_btn_save_ticket',
            'click .btn_pagination': '_search_tickets_pagination',
            'change #helpdesk_stage': '_search_ticket_stage',
            'click .next_pagination': '_btn_next_pagination',
            'click .previous_pagination': '_btn_previous_pagination',
        },

        start: function () {
            this.self = this
            qweb.add_template("/to_helpdesk_extension/static/src/xml/support_ticket_list.xml");
            this._default_render()
        },

        stop: function () {
            // Detener la animación
        },

        _default_render: function (ev) {
            var self = this;
            ajax.jsonRpc('/ticket/list', 'call', {
                'website_input_page': "default",
            }).then(function (result) {
                self._template_rendering(result)
                var page_number = 1
                var tags = self._generate_pagination(result, page_number)
                $('#insert_pagination').append(tags)
            });
        },

        _search_ticket_name: function (ev){
            var search_field = $(ev.target).val()
            var page_number = false
            var stage = $('#select_helpdesk_stage').val();
            this._update_records(ev, search_field, page_number, stage)
        },

        _search_tickets_pagination: function (ev){
            var search_field = false
            var page_number = $(ev.target).attr('id');
            var stage = $('#select_helpdesk_stage').val();
            this._update_records(ev, search_field, page_number, stage)
        },

        _search_ticket_stage: function (ev){
            var search_field = false
            var page_number = false;
            var stage = $('#select_helpdesk_stage').val();
            this._update_records(ev, search_field, page_number, stage)
        },

        _btn_next_pagination: function (ev){
            var search_field = $('#search_ticket').val()
            var page_number = parseInt($(ev.target).attr('id'));
            var stage = $('#select_helpdesk_stage').val();
            this._update_records(ev, search_field, page_number, stage)
        },

        _btn_previous_pagination: function (ev){
            var search_field = $('#search_ticket').val()
            var page_number = parseInt($(ev.target).attr('id'));
            var stage = $('#select_helpdesk_stage').val();
            this._update_records(ev, search_field, page_number, stage)
        },

        _update_records: function (ev, search_field, page_number, stage){
            var self = this;
            ajax.jsonRpc('/ticket/list', 'call', {
                'website_input_page': page_number,
                'website_input_stage': stage,
                'website_input_search': search_field,
            }).then(function (result) {
                self._template_rendering(result)
                var tags = self._generate_pagination(result, page_number)
                $('#insert_pagination').empty();
                $('#insert_pagination').append(tags);
            });
        },

        _template_rendering: function (result){
            $('#list_tickets').html(qweb.render('to_helpdesk_extension.support_ticket_list', {
                    'tickets': result
            }));
            $('#helpdesk_stage').html(qweb.render('to_helpdesk_extension.helpdesk_stages', {
                'tickets': result
            }));
            $('#user_messages').html(qweb.render('to_helpdesk_extension.website_support_messages', {
                'result': result
            }));
        },

        _generate_pagination: function(result, page_number){
            var start = 0
            var end = 0

            // LOGICA ENCARGADA DE GENERAR LOS RANGOS DE LA PAGINACIÓN
            if(page_number == 1 || page_number == 0){
                if(result.number_pages >= 5){
                    start = 1
                    end = 5
                }else{
                    start = 1
                    end = result.number_pages
                }
            }else{
                if((page_number - 2) > 0){
                    start = page_number - 2
                }else if((page_number - 1) > 0){
                    start = page_number - 1
                }
                if(start + 4 <= result.number_pages){
                    end = start + 4
                }else{
                    // DETERMINAR CUENTAS VALORES SE PUEDEN SUMAR AL COMIENZO DE LA PAGINACIÓN
                    var result_operation = (result.number_pages) - start
                    end = start + result_operation
                    var star_end_values = []
                    for (var i = start; i <= end; i++) {
                        star_end_values.push(i)
                    }
                    if (star_end_values.length < 5 ){
                        var difference = 5 - star_end_values.length
                        if(result.number_pages > 5){
                            start = start - difference
                        }
                    }
                }
            }

            var tags = ''
            var active_pagination_id = false
            if (end) {
                for (var i = start; i <= end; i++) {
                    if (page_number == i) {
                        if(result.number_pages == 1){
                            tags += `
                            <li class="page-item btn_pagination active">
                                <a class="page-link to_a_5" href="#" id="${i}" style="background-color: #e3e3e3 !important;
                                    border: solid 1px #DEE2E6 !important;">
                                    ` + i + `
                                </a>
                            </li>`
                        }else{
                            tags += `
                            <li class="page-item btn_pagination active">
                                <a class="page-link" href="#" id="${i}">
                                    ` + i + `
                                </a>
                            </li>`
                        }

                        active_pagination_id = i
                    } else {
                        tags += `
                            <li class="page-item btn_pagination">
                                <a class="page-link" href="#" id="${i}">
                                    ` + i + `
                                </a>
                            </li>`
                    }
                }
                var val_next = 0
                var val_previous = 0
                if(active_pagination_id == result.number_pages){
                    val_next = active_pagination_id
                }else if (active_pagination_id < result.number_pages) {
                    val_next = active_pagination_id + 1
                }
                if(active_pagination_id - 1 > 0){
                        val_previous = active_pagination_id - 1
                }else{
                    val_previous = 1
                }
                var tag_next = `
                        <li class="page-item">
                            <a class="page-link next_pagination to_a_3" 
                            href="#" id="${val_next}">Siguiente</a>
                        </li>`
                var tag_previous = `
                    <li class="page-item">
                        <a class="page-link to_a_2 previous_pagination" id="${val_previous}" href="#">Anterior</a>
                    </li>`
                tags = tag_previous + tags + tag_next
            }
            return tags
        },
    });
    return animation.registry.HelpdeskTicketSupportAnimation;
});
