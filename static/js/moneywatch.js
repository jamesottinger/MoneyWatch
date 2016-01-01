//===============================================================================
// Copyright (c) 2015, James Ottinger. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// MoneyWatch - https://github.com/jamesottinger/moneywatch
//===============================================================================
"use strict";
var MW = MW || {};

MW = {
    moneyWatchURL: '/x/moneywatch-relay.py',
    activeRowId: '',

    paintScreen: function () {
        MW.comm.sendCommand('I.SUMMARY.GET');
        MW.comm.sendCommand('B.SUMMARY.GET');
        $('#rightcontent2').hide();
        MW.comm.sendCommand('U.LINKS.GET');
        MW.timers.startTimers();
    },

    calcNetWorth: function () {
        var nw = MW.util.formatCurrency(($('#networth-investments').val() * 1.00) + ($('#networth-banks').val() * 1.00));
        $('#sum-worth-inv').html(MW.util.formatCurrency($('#networth-investments').val()));
        $('#sum-worth-bank').html(MW.util.formatCurrency($('#networth-banks').val()));
        $('#sum-worth-all').html(nw);
    }
};

// ------------------------------------------------------------------
// [== COMMUNICATION ==]
// ------------------------------------------------------------------
MW.comm = {
    sendCommand: function (in_job) {
        var formdata;
        var urlpost = MW.moneyWatchURL + '/action/' + in_job;

        switch(in_job) {
            case 'I.SUMMARY.GET':
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        $('#rightcontent1').html(data);
                        MW.calcNetWorth();
                    }
                );
                });
                break;
            case 'I.BULKADD.EDIT':
                MW.yui.panelUniversal.set('width', 950);
                MW.yui.panelUniversal.set('headerContent', "Investments - Bulk Add" + MW.yui.YUIcloseMarkup);
                $.ajax({
                    url: urlpost,
                    data: {job: in_job},
                    success: function(data) {
                        $('#paneluniversal-inner').html(data);
                        MW.yui.panelUniversal.show();
                    }
                });
                break;
            case 'I.BULKADD.SAVE':
                formdata = $('#ibulkedit').serialize();
                $.ajax({
                    type: 'POST',
                    url: urlpost,
                    data: formdata,
                    success: function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            MW.yui.panelUniversal.hide();
                            MW.comm.sendCommand('I.SUMMARY.GET');
                            MW.comm.sendCommand('B.SUMMARY.GET');
                        }
                    }
                });
                break;
            case 'I.ENTRY.EDITSAVE':
            case 'I.ENTRY.ADDSAVE':
                formdata = $('#ieditsingle').serialize();
                var ielectionid = $('#ieditsingle-ielectionid').val();
                $.post(MW.moneyWatchURL,
                    formdata,
                    function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            $('#' + MW.activeRowId).removeClass('activeinvrow');
                            $.post(MW.moneyWatchURL,
                                {job: 'I.ELECTION.GET', 'ielectionid': ielectionid, pu: MW.util.poisonURL()},
                                function(data) {
                                    $('#transactionslist').html(data);
                                    $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
                                }
                            );
                            $.post(MW.moneyWatchURL,
                                {job: 'I.ENTRY.ADD', 'ielectionid': ielectionid, pu: MW.util.poisonURL()},
                                function(data) {
                                    $('#transactionsrightedit').html(data);
                                }
                            );
                            // reload underneath
                            MW.comm.sendCommand('I.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                );
                break;
            case 'B.SUMMARY.GET':
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        $('#rightcontent2').html(data);
                        MW.calcNetWorth();
                    }
                });
                break;
            case 'B.BULKINTEREST.EDIT':
                MW.yui.panelUniversal.set('width', 350);
                MW.yui.panelUniversal.set('headerContent', "Bank - Bulk Interest" + MW.yui.YUIcloseMarkup);
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        $('#paneluniversal-inner').html(data);
                        MW.yui.panelUniversal.show();
                    }
                });
                break;
            case 'B.BULKINTEREST.SAVE':
                formdata = $('#bbulkinterestedit').serialize();
                $.ajax({
                    type: 'POST',
                    url: urlpost,
                    data: formdata,
                    success: function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            MW.yui.panelUniversal.hide();
                            MW.comm.sendCommand('I.SUMMARY.GET');
                            MW.comm.sendCommand('B.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                });
                break;
            case 'B.BULKBILLS.EDIT':
                MW.yui.panelUniversal.set('width', 750);
                MW.yui.panelUniversal.set('headerContent', "Bank - Bulk Bills" + MW.yui.YUIcloseMarkup);
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        $('#paneluniversal-inner').html(data);
                        MW.yui.panelUniversal.show();
                    }
                });
                break;
            case 'B.BULKBILLS.SAVE':
                formdata = $('#bbulkbillsedit').serialize();
                $.ajax({
                    type: 'POST',
                    url: urlpost,
                    data: formdata,
                    success: function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            MW.yui.panelUniversal.hide();
                            MW.comm.sendCommand('I.SUMMARY.GET');
                            MW.comm.sendCommand('B.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                });
                break;
            case 'B.ENTRY.EDITSAVE':
            case 'B.ENTRY.ADDSAVE':
                var bacctid = $('#beditsingle-bacctid').val();
                formdata = $('#beditsingle').serialize();
                $.post(MW.moneyWatchURL,
                    formdata,
                    function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            $('#' + MW.activeRowId).removeClass('activebankrow');
                            $.post(MW.moneyWatchURL,
                                {job: 'B.ACCOUNT.GET', 'bacctid': bacctid, pu: MW.util.poisonURL()},
                                function(data) {
                                    $('#transactionslist').html(data);
                                    $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
                                }
                            );
                            $.post(MW.moneyWatchURL,
                                {job: 'B.ENTRY.ADD', 'bacctid': bacctid, pu: MW.util.poisonURL()},
                                function(data) {
                                    $('#transactionsrightedit').html(data);
                                }
                            );
                            // reload underneath
                            MW.comm.sendCommand('B.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                );
                break;
            case 'U.UPDATEQUOTES':
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            MW.comm.sendCommand('I.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                });
                break;
            case 'U.UPDATEBANKTOTALS':
                $.post(MW.moneyWatchURL,
                    {job: in_job, pu: MW.util.poisonURL()},
                    function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            MW.comm.sendCommand('B.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                );
                break;
            case 'U.IMPORTFILE.EDIT':
                MW.yui.panelUniversal.set('width', 420);
                MW.yui.panelUniversal.set('headerContent', "Import Menu" + MW.yui.YUIcloseMarkup);
                $.post(MW.moneyWatchURL,
                    {job: in_job, pu: MW.util.poisonURL()},
                    function(data) {
                        $('#paneluniversal-inner').html(data);
                        MW.yui.panelUniversal.show();
                    }
                );
                break;
            case 'U.LINKS.GET':
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        $('#ui-links').html(data);
                    }
                });
                break;
            case 'U.WEATHER.GET':
                $('#weather-forcast').html('');
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        $('#weather-forcast').html(data);
                    }
                });
                break;
            default:
        }
    },

    getInvElection: function (in_ielectionid) {
        $.post(MW.moneyWatchURL,
            {job: 'I.ELECTION.GET', 'ielectionid': in_ielectionid, pu: MW.util.poisonURL()},
            function(data) {
                $('#transactionslist').html(data);
                // clear any previous highlights
                $('#' + MW.activeRowId).removeClass('activeinvrow');
                $('#transactionsrightedit').removeClass('activeinveditmenu');
                $('#transactionsheaderinv').show();
                $('#transactionsheaderbank').hide();
                MW.yui.panelTransactions.show();
                // animate scroll to bottom
                // $('#transactionslist').stop().animate({ scrollTop: $('#scrollmeinv').offset().top },120);
                $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
            }
        );
        $.post(MW.moneyWatchURL,
            {job: 'I.ENTRY.ADD', 'ielectionid': in_ielectionid, pu: MW.util.poisonURL()},
            function(data) {
                $('#transactionsrightedit').html(data);
            }
        );
        $.post(MW.moneyWatchURL,
            {job: 'I.ENTRY.CHART', 'ielectionid': in_ielectionid, pu: MW.util.poisonURL()},
            function(data) {
                $('#transactionsrightchart').html(data);
            }
        );
        //$('#paneluniversal-inner').html('');
    },

    getInvElectionEdit: function (in_ielectionid, in_itransid) {
        $.ajax({
            url: MW.moneyWatchURL + '/action/I.ENTRY.EDIT',
            data: {'ielectionid': in_ielectionid, 'itransid': in_itransid},
            success: function(data) {
                $('#transactionsrightedit').html(data);
                if (MW.activeRowId !== '') {
                    $('#' + MW.activeRowId).removeClass('activeinvrow');
                }
                MW.activeRowId = in_ielectionid + in_itransid;
                $('#' + MW.activeRowId).addClass('activeinvrow');
                $('#transactionsrightedit').addClass('activeinveditmenu');
            }
        });
    },

    getInvGraph: function (in_ielectionid) {
        MW.yui.panelUniversal.set('width', 950);
        MW.yui.panelUniversal.set('headerContent', "Investment - Graph" + MW.yui.YUIcloseMarkup);
        $.ajax({
            url: MW.moneyWatchURL + '/action/I.GRAPH.GET',
            data: {'ielectionid': in_ielectionid},
            success: function(data) {
                $('#paneluniversal-inner').html(data);
                MW.yui.panelUniversal.show();
            }
        });
    },

    sendInvDelete: function (in_ielectionid, in_itransid) {
        var r = confirm("Are you sure you want to delete MW transaction?");
        if (r === true) {
            $.post(MW.moneyWatchURL,
                {job: 'I.ENTRY.DELETE', 'itransid': in_itransid, pu: MW.util.poisonURL()},
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        // reload left side, reflecting the deletion
                        $.post(MW.moneyWatchURL,
                            {job: 'I.ELECTION.GET', 'ielectionid': in_ielectionid, pu: MW.util.poisonURL()},
                            function(data) {
                                $('#transactionslist').html(data);
                            }
                        );
                        // reload underneath
                        MW.comm.sendCommand('I.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            );
        } else {
            return false;
        }
    },

    getBankEdit: function (in_btransid) {
        $.post(MW.moneyWatchURL,
            {job: 'B.ENTRY.EDIT', 'btransid': in_btransid, pu: MW.util.poisonURL()},
            function(data) {
                $('#transactionsrightedit').html(data);
                if (MW.activeRowId !== '') {
                    $('#' + MW.activeRowId).removeClass('activeinvrow');
                }
                MW.activeRowId = 'b' + in_btransid;
                $('#' + MW.activeRowId).addClass('activeinvrow');
                $('#transactionsrightedit').addClass('activeinveditmenu');
            }
        );
    },

    sendBankDelete: function (in_bacctid, in_btransid) {
        var r = confirm("Are you sure you want to delete MW transaction?");
        if (r === true) {
            $.post(MW.moneyWatchURL,
                {job: 'B.ENTRY.DELETE', 'btransid': in_btransid, pu: MW.util.poisonURL()},
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        // reload left side, reflecting the deletion
                        $.post(MW.moneyWatchURL,
                            {job: 'B.ACCOUNT.GET', 'bacctid': in_bacctid, pu: MW.util.poisonURL()},
                            function(data) {
                                $('#transactionslist').html(data);
                            }
                        );
                        // reload underneath
                        MW.comm.sendCommand('B.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            );
            return true;
        } else {
            return false;
        }
    },

    getBankAccount: function (in_bacctid) {
        $.post(MW.moneyWatchURL,
            {job: 'B.ACCOUNT.GET', 'bacctid': in_bacctid, pu: MW.util.poisonURL()},
            function(data) {
                $('#transactionslist').html(data);
                // clear any previous highlights
                $('#' + MW.activeRowId).removeClass('activeinvrow');
                $('#transactionsrightedit').removeClass('activeinveditmenu');
                $('#transactionsheaderinv').hide();
                $('#transactionsheaderbank').show();
                MW.yui.panelTransactions.show();
                $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
            }
        );
        $.post(MW.moneyWatchURL,
            {job: 'B.ENTRY.ADD', 'bacctid': in_bacctid, pu: MW.util.poisonURL()},
            function(data) {
                $('#transactionsrightedit').html(data);
            }
        );
    },

    cancelEdit: function (in_type, in_xacctid) {
        // unhighlight the selected row
        $('#' + MW.activeRowId).removeClass('activeinvrow');
        // unhighlight the right control box
        $('#transactionsrightedit').removeClass('activeinveditmenu');
        // reload the right side
        if (in_type == 'bank') {
            $.post(MW.moneyWatchURL,
                {job: 'B.ENTRY.ADD', 'bacctid': in_xacctid, pu: MW.util.poisonURL()},
                function(data) {
                    $('#transactionsrightedit').html(data);
                }
            );
        } else if (in_type == 'investment') {
            $.post(MW.moneyWatchURL,
                {job: 'I.ENTRY.ADD', 'ielectionid': in_xacctid, pu: MW.util.poisonURL()},
                function(data) {
                    $('#transactionsrightedit').html(data);
                }
            );
        }

    }
};


// ------------------------------------------------------------------
// [== MOVEMENT ==]
// ------------------------------------------------------------------
MW.move = {
    viewcurrent: 'investments',
    viewprevious: 'none',

    goTo: function ( whereto ) {
        if (whereto === 'investments') {
            $('#accttype-toggle1').addClass('active');
            $('#accttype-toggle2').removeClass('active');

            $('#rightcontent2').hide();
            $('#rightcontent1').show();
        } else if (whereto === 'bank') {
            $('#accttype-toggle2').addClass('active');
            $('#accttype-toggle1').removeClass('active');

            $('#rightcontent1').hide();
            $('#rightcontent2').show();
        }
    },

    back: function () {
        // close the level 2 view

        // load correct level 1 view
        // MW.move.goTo(MW.move.viewcurrent);
    }
};

// ------------------------------------------------------------------
// [== TIMER RELATED ==]
// ------------------------------------------------------------------
MW.timers = {
    laststockfetch: 0,

    startTimers: function () {
        setInterval(MW.timers.stockFetchTimer, 60000); // tick every minute
    },

    stockFetchTimer: function () {
        // fetch quotes every day at 6 PM local time
        var getdate = new Date();
        if (getdate.getDate() !== MW.timers.laststockfetch) { // day of the month, new day?
            // we didn't already do the stock fetch dance today
            if (MW.timers.laststockfetch === 0) {
                if( getdate.getHours() >= 18) {
                    // MW will be the one for today
                    MW.timers.laststockfetch = getdate.getDate();
                } else {
                    // runs now below, but we will need to run again later today
                    MW.timers.laststockfetch = -1;
                }
                MW.comm.sendCommand('U.UPDATEQUOTES');
            } else if (getdate.getHours() >= 18) { // 6 PM local time
                MW.timers.laststockfetch = getdate.getDate();
                MW.comm.sendCommand('U.UPDATEQUOTES');
            }
        }
    }
};


// ------------------------------------------------------------------
// [== UTILITIES ==]
// ------------------------------------------------------------------
MW.util = {
    // ------------------------------------------------------------------
    // poison part of the URL so that it doesn't cache
    // ------------------------------------------------------------------
    poisonURL: function () {
        return new Date().getTime();
    },
    // ------------------------------------------------------------------
    // converts number to $xx.xx format (readable, not for math)
    // ------------------------------------------------------------------
    formatCurrency: function (num) {
        if (typeof num != 'undefined') {
            var cents, sign;
            num = num.toString().replace(/\$|\,/g, '');
            if (isNaN(num)) num = "0";
            sign = (num == (num = Math.abs(num)));
            num = Math.floor(num * 100 + 0.50000000001);
            cents = num % 100;
            num = Math.floor(num / 100).toString();
            if (cents < 10) cents = "0" + cents;
            for (var i = 0; i < Math.floor((num.length - (1 + i)) / 3); i++)
            num = num.substring(0, num.length - (4 * i + 3)) + ',' + num.substring(num.length - (4 * i + 3));
            return (((sign) ? "" : "-") + "$" + num + '.' + cents);
        } else {
            return "$0.00";
        }
    },
    // ------------------------------------------------------------------
    // converts a number to a dollar (two decimals)  450.95 format
    // ------------------------------------------------------------------
    checkValueDecimals: function (in_obj, places) {
        in_obj.value = in_obj.value.toString().replace(/\$|\,/g, '');
        if (in_obj.value !== "" && !isNaN(in_obj.value)) {
            if ((in_obj.value * 1) >= 0) {
                in_obj.value = (in_obj.value * 1.0).toFixed(places);
            } else {
                in_obj.value = '';
            }
        } else {
            in_obj.value = '';
        }
    }
};


// -------  YUI STUFF
if (typeof (YUI) !== 'undefined') {

    MW.yui = {
        // YUI panels
        panelUniversal: null,
        panelTransactions: null,
        // make the YUI control close my way
        YUIcloseMarkup: '<span class="yui3-widget-button-wrapper"><a href="#" class="yui3-button yui3-button-close" onClick="MW.yui.utilClosePanel();"><span class="yui3-button-content"><span class="yui3-button-icon"></span></span></a></span>',

        utilClosePanel: function () {
            MW.yui.panelUniversal.hide();
            $('#paneluniversal-inner').html('');
        }
    };

    // YUI Components
    YUI({
         gallery: 'gallery-2011.06.01-20-18' // Last Gallery Build of this module
    }).use("panel", "dd-plugin", "autocomplete", "autocomplete-filters", "autocomplete-highlighters", "json", "json-parse", function(Y) {

        MW.yui.panelTransactions = new Y.Panel({
            srcNode: '#paneltransactions',
            width: 1200,
            centered: true,
            zIndex: 5,
            headerContent: "Transactions",
            plugins: [Y.Plugin.Drag],
            visible: false,
            render: true
        });

        MW.yui.panelUniversal = new Y.Panel({
            srcNode: '#paneluniversal',
            width: 420,
            centered: true,
            zIndex: 5,
            headerContent: "i'm all of the windoze",
            plugins: [Y.Plugin.Drag],
            visible: false,
            render: true
        });
    });
}
