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



'''
CREATE TABLE `devmoney_invelections` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `parentname` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `ticker` varchar(20) DEFAULT NULL,
  `active` tinyint(4) DEFAULT '0',
  `shares` double DEFAULT NULL,
  `sharesbydividend` double DEFAULT '0',
  `costbasis` double DEFAULT NULL,
  `balance` double DEFAULT NULL,
  `quotedate` date DEFAULT NULL,
  `quoteprice` double DEFAULT NULL,
  `quotechange` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=latin1;


CREATE TABLE `devmoney_invtransactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `parentid` int(11) DEFAULT '0',
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
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;


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
                                </tr>
                    ''' % (h_showmoney(parent_costbasis), h_showmoney(parent_market), h_showmoney(parent_income), h_showmoney(parent_appres), h_showmoney(parent_gain))
                parent_costbasis = 0
                parent_market = 0
                parent_income = 0
                parent_appres = 0
                parent_gain = 0
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
                    </tr>
        ''' % (dbrow['ticker'], dbrow['ticker'], dbrow['name'], "{:.3f}".format(dbrow['shares']), h_showmoney(dbrow['quoteprice']), h_showmoney(dbrow['costbasis']), h_showmoney(each_market), h_showmoney(each_income), each_apprecclass, h_showmoney(each_appres), h_showmoney(each_gain))

    markup += '''\
                    <tr>
                        <td colspan="4">&nbsp;</td>
                        <td style="text-align: right;background-color: #efefef;"><!-- cost basis -->%s</td>
                        <td style="text-align: right;background-color: #efefef;"><!-- market value --><b>%s</b></td>
                        <td style="text-align: right;background-color: #efefef;"><!-- income -->%s</td>
                        <td style="text-align: right;background-color: #efefef;"><!-- apprec -->%s</td>
                        <td style="text-align: right;background-color: #efefef;"><!-- gain -->%s</td>
                    </tr>
        ''' % (h_showmoney(parent_costbasis), h_showmoney(parent_market), h_showmoney(parent_income), h_showmoney(parent_appres), h_showmoney(parent_gain))


    markup += '''\
                    <tr>
                        <td colspan="4">&nbsp;</td>
                        <td class="invtotalsbottom"><!-- cost basis -->%s</td>
                        <td class="invtotalsbottom"><!-- market value --><b>%s</b></td>
                        <td class="invtotalsbottom"><!-- income -->%s</td>
                        <td class="invtotalsbottom"><!-- apprec -->%s</td>
                        <td class="invtotalsbottom"><!-- gain -->%s</td>
                    </tr>
        ''' % (h_showmoney(all_costbasis), h_showmoney(all_market), h_showmoney(all_income), h_showmoney(all_appres), h_showmoney(all_gain))


    dbcon.close()
    return markup + '</table>'


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
            amtup = "+" + str(dbrow['sharesamt'])#locale.currency(trans['transactionamt'], grouping=True)
            amtdown = ''
            rtotal += float(dbrow['sharesamt'])
        else:
            amtup = ''
            amtdown = "-" + str(dbrow['sharesamt'])#locale.currency(trans['transactionamt'], grouping=True)
            rtotal -= float(dbrow['sharesamt'])

        if dbrow['totalshould'] != 0 and (dbrow['totalshould'] != round(rtotal, 3)):
            showcheck = """%s diff: %s""" % (dbrow['totalshould'],"{:.3f}".format(rtotal - float(dbrow['totalshould'])))

        if counter % 2 == 0:
            classoe = 'recordeven'
        else:
            classoe = 'recordodd'

        markup += '''<div class="%s">\
                        <span class="rdate">%s</span>
                        <span class="rnum">%s</span>
                        <span class="invinfo"> ($%s @ $%s each)</span>
                        <span class="rup">%s</span>
                        <span class="rdown">%s</span>
                        <span class="rbalpos"> %s</span>
                        <span class="rbalpos"> %s</span>
                     </div>''' % (classoe, dbrow['transdate'], dbrow['action'], "{:.2f}".format(float(dbrow['transprice'])), "{:.3f}".format(float(dbrow['shareprice'])), amtup, amtdown, "{:.3f}".format(rtotal), showcheck)
                    #//$R .= $ecounter . "==" . $election['shares'] . "|"; //'<a href="#" onClick="return bank_gettransactions(' . "'" . $document['name'] . "');" . '">' . $document['name'] . " $" .  number_format($document['total'], 2, '.', ',') . "</a><br>";
        counter +=1
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
                        <td>Name</td>
                        <td>Ticker</td>
                        <td>Funded From</td>
                        <td>Trade Date</td>
                        <td>Action</td>
                        <td># Shares</td>
                        <td>Trade Cost</td>
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
        ''' % (dbrow['name'], dbrow['ticker'], dbrow['id'], dbrow['ticker'], dbrow['ticker'], b_makeselects(), each_datepicker, each_datepicker, dbrow['ticker'], dbrow['ticker'], dbrow['ticker'])

        #markup += '<div><span>' +  dbrow['name'] + '</span><span><input type="text" class="tickerentry" size="8" name="' + dbrow['ticker'] + '-shares" value=""></span></div>'
    dbcon.close()

    markup += '</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="I.BULKADD.SAVE"><input type="button" name="doit" VALUE="Save" onClick="sendCommand("I.BULKADD.SAVE");"></div></form><script>'
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

    each_bank = 0
    each_action = ''
    each_shares = 0
    each_cost = '' # cost of full sale

    for dbrow in dbrows:
        each_parentid = g_formdata.getvalue(dbrow['ticker'] + '-parentid')
        each_date = g_formdata.getvalue(dbrow['ticker'] + str(dbrow['id']) + '-date')
        each_bankid = int(g_formdata.getvalue(dbrow['ticker'] + '-fromaccount'))
        each_action = g_formdata.getvalue(dbrow['ticker'] + '-action')
        each_shares = g_formdata.getvalue(dbrow['ticker'] + '-shares')
        each_cost = g_formdata.getvalue(dbrow['ticker'] + '-cost') # cost of full sale


        if each_shares != '' and each_cost != '':
            if each_action == 'SELL':
                each_updown = '-'
            else:
                each_updown = '+'

            each_costpershare = "{:.3f}".format(float(each_cost) / float(each_shares))

            # enter transaction in db
            sqlstr = """INSERT INTO devmoney_invtransactions (parentid, transdate, ticker, updown, action, sharesamt, shareprice, transprice) VALUES (%s, '%s', '%s', '%s', '%s', %s, %s, %s)""" % (each_parentid, each_date, dbrow['ticker'], each_updown, each_action, each_shares, each_costpershare, each_cost)
            cursor.execute(sqlstr)
            dbcon.commit()

            if each_bank > 0:
                # enter bank transaction
                # Category: Buy Investment/CD: The Name Of Account
                # Buy: Mutual Fund Name 4.439 @ $22.754
                each_whom1 = 'Buy : ' + dbrow['name'] + ' ' + each_shares + ' @ ' + h_showmoney(each_costpershare)
                each_whom2 = 'Buy Investment/CD: ' + dbrow['parentname']
                sqlstr = """INSERT INTO devmoney_banktransactions (parentid, transdate, type, updown, amt, whom1, whom2, numnote, splityn, transferid) \
                            VALUES (%s, '%s', 'r', '-', %s, '%s', '%s', 'INV', 0, 0)""" % (each_bankid, each_date, each_updown , each_cost, each_whom1, each_whom2)
                cursor.execute(sqlstr)
                dbcon.commit()

    dbcon.close()


# I.ENTRY.ADD = generates body needed for "Investment Signle Add" Section
def i_entry_edit():
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
                        <td>Name</td>
                        <td>Ticker</td>
                        <td>Funded From</td>
                        <td>Trade Date</td>
                        <td>Action</td>
                        <td># Shares</td>
                        <td>Trade Cost</td>
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
        ''' % (dbrow['name'], dbrow['ticker'], dbrow['id'], dbrow['ticker'], dbrow['ticker'], b_makeselects(), each_datepicker, each_datepicker, dbrow['ticker'], dbrow['ticker'], dbrow['ticker'])

        #markup += '<div><span>' +  dbrow['name'] + '</span><span><input type="text" class="tickerentry" size="8" name="' + dbrow['ticker'] + '-shares" value=""></span></div>'
    dbcon.close()

    markup += '</table><div style="text-align:right; padding-top: 20px; padding-right: 25px;"><input type="hidden" name="job" value="I.BULKADD.SAVE"><input type="button" name="doit" VALUE="Save" onClick="sendCommand("I.BULKADD.SAVE");"></div></form><script>'
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


def b_makeselects():
    dbcon = mdb.connect(g_dbauth[0], g_dbauth[1], g_dbauth[2], g_dbauth[3])
    cursor = dbcon.cursor(mdb.cursors.DictCursor)
    sqlstr = "SELECT * FROM devmoney_bankaccounts ORDER BY accountname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    for dbrow in dbrows:
        markup += '<option value="' + str(dbrow['id']) + '">[Bank] ' + dbrow['accountname'] + '</option>'
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
    markup += '''<table class="invtable" width="800">\
                    <tr style="background-color: #efefef;">
                        <td>Bank</td>
                        <td>Account</td>
                        <td>Value</td>
                        <td>My(Today)</td>
                        <td>My</td>
                    </tr>
    '''

    for dbrow in dbrows:
        if dbrow['mine'] == 1:
            ownvaluetoday = h_showmoney(dbrow['totaluptotoday'])
            ownvalueextended = h_showmoney(dbrow['totalall'])
        else:
            ownvaluetoday = ''
            ownvalueextended = ''

        markup += '''\
                    <tr>
                        <td style="width:100px;">%s</td>
                        <td><a href="#" onClick="getInvElection('%s');">%s</a></td>
                        <td style="width:60px;text-align: right;"><!-- value extended -->%s</td>
                        <td style="width:60px;text-align: right;"><!-- MINE - value current/today -->%s</td>
                        <td style="width:60px;text-align: right;"><!-- MINE - value extended -->%s</td>
                    </tr>''' % (dbrow['bank'], dbrow['id'], dbrow['accountname'], h_showmoney(dbrow['totalall']), ownvaluetoday, ownvalueextended)

    dbcon.close()
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

        markup += '''<div class="%s %s">\
                        <span class="rdate">%s</span>
                        <span class="rnum">%s</span>
                        <span class="%s">%s</span>
                        <span class="rup">%s</span>
                        <span class="rdown">%s</span>
                        <span class="%s">%s</span>
                     </div>''' % (classoe, classfuture, dbrow['transdate'], dbrow['numnote'], whomclass, showwho, amtup, amtdown, rtotalclass, rtotalshow)
        counter +=1
    return markup


#================================================================================================================
# UTILITIES
#================================================================================================================

# U.IMPORTFILE.EDIT
#<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js" ></script>
def u_importfile_edit():
    return """\
<form enctype="multipart/form-data" action="save_file.py" method="post">
<p>File: <input type="file" name="file"></p>
<select name="import-acct" onChange="uploadSelect(this);">
  %s
  %s
  <option value="New">- NEW -</option>
</select><br><br>
<div id="upload-exist">
    <input type="radio" name="importtype" value="merge" checked> Merge <input type="radio" name="importtype" value="replace"> Replace<br><br>
</div>
<div id="upload-new" style="display: none">
   <input type="radio" name="accounttype" value="bank" checked> Bank <input type="radio" name="accounttype" value="investment"> Investment<br>
    Name: <input type="text" size="30" name="newname" value="">
</div>
<p><input type="submit" value="Upload"></p>
</form>
<script>
function uploadSelect(obj) {
    if (obj.value == 'New') {
        jQuery('#upload-new').show('slow');
        jQuery('#upload-exist').hide('slow');
    } else {
        jQuery('#upload-new').hide('slow');
        jQuery('#upload-exist').show('slow');
    }
}
</script>""" % (bank_makeselects(), inv_makeselects())



# U.IMPORTFILE.SAVE - File Upload
# http://webpython.codepoint.net/cgi_file_upload
# http://en.wikipedia.org/wiki/Here_document#Python
def u_importfile_save():
    fileitem = form['file']
    # Test if the file was uploaded
    if fileitem.filename:
        # strip leading path from file name to avoid directory traversal attacks
        fn = os.path.basename(fileitem.filename)
        open('files/' + fn, 'wb').write(fileitem.file.read())
        #message = 'The file "' + fn + '" was uploaded successfully'


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
        sqlstr = 'UPDATE devmoney_invelections SET quoteprice =' + row[2] + ', quotechange="' + row[4] + '" WHERE ticker ="' + row[0] + '"'
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


#================================================================================================================
# CLEAN-UP
#================================================================================================================








# AJAX.BANK.MAKEBULKINTEREST = generates body needed for "Bulk Interest" utility panel
def  bank_makebulkinterest():
    markup = ''
    collection = g_db.bankaccounts.find({}).sort("name") # ORDER BY name
    for account in collection:
        markup += '<div><span class="interestamount">$<input type="text" class="moneyentry" size="8" name="interest' + account['name'] + '"> </span><span class="interestaccount" name="' + account['name']  + '">' + account['name'] + '</span></div>'
    return markup


# AJAX.INVESTMENT.MAKEEDITSETTINGS = generates body needed for "Investment Account Edit" utility panel
def investment_makeeditsettings():
    markup = ''
    collection = g_db.investmentaccounts.find({}).sort("name") # ORDER BY name
    for account in collection:
        markup += '<div class="investmentparent">' + account['name'] + '</div>'
        for k, v in account['elections'].items():
            nameclean = k.replace(' ', '-').replace("&", '~')
            if 'ticker' in v:
                useticker = v['ticker']
            else:
                useticker = ''
            markup += '<div><span class="ticker"><input type="text" class="tickerentry" size="8" name="' + nameclean + '" value="' + useticker + '"></span> <span class="investmentelection">' + k + '</span></div>'
    return markup









def inv_makeselects():
    markup = ''
    collection = g_db.investmentaccounts.find({}).sort("name") # ORDER BY name
    for account in collection:
        markup += '<option value="' + account['name']  + '">[Investment] ' + account['name'] + '</option>'
    return markup
