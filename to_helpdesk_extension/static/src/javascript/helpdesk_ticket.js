odoo.define('to_helpdesk_extension.HelpdeskTicket', function (require) {
    "use strict";

    var core = require('web.core');
    var animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var qweb = core.qweb;

    animation.registry.HelpdeskTicket = animation.Class.extend({
        selector: '#template_support_ticket',
        events: {
            'click #add_incident': '_add_incident',
            'click #save_additional_incident': '_save_additional_incident',
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
            //
        },

        _add_incident: function (ev){
            $('#incident_1').after(`
                <div class="row to_div_27 to_div_36" id="new_incident">
                    <div class="col-12 to_div_26">
                        <div class="to_div_24 to_div_35">
    
                            <div class="col-12 to_div_28">
                                <textarea type="text" class="form-control to_input_2 to_disable_element" id="input_description_incident_new"
                                          aria-describedby="emailHelp" placeholder="Description"/>
                            </div>
    
                            <div class="col-12" style="display: flex; justify-content: end; padding: 0px !important;">
                                <button id="save_additional_incident" type="button" class="btn btn-primary to_button_2">
                                <i class="fa fa-save"/><span class="to_span_8">Save</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `)
            $('#add_incident').remove()
        },

        _save_additional_incident: function (ev){
            var additional_incident = $('#input_description_incident_new').val()
            var ticket_number = $('#helpdesk_ticket_number').text()
            $('#ticket_identification').after("<p>" + additional_incident + "</p>")
            if(additional_incident.replace(/ /g, '')){
                ajax.jsonRpc('/ticket/additional/incident', 'call', {
                    'ticket_number': ticket_number,
                    'additional_incident': additional_incident,
                }).then(function (result) {
                    // Código aquí
                });
            }
            $('#new_incident').remove()

        }

    });
    return animation.registry.HelpdeskTicketSupportAnimation;
});