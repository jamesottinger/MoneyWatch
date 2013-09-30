
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
        width: 1000,
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
    } else if (in_action === 'ACTION.IMPORTMENU') {
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

function sendCommand(in_job) {
    switch(in_job) {
        case 'I.SUMMARY.GET':
            jQuery.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    jQuery('#rightcontent1').html(data);
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
        case 'B.SUMMARY.GET':
            jQuery.post(moneyWatchX,
                {job: in_job, pu: poisonURL()},
                function(data) {
                    jQuery('#rightcontent2').html(data);
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
                    }
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
            jQuery('#transactionsleft').html(data);
            panelTransactions.show();
        }
    );
    //jQuery('#paneluniversal-inner').html('');
}

function getBankAccount(in_parentid) {
    jQuery.post(moneyWatchX,
        {job: 'B.ACCOUNT.GET', parentid: in_parentid, pu: poisonURL()},
        function(data) {
            jQuery('#transactionsleft').html(data);
            panelTransactions.show();
        }
    );
    //jQuery('#paneluniversal-inner').html('');
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
