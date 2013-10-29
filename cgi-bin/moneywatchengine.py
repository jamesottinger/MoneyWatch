#!/usr/bin/python

# sudo su
# wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python
# easy_install pymongo
# easy_install -U pymongo


#===============================================================================
# Code written by James Ottinger
#===============================================================================
import MySQLdb as mdb #sudo apt-get install python-mysqldb
import pymongo
from pymongo import Connection
import cgi, cgitb, os, datetime, locale, urllib2, csv, time

cgitb.enable()
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
g_c = Connection('192.168.15.102', 27017)
g_db = g_c.moneywatch
g_dbauth = ['192.168.15.102', 'xx', 'xxxx', 'devmoney']
g_formdata = cgi.FieldStorage()
dirDebug = '/log/'



'''
CREATE TABLE `devmoney_invelections` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `parentname` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `ticker` varchar(20) DEFAULT NULL,
  `shares` double DEFAULT NULL,
  `active` tinyint(11) DEFAULT NULL,
  `sharesbydividend` double DEFAULT '0',
  `costbasis` double DEFAULT NULL,
  `balance` double DEFAULT NULL,
  `quotedate` datetime DEFAULT NULL,
  `quoteprice` double DEFAULT NULL,
  `quotechange` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=latin1;


CREATE TABLE `devmoney_invtransactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `parentid` int(11) DEFAULT '0',
  `banktransid` int(11) DEFAULT '0',
  `transdate` date DEFAULT NULL,
  `ticker` varchar(20) DEFAULT NULL,
  `updown` varchar(20) DEFAULT NULL,
  `action` varchar(20) DEFAULT NULL,
  `sharesamt` double DEFAULT '0',
  `shareprice` double DEFAULT '0',
  `transprice` double DEFAULT '0',
  `totalshould` double DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=890 DEFAULT CHARSET=latin1;

CREATE TABLE `devmoney_banktransactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `parentid` int(11) NOT NULL,
  `transdate` date NOT NULL,
  `type` varchar(4) NOT NULL,
  `updown` varchar(4) DEFAULT NULL,
  `amt` double NOT NULL,
  `whom1` varchar(255) DEFAULT NULL,
  `whom2` varchar(255) DEFAULT NULL,
  `numnote` varchar(50) DEFAULT NULL,
  `splityn` tinyint(4) DEFAULT '0',
  `transferid` int(11) DEFAULT '0',
  `transferparentid` int(11) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=216 DEFAULT CHARSET=latin1;


CREATE TABLE `devmoney_banktransactions_splits` (
  `accountid` int(11) NOT NULL,
  `transactionid` int(11) NOT NULL,
  `whom1` varchar(255) DEFAULT NULL,
  `whom2` varchar(255) DEFAULT NULL,
  `amt` double NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `devmoney_bankaccounts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `accountname` varchar(255) DEFAULT NULL,
  `mine` tinyint(4) DEFAULT '0',
  `accounttype` varchar(50) DEFAULT NULL,
  `bank` varchar(255) DEFAULT NULL,
  `totalall` double DEFAULT NULL,
  `totaluptotoday` double DEFAULT NULL,
  `todaywas` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

'''


#================================================================================================================
# INVESTMENT
#================================================================================================================

def i_electiontally(in_ticker):
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_invtransactions WHERE ticker='" + in_ticker + "' ORDER BY transdate,action"
    cursor.execute(sqlstr)
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

    sqlstr = """UPDATE devmoney_invelections SET shares=%s, costbasis=%s, sharesbydividend=%s WHERE ticker='%s'""" % ("{:.3f}".format(rtotal), "{:.3f}".format(costbasis), "{:.3f}".format(sharesbydividend), in_ticker)
    cursor.execute(sqlstr)
    dbcon.commit()
    dbcon.close()


def i_makeselectsparents(selected, identifier):
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT DISTINCT(parentname) FROM devmoney_invelections ORDER BY parentname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    for dbrow in dbrows:
        if str(dbrow['parentname']) == selected:
            selectedsay = ' selected'
        else:
            selectedsay = ''
        markup += '<option value="' + identifier + str(dbrow['parentname']) + '"' + selectedsay + '>[Investment] ' + dbrow['parentname'] + '</option>'
    dbcon.close()
    return markup


# I.SUMMARY.GET = Shows Summary of Investment Accounts
def i_summary():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_invelections WHERE shares > 0 AND ticker IS NOT NULL ORDER BY parentname,name"
    cursor.execute(sqlstr)

    markup = '<div class="summary1heading">Investment Accounts</div>'
    markup += '''<table class="invtable">\
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
                    </tr>
    '''
    all_costbasis = 0
    all_market = 0
    all_appres = 0
    all_income = 0
    all_gain = 0
    parent = ''
    parent_costbasis = 0
    parent_market = 0
    parent_income = 0
    parent_appres = 0
    parent_gain = 0
    quotedate = ''

    dbrows = cursor.fetchall()
    for dbrow in dbrows:
        if dbrow['parentname'] != parent:
            if dbrows[0] != dbrow:
                markup += '''\
                                <tr>
                                    <td colspan="4">&nbsp;</td>
                                    <td style="text-align: right;background-color: #efefef;"><!-- cost basis -->%s</td>
                                    <td style="text-align: right;background-color: #efefef;"><!-- market value --><b>%s</b></td>
                                    <td style="text-align: right;background-color: #efefef;"><!-- income -->%s</td>
                                    <td style="text-align: right;background-color: #efefef;"><!-- apprec -->%s</td>
                                    <td style="text-align: right;background-color: #efefef;"><!-- gain -->%s</td>
                                    <td>&nbsp;</td>
                                </tr>
                    ''' % (h_showmoney(parent_costbasis), h_showmoney(parent_market), h_showmoney(parent_income), h_showmoney(parent_appres), h_showmoney(parent_gain))
                parent_costbasis = 0
                parent_market = 0
                parent_income = 0
                parent_appres = 0
                parent_gain = 0
                quotedate = str(dbrow['quotedate'])
            markup += '<tr class="invtablehead"><td colspan="9"><b>' + dbrow['parentname'] + '</b></td></tr>'
            parent = dbrow['parentname']

        each_market = dbrow['shares'] * dbrow['quoteprice']
        each_appres = (dbrow['shares'] * dbrow['quoteprice']) - dbrow['costbasis']
        each_apprecclass = 'numpos'
        if each_appres <= 0:
            each_apprecclass = 'numneg'
        each_income = dbrow['sharesbydividend'] * dbrow['quoteprice']
        each_gain = (((dbrow['shares'] * dbrow['quoteprice']) - dbrow['costbasis']) + (dbrow['sharesbydividend'] * dbrow['quoteprice']))
        parent_costbasis += dbrow['costbasis']
        parent_market += each_market
        parent_appres += each_appres
        parent_income += each_income
        parent_gain += each_gain
        all_costbasis += dbrow['costbasis']
        all_market += each_market
        all_appres += each_appres
        all_income += each_income
        all_gain += each_gain

        markup += '''\
                    <tr>
                        <td>%s</td>
                        <td><a href="#" onClick="getInvElection('%s');">%s</a></td>
                        <td style="text-align: right;">%s</td>
                        <td style="text-align: right;">%s</td>
                        <td style="text-align: right;">%s</td>
                        <td style="text-align: right;"><!-- market value --><b>%s</b></td>
                        <td style="text-align: right;"><!-- income -->%s</td>
                        <td style="text-align: right;" class="%s"><!-- apprec -->%s</td>
                        <td style="text-align: right;"><!-- gain -->%s</td>
                        <td>[<a href="http://www.google.com/finance?q=%s" target="_blank">G</a>] [<a href="http://finance.yahoo.com/q?s=%s" target="_blank">Y!</a>] [%s]</td>
                    </tr>
        ''' % (dbrow['ticker'], dbrow['ticker'], dbrow['name'], "{:.3f}".format(dbrow['shares']), h_showmoney(dbrow['quoteprice']), h_showmoney(dbrow['costbasis']), h_showmoney(each_market), h_showmoney(each_income), each_apprecclass, h_showmoney(each_appres), h_showmoney(each_gain), dbrow['ticker'], dbrow['ticker'], dbrow['divschedule'])

    markup += '''\
                    <tr>
                        <td colspan="4">&nbsp;</td>
                        <td style="text-align: right;background-color: #efefef;"><!-- cost basis -->%s</td>
                        <td style="text-align: right;background-color: #efefef;"><!-- market value --><b>%s</b></td>
                        <td style="text-align: right;background-color: #efefef;"><!-- income -->%s</td>
                        <td style="text-align: right;background-color: #efefef;"><!-- apprec -->%s</td>
                        <td style="text-align: right;background-color: #efefef;"><!-- gain -->%s</td>
                        <td>&nbsp;</td>
                    </tr>
        ''' % (h_showmoney(parent_costbasis), h_showmoney(parent_market), h_showmoney(parent_income), h_showmoney(parent_appres), h_showmoney(parent_gain))


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
    return quotedate + '<br>' + markup + '</table>'


# I.ELECTION.GET
def i_electionget():
    markup = ''
    counter = 0
    rtotal = 0
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_invtransactions WHERE ticker='" + g_formdata.getvalue('ticker') + "' ORDER BY transdate,action"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()
    #parentid, transdate, ticker, updown, action, sharesamt, shareprice, transprice, totalshould

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

        identifier = dbrow['ticker'] + str(dbrow['id'])

        markup += '''<div class="%s" id="%s">\
                        <span class="irow0"><input type="button" value="D" onclick="return sendInvDelete('%s','%s');"> <input type="button" value="E" onclick="return getInvElectionEdit('%s', '%s');"></span>
                        <span class="irow1"> %s</span>
                        <span class="irow2">%s</span>
                        <span class="irow3"> ($%s @ $%s each)</span>
                        <span class="irow4">%s</span>
                        <span class="irow5">%s</span>
                        <span class="irow6pos"> %s %s</span>
                     </div>''' % (classoe, identifier, dbrow['ticker'], str(dbrow['id']), dbrow['ticker'], str(dbrow['id']), dbrow['transdate'], dbrow['action'], "{:.2f}".format(float(dbrow['transprice'])), "{:.3f}".format(float(dbrow['shareprice'])), amtup, amtdown, "{:.3f}".format(rtotal), showcheck)
                    #//$R .= $ecounter . "==" . $election['shares'] . "|"; //'<a href="#" onClick="return bank_gettransactions(' . "'" . $document['name'] . "');" . '">' . $document['name'] . " $" .  number_format($document['total'], 2, '.', ',') . "</a><br>";
        counter +=1
        markup += '<div id="scrollmeinv"></div>'
    return markup


# I.BULKADD.EDIT = generates body needed for "Investment Bulk Add" utility panel
def i_bulkadd_edit():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_invelections WHERE ticker IS NOT NULL AND active = 1 ORDER BY parentname,name"
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
                    </tr>
    '''
    for dbrow in dbrows:

        if dbrow['parentname'] != parent:
            markup += '<tr><td colspan="7" style="background-color: #efefef;"><span class="bigbluetext">' + dbrow['parentname'] + '</span></td></tr>'
            parent = dbrow['parentname']

        each_datepicker = dbrow['ticker'] + str(dbrow['id']) + '-date'
        javascriptcalls.append(' jQuery("#' + each_datepicker + '").datepicker({ dateFormat: "yy-mm-dd" });')

        markup += '''\
                    <tr>
                        <td>%s<input type="hidden" name="%s-parentid" value="%s"></td>
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
                    </tr>
        ''' % (dbrow['name'], dbrow['ticker'], dbrow['id'], dbrow['ticker'], dbrow['ticker'], b_makeselects(selected='', identifier=''), each_datepicker, each_datepicker, dbrow['ticker'], dbrow['ticker'], dbrow['ticker'])

        #markup += '<div><span>' +  dbrow['name'] + '</span><span><input type="text" class="tickerentry" size="8" name="' + dbrow['ticker'] + '-shares" value=""></span></div>'
    dbcon.close()

    markup += '''</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="I.BULKADD.SAVE"><input type="button" name="doit" VALUE="Save" onClick="sendCommand('I.BULKADD.SAVE');"></div></form><script>'''
    for js in javascriptcalls:
        markup += js

    return markup + '</script>'


# I.BULKADD.SAVE = save "Investment Bulk Add" submission
def i_bulkadd_save():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_invelections WHERE ticker IS NOT NULL AND active = 1 ORDER BY parentname,name"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        each_shares = g_formdata.getvalue(dbrow['ticker'] + '-shares')
        each_cost = g_formdata.getvalue(dbrow['ticker'] + '-cost') # cost of full sale
        each_date = g_formdata.getvalue(dbrow['ticker'] + str(dbrow['id']) + '-date')
        if each_shares is not None and each_cost is not None and each_date is not None:
            each_parentid = int(g_formdata.getvalue(dbrow['ticker'] + '-parentid'))
            each_fromid = int(g_formdata.getvalue(dbrow['ticker'] + '-fromaccount'))
            each_action = g_formdata.getvalue(dbrow['ticker'] + '-action')

            i_saveadd(ticker=dbrow['ticker'], tdate=each_date, shares=each_shares, cost=each_cost, fromacct=each_fromid, action=each_action, parentid=each_parentid, fundname=dbrow['name'])

    dbcon.close()


# I.ENTRY.ADD = generates body needed for "Investment Single Add" Section
def i_entry_prepareadd():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_invelections WHERE ticker='" + g_formdata.getvalue('ticker') + "'"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()
    dbcon.close()

    for dbrow in dbrows:
        return i_edit_template(mode='add', fundname=dbrow['name'], ticker=dbrow['ticker'], transid="", parentid=str(dbrow['id']), banktransid="", tdate="", action="", shares="", cost="", fundsorigin=0)

# I.ENTRY.EDIT = generates body needed for "Investment Single Edit" Section
def i_entry_prepareedit():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = """SELECT it.*, ie.name AS fundname, ie.id AS fundsorigin FROM devmoney_invtransactions it \
                INNER JOIN devmoney_invelections ie ON it.parentid=ie.id WHERE it.id=%s""" % (g_formdata.getvalue('transid'))
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()
    dbcon.close()

    for dbrow in dbrows:
        return i_edit_template(mode='edit', fundname=dbrow['fundname'], ticker=dbrow['ticker'], transid=str(dbrow['id']), parentid=str(dbrow['parentid']), banktransid=dbrow['banktransid'], tdate=str(dbrow['transdate']), action=dbrow['action'], shares="{:.3f}".format(float(dbrow['sharesamt'])), cost="{:.2f}".format(float(dbrow['transprice'])), fundsorigin=str(dbrow['fundsorigin']))


# created the single
def i_edit_template(mode, fundname, ticker, transid, parentid, banktransid, tdate, action, shares, cost, fundsorigin):

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

                        <input type="hidden" name="fundname" value="%s">
                        <input type="hidden" name="parentid" value="%s">

                        <input type="hidden" name="transid" value="%s">
                        <input type="hidden" name="banktransid" value="%s">
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
        ''' % (fundname, ticker, b_makeselects(selected=fundsorigin, identifier=''), actionselect, tdate, shares, cost, sendcmd, ticker, fundname, parentid, transid, banktransid, buttonsay, sendcmd)

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
    in_date     = g_formdata.getvalue('tradedate')
    in_shares   = g_formdata.getvalue('shares')
    in_cost     = g_formdata.getvalue('cost')
    in_action   = g_formdata.getvalue('action')
    in_banktransid = g_formdata.getvalue('banktransid')      # updates only (hidden field)
    in_transid     = g_formdata.getvalue('transid')          # updates only (hidden field)
    in_parentid = int(g_formdata.getvalue('parentid'))
    in_fundname = g_formdata.getvalue('fundname')
    in_fromid   = int(g_formdata.getvalue('fromaccount'))

    if in_job == 'I.ENTRY.ADDSAVE':
        i_saveadd(ticker=in_ticker, tdate=in_date, shares=in_shares, cost=in_cost, fromacct=in_fromid, action=in_action, parentid=in_parentid, fundname=in_fundname)

    if in_job == 'I.ENTRY.EDITSAVE':
        i_saveupdate(ticker=in_ticker, tdate=in_date, shares=in_shares, cost=in_cost, fromacct=in_fromid, action=in_action, parentid=in_parentid, fundname=in_fundname, banktransid=in_banktransid, transid=in_transid)



def i_saveadd(ticker, tdate, shares, cost, fromacct, action, parentid, fundname):
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)

    costpershare = "{:.3f}".format(float(cost) / float(shares))

    if action == 'SELL' or action == 'SELLX':
        updown = '-'
    else: # BUY BUYX REINVDIV
        updown = '+'

    banktransid = 0
    transferid = 0
    # do bank insert first, since we will need to learn the transaction id
    if fromacct > 0: # was this bank funded?
        # enter bank transaction
        # Category: Buy Investment/CD: The Name Of Account
        # Buy: Mutual Fund Name 4.439 @ $22.754
        whom1 = 'Buy : ' + ticker + ' ' + shares + ' @ ' + h_showmoney(float(cost) / float(shares))
        whom2 = 'Buy Investment/CD: ' + fundname
        sqlstr = """INSERT INTO devmoney_banktransactions (parentid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferid, transferparentid) \
                            VALUES (%s, '%s', 'w', '-', %s, '%s', '%s', 'INV', 0, 0, 0)""" % (fromacct, tdate, cost, whom1, whom2)
        h_logsql(sqlstr)
        cursor.execute(sqlstr)
        dbcon.commit()
        b_accounttally(fromacct)
        banktransid = cursor.lastrowid

    # enter transaction in db
    sqlstr = """INSERT INTO devmoney_invtransactions (parentid, banktransid, transdate, ticker, updown, action, sharesamt, shareprice, transprice, totalshould)  \
              VALUES (%s, %s, '%s', '%s', '%s', '%s', %s, %s, %s, 0)""" % (parentid, banktransid, tdate, ticker, updown, action, shares, costpershare, cost)
    h_logsql(sqlstr)
    cursor.execute(sqlstr)
    dbcon.commit()
    i_electiontally(ticker)

    if fromacct > 0: # was this bank funded?
        # update the bank account to show transid
        sqlstr = """UPDATE devmoney_banktransactions SET \
                    transferid=%s
                    WHERE id=%s""" % (cursor.lastrowid, banktransid)
        h_logsql(sqlstr)
        cursor.execute(sqlstr)
        dbcon.commit()

    dbcon.close()



def i_saveupdate(ticker, tdate, shares, cost, fromacct, action, parentid, fundname, banktransid, transid):
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)

    costpershare = "{:.3f}".format(float(cost) / float(shares))

    if action == 'SELL' or action == 'SELLX':
        updown = '-'
    else: # BUY BUYX REINVDIV
        updown = '+'

    # ---------  [update investment transaction]  ---------
    # if the transactionid was 0 but now we have a fromacct, we need to create a bank transaction to match the investment update
    if banktransid == 0 and fromacct > 0:
        # need to create a bank entry

        # enter bank transaction
        # Category: Buy Investment/CD: The Name Of Account
        # Buy: Mutual Fund Name 4.439 @ $22.754
        whom1 = 'Buy : ' + ticker + ' ' + shares + ' @ ' + h_showmoney(costpershare)
        whom2 = 'Buy Investment/CD: ' + fundname
        sqlstr = """INSERT INTO devmoney_banktransactions (parentid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferid, transferparentid) \
                            VALUES (%s, '%s', 'w', '%s', %s, '%s', '%s', 'INV', 0, %s, 0)""" % (fromacct, tdate, updown, cost, whom1, whom2, transid)
        h_logsql(sqlstr)
        cursor.execute(sqlstr)
        dbcon.commit()
        banktransid = cursor.lastrowid # use new banktransid
        b_accounttally(fromacct)

    # update the investment entry
    sqlstr = """UPDATE devmoney_invtransactions SET \
        transdate='%s',
        action='%s',
        updown='%s',
        sharesamt=%s,
        shareprice=%s,
        transprice=%s,
        banktransid=%s,
        WHERE id=%s""" % (tdate, action, updown, shares, costpershare, cost, fromacct, banktransid, transid)
    h_logsql(sqlstr)
    cursor.execute(sqlstr)
    dbcon.commit()
    i_electiontally(ticker)

    # ---------  [update bank transaction]  ---------
    # devmoney_banktransactions.parentid (fromacct
    # devmoney_banktransactions.id  <== devmoney_invtransactions.banktransid

    if banktransid > 0: # was this bank funded?

        sqlstr = "SELECT parentid FROM devmoney_banktransactions WHERE id=" + str(banktransid)
        h_logsql(sqlstr)
        cursor.execute(sqlstr)
        dbrow = cursor.fetchone()
        bankacctid = dbrow['parentid'] # need to parent bank acct for re-tally

        if fromacct == 0:
            # not assiciated with a bank account anymore, delete the bank entry
            sqlstr = """DELETE FROM devmoney_banktransactions WHERE id=%s""" % (tbanktransid)
            h_logsql(sqlstr)
            cursor.execute(sqlstr)
            dbcon.commit()

            b_accounttally(bankacctid)

        else:
            # update the bank account transaction with new details
            # enter bank transaction
            # Category: Buy Investment/CD: The Name Of Account
            # Buy: Mutual Fund Name 4.439 @ $22.754
            whom1 = 'Buy : ' + ticker + ' ' + shares + ' @ ' + h_showmoney(costpershare)
            whom2 = 'Buy Investment/CD: ' + fundname

            sqlstr = """UPDATE devmoney_banktransactions SET \
                parentid=%s
                transdate='%s',
                type='i',
                amt=%s,
                whom1='%s',
                whom2='%s',
                transferid=%s
                WHERE id=%s""" % (fromacct, tdate, cost, whom1, whom2, transid, banktransid)
            h_logsql(sqlstr)
            cursor.execute(sqlstr)
            dbcon.commit()

            b_accounttally(fromacct)
            if fromacct != bankacctid:
                b_accounttally(bankacctid)

    dbcon.close()


    # I.ENTRY.DELETE = removes an investment entry and possibly a transfer
def i_entry_delete():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_invtransactions WHERE id=" + g_formdata.getvalue('transid')
    cursor.execute(sqlstr)
    dbrow = cursor.fetchone()

    # delete inv transaction
    sqlstr = """DELETE FROM devmoney_invtransactions WHERE id=%s""" % (str(dbrow['id']))
    h_logsql(sqlstr)
    cursor.execute(sqlstr)
    dbcon.commit()
    i_accounttally(dbrow['parentid'])

    dbcon.close()


# I.ENTRY.ADD = generates body needed for "Investment Single Add" Section
def i_entry_edit():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_invelections WHERE ticker IS NOT NULL AND active = 1 AND ticker='" + g_formdata.getvalue('ticker') + "' ORDER BY parentname,name"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    parent = ''
    javascriptcalls = []

    markup += '''<form name="ibulkedit" id="ibulkedit"><table class="cleantable">'''
    for dbrow in dbrows:

        if dbrow['parentname'] != parent:
            #markup += '<tr><td colspan="2" style="background-color: #efefef;"><span class="bigbluetext">' + dbrow['parentname'] + '</span></td></tr>'
            parent = dbrow['parentname']

        each_datepicker = dbrow['ticker'] + str(dbrow['id']) + '-date'
        javascriptcalls.append(' jQuery("#' + each_datepicker + '").datepicker({ dateFormat: "yy-mm-dd" });')

        markup += '''\
                    <tr>
                        <td colspan="2" style="box-shadow: 0px 1px 2px #999999;background-color: #ffffff;">%s<input type="hidden" name="%s-parentid" value="%s"> [ <b>%s</b> ]</td>
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
        ''' % (dbrow['name'], dbrow['ticker'], dbrow['id'], dbrow['ticker'], dbrow['ticker'], b_makeselects(selected='', identifier=''), each_datepicker, each_datepicker, dbrow['ticker'], dbrow['ticker'], dbrow['ticker'])

        #markup += '<div><span>' +  dbrow['name'] + '</span><span><input type="text" class="tickerentry" size="8" name="' + dbrow['ticker'] + '-shares" value=""></span></div>'
    dbcon.close()

    markup += '</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="I.ENTRY.ADD"><input type="button" name="doit" VALUE="Add New" onClick="sendCommand("I.BULKADD.SAVE");"></div></form><script>'
    for js in javascriptcalls:
        markup += js

    return markup + '</script>'






#================================================================================================================
# BANK
#================================================================================================================

def b_accounttally(in_account):
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_banktransactions WHERE parentid=" + str(in_account) + " ORDER BY transdate,amt"
    cursor.execute(sqlstr)
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

    sqlstr = """UPDATE devmoney_bankaccounts SET totalall=%s, totaluptotoday=%s, todaywas='%s' WHERE id=%s""" % ("{:.2f}".format(float(totalall)), "{:.2f}".format(float(totaluptotoday)), h_todaydateformysql(), str(in_account))
    cursor.execute(sqlstr)
    dbcon.commit()
    dbcon.close()


def b_makeselects(selected,identifier):
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_bankaccounts ORDER BY accountname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    for dbrow in dbrows:
        if str(dbrow['id']) == selected:
            selectedsay = ' selected'
        else:
            selectedsay = ''
        markup += '<option value="' + identifier + str(dbrow['id']) + '"' + selectedsay + '>[Bank] ' + dbrow['accountname'] + '</option>'
    dbcon.close()
    return markup


# B.SUMMARY.GET = Shows Summary of Bank Accounts
def b_summary():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_bankaccounts ORDER BY accountname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = '<div class="summary1heading">Bank Accounts</div>'
    markup += '''<table class="invtable">\
                    <tr style="background-color: #efefef;">
                        <td>Bank</td>
                        <td width="326">Account</td>
                        <td>Value</td>
                        <td>My(Today)</td>
                        <td>My</td>
                    </tr>
    '''
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
                    </tr>''' % (dbrow['bank'], dbrow['id'], dbrow['accountname'], h_showmoney(dbrow['totalall']), ownvaluetoday, ownvalueextended)

    dbcon.close()
    markup += '''\
                <tr>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    <td class="invtotalsbottom" style="width:60px;text-align: right;"><!-- MINE - value current/today --><b>%s</b>  <input type="hidden" id="networth-banks" name="networth-banks" value="%s"></td>
                    <td style="text-align: right;"><!-- MINE - value extended --></td>
                </tr>''' % (h_showmoney(totalmytoday),totalmytoday)

    return markup + '</table>'


# B.ACCOUNT.GET
def b_accountget():

    markup = ''
    counter = 0
    rtotal = 0
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)

    sqlstr = "SELECT * FROM devmoney_banktransactions WHERE parentid=" + g_formdata.getvalue('parentid') + " ORDER BY transdate,numnote"
    cursor.execute(sqlstr)
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

        if dbrow['type'] == 't':
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
                     </div>''' % (dbrow['id'], classoe, classfuture, dbrow['parentid'], dbrow['id'], dbrow['id'], dbrow['transdate'], dbrow['numnote'], whomclass, showwho, amtup, amtdown, rtotalclass, rtotalshow)
        counter +=1
    return markup


# B.ENTRY.ADD = generates body needed for "Bank Single Add" Section
def b_entry_prepareadd():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_bankaccounts WHERE id=" + g_formdata.getvalue('bankacctid')
    cursor.execute(sqlstr)
    dbrow = cursor.fetchone()
    dbcon.close()
    return b_edit_template(mode='add', thisname=dbrow['accountname'], thisid="0", thisparentid=str(dbrow['id']), transferid="0", transferparentid="0", tdate="", ttype="", updown="", amt="", numnote="", whom1="", whom2="")


# B.ENTRY.EDIT = generates body needed for "Bank Single Edit" Section
def b_entry_prepareedit():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = """SELECT bt.*, ba.accountname AS accountname, ba.id AS thisid FROM devmoney_banktransactions bt \
                INNER JOIN devmoney_bankaccounts ba ON bt.parentid=ba.id WHERE bt.id=%s""" % (g_formdata.getvalue('transid'))
    cursor.execute(sqlstr)
    dbrow = cursor.fetchone()
    dbcon.close()
    return b_edit_template(mode='edit', thisname=dbrow['accountname'], thisid=str(dbrow['thisid']), thisparentid=str(dbrow['parentid']), transferid=str(dbrow['transferid']), transferparentid=str(dbrow['transferparentid']), tdate=dbrow['transdate'], ttype=dbrow['type'], updown="", amt="{:.2f}".format(float(dbrow['amt'])), numnote=dbrow['numnote'], whom1=dbrow['whom1'], whom2=dbrow['whom2'])


# created the single template
def b_edit_template(mode, thisname, thisid, thisparentid, transferid, transferparentid, tdate, ttype, updown, amt, numnote, whom1, whom2):

    if mode == 'edit':
        sendcmd = 'B.ENTRY.EDITSAVE'
        buttonsay = 'Save Edit'
    else:
        sendcmd = 'B.ENTRY.ADDSAVE'
        buttonsay = 'Add New'

    # add type options here
    if ttype == 'w':
        typeselect = '<option value="d">Deposit</option><option value="w" selected>Withdraw</option><option value="to">Transfer Out</option><option value="ti">Transfer In</option>'
    elif ttype == 'to':
        typeselect = '<option value="d">Deposit</option><option value="w">Withdraw</option><option value="to" selected>Transfer Out</option><option value="ti">Transfer In</option>'
    elif ttype == 'ti':
        typeselect = '<option value="d">Deposit</option><option value="w">Withdraw</option><option value="to">Transfer Out</option><option value="ti" selected>Transfer In</option>'
    else: # d = deposit
        typeselect = '<option value="d" selected>Deposit</option><option value="w">Withdraw</option><option value="to">Transfer Out</option><option value="ti">Transfer In</option>'

    markup = '''<form name="beditsingle" id="beditsingle">\
                    <table class="cleantable" width="300">
                        <tr>
                            <td colspan="2" style="box-shadow: 0px 1px 2px #999999;background-color: #ffffff;text-align:center;">%s</td>
                        </tr>
                        <tr>
                            <td class="tdborderright">Action:<br>
                                <select name="ttype" id="addbanktype" onChange="beditsingle_typechanged(this);">
                                    %s
                                </select>
                            </td>
                            <td>Date:<br><input type="text" name="transdate" id="beditsingle-transdate" size="10" value="%s"></td>
                        </tr>
                        <tr>
                            <td class="tdborderright">Num-Note:<br><input type="text" size="10" placeholder="Num" name="numnote" id="beditsingle-numnote" value="%s"></td>
                            <td>Value:<br><nobr>$<input type="text" size="8" name="amt" id="beditsingle-amt" value="%s" onChange="checkValueDecimals(this, 2);"></nobr></td>
                        </tr>
                        <tr>
                            <td colspan="2">
                            <div id="beditsingle-transblock" style="display: none">Transfer <span id="beditsingle-transsay">To</span>:<br><select name="transferaccount"><option value="0">--none--</option>%s</select></div></td>
                        </tr>
                        <tr>
                            <td colspan="2">
                                Whom:<br>
                                <input type="text" name="whom1" value="%s" id="beditsingle-whom1" size="35" style="margin-bottom: 4px;"/><br>
                                <input type="text" name="whom2" value="%s" placeholder="Memo (optional)" size="35" />
                            </td>
                        </tr>
                        <tr>
                            <td colspan="2">Category:<br><input type="text" name="category" id="autocategories" size="35" /></td>
                        </tr>
                    </table>
                    <div style="text-align:right; padding-top: 20px; padding-right: 25px;">
                        <input type="hidden" name="job" value="%s">
                        <input type="hidden" name="thisname" value="%s">
                        <input type="hidden" name="thisid" value="%s">
                        <input type="hidden" name="thisparentid" id="beditsingle-thisparentid" value="%s">
                        <input type="hidden" name="transferid" value="%s">
                        <input type="hidden" name="transferparentid" value="%s">
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
                        } else if (in_obj.value == "to") {
                            // transfer out
                            jQuery('#beditsingle-transsay').html('To');
                            jQuery('#beditsingle-transblock').show('slow');
                        } else {
                            // d (deposit) or w (withdrawal)
                            jQuery('#beditsingle-transblock').hide('slow');
                        }
                    }

                </script>
        ''' % (thisname, typeselect, tdate, numnote, amt, b_makeselects(transferparentid,''), whom1, whom2, sendcmd, thisname, thisid, thisparentid, transferid, transferparentid, buttonsay, sendcmd)

    return markup


def b_prepare_addupdate():
    # get form items
    in_job      = g_formdata.getvalue('job')
    in_date     = g_formdata.getvalue('transdate')
    in_numnote  = g_formdata.getvalue('numnote')
    in_amt      = g_formdata.getvalue('amt')
    in_type     = g_formdata.getvalue('ttype')
    in_whom1    = g_formdata.getvalue('whom1')
    in_whom2    = g_formdata.getvalue('whom2')
    in_thisname = g_formdata.getvalue('thisname')
    in_thisid       = int(g_formdata.getvalue('thisid'))                  # (transaction id) updates only (hidden field)
    in_thisparentid = int(g_formdata.getvalue('thisparentid'))
    in_transferid         = int(g_formdata.getvalue('transferid'))        # updates only (hidden field)
    in_transferparentid   = int(g_formdata.getvalue('transferparentid'))  # updates only (hidden field)

    if 'transferaccount' in g_formdata: # transferaccount can be hidden and may not be included
        in_transferacct = g_formdata.getvalue('transferaccount')
    else:
        in_transferacct = '0'

    if in_job == 'B.ENTRY.ADDSAVE':
        b_saveadd(thisid=in_thisid, thisparentid=in_thisparentid, transferid=in_transferid, transferparentid=in_transferparentid, tdate=in_date, ttype=in_type, amt=in_amt, numnote=in_numnote, whom1=in_whom1, whom2=in_whom2, transferacct=in_transferacct)

    if in_job == 'B.ENTRY.UPDATESAVE':
        b_saveupdate(thisid=in_thisid, thisparentid=in_thisparentid, transferid=in_transferid, transferparentid=in_transferparentid, tdate=in_date, ttype=in_type, amt=in_amt, numnote=in_numnote, whom1=in_whom1, whom2=in_whom2, transferacct=in_transferacct)


def b_saveadd(thisid, thisparentid, transferid, transferparentid, tdate, ttype, amt, numnote, whom1, whom2, transferacct):
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)

    if ttype == 'w':     # withdrawal
        updown = '-'
    elif ttype == 'to': # transfer out
        updown = '-'
        updownother = '+'
        actiontrans = 'ti'
    elif ttype == 'ti': # transfer in
        updown = '+'
        updownother = '-'
        actiontrans = 'to'
    else: # d = deposit
        updown = '+'

    # enter transaction in db
    sqlstr = """INSERT INTO devmoney_banktransactions (parentid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferid, transferparentid) \
                            VALUES (%s, '%s', '%s', '%s', %s, '%s', '%s', '%s', 0, %s, %s)""" % (thisparentid, tdate, ttype, updown, amt, whom1, whom2, numnote, transferid, transferparentid)
    h_logsql(sqlstr)
    cursor.execute(sqlstr)
    dbcon.commit()
    firsttransid = cursor.lastrowid
    b_accounttally(thisparentid)

    if ttype == 'to' or ttype == 'ti': # do the transfer part
        sqlstr = """INSERT INTO devmoney_banktransactions (parentid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferid, transferparentid) \
                            VALUES (%s, '%s', '%s', '%s', %s, '%s', '%s', '%s', 0, %s, %s)""" % (transferacct, tdate, actiontrans , updownother, amt, whom1, whom2, numnote, firsttransid, transferparentid)
        h_logsql(sqlstr)
        cursor.execute(sqlstr)
        dbcon.commit()
        b_accounttally(transferacct)
        sectransid = cursor.lastrowid

        # update the bank account to show transid
        sqlstr = """UPDATE devmoney_banktransactions SET \
                    transferid=%s
                    WHERE id=%s""" % (sectransid, firsttransid)
        h_logsql(sqlstr)
        cursor.execute(sqlstr)
        dbcon.commit()

    dbcon.close()


    # B.ENTRY.DELETE = removes a bank entry and possibly a transfer
def b_entry_delete():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_banktransactions WHERE id=" + g_formdata.getvalue('transid')
    cursor.execute(sqlstr)
    dbrow = cursor.fetchone()

    # delete bank transaction
    sqlstr = """DELETE FROM devmoney_banktransactions WHERE id=%s""" % (str(dbrow['id']))
    h_logsql(sqlstr)
    cursor.execute(sqlstr)
    dbcon.commit()
    b_accounttally(dbrow['parentid'])

    if dbrow['splityn'] > 0:
        # delete any splits
        sqlstr = """DELETE FROM devmoney_banktransactions_splits WHERE transactionid=%s""" % (str(dbrow['id']))
        h_logsql(sqlstr)
        cursor.execute(sqlstr)
        dbcon.commit()

    if dbrow['transferid'] > 0:
        # delete any transfers
        sqlstr = """DELETE FROM devmoney_banktransactions WHERE transactionid=%s""" % (str(dbrow['transferid']))
        h_logsql(sqlstr)
        cursor.execute(sqlstr)
        dbcon.commit()
        b_accounttally(dbrow['transferparentid'])

    dbcon.close()


# B.BULKINTEREST.EDIT = generates body needed for "Interest Bulk Add" utility panel
def b_bulkinterest_edit():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_bankaccounts ORDER BY accountname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    parent = ''
    javascriptcalls = []

    markup += '''<form name="bbulkinterestedit" id="bbulkinterestedit"><table class="invtable">\
                    <tr>
                        <td colspan="2">Date <input type="text" name="bbulkinterest-date" id="bbulkinterest-date" size="10"></td>
                    </tr>
                    <tr>
                        <td><strong>Account Name</strong></td>
                        <td><strong>Amount</strong></td>
                    </tr>
    '''

    for dbrow in dbrows:
        markup += '''\
                    <tr>
                        <td>%s</td>
                        <td><nobr>$<input type="text" size="8" name="%s-amt" value="" onChange="checkValueDecimals(this, 2);"></nobr></td>
                    </tr>
        ''' % (dbrow['accountname'], str(dbrow['id']))

    dbcon.close()

    markup += '''</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="B.BULKINTEREST.SAVE"><input type="button" name="doit" VALUE="Save" onClick="sendCommand('B.BULKINTEREST.SAVE');"></div></form><script>'''
    markup += '''jQuery("#bbulkinterest-date").datepicker({ dateFormat: "yy-mm-dd" });'''

    return markup + '</script>'


# B.BULKINTEREST.SAVE = save "Interest Bulk Save" submission
def b_bulkinterest_save():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_bankaccounts ORDER BY accountname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    in_date = g_formdata.getvalue('bbulkinterest-date')

    for dbrow in dbrows:
        each_amt = g_formdata.getvalue(str(dbrow['id']) + '-amt')
        if each_amt is not None and in_date is not None:
            sqlstr = """INSERT INTO devmoney_banktransactions (parentid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferid, transferparentid) \
                                VALUES (%s, '%s', 'd', '+', %s, 'Interest', '', 'INT', 0, 0, 0)""" % (str(dbrow['id']), in_date, each_amt)
            h_logsql(sqlstr)
            cursor.execute(sqlstr)
            dbcon.commit()
            b_accounttally(dbrow['id'])

    dbcon.close()


# B.BULKBILLS.EDIT = generates body needed for "Bills Bulk Add" utility panel
def b_bulkbills_edit():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_bankbills ORDER BY payeename"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    javascriptcalls = []

    markup += '''<form name="bbulkbillsedit" id="bbulkbillsedit"><table class="invtable">\
                    <tr>
                        <td><strong>Payee Name</strong></td>
                        <td><strong>Paid From</strong></td>
                        <td><strong>Date</strong></td>
                        <td><strong>Amount</strong></td>
                    </tr>
    '''

    for dbrow in dbrows:

        each_datepicker = 'bbulkbillsedit-' + str(dbrow['id']) + '-date'
        javascriptcalls.append(' jQuery("#' + each_datepicker + '").datepicker({ dateFormat: "yy-mm-dd" });')

        markup += '''\
                    <tr>
                        <td>%s</td>
                        <td><select name="%s-fromaccount">%s</select></td>
                        <td><input type="text" name="%s" id="%s" size="10"></td>
                        <td><nobr>$<input type="text" size="8" name="%s-amt" value="" onChange="checkValueDecimals(this, 2);"></nobr></td>
                    </tr>
        ''' % (dbrow['payeename'], str(dbrow['id']), b_makeselects(selected='8', identifier=''), each_datepicker, each_datepicker, str(dbrow['id']))

    dbcon.close()

    markup += '''</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="B.BULKBILLS.SAVE"><input type="button" name="doit" VALUE="Save" onClick="sendCommand('B.BULKBILLS.SAVE');"></div></form><script>'''
    for js in javascriptcalls:
        markup += js

    return markup + '</script>'

# B.BULKBILLS.SAVE = save "Bills Bulk SAVE" submission
def b_bulkbills_save():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_bankbills ORDER BY payeename"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        each_fromacct = g_formdata.getvalue(str(dbrow['id']) + '-fromaccount')
        each_date = g_formdata.getvalue('bbulkbillsedit-' + str(dbrow['id']) + '-date')
        each_amt = g_formdata.getvalue(str(dbrow['id']) + '-amt')

        if each_amt is not None and each_date is not None:
            sqlstr = """INSERT INTO devmoney_banktransactions (parentid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferid, transferparentid) \
                                VALUES (%s, '%s', 'w', '-', %s, '%s', 'Bill', 'EBILLPAY', 0, 0, 0)""" % (each_fromacct, each_date, each_amt, dbrow['payeename'])
            h_logsql(sqlstr)
            cursor.execute(sqlstr)
            dbcon.commit()
            b_accounttally(each_fromacct)

    dbcon.close()


# U.UPDATEQUOTES
def u_fetchquotes():
#http://finance.yahoo.com/d/quotes.csv?s=LLL+VFINX&f=snl1d1c
#"LLL","L-3 Communication",66.24,"12/2/2011","+0.23"
#"VFINX","VANGUARD INDEX TR",115.07,"12/1/2011","-0.21"
#stockstring = 'VBINX+LLL'
#   0 = Ticker
#   1 = Name
#   2 = Price
#   3 = Date of Price
#   4 = Change
#   5 = 52 week low
#   6 = 52 week high

    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT ticker FROM devmoney_invelections WHERE ticker IS NOT NULL"
    cursor.execute(sqlstr)

    dbrows = cursor.fetchall()
    stockstring = ""
    for dbrow in dbrows:
      if dbrow == dbrows[0]:
        stockstring = dbrow['ticker']
      else:
        stockstring += '+' + dbrow['ticker']

    response = urllib2.urlopen('http://finance.yahoo.com/d/quotes.csv?s=' + stockstring + '&f=snl1d1cjk&e=.csv')
    csvdatalines = filter(None, response.read().split('\r\n'))
    #csvreader = csv.reader(csvdata)
    #print csvdatalines
    for line in csvdatalines:
        row = line.split(',')
        row[0] = str(row[0].replace('"', ''))
        row[3] = str(row[3].replace('"', ''))
        row[4] = str(row[4].replace('"', ''))
        #print row[0] + " " + row[2] + " " + row[3] + " " + row[4]
        #sqlstr = "UPDATE newslettermanager SET id_active='Y', date_subactivated='" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "' WHERE user_email='" + user_email_lookup + "'

        i_electiontally(row[0])
        sqlstr = """UPDATE devmoney_invelections SET quoteprice ='%s', quotechange='%s', quotedate='%s' WHERE ticker ='%s'""" % (row[2], row[4], h_todaydatetimeformysql(), row[0])
        cursor.execute(sqlstr)
        dbcon.commit()
    dbcon.close()


def u_banktotals():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_bankaccounts ORDER BY accountname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        b_accounttally(dbrow['id'])
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
    debugout = open(dirDebug + 'sqllog.txt', 'a')
    debugout.write('Entered: ' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "\n" + in_sqlstr + "\n")
    debugout.close()
