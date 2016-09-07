//===============================================================================
// Copyright (c) 2016, James Ottinger. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// MoneyWatch - https://github.com/jamesottinger/moneywatch
//===============================================================================
var MW = MW || {};

MW = {
    moneyWatchURL: '.',
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
                });
                break;
            case 'I.BULKADD.EDIT':
                $.ajax({
                    url: urlpost,
                    data: {job: in_job},
                    success: function(data) {
                        MW.modaluniversal.show("Investments - Bulk Add", "950", data);
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
                            MW.modaluniversal.hide();
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
                $.ajax({
                    type: 'POST',
                    url: urlpost,
                    data: formdata,
                    success: function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            $('#' + MW.activeRowId).removeClass('activeinvrow');
                            $.ajax({
                                url: MW.moneyWatchURL + '/action/I.ELECTION.GET',
                                data: {'ielectionid': ielectionid},
                                success: function(data) {
                                    $('#transactionslist').html(data);
                                    $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
                                }
                            });
                            $.ajax({
                                url: MW.moneyWatchURL + '/action/I.ENTRY.ADD',
                                data: {'ielectionid': ielectionid},
                                success: function(data) {
                                    $('#transactionsrightedit').html(data);
                                    // unhighlight the right control box
                                    $('#transactionsrightedit').removeClass('activeinveditmenu');
                                }
                            });
                            // reload underneath
                            MW.comm.sendCommand('I.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                });
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
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        MW.modaluniversal.show("Bank - Bulk Interest", "350", data);
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
                            MW.modaluniversal.hide();
                            MW.comm.sendCommand('I.SUMMARY.GET');
                            MW.comm.sendCommand('B.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                });
                break;
            case 'B.BULKBILLS.EDIT':
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        MW.modaluniversal.show("Bank - Bulk Bills", "750", data);
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
                            MW.modaluniversal.hide();
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
                $.ajax({
                    type: 'POST',
                    url: urlpost,
                    data: formdata,
                    success: function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            $('#' + MW.activeRowId).removeClass('activebankrow');
                            $.ajax({
                                url: MW.moneyWatchURL + '/action/B.ACCOUNT.GET',
                                data: {'bacctid': bacctid},
                                success: function(data) {
                                    $('#transactionslist').html(data);
                                    $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
                                }
                            });
                            $.ajax({
                                url: MW.moneyWatchURL + '/action/B.ENTRY.ADD',
                                data: {'bacctid': bacctid},
                                success: function(data) {
                                    $('#transactionsrightedit').html(data);
                                    // unhighlight the right control box
                                    $('#transactionsrightedit').removeClass('activeinveditmenu');
                                }
                            });
                            // reload underneath
                            MW.comm.sendCommand('B.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                });
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
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        data = data.replace(/\n/gm, '');
                        if (data == 'ok') {
                            MW.comm.sendCommand('B.SUMMARY.GET');
                        } else {
                            alert(data.substr(0,500));
                        }
                    }
                });
                break;
            case 'U.IMPORTFILE.EDIT':
                $.ajax({
                    url: urlpost,
                    data: {},
                    success: function(data) {
                        MW.modaluniversal.show("Import Menu", "420", data);
                    }
                });
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
        MW.modaltransactions.show("investment");
        $.ajax({
            url: MW.moneyWatchURL + '/action/I.ENTRY.ADD',
            data: {'ielectionid': in_ielectionid},
            success: function(data) {
                $('#transactionsrightedit').html(data);
            }
        });
        $.ajax({
            url: MW.moneyWatchURL + '/action/I.ELECTION.GET',
            data: {'ielectionid': in_ielectionid},
            success: function(data) {
                $('#transactionslist').html(data);
                $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
            }
        });
        $.ajax({
            url: MW.moneyWatchURL + '/action/I.ENTRY.CHART',
            data: {'ielectionid': in_ielectionid},
            success: function(data) {
                $('#transactionsrightchart').html(data);
            }
        });
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
        $.ajax({
            url: MW.moneyWatchURL + '/action/I.GRAPH.GET',
            data: {'ielectionid': in_ielectionid},
            success: function(data) {
                MW.modaluniversal.show("Investment - Graph", "950", data);
            }
        });
    },

    sendInvDelete: function (in_ielectionid, in_itransid) {
        var r = confirm("Are you sure you want to delete MW transaction?");
        if (r === true) {
            $.ajax({
                url: MW.moneyWatchURL + '/action/I.ENTRY.DELETE',
                data: {'itransid': in_itransid},
                success: function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        // reload left side, reflecting the deletion
                        $.ajax({
                            url: MW.moneyWatchURL + '/action/I.ELECTION.GET',
                            data: {'ielectionid': in_ielectionid},
                            success: function(data) {
                                $('#transactionslist').html(data);
                            }
                        });
                        // reload underneath
                        MW.comm.sendCommand('I.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            });
        } else {
            return false;
        }
    },

    getBankEdit: function (in_btransid) {
        $.ajax({
            url: MW.moneyWatchURL + '/action/B.ENTRY.EDIT',
            data: {'btransid': in_btransid},
            success: function(data) {
                $('#transactionsrightedit').html(data);
                if (MW.activeRowId !== '') {
                    $('#' + MW.activeRowId).removeClass('activeinvrow');
                }
                MW.activeRowId = 'b' + in_btransid;
                $('#' + MW.activeRowId).addClass('activeinvrow');
                $('#transactionsrightedit').addClass('activeinveditmenu');
            }
        });
    },

    sendBankDelete: function (in_bacctid, in_btransid) {
        var r = confirm("Are you sure you want to delete MW transaction?");
        if (r === true) {
            $.ajax({
                url: MW.moneyWatchURL + '/action/B.ENTRY.DELETE',
                data: {'btransid': in_btransid},
                success: function(data) {
                    data = data.replace(/\n/gm, '');
                    if (data == 'ok') {
                        // reload left side, reflecting the deletion
                        $.ajax({
                            url: MW.moneyWatchURL + '/action/B.ACCOUNT.GET',
                            data: {'bacctid': in_bacctid},
                            success: function(data) {
                                $('#transactionslist').html(data);
                            }
                        });
                        // reload underneath
                        MW.comm.sendCommand('B.SUMMARY.GET');
                    } else {
                        alert(data.substr(0,500));
                    }
                }
            });
            return true;
        } else {
            return false;
        }
    },

    getBankAccount: function (in_bacctid) {
        MW.modaltransactions.show("bank");
        $.ajax({
            url: MW.moneyWatchURL + '/action/B.ENTRY.ADD',
            data: {'bacctid': in_bacctid},
            success: function(data) {
                $('#transactionsrightedit').html(data);
            }
        });
        $.ajax({
            url: MW.moneyWatchURL + '/action/B.ACCOUNT.GET',
            data: {'bacctid': in_bacctid},
            success: function(data) {
                $('#transactionslist').html(data);
                $("#transactionslist").scrollTop($("#transactionslist")[0].scrollHeight);
            }
        });
    },

    cancelEdit: function (in_type, in_xacctid) {
        // unhighlight the selected row
        $('#' + MW.activeRowId).removeClass('activeinvrow');
        // unhighlight the right control box
        $('#transactionsrightedit').removeClass('activeinveditmenu');
        // reload the right side
        if (in_type == 'bank') {
            $.ajax({
                url: MW.moneyWatchURL + '/action/B.ENTRY.ADD',
                data: {'bacctid': in_xacctid},
                success: function(data) {
                    $('#transactionsrightedit').html(data);
                }
            });
        } else if (in_type == 'investment') {
            $.ajax({
                url: MW.moneyWatchURL + '/action/I.ENTRY.ADD',
                data: {'ielectionid': in_xacctid},
                success: function(data) {
                    $('#transactionsrightedit').html(data);
                }
            });
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


MW.modaluniversal = {
    // ------------------------------------------------------------------
    // preps and shows universal modal
    // ------------------------------------------------------------------
    show: function (title, width, content) {
        $('#modaluniversal-inner').html(content);
        $('.modal-dialog').css("width", width);
        $('.modal-title').html(title);
        $('#modaluniversal').modal('show');
    },
    // ------------------------------------------------------------------
    // hides universal modal window and does cleanup
    // ------------------------------------------------------------------
    hide: function () {
        $('#modaluniversal').modal('hide');
        $('#modaluniversal-inner').html('');
    }
};

MW.modaltransactions = {
    // ------------------------------------------------------------------
    // preps and shows transaction bank/investment accounts modal
    // ------------------------------------------------------------------
    show: function (mode) {
        // clear any previous highlights
        $('#' + MW.activeRowId).removeClass('activeinvrow');
        $('#transactionsrightedit').removeClass('activeinveditmenu');
        $('#transactionslist').html('<div style="text-align:center;padding-top:50px;">' +
                                    '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i></div>');
        $('#transactionsrightedit').html('');
        $('.modal-dialog').css("width", "1224");
        // $('.modal-title').html(title);
        if (mode === "bank") {
            $('#transactionsheaderinv').hide();
            $('#transactionsheaderbank').show();
        } else {
            $('#transactionsheaderbank').hide();
            $('#transactionsheaderinv').show();
        }
        $('#modaltransactions').modal('show');
    }
};
