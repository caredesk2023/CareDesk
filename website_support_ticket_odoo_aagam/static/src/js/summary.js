odoo.define('website_support_ticket_odoo_aagam.helpdesk_ticket_dashboard', function (require) {
"use strict";
var BoardView = require('board.BoardView');
var viewRegistry = require('web.view_registry');
var FormRenderer = require('web.FormRenderer');

var BoardView = BoardView.extend({
    config: _.extend({}, BoardView.prototype.config, {
      
    }),

    init: function () {
        this._super.apply(this, arguments);
        this.controllerParams.customViewID = '';
    },
});
viewRegistry.add('board', BoardView);

});



