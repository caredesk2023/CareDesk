odoo.define('website_support_ticket_odoo_aagam.dashboard', function (require) {
"use strict";
var core = require('web.core');
var KanbanController = require('web.KanbanController');
var KanbanModel = require('web.KanbanModel');
var KanbanRenderer = require('web.KanbanRenderer');
var KanbanView = require('web.KanbanView');
var session = require('web.session');
var view_registry = require('web.view_registry');
var ajax = require('web.ajax');
var QWeb = core.qweb;
var _t = core._t;
var _lt = core._lt;
var rpc = require('web.rpc');
var HelpdeskFilterStageRenderer = KanbanRenderer.extend({

    jsLibs: [
        '/website_support_ticket_odoo_aagam/static/src/js/Chart.js',

    ],
    events: _.extend({}, KanbanRenderer.prototype.events, {
        'click .o_dashboard_action': '_onDashboardActionClicked',
        'click .o_target_to_set': '_onDashboardTargetClicked',
            'change  .o_team_lead': '_onChangeTeamLead',
            'change  .o_team': '_onChangeTeamLead',
            'change  .o_assign': '_onChangeTeamLead',
            'change  #date_filter': '_onChangeTeamLead',
            'change .custom_selection': '_onChangeTeamLead',
    }),


     _onChangeTeamLead: function(e) {
            var teamLead_id = $('.o_team_lead').find(':selected').val();
            var team_id = $('.o_team').find(':selected').val();
            var assignUser_id = $('.o_assign').find(':selected').val();
            var date_id = $('#date_filter').find(':selected').val();

            if (date_id == 9) {
                $('.datepicker').css("display","flex");
            }
            else {
                $('.datepicker').css("display","none");
                this._render()
            }

            var custome_date_id = $('.custom_selection').val();

            ajax.jsonRpc('/getData', 'call', {
                'teamLead_id': teamLead_id,
                'team_id':team_id,
                'assignUser_id': assignUser_id,
                'date_id' : date_id,
                'custome_date_id': custome_date_id

            }).then(function(data) {

                var result = data;
                var teamdata_new = result.teamdata_new;
                var teamdata_inprogress = result.teamdata_inprogress;
                var teamdata_solved = result.teamdata_solved;
                var teamdata_cancelled = result.teamdata_cancelled;
                var teamdata_others = result.teamdata_others;

                var new_cnt = result.len_teamdata_new;
                var new_count = document.getElementById('new_count');
                new_count.innerHTML = new_cnt;

                 var inprogrss_cnt = result.len_teamdata_inprogress;
                 var progress_count = document.getElementById('progress_count');
                progress_count.innerHTML = inprogrss_cnt;


                 var solve_cnt = result.len_teamdata_solved;
                 var solved_count = document.getElementById('solved_count');
                solved_count.innerHTML = solve_cnt;

                var cancel_cnt = result.len_teamdata_cancelled;
                 var cancel_count = document.getElementById('cancel_count');
                cancel_count.innerHTML = cancel_cnt;


                var i;
                for (const [key, value] of Object.entries(teamdata_new)) {
                    var data_value = value;
                    for (const [k, v] of Object.entries(data_value)) {
//                        console.log("k,v for new team data:",k, v);
                    }
                }
                $("#tbody_new").empty();
                for (const [key, value] of Object.entries(teamdata_new)) {
                    var data_value = value;
                    var html = "<tr><td>" + data_value.number + "</td><td>"+data_value.customer+"</td><td>"+data_value.create_date+"</td><td>"+data_value.write_date+"</td><td>"+data_value.assign_user+"</td><td>"+data_value.stage+"</td></tr>";
                    $("#tbody_new").append(html);
                }
                $("#tbody_inProgress").empty();
                for (const [key, value] of Object.entries(teamdata_inprogress)) {
                    var data_value = value;
                    var html = "<tr><td>" + data_value.number + "</td><td>"+data_value.customer+"</td><td>"+data_value.create_date+"</td><td>"+data_value.write_date+"</td><td>"+data_value.assign_user+"</td><td>"+data_value.stage+"</td></tr>";
                    $("#tbody_inProgress").append(html);
                }
                $("#tbody_solved").empty();
                for (const [key, value] of Object.entries(teamdata_solved)) {
                    var data_value = value;
                    var html = "<tr><td>" + data_value.number + "</td><td>"+data_value.customer+"</td><td>"+data_value.create_date+"</td><td>"+data_value.write_date+"</td><td>"+data_value.assign_user+"</td><td>"+data_value.stage+"</td></tr>";
                    $("#tbody_solved").append(html);
                }
                $("#tbody_cancelled").empty();
                for (const [key, value] of Object.entries(teamdata_cancelled)) {
                    var data_value = value;
                    var html = "<tr><td>" + data_value.number + "</td><td>"+data_value.customer+"</td><td>"+data_value.create_date+"</td><td>"+data_value.write_date+"</td><td>"+data_value.assign_user+"</td><td>"+data_value.stage+"</td></tr>";
                    $("#tbody_cancelled").append(html);
                }
                $("#tbody_others").empty();
                for (const [key, value] of Object.entries(teamdata_others)) {
                    var data_value = value;
                    var html = "<tr><td>" + data_value.number + "</td><td>"+data_value.customer+"</td><td>"+data_value.create_date+"</td><td>"+data_value.write_date+"</td><td>"+data_value.assign_user+"</td><td>"+data_value.stage+"</td></tr>";
                    $("#tbody_others").append(html);
                }
            });

        },

        // _onDashboardTargetClicked: function(e) {
        //     var self = this;
        // },
    _notifyTargetChange: function (target_name, value) {
        this.trigger_up('dashboard_edit_target', {
            target_name: target_name,
            target_value: value,
        });
    },
    _render: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            var values = self.state.dashboardValues;
            var helpdesk_ticket_filter = QWeb.render('website_support_ticket_odoo_aagam.HelpdeskFilterStage', {
                widget: self,
                show_demo: values.show_demo,
                rating_enable: values.rating_enable,
                success_rate_enable: values.success_rate_enable,
                values: values,
            });
            self.$el.prepend(helpdesk_ticket_filter);
        });
    },
    _onDashboardActionClicked: function (e) {
        e.preventDefault();
        var $action = $(e.currentTarget);
        this.trigger_up('dashboard_open_action', {
            action_name: $action.attr('name'),
        });
    },
    _onDashboardTargetClicked: function (e) {
        var self = this;
        var $target = $(e.currentTarget);
        var target_name = $target.attr('name');
        var target_value = $target.attr('value');

        var $input = $('<input/>', {type: "text", name: target_name});
        if (target_value) {
            $input.attr('value', target_value);
        }
        $input.on('keyup input', function (e) {
            if (e.which === $.ui.keyCode.ENTER) {
                self._notifyTargetChange(target_name, $input.val());
            }
        });
        $input.on('blur', function () {
            self._notifyTargetChange(target_name, $input.val());
        });
        $input.replaceAll($target)
              .focus()
              .select();
    },
});

var HelpdeskFilterStageModel = KanbanModel.extend({
    init: function () {
        this.dashboardValues = {};
        this._super.apply(this, arguments);
    },
    get: function (localID) {
        var result = this._super.apply(this, arguments);
        if (_.isObject(result)) {
            result.dashboardValues = this.dashboardValues[localID];
        }
        return result;
    },
    load: function () {
        return this._loadDashboard(this._super.apply(this, arguments));
    },
    reload: function () {
        return this._loadDashboard(this._super.apply(this, arguments));
    },
    _loadDashboard: function (super_def) {
        var self = this;
        var dashboard_def = this._rpc({
            model: 'aagam.helpdesk.ticket.team',
            method: 'retrieve_dashboard',
        });
        return Promise.all([super_def, dashboard_def]).then(function(results) {
            var id = results[0];
            var dashboardValues = results[1];
            self.dashboardValues[id] = dashboardValues;
            return id;
        });
    },
});

var HelpdeskFilterStageController = KanbanController.extend({
    custom_events: _.extend({}, KanbanController.prototype.custom_events, {
        dashboard_open_action: '_onDashboardOpenAction',
        dashboard_edit_target: '_onDashboardEditTarget',
    }),
    _onDashboardEditTarget: function (e) {
        var target_name = e.data.target_name;
        var target_value = e.data.target_value;
        if (isNaN(target_value)) {
            this.do_warn(_t("Wrong value entered!"), _t("Only Integer Value should be valid."));
        } else {
            var values = {};
            values[target_name] = parseInt(target_value);
            this._rpc({
                    model: 'res.users',
                    method: 'write',
                    args: [[session.uid], values],
                })
                .then(this.reload.bind(this));
        }
    },
    _onDashboardOpenAction: function (e) {
        var self = this;
        var action_name = e.data.action_name;
        if (_.contains(['action_view_rating_today', 'action_view_rating_7days'], action_name)) {
            return this._rpc({model: this.modelName, method: action_name})
                .then(function (data) {
                    if (data) {
                    return self.do_action(data);
                    }
                });
        }
        return this.do_action(action_name);
    },
});

var HelpdeskFilterStageView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Model: HelpdeskFilterStageModel,
        Renderer: HelpdeskFilterStageRenderer,
        Controller: HelpdeskFilterStageController,
    }),
    display_name: _lt('Dashboard'),
    icon: 'fa-dashboard',
    searchview_hidden: true,
});

view_registry.add('helpdesk_ticket_filter', HelpdeskFilterStageView);

return {
    Model: HelpdeskFilterStageModel,
    Renderer: HelpdeskFilterStageRenderer,
    Controller: HelpdeskFilterStageController,
};

});
