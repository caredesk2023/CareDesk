odoo.define('to_helpdesk_extension.NewSupport', function (require) {
    "use strict";

    var core = require('web.core');
    var animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var qweb = core.qweb;

    animation.registry.NewSupportAnimation = animation.Class.extend({
        selector: '#template_new_support_ticket',
        events: {
            'click #btn_save_ticket': '_btn_save_ticket',
        },

        start: function () {
            this.self = this
            this._default_render()
        },

        stop: function () {
            // Detener la animación
        },

        _default_render: function (ev) {
            //Instrucciones al ejecutarse el javascript
        },

        _btn_save_ticket: function (ev){
            var title = $('#input_title').val()
            var description = $('#input_description').val()
            var priority = $('#ticket_priority').find(":selected").val();
            var type = $('#ticket_type').find(":selected").attr('value');
            var value_priority = $('#ticket_priority').find(":selected").attr('value')
            if(!value_priority){
                priority = false
            }
            ajax.jsonRpc('/ticket/save', 'call', {
                'title': title,
                'description': description,
                'priority': priority,
                'type': type,
            }).then(function (result) {
                window.location.href = "/support/tickets";
            });
        },

    });
    return animation.registry.NewSupportAnimation;
});