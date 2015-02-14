//===============================================================================
// Copyright (c) 2014, James Ottinger. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// MoneyWatch - https://github.com/jamesottinger/moneywatch
//===============================================================================
var MW = MW || {};



var moneyWatchX = '/x/moneywatch-relay.py';
//var moneyWatchX = '/devmoney-x/moneywatch-relay.py';
var activeInvRowId = '';
var g_laststockfetch = 0;

var panelUniversal, panelTransactions; // global variables (YUI panels)



// make the YUI control close my way
var YUIcloseMarkup = '<span class="yui3-widget-button-wrapper"><a href="#" class="yui3-button yui3-button-close" onClick="utilClosePanel();"><span class="yui3-button-content"><span class="yui3-button-icon"></span></span></a></span>';

function utilClosePanel() {
    panelUniversal.hide();
    $('#paneluniversal-inner').html('');
}

/*
===========================================================
CALL LIST:

I.SUMMARY.GET
I.ELECTION.GET
I.BULKADD.EDIT
I.BULKADD.SAVE
*- I.TICKERS.EDIT
*- I.TICKERS.SAVE
I.ENTRY.ADD
I.ENTRY.EDIT
I.ENTRY.SAVE
I.ENTRY.DEL
I.GRAPH.GET

B.SUMMARY.GET
B.ACCOUNT.GET
B.BULKADD.EDIT
B.BULKADD.SAVE
B.BULKINT.EDIT
B.BULKINT.SAVE
*- B.MYACCT.ON
*- B.MYACCT.OFF
B.ENTRY.ADD
B.ENTRY.EDIT
B.ENTRY.SAVE
B.ENTRY.DEL

*- U.IMPORTFILE.EDIT
*- U.IMPORTFILE.SAVE
U.UPDATEQUOTES
===========================================================
*/

MW.init = function () {
    this.sendCommand('I.SUMMARY.GET');
    this.sendCommand('B.SUMMARY.GET');
    this.sendCommand('U.LINKS.GET');
    setInterval(this.stockFetchTimer, 60000); // tick every minute
}

MW.calcNetWorth = function () {
    var nw = this.util.formatCurrency(($('#networth-investments').val() * 1.00) + ($('#networth-banks').val() * 1.00));
    $('#sum-worth-inv').html(formatCurrency($('#networth-investments').val()));
    $('#sum-worth-bank').html(formatCurrency($('#networth-banks').val()));
    $('#sum-worth-all').html(nw);
}

MW.sendCommand = function (in_job) {
    var formdata;
    switch(in_job) {
        case 'I.SUMMARY.GET':
            $.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    $('#rightcontent1').html(data);
                    this.calcNetWorth();
                }
            );
            break;
        case 'I.BULKADD.EDIT':
            panelUniversal.set('width', 950);
            panelUniversal.set('headerContent', "Investments - Bulk Add" + YUIcloseMarkup);
            $.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    $('#paneluniversal-inner').html(data);
                    panelUniversal.show();
                }
            );
            break;
        case 'I.BULKADD.SAVE':
            formdata = $('#ibulkedit').serialize();
            $.post(moneyWatchX,
                formdata,
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        panelUniversal.hide();
                        sendCommand('I.SUMMARY.GET');
                        sendCommand('B.SUMMARY.GET');
                    }
                }
            );
            break;
        case 'I.ENTRY.EDITSAVE':
        case 'I.ENTRY.ADDSAVE':
            formdata = $('#ieditsingle').serialize();
            var ielectionid = $('#ieditsingle-ielectionid').val();
            $.post(moneyWatchX,
                formdata,
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        $('#' + activeInvRowId).removeClass('activeinvrow');
                        $.post(moneyWatchX,
                            {job: 'I.ELECTION.GET', 'ielectionid': ielectionid, pu: poisonURL()},
                            function(data) {
                                $('#transactionslist').html(data);
                                $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
                            }
                        );
                        $.post(moneyWatchX,
                            {job: 'I.ENTRY.ADD', 'ielectionid': ielectionid, pu: poisonURL()},
                            function(data) {
                                $('#transactionsrightedit').html(data);
                            }
                        );
                        // reload underneath
                        sendCommand('I.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            );
            break;
        case 'B.SUMMARY.GET':
            $.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    $('#rightcontent2').html(data);
                    this.calcNetWorth();
                }
            );
            break;
        case 'B.BULKINTEREST.EDIT':
            panelUniversal.set('width', 350);
            panelUniversal.set('headerContent', "Bank - Bulk Interest" + YUIcloseMarkup);
            $.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    $('#paneluniversal-inner').html(data);
                    panelUniversal.show();
                }
            );
            break;
        case 'B.BULKINTEREST.SAVE':
            formdata = $('#bbulkinterestedit').serialize();
            $.post(moneyWatchX,
                formdata,
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        panelUniversal.hide();
                        sendCommand('I.SUMMARY.GET');
                        sendCommand('B.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            );
            break;
        case 'B.BULKBILLS.EDIT':
            panelUniversal.set('width', 750);
            panelUniversal.set('headerContent', "Bank - Bulk Bills" + YUIcloseMarkup);
            $.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    $('#paneluniversal-inner').html(data);
                    panelUniversal.show();
                }
            );
            break;
        case 'B.BULKBILLS.SAVE':
            formdata = $('#bbulkbillsedit').serialize();
            $.post(moneyWatchX,
                formdata,
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        panelUniversal.hide();
                        sendCommand('I.SUMMARY.GET');
                        sendCommand('B.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            );
            break;
        case 'B.ENTRY.EDITSAVE':
        case 'B.ENTRY.ADDSAVE':
            var bacctid = $('#beditsingle-bacctid').val();
            formdata = $('#beditsingle').serialize();
            $.post(moneyWatchX,
                formdata,
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        $('#' + activeInvRowId).removeClass('activebankrow');
                        $.post(moneyWatchX,
                            {job: 'B.ACCOUNT.GET', 'bacctid': bacctid, pu: poisonURL()},
                            function(data) {
                                $('#transactionslist').html(data);
                                $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
                            }
                        );
                        $.post(moneyWatchX,
                            {job: 'B.ENTRY.ADD', 'bacctid': bacctid, pu: poisonURL()},
                            function(data) {
                                $('#transactionsrightedit').html(data);
                            }
                        );
                        // reload underneath
                        sendCommand('B.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            );
            break;
        case 'U.UPDATEQUOTES':
            $.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        sendCommand('I.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            );
            break;
        case 'U.UPDATEBANKTOTALS':
            $.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        sendCommand('B.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            );
            break;
        case 'U.IMPORTFILE.EDIT':
            panelUniversal.set('width', 420);
            panelUniversal.set('headerContent', "Import Menu" + YUIcloseMarkup);
            $.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    $('#paneluniversal-inner').html(data);
                    panelUniversal.show();
                }
            );
            break;
        case 'U.LINKS.GET':
            $.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    $('#ui-links').html(data);
                }
            );
            break;
        default:
    }
}

function getInvElection(in_ielectionid) {
    $.post(moneyWatchX,
        {job: 'I.ELECTION.GET', 'ielectionid': in_ielectionid, pu: poisonURL()},
        function(data) {
            $('#transactionslist').html(data);
            // clear any previous highlights
            $('#' + activeInvRowId).removeClass('activeinvrow');
            $('#transactionsrightedit').removeClass('activeinveditmenu');
            $('#transactionsheaderinv').show();
            $('#transactionsheaderbank').hide();
            panelTransactions.show();
            // animate scroll to bottom
            // $('#transactionslist').stop().animate({ scrollTop: $('#scrollmeinv').offset().top },120);
            $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
        }
    );
    $.post(moneyWatchX,
        {job: 'I.ENTRY.ADD', 'ielectionid': in_ielectionid, pu: poisonURL()},
        function(data) {
            $('#transactionsrightedit').html(data);
        }
    );
    $.post(moneyWatchX,
        {job: 'I.ENTRY.CHART', 'ielectionid': in_ielectionid, pu: poisonURL()},
        function(data) {
            $('#transactionsrightchart').html(data);
        }
    );
    //$('#paneluniversal-inner').html('');
}

function getInvElectionEdit(in_ielectionid, in_itransid) {
    $.post(moneyWatchX,
        {job: 'I.ENTRY.EDIT', 'ielectionid': in_ielectionid, 'itransid': in_itransid, pu: poisonURL()},
        function(data) {
            $('#transactionsrightedit').html(data);
            if (activeInvRowId !== '') {
                $('#' + activeInvRowId).removeClass('activeinvrow');
            }
            activeInvRowId = in_ielectionid + in_itransid;
            $('#' + activeInvRowId).addClass('activeinvrow');
            $('#transactionsrightedit').addClass('activeinveditmenu');
        }
    );
}

function getInvGraph(in_ielectionid) {
    panelUniversal.set('width', 950);
    panelUniversal.set('headerContent', "Investment - Graph" + YUIcloseMarkup);
    $.post(moneyWatchX,
        {job: 'I.GRAPH.GET', 'ielectionid': in_ielectionid, pu: poisonURL()},
        function(data) {
            $('#paneluniversal-inner').html(data);
            panelUniversal.show();
        }
    );
}

function sendInvDelete(in_ielectionid, in_itransid) {
    var r = confirm("Are you sure you want to delete this transaction?");
    if (r === true) {
        $.post(moneyWatchX,
            {job: 'I.ENTRY.DELETE', 'itransid': in_itransid, pu: poisonURL()},
            function(data) {
                data = data.replace(/\n/gm, '');
                if (data == 'ok') {
                    // reload left side, reflecting the deletion
                    $.post(moneyWatchX,
                        {job: 'I.ELECTION.GET', 'ielectionid': in_ielectionid, pu: poisonURL()},
                        function(data) {
                            $('#transactionslist').html(data);
                        }
                    );
                    // reload underneath
                    sendCommand('I.SUMMARY.GET');
                } else {
                    alert(data.substr(0,500));
                }
            }
        );
    } else {
        return false;
    }
}

function getBankEdit(in_btransid) {
    $.post(moneyWatchX,
        {job: 'B.ENTRY.EDIT', 'btransid': in_btransid, pu: poisonURL()},
        function(data) {
            $('#transactionsrightedit').html(data);
            if (activeInvRowId !== '') {
                $('#' + activeInvRowId).removeClass('activeinvrow');
            }
            activeInvRowId = 'b' + in_btransid;
            $('#' + activeInvRowId).addClass('activeinvrow');
            $('#transactionsrightedit').addClass('activeinveditmenu');
        }
    );
}

function sendBankDelete(in_bacctid, in_btransid) {
    var r = confirm("Are you sure you want to delete this transaction?");
    if (r === true) {
        $.post(moneyWatchX,
            {job: 'B.ENTRY.DELETE', 'btransid': in_btransid, pu: poisonURL()},
            function(data) {
                data = data.replace(/\n/gm, '');
                if (data == 'ok') {
                    // reload left side, reflecting the deletion
                    $.post(moneyWatchX,
                        {job: 'B.ACCOUNT.GET', 'bacctid': in_bacctid, pu: poisonURL()},
                        function(data) {
                            $('#transactionslist').html(data);
                        }
                    );
                    // reload underneath
                    sendCommand('B.SUMMARY.GET');
                } else {
                    alert(data.substr(0,500));
                }
            }
        );
        return true;
    } else {
        return false;
    }
}

function getBankAccount(in_bacctid) {
    $.post(moneyWatchX,
        {job: 'B.ACCOUNT.GET', 'bacctid': in_bacctid, pu: poisonURL()},
        function(data) {
            $('#transactionslist').html(data);
            // clear any previous highlights
            $('#' + activeInvRowId).removeClass('activeinvrow');
            $('#transactionsrightedit').removeClass('activeinveditmenu');
            $('#transactionsheaderinv').hide();
            $('#transactionsheaderbank').show();
            panelTransactions.show();
            $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
        }
    );
    $.post(moneyWatchX,
        {job: 'B.ENTRY.ADD', 'bacctid': in_bacctid, pu: poisonURL()},
        function(data) {
            $('#transactionsrightedit').html(data);
        }
    );
}

function cancelEdit(in_type, in_xacctid) {
    // unhighlight the selected row
    $('#' + activeInvRowId).removeClass('activeinvrow');
    // unhighlight the right control box
    $('#transactionsrightedit').removeClass('activeinveditmenu');
    // reload the right side
    if (in_type == 'bank') {
        $.post(moneyWatchX,
            {job: 'B.ENTRY.ADD', 'bacctid': in_xacctid, pu: poisonURL()},
            function(data) {
                $('#transactionsrightedit').html(data);
            }
        );
    } else if (in_type == 'investment') {
        $.post(moneyWatchX,
            {job: 'I.ENTRY.ADD', 'ielectionid': in_xacctid, pu: poisonURL()},
            function(data) {
                $('#transactionsrightedit').html(data);
            }
        );
    }

}

function addbank_typechange() {
    var selectedtype;
    selectedtype = $('#addbanktype').val();

    if(selectedtype === "transfer") {
         $('#hidetransfer').show();
         $('#addbanknum').val('TRANS');
         $('#autocategories').hide();
    } else {
        // withdraw|deposit
        $('#hidetransfer').hide();
        $('#addbanknum').val('');
        $('#autocategories').show();
    }
}


// ------------------------------------------------------------------
// [== TIMER RELATED ==]
// ------------------------------------------------------------------
MW.timers = {
    laststockfetch: 0,

    startTimers: function () {
        setInterval(MW.stockFetchTimer, 60000); // tick every minute
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
