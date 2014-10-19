#!/usr/bin/python
#===============================================================================
# Copyright (c) 2014, James Ottinger. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# MoneyWatch - https://github.com/jamesottinger/moneywatch
#===============================================================================
import MySQLdb as mdb # sudo apt-get install python-mysqldb
import cgi, cgitb, os, datetime, locale, urllib2, csv, time, json
import moneywatchconfig

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
g_formdata = cgi.FieldStorage()
cgitb.enable(
    logdir=moneywatchconfig.direrrors,
    display=True,
    format='text'
)

#================================================================================================================
# INVESTMENT
#================================================================================================================

def i_electiontally(in_ielectionid):
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_invtransactions WHERE ielectionid=%s ORDER BY transdate,action"
    cursor.execute(sqlstr, (in_ielectionid))
    dbrows = cursor.fetchall()
    rtotal = 0
    costbasis = 0
    sharesbydividend = 0 # from dividends (shown as income)

    for dbrow in dbrows:
        if dbrow['updown'] == '+':
            rtotal += float(dbrow['sharesamt'])
            costbasis += float(dbrow['transprice'])
            if dbrow['action'] == 'REINVDIV':
                sharesbydividend += float(dbrow['sharesamt'])
        else:
            rtotal -= float(dbrow['sharesamt'])
            costbasis -= float(dbrow['transprice'])
            if dbrow['action'] == 'REINVDIV':
                sharesbydividend -= float(dbrow['sharesamt'])

    sqlstr = "UPDATE moneywatch_invelections SET shares=%s, costbasis=%s, sharesbydividend=%s WHERE ielectionid=%s"
    cursor.execute(sqlstr, (
        "{:.3f}".format(rtotal),
        "{:.3f}".format(costbasis),
        "{:.3f}".format(sharesbydividend),
        in_ielectionid))
    dbcon.commit()
    dbcon.close()


def i_electiontallyall():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT ielectionid FROM moneywatch_invelections WHERE active=1"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        i_electiontally(dbrow['ielectionid'])
    dbcon.close()


def i_makeselectsparents(selected, identifier):
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT DISTINCT(iacctname) FROM moneywatch_invelections ORDER BY iacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    for dbrow in dbrows:
        if str(dbrow['iacctname']) == selected:
            selectedsay = ' selected'
        else:
            selectedsay = ''
        markup += '<option value="' + identifier + str(dbrow['iacctname']) + '"' + selectedsay + '>[Investment] ' + dbrow['iacctname'] + '</option>'
    dbcon.close()
    return markup


# I.SUMMARY.GET = Shows Summary of Investment Accounts
def i_summary():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_invelections WHERE active > 0 AND ticker IS NOT NULL ORDER BY iacctname,ielectionname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = '''\
                <div class="summary1heading">Investment Accounts <span class="smgraytext">( last fetch: %s <a href="#" onClick="return sendCommand('U.UPDATEQUOTES');">fetch</a> )</span></div>
                <table class="invtable">
                    <tr>
                        <td>Symbol</td>
                        <td>Name</td>
                        <td>Total Qty</td>
                        <td>Last Price</td>
                        <td>Cost Basis</td>
                        <td>Market Value</td>
                        <td>Income</td>
                        <td>Apprec.</td>
                        <td>Gain</td>
                        <td>Links/Schedule</td>
                    </tr>
    ''' % (str(dbrows[0]['quotedate'].strftime("%A  %B %d, %Y %r")))
    all_costbasis = 0
    all_market = 0
    all_appres = 0
    all_income = 0
    all_gain = 0
    parent = ''
    election_costbasis = 0
    election_market = 0
    election_income = 0
    election_appres = 0
    election_gain = 0
    election_showquote = 0
    election_useprice = 0

    for dbrow in dbrows:
        if dbrow['iacctname'] != parent:
            if dbrows[0] != dbrow:
                markup += '''\
                                <tr>
                                    <td class="invtabletrgraytop" colspan="4">&nbsp;</td>
                                    <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- cost basis -->%s</td>
                                    <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- market value --><b>%s</b></td>
                                    <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- income -->%s</td>
                                    <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- apprec -->%s</td>
                                    <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- gain -->%s</td>
                                    <td class="invtabletrgraytop">&nbsp;</td>
                                </tr>
                    ''' % (h_showmoney(election_costbasis), h_showmoney(election_market), h_showmoney(election_income), h_showmoney(election_appres), h_showmoney(election_gain))
                election_costbasis = 0
                election_market = 0
                election_income = 0
                election_appres = 0
                election_gain = 0
            markup += '<tr class="invtablehead"><td colspan="10"><b>' + dbrow['iacctname'] + '</b></td></tr>'
            parent = dbrow['iacctname']

        if dbrow['manualoverrideprice'] is not None:
            election_useprice = dbrow['manualoverrideprice']
        else:
           election_useprice = dbrow['quoteprice']

        each_market = dbrow['shares'] * election_useprice
        each_appres = (dbrow['shares'] * election_useprice) - dbrow['costbasis']
        election_showquote = h_showmoney(election_useprice)
        each_gain = (((dbrow['shares'] * election_useprice) - dbrow['costbasis']) + (dbrow['sharesbydividend'] * election_useprice))
        each_income = dbrow['sharesbydividend'] * election_useprice

        each_apprecclass = 'numpos'
        if each_appres < 0:
            each_apprecclass = 'numneg'
        election_costbasis += dbrow['costbasis']
        election_market += each_market
        election_appres += each_appres
        election_income += each_income
        election_gain += each_gain
        all_costbasis += dbrow['costbasis']
        all_market += each_market
        all_appres += each_appres
        all_income += each_income
        all_gain += each_gain

        markup += '''\
                    <tr>
                        <td><a href="#" onClick="getInvGraph('%s');">%s</a></td>
                        <td><a href="#" onClick="getInvElection('%s');">%s</a></td>
                        <td style="text-align: right;">%s</td>
                        <td style="text-align: right;">%s</td>
                        <td style="text-align: right;">%s</td>
                        <td style="text-align: right;"><!-- market value --><b>%s</b></td>
                        <td style="text-align: right;"><!-- income -->%s</td>
                        <td style="text-align: right;" class="%s"><!-- apprec -->%s</td>
                        <td style="text-align: right;"><!-- gain -->%s</td>
                        <td><a href="http://www.google.com/finance?q=%s" target="_blank">G</a> <a href="http://finance.yahoo.com/q?s=%s" target="_blank">Y</a> <a href="http://quotes.morningstar.com/fund/%s/f?t=%s" target="_blank">MS</a> [%s]</td>
                    </tr>
        ''' % (dbrow['ielectionid'], dbrow['ticker'], dbrow['ielectionid'], dbrow['ielectionname'], "{:.3f}".format(dbrow['shares']), election_showquote, h_showmoney(dbrow['costbasis']), h_showmoney(each_market), h_showmoney(each_income), each_apprecclass, h_showmoney(each_appres), h_showmoney(each_gain), dbrow['ticker'], dbrow['ticker'], dbrow['ticker'], dbrow['ticker'], dbrow['divschedule'])

    markup += '''\
                    <tr>
                        <td class="invtabletrgraytop" colspan="4">&nbsp;</td>
                        <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- cost basis -->%s</td>
                        <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- market value --><b>%s</b></td>
                        <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- income -->%s</td>
                        <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- apprec -->%s</td>
                        <td class="invtabletrgraytop" style="text-align: right;background-color: #efefef;"><!-- gain -->%s</td>
                        <td class="invtabletrgraytop">&nbsp;</td>
                    </tr>
        ''' % (h_showmoney(election_costbasis), h_showmoney(election_market), h_showmoney(election_income), h_showmoney(election_appres), h_showmoney(election_gain))


    markup += '''\
                    <tr>
                        <td colspan="4">&nbsp;</td>
                        <td class="invtotalsbottom"><!-- cost basis -->%s</td>
                        <td class="invtotalsbottom"><!-- market value --><b>%s</b> <input type="hidden" id="networth-investments" name="networth-investments" value="%s"></td>
                        <td class="invtotalsbottom"><!-- income -->%s</td>
                        <td class="invtotalsbottom"><!-- apprec -->%s</td>
                        <td class="invtotalsbottom"><!-- gain -->%s</td>
                        <td>&nbsp;</td>
                    </tr>
        ''' % (h_showmoney(all_costbasis), h_showmoney(all_market), all_market, h_showmoney(all_income), h_showmoney(all_appres), h_showmoney(all_gain))


    dbcon.close()
    return markup + '</table>'


# I.ELECTION.GET
def i_electionget():
    markup = ''
    counter = 0
    rtotal = 0
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_invtransactions WHERE ielectionid=%s ORDER BY transdate,action"
    cursor.execute(sqlstr, (g_formdata.getvalue('ielectionid')))
    dbrows = cursor.fetchall()
    #ielectionid, transdate, ticker, updown, action, sharesamt, shareprice, transprice, totalshould

    for dbrow in dbrows:
        amtup = ''
        amtdown = ''
        showwho = ''
        whomclass = ''
        classfuture = ''
        showcheck = ''

        if dbrow['updown'] == '+':
            amtup = "+" + "{:.3f}".format(float(dbrow['sharesamt'])) #locale.currency(trans['transactionamt'], grouping=True)
            amtdown = '&nbsp;'
            rtotal += float(dbrow['sharesamt'])
        else:
            amtup = '&nbsp;'
            amtdown = "-" + "{:.3f}".format(float(dbrow['sharesamt'])) #locale.currency(trans['transactionamt'], grouping=True)
            rtotal -= float(dbrow['sharesamt'])

        if dbrow['totalshould'] != 0 and (dbrow['totalshould'] != round(rtotal, 3)):
            showcheck = """%s diff: %s""" % (dbrow['totalshould'],"{:.3f}".format(rtotal - float(dbrow['totalshould'])))

        if counter % 2 == 0:
            classoe = 'recordeven'
        else:
            classoe = 'recordodd'

        identifier = str(dbrow['ielectionid']) + str(dbrow['itransid'])

        markup += '''<div class="%s" id="%s">\
                        <span class="irow0"><input type="button" value="D" onclick="return sendInvDelete('%s','%s');"> <input type="button" value="E" onclick="return getInvElectionEdit('%s', '%s');"></span>
                        <span class="irow1"> %s</span>
                        <span class="irow2">%s</span>
                        <span class="irow3"> ($%s @ $%s each)</span>
                        <span class="irow4">%s</span>
                        <span class="irow5">%s</span>
                        <span class="irow6pos"> %s %s</span>
                     </div>''' % (classoe, identifier, str(dbrow['ielectionid']), str(dbrow['itransid']), str(dbrow['ielectionid']), str(dbrow['itransid']), dbrow['transdate'], dbrow['action'], "{:.2f}".format(float(dbrow['transprice'])), "{:.3f}".format(float(dbrow['shareprice'])), amtup, amtdown, "{:.3f}".format(rtotal), showcheck)
                    #//$R .= $ecounter . "==" . $election['shares'] . "|"; //'<a href="#" onClick="return bank_gettransactions(' . "'" . $document['name'] . "');" . '">' . $document['name'] . " $" .  number_format($document['total'], 2, '.', ',') . "</a><br>";
        counter +=1
        markup += '<div id="scrollmeinv"></div>'
    return markup


# I.BULKADD.EDIT = generates body needed for "Investment Bulk Add" utility panel
def i_bulkadd_edit():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_invelections WHERE ticker IS NOT NULL AND active=1 ORDER BY iacctname,ielectionname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    parent = ''
    javascriptcalls = []

    markup += '''<form name="ibulkedit" id="ibulkedit"><table class="invtable">\
                    <tr>
                        <td><strong>Name</strong></td>
                        <td><strong>Ticker</strong></td>
                        <td><strong>Funded From</strong></td>
                        <td><strong>Trade Date</strong></td>
                        <td><strong>Action</strong></td>
                        <td><strong># Shares</strong></td>
                        <td><strong>Trade Cost</strong></td>
                        <td><strong>Update Price</strong></td>
                    </tr>
    '''
    for dbrow in dbrows:

        if dbrow['iacctname'] != parent:
            markup += '<tr><td colspan="8" style="background-color: #efefef;"><span class="bigbluetext">' + dbrow['iacctname'] + '</span></td></tr>'
            parent = dbrow['iacctname']

        tocheckornottocheck = ''
        if dbrow['fetchquotes'] == 0:
            tocheckornottocheck = 'checked'

        each_datepicker = str(dbrow['ielectionid']) + '-date'
        javascriptcalls.append(' jQuery("#' + each_datepicker + '").datepicker({ dateFormat: "yy-mm-dd" });')

        markup += '''\
                    <tr>
                        <td>%s<input type="hidden" name="%s-ielectionid" value="%s"></td>
                        <td>%s</td>
                        <td><select name="%s-fromaccount"><option value="0">--none--</option>%s</select></td>
                        <td><input type="text" name="%s" id="%s" size="10"></td>
                        <td>
                            <select name="%s-action">
                              <option value="BUY">Buy</option>
                              <option value="REINVDIV">Dividend(ReInvest)</option>
                              <option value="SELL">Sell</option>
                            </select>
                        </td>
                        <td><input type="text" size="8" name="%s-shares" value="" onChange="checkValueDecimals(this, 3);"></td>
                        <td><nobr>$<input type="text" size="8" name="%s-cost" value="" onChange="checkValueDecimals(this, 2);"></nobr></td>
                        <td><input type="checkbox" name="%s-updateprice" value="yes" %s/></td>
                    </tr>
        ''' % (dbrow['ielectionname'], str(dbrow['ielectionid']), str(dbrow['ielectionid']), dbrow['ticker'], str(dbrow['ielectionid']), b_makeselects(selected='', identifier=''), each_datepicker, each_datepicker, str(dbrow['ielectionid']), str(dbrow['ielectionid']), str(dbrow['ielectionid']), str(dbrow['ielectionid']), tocheckornottocheck)

        #markup += '<div><span>' +  dbrow['name'] + '</span><span><input type="text" class="tickerentry" size="8" name="' + dbrow['ticker'] + '-shares" value=""></span></div>'
    dbcon.close()

    markup += '''</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="I.BULKADD.SAVE"><input type="button" name="doit" VALUE="Save" onClick="sendCommand('I.BULKADD.SAVE');"></div></form><script>'''
    for js in javascriptcalls:
        markup += js

    return markup + '</script>'


# I.BULKADD.SAVE = save "Investment Bulk Add" submission
def i_bulkadd_save():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_invelections WHERE ticker IS NOT NULL AND active=1 ORDER BY iacctname,ielectionname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        each_shares = g_formdata.getvalue(str(dbrow['ielectionid']) + '-shares')
        each_cost = g_formdata.getvalue(str(dbrow['ielectionid']) + '-cost') # cost of full sale
        each_date = g_formdata.getvalue(str(dbrow['ielectionid']) + '-date')
        if each_shares is not None and each_cost is not None and each_date is not None:
            each_ielectionid = int(g_formdata.getvalue(str(dbrow['ielectionid']) + '-ielectionid'))
            each_fromid = int(g_formdata.getvalue(str(dbrow['ielectionid']) + '-fromaccount'))
            each_action = g_formdata.getvalue(str(dbrow['ielectionid']) + '-action')

            i_saveadd(ticker=dbrow['ticker'], transdate=each_date, shares=each_shares, cost=each_cost, fromacct=each_fromid, action=each_action, ielectionid=each_ielectionid, ielectionname=dbrow['ielectionname'])

    dbcon.close()


# I.ENTRY.ADD = generates body needed for "Investment Single Add" Section
def i_entry_prepareadd():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_invelections WHERE ielectionid=%s"
    cursor.execute(sqlstr, (g_formdata.getvalue('ielectionid')))
    dbrows = cursor.fetchall()
    dbcon.close()

    for dbrow in dbrows:
        return i_edit_template(mode='add', ielectionname=dbrow['ielectionname'], ticker=dbrow['ticker'], itransid="", ielectionid=str(dbrow['ielectionid']), btransid="", transdate="", action="", shares="", cost="", fundsorigin=0)

# I.ENTRY.EDIT = generates body needed for "Investment Single Edit" Section
def i_entry_prepareedit():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = """SELECT it.*, ie.ielectionname FROM moneywatch_invtransactions it \
                INNER JOIN moneywatch_invelections ie ON it.ielectionid=ie.ielectionid WHERE it.itransid=%s"""
    cursor.execute(sqlstr, (g_formdata.getvalue('itransid')))
    dbrows = cursor.fetchall()
    dbcon.close()

    for dbrow in dbrows:
        return i_edit_template(mode='edit', ielectionname=dbrow['ielectionname'], ticker=dbrow['ticker'], itransid=str(dbrow['itransid']), ielectionid=str(dbrow['ielectionid']), btransid=dbrow['btransid'], transdate=str(dbrow['transdate']), action=dbrow['action'], shares="{:.3f}".format(float(dbrow['sharesamt'])), cost="{:.2f}".format(float(dbrow['transprice'])), fundsorigin=str(dbrow['btransid']))


# created the single
def i_edit_template(mode, ielectionname, ticker, itransid, ielectionid, btransid, transdate, action, shares, cost, fundsorigin):

    if mode == 'edit':
        sendcmd = 'I.ENTRY.EDITSAVE'
        buttonsay = 'Save Edit'
    else:
        sendcmd = 'I.ENTRY.ADDSAVE'
        buttonsay = 'Add New'

    if action == 'BUY' or action == 'BUYX':
        # the save will deal with the difference of a BUY or a BUYX (one finded by a bank transfer)
        actionselect = '<option value="BUY" selected>Buy</option><option value="REINVDIV">Dividend(ReInvest)</option><option value="SELL">Sell</option>'
    elif action == 'REINVDIV':
        actionselect = '<option value="BUY">Buy</option><option value="REINVDIV" selected>Dividend(ReInvest)</option><option value="SELL">Sell</option>'
    elif action == 'SELL' or action == 'SELLX':
        # the save will deal with the difference of a SELL or a SELLX(one finded by a bank transfer)
        # TODO: may need to revisit when dealing with SELLs that transfer money to a bank account (SELLX)
        actionselect = '<option value="BUY">Buy</option><option value="REINVDIV">Dividend(ReInvest)</option><option value="SELL" selected>Sell</option>'
    else:
        actionselect = '<option value="BUY">Buy</option><option value="REINVDIV">Dividend(ReInvest)</option><option value="SELL">Sell</option>'

    markup = '''<form name="ieditsingle" id="ieditsingle">\
                    <table class="cleantable" width="300">
                        <tr>
                            <td colspan="2" style="box-shadow: 0px 1px 2px #999999;background-color: #ffffff;text-align:center;">%s [ <b>%s</b> ]</td>
                        </tr>
                        <tr>
                            <td colspan="2">Funded From:<br><select name="fromaccount"><option value="0">--none--</option>%s</select></td>
                        </tr>
                        <tr>
                            <td class="tdborderright">Action:<br>
                                <select name="action">
                                    %s
                                </select>
                            </td>
                            <td>Trade Date:<br><input type="text" name="tradedate" id="ieditsingle-tradedate" size="10" value="%s"></td>
                        </tr>
                        <tr>
                            <td class="tdborderright"># Shares:<br><input type="text" size="10" id="ieditsingle-shares" name="shares" value="%s" onChange="checkValueDecimals(this, 3);"></td>
                            <td>Trade Cost:<br><nobr>$<input type="text" size="8" id="ieditsingle-cost" name="cost" value="%s" onChange="checkValueDecimals(this, 2);"></nobr></td>
                        </tr>
                    </table>
                    <div style="text-align:right; padding-top: 20px; padding-right: 25px;">
                        <input type="hidden" name="job" value="%s">
                        <input type="hidden" name="ticker" id="ieditsingle-ticker" value="%s">

                        <input type="hidden" name="ielectionname" value="%s">
                        <input type="hidden" name="ielectionid" id="ieditsingle-ielectionid" value="%s">

                        <input type="hidden" name="itransid" value="%s">
                        <input type="hidden" name="btransid" value="%s">
                        <input type="button" name="doit" VALUE="%s" onClick="ieditsingle_validate('%s');">
                    </div>
                </form><br>
                <script>
                    jQuery("#ieditsingle-tradedate").datepicker({ dateFormat: "yy-mm-dd" });

                    function ieditsingle_validate(in_sendjob) {
                        if(jQuery('#ieditsingle-tradedate').val() == '') {
                            alert("Please provide a transaction date.");
                        } else if(jQuery('#ieditsingle-shares').val() == '') {
                            alert("Please provide the total number of shares for this transaction.");
                        } else if(jQuery('#ieditsingle-cost').val() == '') {
                            alert("Please provide the total cost for this transaction.");
                        } else {
                            sendCommand(in_sendjob);
                        }
                    }
                </script>
        ''' % (ielectionname, ticker, b_makeselects(selected=fundsorigin, identifier=''), actionselect, transdate, shares, cost, sendcmd, ticker, ielectionname, ielectionid, itransid, btransid, buttonsay, sendcmd)

    return markup

def i_edit_liveinvchart():
    return '''
           <!-- widget came from http://www.macroaxis.com/invest/widgets/native/intradaySymbolFeed?ip=true&s=VFIAX -->
                <iframe bgcolor='#ffffff' id='intraday_symbol_feed' name='intraday_symbol_feed' marginheight='0' marginwidth='0' SCROLLING='NO' height='300px' width='300px' frameborder='0' src='http://widgets.macroaxis.com/widgets/intradaySymbolFeed.jsp?gia=t&tid=279&t=24&s=%s&_=1381101748535'></iframe>
    ''' % (g_formdata.getvalue('ticker'))

def i_prepare_addupdate():

    # get form items
    in_job      = g_formdata.getvalue('job')
    in_ticker   = g_formdata.getvalue('ticker')
    in_transdate = g_formdata.getvalue('tradedate')
    in_shares   = g_formdata.getvalue('shares')
    in_cost     = g_formdata.getvalue('cost')
    in_action   = g_formdata.getvalue('action')
    in_btransid = int(g_formdata.getvalue('btransid'))             # updates only (hidden field)
    in_itransid    = int(g_formdata.getvalue('itransid'))          # updates only (hidden field)
    in_ielectionid = int(g_formdata.getvalue('ielectionid'))
    in_ielectionname = g_formdata.getvalue('ielectionname')
    in_fromid   = int(g_formdata.getvalue('fromaccount'))

    if in_job == 'I.ENTRY.ADDSAVE':
        i_saveadd(ticker=in_ticker, transdate=in_transdate, shares=in_shares, cost=in_cost, fromacct=in_fromid, action=in_action, ielectionid=in_ielectionid, ielectionname=in_ielectionname)

    if in_job == 'I.ENTRY.EDITSAVE':
        i_saveupdate(ticker=in_ticker, transdate=in_transdate, shares=in_shares, cost=in_cost, fromacct=in_fromid, action=in_action, ielectionid=in_ielectionid, ielectionname=in_ielectionname, btransid=in_btransid, itransid=in_itransid)


def i_saveadd(ticker, transdate, shares, cost, fromacct, action, ielectionid, ielectionname):
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)

    costpershare = "{:.3f}".format(float(cost) / float(shares))

    if action == 'SELL' or action == 'SELLX':
        updown = '-'
    else: # BUY BUYX REINVDIV
        updown = '+'

    btransid = 0
    transferbtransid = 0
    # do bank insert first, since we will need to learn the transaction id
    if fromacct > 0: # was this bank funded?
        # enter bank transaction
        # Category: Buy Investment/CD: The Name Of Account
        # Buy: Mutual Fund Name 4.439 @ $22.754
        whom1 = 'Buy : ' + ticker + ' ' + shares + ' @ ' + h_showmoney(float(cost) / float(shares))
        whom2 = 'Buy Investment/CD: ' + ielectionname
        sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferbtransid, transferbacctid, itransid) \
                    VALUES (%s, %s, 'w', '-', %s, %s, %s, 'INV', 0, 0, 0, 0)"""
        cursor.execute(sqlstr, (fromacct, transdate, cost, whom1, whom2))
        h_logsql(cursor._executed)
        dbcon.commit()
        b_accounttally(fromacct)
        btransid = cursor.lastrowid

    # enter transaction in db
    sqlstr = """INSERT INTO moneywatch_invtransactions (ielectionid, btransid, transdate, ticker, updown, action, sharesamt, shareprice, transprice, totalshould)  \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)"""

    cursor.execute(sqlstr, (ielectionid, btransid, transdate, ticker, updown, action, shares, costpershare, cost))
    h_logsql(cursor._executed)
    dbcon.commit()

    if  str(ielectionid) + '-updateprice' in g_formdata: # update price based on new entry
        # update the elections price
        sqlstr = "UPDATE moneywatch_invelections SET quoteprice=%s, quotedate=%s WHERE ielectionid=%s"
        cursor.execute(sqlstr, ("{:.3f}".format(float(cost) / float(shares)), h_todaydatetimeformysql(), ielectionid))
        dbcon.commit()


    i_electiontally(ielectionid)

    if fromacct > 0: # was this bank funded?
        # update the bank account to show investmentid
        sqlstr = """UPDATE moneywatch_banktransactions SET \
            itransid=%s
            WHERE btransid=%s"""
        cursor.execute(sqlstr, (cursor.lastrowid, btransid))
        h_logsql(cursor._executed)
        dbcon.commit()

    dbcon.close()


def i_saveupdate(ticker, transdate, shares, cost, fromacct, action, ielectionid, ielectionname, btransid, itransid):
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)

    update_btransid = 0
    costpershare = "{:.3f}".format(float(cost) / float(shares))

    if action == 'SELL' or action == 'SELLX':
        updown = '-'
    else: # BUY BUYX REINVDIV
        updown = '+'

    # ---------  [update investment transaction]  ---------
    # 1) it wasn't bank funded before, but it is now
    # 2) it was bank funded before, but it isn't anymore
    # 3) it was bank funded before and still is, but it might be from a different bank account
    # 4) it wasn't bank funded before and it still isn't

    # (1) it wasn't bank funded before, but it is now
    if btransid == 0 and fromacct > 0:
        # need to create a bank entry

        # -- [insert bank transaction]
        # Category: Buy Investment/CD: The Name Of Account
        # Buy: Mutual Fund Name 4.439 @ $22.754
        whom1 = 'Buy : ' + ticker + ' ' + shares + ' @ ' + h_showmoney(costpershare)
        whom2 = 'Buy Investment/CD: ' + ielectionname
        sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferbtransid, transferielectionid, itransid) \
                    VALUES (%s, %s, 'w', %s, %s, %s, %s, 'INV', 0, %s, 0, 0)"""
        cursor.execute(sqlstr, (fromacct, transdate, updown, cost, whom1, whom2, itransid))
        h_logsql(cursor._executed)
        dbcon.commit()
        b_accounttally(fromacct)

        update_btransid = cursor.lastrowid # use new btransid

    # (2) it was bank funded before, but it isn't anymore
    elif btransid > 0 and fromacct == 0:

        # -- [delete bank transaction]
        sqlstr = "SELECT bacctid FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (btransid))
        h_logsql(cursor._executed)
        dbrow = cursor.fetchone()
        bacctid_lookup = dbrow['bacctid'] # need to parent bank acct for re-tally

        # not assiciated with a bank account anymore, delete the bank entry
        sqlstr = "DELETE FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (btransid))
        h_logsql(cursor._executed)
        dbcon.commit()
        b_accounttally(bacctid_lookup)

        update_btransid = 0

    # 3) it was bank funded before and still is, but it might be from a different bank account
    elif btransid > 0 and fromacct > 0:

        # -- [update bank transaction]
        # update the bank account transaction with new details
        # enter bank transaction
        # Category: Buy Investment/CD: The Name Of Account
        # Buy: Mutual Fund Name 4.439 @ $22.754
        whom1 = 'Buy : ' + ticker + ' ' + shares + ' @ ' + h_showmoney(costpershare)
        whom2 = 'Buy Investment/CD: ' + ielectionname

        sqlstr = """UPDATE moneywatch_banktransactions SET \
            transdate=%s,
            type='w',
            amt=%s,
            whom1=%s,
            whom2=%s,
            itransid=%s WHERE btransid=%s"""

        cursor.execute(sqlstr, (transdate, cost, whom1, whom2, itransid, btransid))
        h_logsql(cursor._executed)
        dbcon.commit()

        b_accounttally(fromacct)

        sqlstr = "SELECT bacctid FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (btransid))
        h_logsql(cursor._executed)
        dbrow = cursor.fetchone()
        bacctid_lookup = dbrow['bacctid'] # need to parent bank acct for re-tally

        if fromacct != bacctid_lookup: # different bank account?
            b_accounttally(bacctid_lookup)

        # btransid is the same, we just changed parts of the bank transaction
        update_btransid = btransid

    # 4) it wasn't bank funded before and it still isn't
    else:
        update_btransid = 0


    # -- [update investment transaction]
    sqlstr = """UPDATE moneywatch_invtransactions SET \
        transdate=%s,
        action=%s,
        updown=%s,
        sharesamt=%s,
        shareprice=%s,
        transprice=%s,
        btransid=%s WHERE itransid=%s"""

    cursor.execute(sqlstr, (transdate, action, updown, shares, costpershare, cost, update_btransid, itransid))
    h_logsql(cursor._executed)
    dbcon.commit()
    i_electiontally(ielectionid)

    dbcon.close()


    # I.ENTRY.DELETE = removes an investment entry and possibly a transfer
def i_entry_delete():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_invtransactions WHERE itransid=%s"
    cursor.execute(sqlstr, (g_formdata.getvalue('itransid')))
    dbrow = cursor.fetchone()


    # delete a bank transaction?
    if dbrow['btransid'] > 0:
        sqlstr = "DELETE FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (dbrow['btransid']))
        h_logsql(cursor._executed)
        dbcon.commit()
        u_banktotals()

    # delete inv transaction
    sqlstr = "DELETE FROM moneywatch_invtransactions WHERE itransid=%s"
    cursor.execute(sqlstr, (dbrow['itransid']))
    h_logsql(cursor._executed)
    dbcon.commit()
    i_electiontally(dbrow['itransid'])

    dbcon.close()


# I.ENTRY.ADD = generates body needed for "Investment Single Add" Section
def i_entry_edit():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_invelections WHERE ticker IS NOT NULL AND active=1 AND ielectionid=%s ORDER BY iacctname,ielectionname"
    cursor.execute(sqlstr, (g_formdata.getvalue('ielectionid')))
    dbrows = cursor.fetchall()

    markup = ''
    parent = ''
    javascriptcalls = []

    markup += '''<form name="ibulkedit" id="ibulkedit"><table class="cleantable">'''
    for dbrow in dbrows:

        if dbrow['iacctname'] != parent:
            #markup += '<tr><td colspan="2" style="background-color: #efefef;"><span class="bigbluetext">' + dbrow['iacctname'] + '</span></td></tr>'
            parent = dbrow['iacctname']

        each_datepicker = dbrow['ticker'] + str(dbrow['ielectionid']) + '-date'
        javascriptcalls.append(' jQuery("#' + each_datepicker + '").datepicker({ dateFormat: "yy-mm-dd" });')

        markup += '''\
                    <tr>
                        <td colspan="2" style="box-shadow: 0px 1px 2px #999999;background-color: #ffffff;">%s<input type="hidden" name="%s-ielectionid" value="%s"> [ <b>%s</b> ]</td>
                    </tr>
                    <tr>
                        <td colspan="2">Funded From:<br><select name="%s-fromaccount"><option value="0">--none--</option>%s</select></td>
                    </tr>
                    <tr>
                        <td class="tdborderright">Trade Date:<br><input type="text" name="%s" id="%s" size="10"></td>
                        <td>Action:<br>
                            <select name="%s-action">
                              <option value="BUY">Buy</option>
                              <option value="REINVDIV">Dividend(ReInvest)</option>
                              <option value="SELL">Sell</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td class="tdborderright"># Shares:<br><input type="text" size="10" name="%s-shares" value="" onChange="checkValueDecimals(this, 3);"></td>
                        <td>Trade Cost:<br><nobr>$<input type="text" size="8" name="%s-cost" value="" onChange="checkValueDecimals(this, 2);"></nobr></td>
                    </tr>
        ''' % (dbrow['ielectionname'], dbrow['ticker'], dbrow['ielectionid'], dbrow['ticker'], dbrow['ticker'], b_makeselects(selected='', identifier=''), each_datepicker, each_datepicker, dbrow['ticker'], dbrow['ticker'], dbrow['ticker'])

        #markup += '<div><span>' +  dbrow['name'] + '</span><span><input type="text" class="tickerentry" size="8" name="' + dbrow['ticker'] + '-shares" value=""></span></div>'
    dbcon.close()

    markup += '</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="I.ENTRY.ADD"><input type="button" name="doit" VALUE="Add New" onClick="sendCommand("I.BULKADD.SAVE");"></div></form><script>'
    for js in javascriptcalls:
        markup += js

    return markup + '</script>'






#================================================================================================================
# BANK
#================================================================================================================

def b_accounttally(in_bacctid):
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_banktransactions WHERE bacctid=%s ORDER BY transdate,amt"
    cursor.execute(sqlstr, (in_bacctid))
    dbrows = cursor.fetchall()
    totalall = 0
    totaluptotoday = 0

    for dbrow in dbrows:
        if dbrow['updown'] == '+':
            totalall += float(dbrow['amt'])
            if h_dateinfuture(dbrow['transdate']) == False:
                totaluptotoday += float(dbrow['amt'])
        else:
            totalall -= float(dbrow['amt'])
            if h_dateinfuture(dbrow['transdate']) == False:
                totaluptotoday -= float(dbrow['amt'])

    sqlstr = """UPDATE moneywatch_bankaccounts SET totalall=%s, totaluptotoday=%s, todaywas='%s', tallytime='%s' WHERE bacctid=%s""" % ("{:.2f}".format(float(totalall)), "{:.2f}".format(float(totaluptotoday)), h_todaydateformysql(), h_todaydatetimeformysql(), str(in_bacctid))
    cursor.execute(sqlstr)
    dbcon.commit()
    dbcon.close()


def b_makeselects(selected,identifier):
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    for dbrow in dbrows:
        if str(dbrow['bacctid']) == selected:
            selectedsay = ' selected'
        else:
            selectedsay = ''
        markup += '<option value="' + identifier + str(dbrow['bacctid']) + '"' + selectedsay + '>[Bank] ' + dbrow['bacctname'] + '</option>'
    dbcon.close()
    return markup


def b_saybacctname(in_bacctid):
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT bacctname FROM moneywatch_bankaccounts WHERE bacctid=%s"
    cursor.execute(sqlstr, (in_bacctid))
    dbrow = cursor.fetchone()
    dbcon.close()
    return dbrow['bacctname']


# B.SUMMARY.GET = Shows Summary of Bank Accounts
def b_summary():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = '''\
                <div class="summary1heading">Bank Accounts <span class="smgraytext">( last tally: %s <a href="#" onClick="return sendCommand('U.UPDATEBANKTOTALS');">tally</a> )</span></div>
                <table class="invtable">
                    <tr style="background-color: #ffffff;">
                        <td style="border-bottom: solid 1px #cccccc;">Bank</td>
                        <td style="border-bottom: solid 1px #cccccc;"width="326">Account</td>
                        <td style="border-bottom: solid 1px #cccccc;">Value</td>
                        <td style="border-bottom: solid 1px #cccccc;">Me (Today)</td>
                        <td style="border-bottom: solid 1px #cccccc;">Me (Future)</td>
                    </tr>
    ''' % (str(dbrows[0]['tallytime'].strftime("%A  %B %d, %Y %r")))
    totalmytoday = 0

    for dbrow in dbrows:
        if dbrow['mine'] == 1:
            totalmytoday += dbrow['totaluptotoday']
            ownvaluetoday = h_showmoney(dbrow['totaluptotoday'])
            ownvalueextended = h_showmoney(dbrow['totalall'])
        else:
            ownvaluetoday = ''
            ownvalueextended = ''

        markup += '''\
                    <tr>
                        <td>%s</td>
                        <td><a href="#" onClick="getBankAccount('%s');">%s</a></td>
                        <td style="text-align: right;"><!-- value extended -->%s</td>
                        <td style="text-align: right;"><!-- MINE - value current/today -->%s</td>
                        <td style="text-align: right;"><!-- MINE - value extended -->%s</td>
                    </tr>''' % (dbrow['bank'], dbrow['bacctid'], dbrow['bacctname'], h_showmoney(dbrow['totalall']), ownvaluetoday, ownvalueextended)

    dbcon.close()
    markup += '''\
                <tr>
                    <td class="invtabletrgraytop" colspan="2">&nbsp;</td>
                    <td class="invtabletrgraytop" >&nbsp;</td>
                    <td class="invtotalsbottom" style="width:60px;text-align: right;"><!-- MINE - value current/today --><b>%s</b>  <input type="hidden" id="networth-banks" name="networth-banks" value="%s"></td>
                    <td class="invtabletrgraytop" style="text-align: right;"><!-- MINE - value extended --></td>
                </tr>''' % (h_showmoney(totalmytoday),totalmytoday)

    return markup + '</table>'


# B.ACCOUNT.GET
def b_accountget():

    markup = ''
    counter = 0
    rtotal = 0
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)

    sqlstr = "SELECT * FROM moneywatch_banktransactions WHERE bacctid=%s ORDER BY transdate,numnote"
    cursor.execute(sqlstr, (g_formdata.getvalue('bacctid')))
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        amtup = ''
        amtdown = ''
        showwho = ''
        whomclass = ''
        classfuture = ''
        rtotalclass = ''
        rtotalshow = ''
        #deletelink = "<a href=\"?action=DELETEBANKENTRY&type={$trans['type']}&account={$document['name']}&transdate={$trans['date']}&transamt={$trans['transactionamt']}\">x</a>";

        if dbrow['updown'] == '+':
            amtup = "+" + h_showmoney(dbrow['amt'])
            amtdown = ''
            rtotal += float(dbrow['amt'])
        else:
            amtup = ''
            amtdown = "-" + h_showmoney(dbrow['amt'])
            rtotal -= float(dbrow['amt'])

        if rtotal >= 0:
            rtotalclass = 'rbalpos'
            rtotalshow = h_showmoney(rtotal)
        else:
            rtotalclass = 'rbalneg'
            rtotalshow = '(' + h_showmoney(rtotal) + ')'

        if dbrow['type'] == 'ti' or dbrow['type'] == 'to':
            if dbrow['whom1'] == '':
                showwho = dbrow['whom2']
            else:
                showwho = dbrow['whom1']
            whomclass = 'rwhomtrans'
        else:
            showwho = dbrow['whom1']
            whomclass = 'rwhom'

        if h_dateinfuture(str(dbrow['transdate'])):
            classfuture = 'future'

        if counter % 2 == 0:
            classoe = 'recordeven'
        else:
            classoe = 'recordodd'

        markup += '''<div id="b%s" class="%s %s">\
                        <span class="irow0"><input type="button" value="D" onclick="return sendBankDelete('%s','%s');"> <input type="button" value="E" onclick="return getBankEdit('%s');"></span>
                        <span class="rdate">%s</span>
                        <span class="rnum">%s</span>
                        <span class="%s">%s</span>
                        <span class="rup">%s</span>
                        <span class="rdown">%s</span>
                        <span class="%s">%s</span>
                     </div>''' % (dbrow['btransid'], classoe, classfuture, dbrow['bacctid'], dbrow['btransid'], dbrow['btransid'], dbrow['transdate'], dbrow['numnote'], whomclass, showwho, amtup, amtdown, rtotalclass, rtotalshow)
        counter +=1
    return markup


# B.ENTRY.ADD = generates body needed for "Bank Single Add" Section
def b_entry_prepareadd():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts WHERE bacctid=%s"
    cursor.execute(sqlstr, (g_formdata.getvalue('bacctid')))
    dbrow = cursor.fetchone()
    dbcon.close()
    return b_edit_template(mode='add', bacctname=dbrow['bacctname'], btransid="0", bacctid=str(dbrow['bacctid']), transferbtransid="0", transferbacctid="0", transdate="", ttype="", updown="", amt="", numnote="", whom1="", whom2="")


# B.ENTRY.EDIT = generates body needed for "Bank Single Edit" Section
def b_entry_prepareedit():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = """SELECT bt.*, ba.bacctname FROM moneywatch_banktransactions bt \
                INNER JOIN moneywatch_bankaccounts ba ON bt.bacctid=ba.bacctid WHERE bt.btransid=%s"""
    cursor.execute(sqlstr, (g_formdata.getvalue('btransid')))
    dbrow = cursor.fetchone()
    dbcon.close()
    return b_edit_template(mode='edit', bacctname=dbrow['bacctname'], btransid=str(dbrow['btransid']), bacctid=str(dbrow['bacctid']), transferbtransid=str(dbrow['transferbtransid']), transferbacctid=str(dbrow['transferbacctid']), transdate=dbrow['transdate'], ttype=dbrow['type'], updown="", amt="{:.2f}".format(float(dbrow['amt'])), numnote=dbrow['numnote'], whom1=dbrow['whom1'], whom2=dbrow['whom2'])


# created the single template
def b_edit_template(mode, bacctname, btransid, bacctid, transferbtransid, transferbacctid, transdate, ttype, updown, amt, numnote, whom1, whom2):

    if mode == 'edit':
        sendcmd = 'B.ENTRY.EDITSAVE'
        buttonsay = 'Save Edit'
    else:
        sendcmd = 'B.ENTRY.ADDSAVE'
        buttonsay = 'Add New'

    transshow = 'none'
    transsay = 'From'
    # add type options here
    if ttype == 'w':
        typeselect = '<option value="d">Deposit</option><option value="w" selected>Withdraw</option><option value="to">Transfer Out</option><option value="ti">Transfer In</option>'
    elif ttype == 'to':
        typeselect = '<option value="d">Deposit</option><option value="w">Withdraw</option><option value="to" selected>Transfer Out</option><option value="ti">Transfer In</option>'
        transshow = 'block'
        transsay = 'To'
    elif ttype == 'ti':
        typeselect = '<option value="d">Deposit</option><option value="w">Withdraw</option><option value="to">Transfer Out</option><option value="ti" selected>Transfer In</option>'
        transshow = 'block'
        transsay = 'From'
    else: # d = deposit
        typeselect = '<option value="d" selected>Deposit</option><option value="w">Withdraw</option><option value="to">Transfer Out</option><option value="ti">Transfer In</option>'

    markup = '''<form name="beditsingle" id="beditsingle">\
                    <table class="cleantable" width="300">
                        <tr>
                            <td colspan="2" style="box-shadow: 0px 1px 2px #999999;background-color: #ffffff;text-align:center;">%s</td>
                        </tr>
                        <tr>
                            <td class="tdborderright">Action:<br>
                                <select name="ttype" id="beditsingle-ttype" onChange="beditsingle_typechanged(this);">
                                    %s
                                </select>
                            </td>
                            <td>Date:<br><input type="text" name="transdate" id="beditsingle-transdate" size="10" value="%s"></td>
                        </tr>
                        <tr>
                            <td class="tdborderright">Num-Note:<br><input type="text" size="10" placeholder="Num" name="numnote" id="beditsingle-numnote" value="%s"></td>
                            <td>Value:<br><nobr>$<input type="text" size="10" name="amt" id="beditsingle-amt" value="%s" onChange="checkValueDecimals(this, 2);"></nobr></td>
                        </tr>
                        <tr>
                            <td colspan="2">
                            <div id="beditsingle-transblock" style="display: %s">Transfer <span id="beditsingle-transsay">%s</span>:<br><select name="bacctid_transferselected" id="beditsingle-bacctid_transferselected"><option value="0">--none--</option>%s</select></div></td>
                        </tr>
                        <tr>
                            <td colspan="2">
                                Whom:<br>
                                <input type="text" name="whom1" value="%s" id="beditsingle-whom1" size="35" style="margin-bottom: 4px;"/><br>
                                <input type="text" name="whom2" value="%s" placeholder="Memo (optional)" size="35" />
                            </td>
                        </tr>
                        <!--
                        <tr>
                            <td colspan="2">Category:<br><input type="text" name="category" id="autocategories" size="35" /></td>
                        </tr>
                        -->
                    </table>
                    <div style="text-align:right; padding-top: 20px; padding-right: 25px;">
                        <input type="hidden" name="job" value="%s">
                        <input type="hidden" name="bacctname" value="%s">
                        <input type="hidden" name="btransid" value="%s">
                        <input type="hidden" name="bacctid" id="beditsingle-bacctid" value="%s">
                        <input type="hidden" name="transferbtransid" value="%s">
                        <input type="hidden" name="transferbacctid" value="%s">
                        <input type="button" name="doit" VALUE="%s" onClick="beditsingle_validate('%s');">
                    </div>
                </form><br>
                <script>
                    jQuery("#beditsingle-transdate").datepicker({ dateFormat: "yy-mm-dd" });

                    function beditsingle_validate(in_sendjob) {
                        if(jQuery('#beditsingle-transdate').val() == '') {
                            alert("Please provide a transaction date.");
                        } else if(jQuery('#beditsingle-numnote').val() == '') {
                            alert("Please provide a number or note for this transaction.");
                        } else if(jQuery('#beditsingle-amt').val() == '') {
                            alert("Please provide the total amount for this transaction.");
                        } else if(jQuery('#beditsingle-whom1').val() == '') {
                            alert("Please provide the who/whom for this transaction.");
                        } else if((jQuery('#beditsingle-ttype').val() == 'ti' || jQuery('#beditsingle-ttype').val() == 'to') && jQuery('#beditsingle-transferaccount').val() == '0') {
                            alert("Please select the transfer account.");
                        } else {
                            sendCommand(in_sendjob);
                        }
                    }

                    function beditsingle_typechanged(in_obj) {
                        // shows/hides transfer selector
                        if (in_obj.value == "ti") {
                            // transfer in
                            jQuery('#beditsingle-transsay').html('From');
                            jQuery('#beditsingle-transblock').show('slow');
                            jQuery('#beditsingle-whom1').val('[autofill accounts]');
                            jQuery('#beditsingle-numnote').val('TRANS');
                        } else if (in_obj.value == "to") {
                            // transfer out
                            jQuery('#beditsingle-transsay').html('To');
                            jQuery('#beditsingle-transblock').show('slow');
                            jQuery('#beditsingle-whom1').val('[autofill accounts]');
                            jQuery('#beditsingle-numnote').val('TRANS');
                        } else {
                            // d (deposit) or w (withdrawal)
                            jQuery('#beditsingle-transblock').hide('slow');
                        }
                    }

                </script>
        ''' % (bacctname, typeselect, transdate, numnote, amt, transshow, transsay, b_makeselects(transferbacctid,''), whom1, whom2, sendcmd, bacctname, btransid, bacctid, transferbtransid, transferbacctid, buttonsay, sendcmd)

    return markup


def b_prepare_addupdate():
    # get form items
    in_job      = g_formdata.getvalue('job')
    in_date     = g_formdata.getvalue('transdate')
    in_numnote  = g_formdata.getvalue('numnote')
    in_amt      = g_formdata.getvalue('amt')
    in_type     = g_formdata.getvalue('ttype')
    in_whom1     = g_formdata.getvalue('whom1')
    in_bacctname = g_formdata.getvalue('bacctname')
    in_btransid  = int(g_formdata.getvalue('btransid'))                  # (bank transaction id) updates only (hidden field)
    in_bacctid   = int(g_formdata.getvalue('bacctid'))
    in_transferbtransid  = int(g_formdata.getvalue('transferbtransid'))  # updates only (hidden field)
    in_transferbacctid   = int(g_formdata.getvalue('transferbacctid'))   # updates only (hidden field)

    if 'bacctid_transferselected' in g_formdata: # bacctid_transferselected can be hidden and may not be included
        in_bacctid_transferselected = int(g_formdata.getvalue('bacctid_transferselected'))
    else:
        in_bacctid_transferselected = 0

    if 'whom2' in g_formdata: # was coming in as None
        in_whom2 = g_formdata.getvalue('whom2')
    else:
        in_whom2 = ''

    if in_job == 'B.ENTRY.ADDSAVE':
        b_saveadd(btransid=in_btransid, bacctid=in_bacctid, transferbtransid=in_transferbtransid, transferbacctid=in_transferbacctid, transdate=in_date, ttype=in_type, amt=in_amt, numnote=in_numnote, whom1=in_whom1, whom2=in_whom2, bacctid_transferselected=in_bacctid_transferselected)

    if in_job == 'B.ENTRY.EDITSAVE':
        b_saveupdate(btransid=in_btransid, bacctid=in_bacctid, transferbtransid=in_transferbtransid, transferbacctid=in_transferbacctid, transdate=in_date, ttype=in_type, amt=in_amt, numnote=in_numnote, whom1=in_whom1, whom2=in_whom2, bacctid_transferselected=in_bacctid_transferselected)


def b_saveadd(btransid, bacctid, transferbtransid, transferbacctid, transdate, ttype, amt, numnote, whom1, whom2, bacctid_transferselected):
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)

    if ttype == 'w':     # withdrawal
        updown = '-'
    elif ttype == 'to': # transfer out
        updown = '-'
        updownother = '+'
        transferaction = 'ti'
        whom1 = '[' + b_saybacctname(bacctid_transferselected) + ']'
        whom1trans = '[' + b_saybacctname(bacctid) + ']'
    elif ttype == 'ti': # transfer in
        updown = '+'
        updownother = '-'
        transferaction = 'to'
        whom1 = '[' + b_saybacctname(bacctid_transferselected) + ']'
        whom1trans = '[' + b_saybacctname(bacctid) + ']'
    else: # d = deposit
        updown = '+'

    # enter transaction in db
    sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferbtransid, transferbacctid, itransid) \
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 0)"""

    cursor.execute(sqlstr, (bacctid, transdate, ttype, updown, amt, whom1, whom2, numnote, transferbtransid, bacctid_transferselected))
    h_logsql(cursor._executed)
    dbcon.commit()
    btransid_learn1 = cursor.lastrowid
    b_accounttally(bacctid)

    if ttype == 'to' or ttype == 'ti': # do the transfer part
        sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferbtransid, transferbacctid, itransid) \
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 0)"""

        cursor.execute(sqlstr, (bacctid_transferselected, transdate, transferaction , updownother, amt, whom1trans, whom2, numnote, btransid_learn1, bacctid))
        h_logsql(cursor._executed)
        dbcon.commit()
        b_accounttally(bacctid_transferselected)
        btransid_learn2 = cursor.lastrowid

        # update the bank account to show transid
        sqlstr = """UPDATE moneywatch_banktransactions SET \
                    transferbtransid=%s
                    WHERE btransid=%s"""
        cursor.execute(sqlstr, (btransid_learn2, btransid_learn1))
        h_logsql(cursor._executed)
        dbcon.commit()

    dbcon.close()


def b_saveupdate(btransid, bacctid, transferbtransid, transferbacctid, transdate, ttype, amt, numnote, whom1, whom2, bacctid_transferselected):
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)

    # these are the previously saved values -> transferbtransid, transferbacctid

    if ttype == 'w':     # withdrawal
        updown = '-'
    elif ttype == 'to': # transfer out
        updown = '-'
        updownother = '+'
        transferaction = 'ti'
        whom1 = '[' + b_saybacctname(bacctid_transferselected) + ']'
        whom1trans = '[' + b_saybacctname(bacctid) + ']'
    elif ttype == 'ti': # transfer in
        updown = '+'
        updownother = '-'
        transferaction = 'to'
        whom1 = '[' + b_saybacctname(bacctid_transferselected) + ']'
        whom1trans = '[' + b_saybacctname(bacctid) + ']'
    else: # d = deposit
        updown = '+'

    # ---------  [update any bank transfers]  ---------
    if ttype == 'd' or ttype == 'w':
        # was it previously a transfer?
        if transferbtransid > 0:
            # delete the transfer, as this is no longer a transfer type
            # delete bank transaction
            sqlstr = "DELETE FROM moneywatch_banktransactions WHERE bacctid=%s"
            cursor.execute(sqlstr, (transferbtransid))
            h_logsql(cursor._executed)
            dbcon.commit()
            b_accounttally(transferbacctid)
    else:
        # this is a transfer
        # was it previously a transfer?
        if transferbtransid > 0:
            # update the transfer (bacctid may change!)
            sqlstr = """UPDATE moneywatch_banktransactions SET \
                bacctid=%s,
                transdate=%s,
                type=%s,
                updown=%s,
                amt=%s,
                whom1=%s,
                whom2=%s,
                numnote=%s,
                transferbtransid=%s,
                transferbacctid=%s
                WHERE btransid=%s"""
            cursor.execute(sqlstr, (bacctid_transferselected, transdate, transferaction, updownother, amt, whom1trans, whom2, numnote, btransid, bacctid, transferbtransid))
            h_logsql(cursor._executed)
            dbcon.commit()
            b_accounttally(bacctid_transferselected)

        else:
            # insert a transfer
            sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferbtransid, transferbacctid, itransid) \
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 0)"""
            cursor.execute(sqlstr, (bacctid_transferselected, transdate, transferaction, updownother, amt, whom1trans, whom2, numnote, btransid, bacctid))
            h_logsql(cursor._executed)
            dbcon.commit()
            transferbtransid = cursor.lastrowid # use new id
            transferbacctid = bacctid_transferselected
            b_accounttally(bacctid_transferselected)

    # update the master bank entry
    sqlstr = """UPDATE moneywatch_banktransactions SET \
        transdate=%s,
        type=%s,
        updown=%s,
        amt=%s,
        whom1=%s,
        whom2=%s,
        numnote=%s,
        transferbtransid=%s,
        transferbacctid=%s
        WHERE btransid=%s"""
    cursor.execute(sqlstr, (transdate, ttype, updown, amt, whom1, whom2, numnote, transferbtransid, transferbacctid, btransid))
    h_logsql(cursor._executed)
    dbcon.commit()
    b_accounttally(bacctid)


    # B.ENTRY.DELETE = removes a bank entry and possibly a transfer
def b_entry_delete():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_banktransactions WHERE btransid=%s"
    cursor.execute(sqlstr, (g_formdata.getvalue('btransid')))
    dbrow = cursor.fetchone()

    # delete bank transaction
    sqlstr = "DELETE FROM moneywatch_banktransactions WHERE btransid=%s"
    cursor.execute(sqlstr, (dbrow['btransid']))
    h_logsql(cursor._executed)
    dbcon.commit()
    b_accounttally(dbrow['bacctid'])

    if dbrow['splityn'] > 0:
        # delete any splits
        sqlstr = "DELETE FROM moneywatch_banktransactions_splits WHERE btransid=%s"
        cursor.execute(sqlstr, (dbrow['btransid']))
        h_logsql(cursor._executed)
        dbcon.commit()

    if dbrow['transferbtransid'] > 0:
        # delete any transfers
        sqlstr = "DELETE FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (dbrow['transferbtransid']))
        h_logsql(cursor._executed)
        dbcon.commit()
        b_accounttally(dbrow['transferbacctid'])

    dbcon.close()


# B.BULKINTEREST.EDIT = generates body needed for "Interest Bulk Add" utility panel
def b_bulkinterest_edit():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    parent = ''
    javascriptcalls = []

    markup += '''<form name="bbulkinterestedit" id="bbulkinterestedit"><table class="invtable" width="100%">\
                    <tr>
                        <td colspan="2">Date <input type="text" name="bbulkinterest-date" id="bbulkinterest-date" size="10"></td>
                    </tr>
                    <tr>
                        <td style="border-bottom: solid 1px #cccccc;border-top: solid 1px #cccccc;"><strong>Account Name</strong></td>
                        <td style="border-bottom: solid 1px #cccccc;border-top: solid 1px #cccccc;"><strong>Amount</strong></td>
                    </tr>
    '''

    for dbrow in dbrows:
        markup += '''\
                    <tr>
                        <td>%s</td>
                        <td><nobr>$<input type="text" size="8" name="%s-amt" value="" onChange="checkValueDecimals(this, 2);"></nobr></td>
                    </tr>
        ''' % (dbrow['bacctname'], str(dbrow['bacctid']))

    dbcon.close()

    markup += '''</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="B.BULKINTEREST.SAVE"><input type="button" name="doit" VALUE="Save" onClick="sendCommand('B.BULKINTEREST.SAVE');"></div></form><script>'''
    markup += '''jQuery("#bbulkinterest-date").datepicker({ dateFormat: "yy-mm-dd" });'''

    return markup + '</script>'


# B.BULKINTEREST.SAVE = save "Interest Bulk Save" submission
def b_bulkinterest_save():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    in_date = g_formdata.getvalue('bbulkinterest-date')

    for dbrow in dbrows:
        each_amt = g_formdata.getvalue(str(dbrow['bacctid']) + '-amt')
        if each_amt is not None and in_date is not None:
            sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferbtransid, transferbacctid, itransid) \
                        VALUES (%s, %s, 'd', '+', %s, 'Interest', '', 'INT', 0, 0, 0, 0)"""
            cursor.execute(sqlstr, (dbrow['bacctid'], in_date, each_amt))
            h_logsql(cursor._executed)
            dbcon.commit()
            b_accounttally(dbrow['bacctid'])

    dbcon.close()


# B.BULKBILLS.EDIT = generates body needed for "Bills Bulk Add" utility panel
def b_bulkbills_edit():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_bankbills ORDER BY payeename"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    javascriptcalls = []

    markup += '''<form name="bbulkbillsedit" id="bbulkbillsedit"><table class="invtable" width="100%">\
                    <tr>
                        <td style="border-bottom: solid 1px #cccccc;"><strong>Payee Name</strong></td>
                        <td style="border-bottom: solid 1px #cccccc;"><strong>Paid From</strong></td>
                        <td style="border-bottom: solid 1px #cccccc;"><strong>Date</strong></td>
                        <td style="border-bottom: solid 1px #cccccc;"><strong>Amount</strong></td>
                    </tr>
    '''

    for dbrow in dbrows:

        each_datepicker = 'bbulkbillsedit-' + str(dbrow['payeeid']) + '-date'
        javascriptcalls.append(' jQuery("#' + each_datepicker + '").datepicker({ dateFormat: "yy-mm-dd" });')

        markup += '''\
                    <tr>
                        <td>%s</td>
                        <td><select name="%s-fromaccount">%s</select></td>
                        <td><input type="text" name="%s" id="%s" size="10"></td>
                        <td><nobr>$<input type="text" size="8" name="%s-amt" value="" onChange="checkValueDecimals(this, 2);"></nobr></td>
                    </tr>
        ''' % (dbrow['payeename'], str(dbrow['payeeid']), b_makeselects(selected='8', identifier=''), each_datepicker, each_datepicker, str(dbrow['payeeid']))

    dbcon.close()

    markup += '''</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="B.BULKBILLS.SAVE"><input type="button" name="doit" VALUE="Save" onClick="sendCommand('B.BULKBILLS.SAVE');"></div></form><script>'''
    for js in javascriptcalls:
        markup += js

    return markup + '</script>'


# B.BULKBILLS.SAVE = save "Bills Bulk SAVE" submission
def b_bulkbills_save():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_bankbills ORDER BY payeename"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        each_fromacct = g_formdata.getvalue(str(dbrow['payeeid']) + '-fromaccount')
        each_date = g_formdata.getvalue('bbulkbillsedit-' + str(dbrow['payeeid']) + '-date')
        each_amt = g_formdata.getvalue(str(dbrow['payeeid']) + '-amt')

        if each_amt is not None and each_date is not None:
            sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferbtransid, transferbacctid, itransid) \
                        VALUES (%s, %s, 'w', '-', %s, %s, 'Bill', 'EBILLPAY', 0, 0, 0, 0)"""
            cursor.execute(sqlstr, (each_fromacct, each_date, each_amt, dbrow['payeename']))
            h_logsql(cursor._executed)
            dbcon.commit()
            b_accounttally(each_fromacct)

    dbcon.close()


#================================================================================================================
# UTILITIES
#================================================================================================================


# U.UPDATEQUOTES
def u_fetchquotes():
#http://finance.yahoo.com/d/quotes.csv?s=LLL+VFINX&f=snl1d1cjkyr1q
#"LLL","L-3 Communication",66.24,"12/2/2011","+0.23"
#"VFINX","VANGUARD INDEX TR",115.07,"12/1/2011","-0.21"
#stockstring = 'VBINX+LLL'
#   0 = Ticker
#   1 = Name
#   2 = Price
#   3 = Date of Price
#   4 = Change
#   5 = 52 week low
#   6 = (k) 52 week high
#   7 = (y) yield
#   8 = (r1) dividend date (next)
#   9 = (q) dividend date (prev)

    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT DISTINCT ticker FROM moneywatch_invelections WHERE active=1 and fetchquotes=1"
    cursor.execute(sqlstr)

    dbrows = cursor.fetchall()
    stockstring = ""
    for dbrow in dbrows:
      if dbrow == dbrows[0]:
        stockstring = dbrow['ticker']
      else:
        stockstring += '+' + dbrow['ticker']

    try:
        response = urllib2.urlopen('http://finance.yahoo.com/d/quotes.csv?s=' + stockstring + '&f=snl1d1cjkyr1q&e=.csv')
    except urllib2.URLError, e:
        print "There was an error fetching quotes: " + e
        return
        #raise MyException("There was an error fetching quotes: %r" % e)

    csvdatalines = filter(None, response.read().split('\r\n'))
    #csvreader = csv.reader(csvdata)
    #print csvdatalines
    for line in csvdatalines:
        row = line.split(',')
        row[0] = str(row[0].replace('"', ''))
        row[3] = str(row[3].replace('"', ''))
        row[4] = str(row[4].replace('"', ''))
        row[7] = str(row[7].replace('"', ''))
        row[8] = str(row[8].replace('"', ''))
        row[9] = str(row[9].replace('"', ''))

        sqlstr = "UPDATE moneywatch_invelections SET quoteprice=%s, quotechange=%s, quotedate=%s, yield=%s, divdatenext=%s, divdateprev=%s WHERE ticker=%s"
        cursor.execute(sqlstr, (row[2], row[4], h_todaydatetimeformysql(), row[7], row[8], row[9], row[0]))
        dbcon.commit()
    dbcon.close()
    i_electiontallyall()


def u_banktotals():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        b_accounttally(dbrow['bacctid'])
    dbcon.close()


#================================================================================================================
# HELPER FUNCTIONS
#================================================================================================================

def h_showmoney(in_num):
    return locale.currency(in_num, grouping=True)

def h_dateclean(in_date):
    # 4/1'2008 or 12/31'2009 format in
    # 2009-12-31 returned
    sp1 = str(in_date).split("'") # [0] = 4/1, [1] = 2008
    sp2 = sp1[0].split("/") # [0] = 4(month), [1] = 1(day)
    return sp1[1] + '-' + sp2[0].zfill(2) + '-' + sp2[1].zfill(2)

def h_dateinfuture(in_date):
    # 2009-12-31 format in
    # boolean returned
    boom = str(in_date).split("-") # [0] = year, [1] = month, [2] = day
    numdate = int(boom[0] + boom[1] + boom[2])

    # import time
    # time.strftime('%Y-%m-%d %H:%M:%S')

    todaydate = int(time.strftime('%Y%m%d'))
    if numdate > todaydate:
        return True
    else:
        return False

def h_todaydateformysql():
    # returns todays date as 2009-12-31
    # import time
    return time.strftime('%Y-%m-%d')

def h_todaydatetimeformysql():
    # returns todays date as 2009-12-31 HH:MM:SS format
    # import time
    return time.strftime('%Y-%m-%d %H:%M:%S')

def h_dateqiftoint(in_date):
    # 4/1'2008 or 12/31'2009 format in
    # 20091231 int returned
    sp1 = str(in_date).split("'") # [0] = 4/1, [1] = 2008
    sp2 = sp1[0].split("/") # [0] = 4(month), [1] = 1(day)
    return int(sp1[1] + sp2[0].zfill(2) + sp2[1].zfill(2))

def h_datemysqltoint(in_date):
    # 2009-12-31 format in
    # 20091231 int returned
    boom = str(in_date).split("-") # [0] = year, [1] = month, [2] = day
    return int(boom[0] + boom[1] + boom[2])

def h_logsql(in_sqlstr):
    debugout = open(moneywatchconfig.dirlogs + 'sqllog.txt', 'a')
    debugout.write('Entered: ' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "\n" + in_sqlstr + "\n")
    debugout.close()


#================================================================================================================
# GRAPHING
#================================================================================================================

def i_graph():
    dbcon = mdb.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = """SELECT it.*, ie.ielectionname FROM moneywatch_invtransactions it \
                INNER JOIN moneywatch_invelections ie ON it.ielectionid=ie.ielectionid WHERE it.ielectionid=%s ORDER BY it.transdate,it.action"""
    cursor.execute(sqlstr, (g_formdata.getvalue('ielectionid')))
    dbrows = cursor.fetchall()
    #ielectionid, transdate, ticker, updown, action, sharesamt, shareprice, transprice, totalshould

    fundstart = str(dbrows[0]['transdate']).split("-")

    fundstartyear = fundstart[0]
    ielectionname = dbrows[0]['ielectionname']
    ticker = dbrows[0]['ticker']
    stotal = 0
    shareslist = []
    priceslist = []

    for dbrow in dbrows:
        datesplit = str(dbrow['transdate']).split("-") # [0] = year, [1] = month, [2] = day
        if dbrow['updown'] == '+':
            stotal += float(dbrow['sharesamt'])
        else:
            stotal -= float(dbrow['sharesamt'])
        # Date.UTC(1971,  1, 24), 1.92],
        shareslist.append('[ Date.UTC(' + datesplit[0] + ', ' + datesplit[1] + ', ' + datesplit[2] + '), ' + "{:.3f}".format(stotal) + ']')
        priceslist.append('[ Date.UTC(' + datesplit[0] + ', ' + datesplit[1] + ', ' + datesplit[2] + '), ' + "{:.3f}".format(float(dbrow['shareprice'])) + ']')

    dbcon.close()

    return """\

<div id="graphpurchases" style="min-width: 310px; height: 400px; margin: 0 auto"></div>
<div>&nbsp;</div>
<div id="graphprices" style="min-width: 310px; height: 400px; margin: 0 auto"></div>

<script>

    jQuery(function () {
        jQuery('#graphpurchases').highcharts({
            chart: {
                zoomType: 'x',
                spacingRight: 20
            },
            title: {
                text: 'Purchases for: %s [ %s ]'
            },
            xAxis: {
                type: 'datetime',
                maxZoom: 14 * 24 * 3600000, // fourteen days
                title: {
                    text: null
                }
            },
            yAxis: {
                title: {
                    text: 'Shares'
                }
            },
            tooltip: {
                shared: true
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                area: {
                    fillColor: {
                        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1},
                        stops: [
                            [0, Highcharts.getOptions().colors[0]],
                            [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
                        ]
                    },
                    lineWidth: 1,
                    marker: {
                        enabled: true
                    },
                    shadow: true,
                    states: {
                        hover: {
                            lineWidth: 1
                        }
                    },
                    threshold: null
                }
            },

            series: [{
                type: 'area',
                name: 'Shares',
                pointInterval: 24 * 3600 * 1000,
                pointStart: Date.UTC(%s, 0, 01),
                data: [ %s ]
            }]
        });

        jQuery('#graphprices').highcharts({
            chart: {
                zoomType: 'x',
                spacingRight: 20
            },
            title: {
                text: 'Prices for: %s [ %s ]'
            },
            xAxis: {
                type: 'datetime',
                maxZoom: 14 * 24 * 3600000, // fourteen days
                title: {
                    text: null
                }
            },
            yAxis: {
                title: {
                    text: 'Prices'
                }
            },
            tooltip: {
                shared: true
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                area: {
                    fillColor: {
                        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1},
                        stops: [
                            [0, Highcharts.getOptions().colors[0]],
                            [1, Highcharts.Color(Highcharts.getOptions().colors[9]).setOpacity(0).get('rgba')]
                        ]
                    },
                    lineWidth: 1,
                    marker: {
                        enabled: true
                    },
                    shadow: true,
                    states: {
                        hover: {
                            lineWidth: 1
                        }
                    },
                    threshold: null
                }
            },

            series: [{
                type: 'area',
                name: 'Prices',
                pointInterval: 24 * 3600 * 1000,
                pointStart: Date.UTC(%s, 0, 01),
                data: [ %s ]
            }]
        });
    });

</script>""" % (ielectionname, ticker, fundstartyear, ', '.join(shareslist), ielectionname, ticker, fundstartyear, ', '.join(priceslist))
