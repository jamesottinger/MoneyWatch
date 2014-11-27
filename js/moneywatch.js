//===============================================================================
// Copyright (c) 2014, James Ottinger. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// MoneyWatch - https://github.com/jamesottinger/moneywatch
//===============================================================================
var moneyWatchX = '/x/moneywatch-relay.py';
//var moneyWatchX = '/devmoney-x/moneywatch-relay.py';
var activeInvRowId = '';

var panelUniversal, panelTransactions; // global variables (YUI panels)

// YUI Components
YUI({
     gallery: 'gallery-2011.06.01-20-18' // Last Gallery Build of this module
}).use("panel", "dd-plugin", "autocomplete", "autocomplete-filters", "autocomplete-highlighters", "json", "json-parse", function(Y) {


    panelTransactions = new Y.Panel({
        srcNode: '#paneltransactions',
        width: 1200,
        centered: true,
        zIndex: 5,
        headerContent: "Transactions",
        plugins: [Y.Plugin.Drag],
        visible: false,
        render: true
    });

    panelUniversal = new Y.Panel({
        srcNode: '#paneluniversal',
        width: 420,
        centered: true,
        zIndex: 5,
        headerContent: "hiya",
        plugins: [Y.Plugin.Drag],
        visible: false,
        render: true
    });

});

// make the YUI control close my way
var YUIcloseMarkup = '<span class="yui3-widget-button-wrapper"><a href="#" class="yui3-button yui3-button-close" onClick="utilClosePanel();"><span class="yui3-button-content"><span class="yui3-button-icon"></span></span></a></span>';

function utilClosePanel() {
    panelUniversal.hide();
    jQuery('#paneluniversal-inner').html('');
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

function init_loadaccounts() {
    sendCommand('I.SUMMARY.GET');
    sendCommand('B.SUMMARY.GET');
}
function calcNetWorth() {
    var nw = formatCurrency((jQuery('#networth-investments').val() * 1.00) + (jQuery('#networth-banks').val() * 1.00));
    jQuery('#sum-worth-inv').html(formatCurrency(jQuery('#networth-investments').val()));
    jQuery('#sum-worth-bank').html(formatCurrency(jQuery('#networth-banks').val()));
    jQuery('#sum-worth-all').html(nw);
}

function sendCommand(in_job) {
    switch(in_job) {
        case 'I.SUMMARY.GET':
            jQuery.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    jQuery('#rightcontent1').html(data);
                    calcNetWorth();
                }
            );
            break;
        case 'I.BULKADD.EDIT':
            panelUniversal.set('width', 950);
            panelUniversal.set('headerContent', "Investments - Bulk Add" + YUIcloseMarkup);
            jQuery.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    jQuery('#paneluniversal-inner').html(data);
                    panelUniversal.show();
                }
            );
            break;
        case 'I.BULKADD.SAVE':
            var formdata = jQuery('#ibulkedit').serialize();
            jQuery.post(moneyWatchX,
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
            var formdata = jQuery('#ieditsingle').serialize();
            var ielectionid = jQuery('#ieditsingle-ielectionid').val();
            jQuery.post(moneyWatchX,
                formdata,
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        jQuery('#' + activeInvRowId).removeClass('activeinvrow');
                        jQuery.post(moneyWatchX,
                            {job: 'I.ELECTION.GET', 'ielectionid': ielectionid, pu: poisonURL()},
                            function(data) {
                                jQuery('#transactionslist').html(data);
                                jQuery("#transactionslist").scrollTop(jQuery("#transactionslist")[0].scrollHeight);
                            }
                        );
                        jQuery.post(moneyWatchX,
                            {job: 'I.ENTRY.ADD', 'ielectionid': ielectionid, pu: poisonURL()},
                            function(data) {
                                jQuery('#transactionsrightedit').html(data);
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
            jQuery.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    jQuery('#rightcontent2').html(data);
                    calcNetWorth();
                }
            );
            break;
        case 'B.BULKINTEREST.EDIT':
            panelUniversal.set('width', 350);
            panelUniversal.set('headerContent', "Bank - Bulk Interest" + YUIcloseMarkup);
            jQuery.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    jQuery('#paneluniversal-inner').html(data);
                    panelUniversal.show();
                }
            );
            break;
        case 'B.BULKINTEREST.SAVE':
            var formdata = jQuery('#bbulkinterestedit').serialize();
            jQuery.post(moneyWatchX,
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
            jQuery.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    jQuery('#paneluniversal-inner').html(data);
                    panelUniversal.show();
                }
            );
            break;
        case 'B.BULKBILLS.SAVE':
            var formdata = jQuery('#bbulkbillsedit').serialize();
            jQuery.post(moneyWatchX,
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
            var formdata = jQuery('#beditsingle').serialize();
            var bacctid = jQuery('#beditsingle-bacctid').val();
            jQuery.post(moneyWatchX,
                formdata,
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        jQuery('#' + activeInvRowId).removeClass('activebankrow');
                        jQuery.post(moneyWatchX,
                            {job: 'B.ACCOUNT.GET', 'bacctid': bacctid, pu: poisonURL()},
                            function(data) {
                                jQuery('#transactionslist').html(data);
                                jQuery("#transactionslist").scrollTop(jQuery("#transactionslist")[0].scrollHeight);
                            }
                        );
                        jQuery.post(moneyWatchX,
                            {job: 'B.ENTRY.ADD', 'bacctid': bacctid, pu: poisonURL()},
                            function(data) {
                                jQuery('#transactionsrightedit').html(data);
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
            jQuery.post(moneyWatchX,
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
            jQuery.post(moneyWatchX,
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
            jQuery.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    jQuery('#paneluniversal-inner').html(data);
                    panelUniversal.show();
                }
            );
            break;
        default:
    }
}

function getInvElection(in_ielectionid) {
    jQuery.post(moneyWatchX,
        {job: 'I.ELECTION.GET', 'ielectionid': in_ielectionid, pu: poisonURL()},
        function(data) {
            jQuery('#transactionslist').html(data);
            // clear any previous highlights
            jQuery('#' + activeInvRowId).removeClass('activeinvrow');
            jQuery('#transactionsrightedit').removeClass('activeinveditmenu');
            jQuery('#transactionsheaderinv').show();
            jQuery('#transactionsheaderbank').hide();
            panelTransactions.show();
            // animate scroll to bottom
            // jQuery('#transactionslist').stop().animate({ scrollTop: jQuery('#scrollmeinv').offset().top },120);
            jQuery("#transactionslist").scrollTop(jQuery("#transactionslist")[0].scrollHeight);
        }
    );
    jQuery.post(moneyWatchX,
        {job: 'I.ENTRY.ADD', 'ielectionid': in_ielectionid, pu: poisonURL()},
        function(data) {
            jQuery('#transactionsrightedit').html(data);
        }
    );
    jQuery.post(moneyWatchX,
        {job: 'I.ENTRY.CHART', 'ielectionid': in_ielectionid, pu: poisonURL()},
        function(data) {
            jQuery('#transactionsrightchart').html(data);
        }
    );
    //jQuery('#paneluniversal-inner').html('');
}

function getInvElectionEdit(in_ielectionid, in_itransid) {
    jQuery.post(moneyWatchX,
        {job: 'I.ENTRY.EDIT', 'ielectionid': in_ielectionid, 'itransid': in_itransid, pu: poisonURL()},
        function(data) {
            jQuery('#transactionsrightedit').html(data);
            if (activeInvRowId != '') {
                jQuery('#' + activeInvRowId).removeClass('activeinvrow');
            }
            activeInvRowId = in_ielectionid + in_itransid;
            jQuery('#' + activeInvRowId).addClass('activeinvrow');
            jQuery('#transactionsrightedit').addClass('activeinveditmenu');
        }
    );
}

function getInvGraph(in_ielectionid) {
    panelUniversal.set('width', 950);
    panelUniversal.set('headerContent', "Investment - Graph" + YUIcloseMarkup);
    jQuery.post(moneyWatchX,
        {job: 'I.GRAPH.GET', 'ielectionid': in_ielectionid, pu: poisonURL()},
        function(data) {
            jQuery('#paneluniversal-inner').html(data);
            panelUniversal.show();
        }
    );
}

function sendInvDelete(in_ielectionid, in_itransid) {
    var r = confirm("Are you sure you want to delete this transaction?");
    if (r == true) {
        jQuery.post(moneyWatchX,
            {job: 'I.ENTRY.DELETE', 'itransid': in_itransid, pu: poisonURL()},
            function(data) {
                data = data.replace(/\n/gm, '');
                if (data == 'ok') {
                    // reload left side, reflecting the deletion
                    jQuery.post(moneyWatchX,
                        {job: 'I.ELECTION.GET', 'ielectionid': in_ielectionid, pu: poisonURL()},
                        function(data) {
                            jQuery('#transactionslist').html(data);
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
    jQuery.post(moneyWatchX,
        {job: 'B.ENTRY.EDIT', 'btransid': in_btransid, pu: poisonURL()},
        function(data) {
            jQuery('#transactionsrightedit').html(data);
            if (activeInvRowId != '') {
                jQuery('#' + activeInvRowId).removeClass('activeinvrow');
            }
            activeInvRowId = 'b' + in_btransid;
            jQuery('#' + activeInvRowId).addClass('activeinvrow');
            jQuery('#transactionsrightedit').addClass('activeinveditmenu');
        }
    );
}

function sendBankDelete(in_bacctid, in_btransid) {
    var r = confirm("Are you sure you want to delete this transaction?");
    if (r == true) {
        jQuery.post(moneyWatchX,
            {job: 'B.ENTRY.DELETE', 'btransid': in_btransid, pu: poisonURL()},
            function(data) {
                data = data.replace(/\n/gm, '');
                if (data == 'ok') {
                    // reload left side, reflecting the deletion
                    jQuery.post(moneyWatchX,
                        {job: 'B.ACCOUNT.GET', 'bacctid': in_bacctid, pu: poisonURL()},
                        function(data) {
                            jQuery('#transactionslist').html(data);
                        }
                    );
                    // reload underneath
                    sendCommand('B.SUMMARY.GET');
                } else {
                    alert(data.substr(0,500));
                }
            }
        );
    } else {
        return false;
    }
}

function getBankAccount(in_bacctid) {
    jQuery.post(moneyWatchX,
        {job: 'B.ACCOUNT.GET', 'bacctid': in_bacctid, pu: poisonURL()},
        function(data) {
            jQuery('#transactionslist').html(data);
            // clear any previous highlights
            jQuery('#' + activeInvRowId).removeClass('activeinvrow');
            jQuery('#transactionsrightedit').removeClass('activeinveditmenu');
            jQuery('#transactionsheaderinv').hide();
            jQuery('#transactionsheaderbank').show();
            panelTransactions.show();
            jQuery("#transactionslist").scrollTop(jQuery("#transactionslist")[0].scrollHeight);
        }
    );
    jQuery.post(moneyWatchX,
        {job: 'B.ENTRY.ADD', 'bacctid': in_bacctid, pu: poisonURL()},
        function(data) {
            jQuery('#transactionsrightedit').html(data);
        }
    );
}

function cancelEdit(in_type, in_xacctid) {
    // unhighlight the selected row
    jQuery('#' + activeInvRowId).removeClass('activeinvrow');
    // unhighlight the right control box
    jQuery('#transactionsrightedit').removeClass('activeinveditmenu');
    // reload the right side
    if (in_type == 'bank') {
        jQuery.post(moneyWatchX,
            {job: 'B.ENTRY.ADD', 'bacctid': in_xacctid, pu: poisonURL()},
            function(data) {
                jQuery('#transactionsrightedit').html(data);
            }
        );
    } else if (in_type == 'investment') {
        jQuery.post(moneyWatchX,
            {job: 'I.ENTRY.ADD', 'ielectionid': in_xacctid, pu: poisonURL()},
            function(data) {
                jQuery('#transactionsrightedit').html(data);
            }
        );
    }

}

function addbank_typechange() {
    var selectedtype;
    selectedtype = jQuery('#addbanktype').val();

    if(selectedtype === "transfer") {
         jQuery('#hidetransfer').show();
         jQuery('#addbanknum').val('TRANS');
         jQuery('#autocategories').hide();
    } else {
        // withdraw|deposit
        jQuery('#hidetransfer').hide();
        jQuery('#addbanknum').val('');
        jQuery('#autocategories').show();
    }
}

function addbank_payeechange() {
    var textboxpayee;
    textboxpayee = jQuery('#addbackpayee').val();

    if(textboxpayee.toUpperCase() === "INTEREST") {
         jQuery('#addbankcategory').val('Interest');
         jQuery('#addbanknum').val('INT');
    } else {
         // withdraw|deposit
         //jQuery('#addbanktransaccount').hide();
    }
}

// ==== UTILITY

function poisonURL() {
    return new Date().getTime();
}

function formatCurrency(num) {
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
    }
}

function checkValueDecimals(in_obj, places) {
    // converts a number to a dollar (two decimals)  450.95 format
    in_obj.value = in_obj.value.toString().replace(/\$|\,/g, '');
    if (in_obj.value != "" && !isNaN(in_obj.value)) {
        if ((in_obj.value * 1) >= 0) {
            in_obj.value = (in_obj.value * 1.0).toFixed(places);
        } else {
            in_obj.value = '';
        }
    } else {
        in_obj.value = '';
    }
}
