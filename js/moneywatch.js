
//====================================================
// INIT
//====================================================
var panelAddBank, panelIntBulk, panelInvSettings, panelUniversal, panelTransactions; // global variables (YUI panels)
    
// YUI Components
YUI({
     gallery: 'gallery-2011.06.01-20-18' // Last Gallery Build of this module
}).use("panel", "dd-plugin", "autocomplete", "autocomplete-filters", "autocomplete-highlighters", "json", "json-parse", function(Y) {

    panelAddBank = new Y.Panel({
        srcNode: '#paneladdbank',
        width: 725,
        centered: true,
        zIndex: 5,
        headerContent: "Add New Bank Entry",
        plugins: [Y.Plugin.Drag],
        visible: false,
        render: true
    });

    panelIntBulk = new Y.Panel({
        srcNode: '#panelbulkinterest',
        width: 420,
        centered: true,
        zIndex: 5,
        headerContent: "Bulk Interest Entry",
        plugins: [Y.Plugin.Drag],
        visible: false,
        render: true
    });

    panelInvSettings = new Y.Panel({
        srcNode: '#panelinvestmentsettings',
        width: 420,
        centered: true,
        zIndex: 5,
        headerContent: "Investment Settings",
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

    Y.one('#autocategories').plug(Y.Plugin.AutoComplete, {
        resultFilters: 'phraseMatch',
        resultHighlighter: 'phraseMatch',
        source: 'php-bank-categories-generate.php?&callback=parseAuto'
    });  
    
    //  Accessing Yahoo Finance - http://yuilibrary.com/gallery/show/yql-finance
    var symbols = ["FSEMX", "FSTMX", "FTBFX", "VFINX", "VBINX", "VHDYX", "VWEHX", "VISVX", "VIVAX"];
   /*
    function display(container, prices) {
        var asset, content = "", c = Y.one(container);
 
        for (asset in prices) {
            if (prices.hasOwnProperty(asset)) {
                content += asset + " -> ";
                content += Y.JSON.stringify(prices[asset]);
                content += "<br />";
            }
        }
        c.setContent(content);    
    }
 
    Y.YQL.Finance.getHistoricalQuotes(symbols, function (prices) {
        display("#histQuotes", prices);
    }, {
        columns: ["Close", "Date"]
    });
 
    Y.YQL.Finance.getHistoricalQuotes(symbols, function (prices) {
        display("#histQuotes2", prices);
    }, {
        columns: ["Close", "Date"],
        frequency: "w",
        startDate: "2010-10-01",
        endDate: "2010-10-30"
    });
 
    Y.YQL.Finance.getQuotes(symbols, function (prices) {
        display("#quotes", prices);
    }, {
        columns: ["PreviousClose", "LastTradePriceOnly", "Change", "LastTradeDate", "Name"]
    });
    */

});

// JQuery Components
jQuery(function() {
    jQuery("#datepicker1").datepicker({ dateFormat: 'yy-mm-dd' });
    jQuery("#datepicker2").datepicker({ dateFormat: 'yy-mm-dd' });
});




//====================================================
// AJAX 
//====================================================
var moneyWatchX = '/x/moneywatch-relay.py';
var xmlHttp = false;
var requestType = "";
var overobj;
var activeInvRowId = '';

var YUIcloseMarkup = '<span class="yui3-widget-button-wrapper"><a href="#" class="yui3-button yui3-button-close" onClick="utilClosePanel();"><span class="yui3-button-content"><span class="yui3-button-icon"></span></span></a></span>';


function ajax_createXMLHttpRequest() {
    if(window.XMLHttpRequest) {
        xmlHttp = new XMLHttpRequest();
    }
    else if(window.ActiveXObject) {
        try {
            xmlHttp = new ActiveXObject("Msxml2.XMLHTTP");
        } catch(e) {
            try {
                xmlHttp = new ActiveXObject("Microsoft.XMLHTTP");
            } catch(e) {
                xmlHttp = false;
            } 
        }
    }
}

function ajax_handleStateChange()
{
    if(xmlHttp.readyState == 4) {
        if(xmlHttp.status == 200 || xmlHttp.status == 304) {
            
            if(requestType == "AJAX.BANK.GETTRANSACTIONS") {
                jQuery('#rightcontent').html(xmlHttp.responseText);
                // animate scroll to bottom
                jQuery('#rightfixed').stop().animate({ scrollTop: jQuery('#rightbottom').offset().top },1600);
            } else if(requestType == "AJAX.BANK.GETACCOUNTS") {
                jQuery('#bankaccounts').html(xmlHttp.responseText);
            } else if(requestType == "AJAX.INVESTMENT.GETACCOUNTS") {
                jQuery('#investmentaccounts').html(xmlHttp.responseText);
            } else if(requestType == "AJAX.BANK.MAKEBULKINTEREST") {
                jQuery('#bulkinterestinner').html(xmlHttp.responseText);
                panelIntBulk.show();
            } else if(requestType == "AJAX.INVESTMENT.MAKEEDITSETTINGS") {
                jQuery('#investmentsettingsinner').html(xmlHttp.responseText);
                panelInvSettings.show();
            } else if(requestType == "AJAX.BANK.MAKEBANKENTRY") {
                jQuery('#bankentryinner').html(xmlHttp.responseText);
                panelAddBank.show();
            } else if(requestType == "AJAX.ALL.GETACCOUNTS") {
                 jQuery('#rightcontent').html(xmlHttp.responseText);
            }
        }
    }
}

// ===========================================================
function runAction(in_action) {
    if (in_action === 'BANK.MAKEBULKINTEREST') {
        panelUniversal.set('width', 420);
        panelUniversal.set('headerContent', "Bulk Interest Entry" + YUIcloseMarkup);
        jQuery.post('/x/moneywatch-engine.py', {job: 'AJAX.INVESTMENT.GETSINGLETICKER', pu: utilPoisonURL()}, function(data) { jQuery('#paneluniversal-inner').html(data); panelUniversal.show(); });
    } else if (in_action === 'U.IMPORTFILE.EDIT') {
        panelUniversal.set('width', 420);
        panelUniversal.set('headerContent', "Import Menu" + YUIcloseMarkup);
        jQuery.post('/x/moneywatch-engine.py', {job: 'AJAX.IMPORTMENU', pu: utilPoisonURL()}, function(data) { jQuery('#paneluniversal-inner').html(data); panelUniversal.show(); });
    }
}

function runActionInv(in_inv) {
    jQuery.post('/x/moneywatch-engine.py', {job: 'AJAX.INV.GETTRANSACTIONS', ticker: in_inv, pu: utilPoisonURL()}, function(data) { jQuery('#rightcontent').html(data); });
}


function utilClosePanel() {
    panelUniversal.hide();
    jQuery('#paneluniversal-inner').html('');
}

function poisonURL() {
    return new Date().getTime();
}


/*
-- I.SUMMARY.GET
-- I.ELECTION.GET
I.BULKADD.EDIT
I.BULKADD.SAVE
I.TICKERS.EDIT
I.TICKERS.SAVE
I.ENTRY.ADD
I.ENTRY.EDIT
I.ENTRY.SAVE
I.ENTRY.DEL

B.SUMMARY.GET
B.ACCOUNT.GET
B.BULKADD.EDIT
B.BULKADD.SAVE
B.BULKINT.EDIT
B.BULKINT.SAVE
B.MYACCT.ON
B.MYACCT.OFF
B.ENTRY.ADD
B.ENTRY.EDIT
B.ENTRY.SAVE
B.ENTRY.DEL

-- U.IMPORTFILE.EDIT
-- U.IMPORTFILE.SAVE
-- U.UPDATEQUOTES
*/

// ===========================================================

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
            var thisticker = jQuery('#ieditsingle-ticker').val();
            jQuery.post(moneyWatchX,
                formdata,
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        jQuery('#' + activeInvRowId).removeClass('activeinvrow');
                        jQuery.post(moneyWatchX,
                            {job: 'I.ELECTION.GET', ticker: thisticker, pu: poisonURL()},
                            function(data) { 
                                jQuery('#transactionslist').html(data);
                                jQuery("#transactionslist").scrollTop(jQuery("#transactionslist")[0].scrollHeight);
                            }
                        );
                        jQuery.post(moneyWatchX,
                            {job: 'I.ENTRY.ADD', ticker: thisticker, pu: poisonURL()},
                            function(data) { 
                                jQuery('#transactionsrightedit').html(data);
                            }
                        );
                        // reload underneath
                        sendCommand('I.SUMMARY.GET');
                    } else {
                        alert(data);
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
                        alert(data);
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
                        alert(data);
                    }
                }
            );
            break;
        case 'B.ENTRY.EDITSAVE':
        case 'B.ENTRY.ADDSAVE':
            var formdata = jQuery('#beditsingle').serialize();
            var thispid = jQuery('#beditsingle-thisparentid').val();
            jQuery.post(moneyWatchX,
                formdata,
                function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        jQuery('#' + activeInvRowId).removeClass('activebankrow');
                        jQuery.post(moneyWatchX,
                            {job: 'B.ACCOUNT.GET', parentid: thispid, pu: poisonURL()},
                            function(data) { 
                                jQuery('#transactionslist').html(data);
                                jQuery("#transactionslist").scrollTop(jQuery("#transactionslist")[0].scrollHeight);
                            }
                        );
                        jQuery.post(moneyWatchX,
                            {job: 'B.ENTRY.ADD', bankacctid: thispid, pu: poisonURL()},
                            function(data) { 
                                jQuery('#transactionsrightedit').html(data);
                            }
                        );
                        // reload underneath
                        sendCommand('B.SUMMARY.GET');
                    } else {
                        alert(data);
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
                        alert(data);
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
                        alert(data);
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

function getInvElection(in_ticker) {
    jQuery.post(moneyWatchX,
        {job: 'I.ELECTION.GET', ticker: in_ticker, pu: poisonURL()},
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
        {job: 'I.ENTRY.ADD', ticker: in_ticker, pu: poisonURL()},
        function(data) { 
            jQuery('#transactionsrightedit').html(data);
        }
    );
    jQuery.post(moneyWatchX,
        {job: 'I.ENTRY.CHART', ticker: in_ticker, pu: poisonURL()},
        function(data) { 
            jQuery('#transactionsrightchart').html(data);
        }
    );
    //jQuery('#paneluniversal-inner').html('');
}

function getInvElectionEdit(in_ticker, in_transid) {
    jQuery.post(moneyWatchX,
        {job: 'I.ENTRY.EDIT', ticker: in_ticker, transid: in_transid, pu: poisonURL()},
        function(data) { 
            jQuery('#transactionsrightedit').html(data);
            if (activeInvRowId != '') {
                jQuery('#' + activeInvRowId).removeClass('activeinvrow');
            }
            activeInvRowId = in_ticker + in_transid;
            jQuery('#' + activeInvRowId).addClass('activeinvrow');
            jQuery('#transactionsrightedit').addClass('activeinveditmenu');
        }
    );
}

function getInvGraph(in_ticker) {
    panelUniversal.set('width', 950);
    panelUniversal.set('headerContent', "Investment - Graph" + YUIcloseMarkup);
    jQuery.post(moneyWatchX,
        {job: 'I.GRAPH.GET', ticker: in_ticker, pu: poisonURL()},
        function(data) { 
            jQuery('#paneluniversal-inner').html(data);
            panelUniversal.show();
        }
    );
}

function sendInvDelete(in_ticker, in_transid) {
    var r = confirm("Are you sure you want to delete this transaction?");
    if (r == true) {
        jQuery.post(moneyWatchX,
            {job: 'I.ENTRY.DELETE', transid: in_transid, pu: poisonURL()},
            function(data) {
                data = data.replace(/\n/gm, '');
                if (data == 'ok') {
                    // reload left side, reflecting the deletion
                    jQuery.post(moneyWatchX,
                        {job: 'I.ELECTION.GET', ticker: in_ticker, pu: poisonURL()},
                        function(data) {
                            jQuery('#transactionslist').html(data);
                        }
                    );
                    // reload underneath
                    sendCommand('I.SUMMARY.GET');
                } else {
                    alert(data);
                }
            }
        );
    } else {
        return false;
    }
}

function getBankEdit(in_transid) {
    jQuery.post(moneyWatchX,
        {job: 'B.ENTRY.EDIT', transid: in_transid, pu: poisonURL()},
        function(data) {
            jQuery('#transactionsrightedit').html(data);
            if (activeInvRowId != '') {
                jQuery('#' + activeInvRowId).removeClass('activeinvrow');
            }
            activeInvRowId = 'b' + in_transid;
            jQuery('#' + activeInvRowId).addClass('activeinvrow');
            jQuery('#transactionsrightedit').addClass('activeinveditmenu');
        }
    );
}

function sendBankDelete(in_parentid, in_transid) {
    var r = confirm("Are you sure you want to delete this transaction?");
    if (r == true) {
        jQuery.post(moneyWatchX,
            {job: 'B.ENTRY.DELETE', transid: in_transid, pu: poisonURL()},
            function(data) {
                data = data.replace(/\n/gm, '');
                if (data == 'ok') {
                    // reload left side, reflecting the deletion
                    jQuery.post(moneyWatchX,
                        {job: 'B.ACCOUNT.GET', parentid: in_parentid, pu: poisonURL()},
                        function(data) { 
                            jQuery('#transactionslist').html(data);
                        }
                    );
                    // reload underneath
                    sendCommand('B.SUMMARY.GET');
                } else {
                    alert(data);
                }
            }
        );
    } else {
        return false;
    }
}


function getBankAccount(in_parentid) {
    jQuery.post(moneyWatchX,
        {job: 'B.ACCOUNT.GET', parentid: in_parentid, pu: poisonURL()},
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
        {job: 'B.ENTRY.ADD', bankacctid: in_parentid, pu: poisonURL()},
        function(data) { 
            jQuery('#transactionsrightedit').html(data);
        }
    );
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


function post_form(formobj) {
    var datatogo = jQuery('#' + formobj.name).serializeObject();
    if (formobj.name == 'I.BLAH.EDIT') {
        var request = jQuery.ajax({
            url: "/x/moneywatch-relay.py",
           type: "POST",
           data: datatogo,
           dataType: "html"
        });
        request.done(function(indata) {
            jQuery('#paneluniversal-inner').html(indata);
            panelUniversal.show();
        });
        //request.fail(function( jqXHR, textStatus ) {
        //    alert( "Request failed: " + textStatus );
        //});
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


function checkValueDecimals(in_obj, places) {
    // converts a number to a dollar (two decimals)  450.95 format
    if (in_obj.value != "" && !isNaN(in_obj.value)) {
        if ((in_obj.value * 1) > 0) {
            in_obj.value = (in_obj.value * 1.0).toFixed(places);
        } else {
            in_obj.value = '';
        }
    } else {
        in_obj.value = '';
    }
}
