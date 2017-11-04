#!/ usr/bin/env python3
# ===============================================================================
# Copyright (c) 2016, James Ottinger. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# MoneyWatch - https://github.com/jamesottinger/moneywatch
# ===============================================================================
import cgitb
import datetime
import locale
import time
import requests
import mysql.connector  # python3-mysql.connector
from decimal import Decimal
from collections import OrderedDict
from flask import request
from moneywatch import moneywatchconfig


locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
cgitb.enable(
    logdir=moneywatchconfig.direrrors,
    display=True,
    format='text')

# ================================================================================================================
# INVESTMENT
# ================================================================================================================


def i_electiontally(in_ielectionid):
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_invtransactions WHERE ielectionid=%s ORDER BY transdate,action"
    cursor.execute(sqlstr, (in_ielectionid,))
    dbrows = cursor.fetchall()

    rtotal = Decimal('0')
    costbasis = Decimal('0')
    sharesbydividend = Decimal('0')  # from dividends (shown as income)
    sharesfromemployer = Decimal('0')  # from employer match or employer direct
    costbasisbydividend = Decimal('0')
    costbasisfromemployer = Decimal('0')
    costbasisme = Decimal('0')

    for dbrow in dbrows:
        if dbrow['updown'] == '+':
            rtotal += dbrow['sharesamt']
            costbasis += dbrow['transprice']

            if dbrow['action'] == 'REINVDIV':
                sharesbydividend += dbrow['sharesamt']
                costbasisbydividend += dbrow['transprice']
            elif dbrow['action'] == 'BUYE':
                sharesfromemployer += dbrow['sharesamt']
                costbasisfromemployer += dbrow['transprice']
            else:
                costbasisme += dbrow['transprice']
        else:
            rtotal -= dbrow['sharesamt']
            costbasis -= dbrow['transprice']
            if dbrow['action'] == 'REINVDIV':
                sharesbydividend -= dbrow['sharesamt']
            elif dbrow['action'] == 'BUYE':
                sharesfromemployer -= dbrow['sharesamt']
                costbasisfromemployer -= dbrow['transprice']
            else:
                costbasisme -= dbrow['transprice']

    sqlstr = "UPDATE moneywatch_invelections SET shares=%s, costbasis=%s, sharesbydividend=%s, sharesfromemployer=%s, \
              costbasisbydividend=%s, costbasisfromemployer=%s, costbasisme=%s WHERE ielectionid=%s"
    cursor.execute(sqlstr, (
        rtotal,
        costbasis,
        sharesbydividend,
        sharesfromemployer,
        costbasisbydividend,
        costbasisfromemployer,
        costbasisme,
        in_ielectionid))
    dbcon.commit()
    dbcon.close()


def i_electiontallyall():
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT ielectionid FROM moneywatch_invelections WHERE active=1"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        i_electiontally(dbrow['ielectionid'])
    dbcon.close()


def i_makeselectsparents(selected, identifier):
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT DISTINCT(iacctname) FROM moneywatch_invelections ORDER BY iacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    markup = ''
    for dbrow in dbrows:
        if str(dbrow['iacctname']) == str(selected):
            selectedsay = ' selected'
        else:
            selectedsay = ''
        markup += '<option value="' + identifier + str(dbrow['iacctname']) + '"' + selectedsay + '>[Investment] ' + \
                  dbrow['iacctname'] + '</option>'
    dbcon.close()
    return markup


def i_summary():
    """I.SUMMARY.GET = Shows Summary of Investment Accounts"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_invelections WHERE active > 0 AND ticker IS NOT NULL ORDER BY \
              iacctname,ielectionname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    i_s = {"accounts": OrderedDict(), "totals": {}}
    i_s["last_fetch"] = dbrows[0]['quotedate']

    i_s['totals']['all_in_me'] = 0
    i_s['totals']['all_in_dividends'] = 0
    i_s['totals']['all_in_employer'] = 0
    i_s['totals']['all_cost_basis'] = 0
    i_s['totals']['all_market'] = 0
    i_s['totals']['all_appreciation'] = 0
    i_s['totals']['all_gain'] = 0
    all_market_last = 0
    parent = ''

    for dbrow in dbrows:
        if dbrow['quotedate'] > i_s["last_fetch"] :
            i_s["last_fetch"] = dbrow['quotedate']

        if dbrow['iacctname'] != parent:
            parent = dbrow['iacctname']
            i_s['accounts'][parent] = {'elections': [], 'totals': {}}
            i_s['accounts'][parent]['totals']['in_me'] = 0
            i_s['accounts'][parent]['totals']['in_dividends'] = 0
            i_s['accounts'][parent]['totals']['in_employer'] = 0
            i_s['accounts'][parent]['totals']['cost_basis'] = 0
            i_s['accounts'][parent]['totals']['market'] = 0
            i_s['accounts'][parent]['totals']['market_last'] = 0
            i_s['accounts'][parent]['totals']['appreciation'] = 0
            i_s['accounts'][parent]['totals']['gain'] = 0

        if dbrow['manualoverrideprice'] is not None:
            election_use_price = dbrow['manualoverrideprice']
            election_last_close_use_price = dbrow['manualoverrideprice']
        else:
            election_use_price = dbrow['quoteprice']
            election_last_close_use_price = dbrow['lastcloseprice']

        each_in_me = dbrow['costbasisme']
        each_in_dividends = dbrow['costbasisbydividend']
        each_in_employer = dbrow['costbasisfromemployer']

        each_cost_basis = dbrow['costbasis']
        each_market = dbrow['shares'] * election_use_price
        each_market_last = dbrow['shares'] * election_last_close_use_price
        each_appreciation = (dbrow['shares'] * election_use_price) - each_cost_basis
        each_gain = each_appreciation + each_in_dividends + each_in_employer

        i_s['accounts'][parent]['elections'].append({
            'ielectionid': dbrow['ielectionid'],
            'ielectionname': dbrow['ielectionname'],
            'ticker': dbrow['ticker'],
            'shares': '{:.3f}'.format(dbrow['shares']),
            'show_quote': h_showmoney(election_use_price),
            'each_in_me': h_showmoney(each_in_me),
            'each_in_dividends': h_showmoney(each_in_dividends),
            'each_in_employer': h_showmoney(each_in_employer),
            'each_cost_basis': h_showmoney(each_cost_basis),
            'each_market': h_showmoney(each_market),
            'each_appreciation': h_showmoney(each_appreciation),
            'each_appreciation_raw': each_appreciation,
            'each_gain': h_showmoney(each_gain),
            'div_schedule': dbrow['divschedule']})

        i_s['accounts'][parent]['totals']['in_me'] += each_in_me
        i_s['accounts'][parent]['totals']['in_dividends'] += each_in_dividends
        i_s['accounts'][parent]['totals']['in_employer'] += each_in_employer
        i_s['accounts'][parent]['totals']['cost_basis'] += each_cost_basis
        i_s['accounts'][parent]['totals']['market'] += each_market
        i_s['accounts'][parent]['totals']['market_last'] += each_market_last
        i_s['accounts'][parent]['totals']['appreciation'] += each_appreciation
        i_s['accounts'][parent]['totals']['gain'] += each_gain

        i_s['totals']['all_in_me'] += each_in_me
        i_s['totals']['all_in_dividends'] += each_in_dividends
        i_s['totals']['all_in_employer'] += each_in_employer
        i_s['totals']['all_cost_basis'] += each_cost_basis
        i_s['totals']['all_market'] += each_market
        i_s['totals']['all_appreciation'] += each_appreciation
        i_s['totals']['all_gain'] += each_gain
        all_market_last += each_market_last

    dbcon.close()

    for a in i_s['accounts']:
        for k, v in i_s['accounts'][a]['totals'].items():
            i_s['accounts'][a]['totals'][k] = h_showmoney(v)

    all_market_raw = i_s['totals']['all_market']
    for k, v in i_s['totals'].items():
        i_s['totals'][k] = h_showmoney(v)

    i_s['totals']['all_market_raw'] = all_market_raw
    i_s["last_fetch"] = i_s["last_fetch"].strftime("%A  %B %d, %Y %r")
    i_s["value_change"] = h_showmoney(all_market_raw - all_market_last)

    return i_s


def i_election_get_transactions():
    """I.ELECTION.GET"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_invtransactions WHERE ielectionid=%s ORDER BY transdate,action"
    cursor.execute(sqlstr, (request.args.get('ielectionid'),))
    dbrows = cursor.fetchall()
    rtotal = 0
    # ielectionid, transdate, ticker, updown, action, sharesamt, shareprice, transprice, totalshould

    for dbrow in dbrows:
        dbrow["showamt"] = "{:.3f}".format(float(dbrow['sharesamt']))
        if dbrow['updown'] == '+':
            rtotal += float(dbrow['sharesamt'])
        else:
            rtotal -= float(dbrow['sharesamt'])
        dbrow["runningtotal"] = rtotal
        dbrow["showtotal"] = "{:.3f}".format(rtotal)
        dbrow["showtransprice"] = "{:.2f}".format(float(dbrow['transprice']))
        dbrow["showshareprice"] = "{:.3f}".format(float(dbrow['shareprice']))
        dbrow["future"] = True if h_dateinfuture(str(dbrow['transdate'])) else False

        if dbrow['totalshould'] != 0 and (dbrow['totalshould'] != round(rtotal, 3)):
            dbrow["showcheck"] = "{} diff:{}".format(dbrow['totalshould'],
                "{:.3f}".format(rtotal - float(dbrow['totalshould'])))
        else:
            dbrow["showcheck"] = ""

    dbcon.close()
    return dbrows


def i_bulkadd_edit():
    """I.BULKADD.EDIT = generates controller data needed for "Investment Bulk Add" utility panel"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_invelections WHERE ticker IS NOT NULL \
              AND active=1 ORDER BY iacctname,ielectionname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    parent = ''
    bulkadd = {"accounts": OrderedDict(), "selects": b_makeselects()}

    for dbrow in dbrows:
        if dbrow['iacctname'] != parent:
            parent = dbrow['iacctname']
            bulkadd['accounts'][parent] = []

        bulkadd['accounts'][parent].append({"id": dbrow['ielectionid'], "name": dbrow['ielectionname'],
                                            "ticker": dbrow['ticker'], "fetch": dbrow['fetchquotes'] })

    dbcon.close()
    return bulkadd


def i_bulkadd_save():
    """I.BULKADD.SAVE = save "Investment Bulk Add" submission"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_invelections WHERE ticker IS NOT NULL AND active=1 \
                ORDER BY iacctname,ielectionname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        each_shares = request.form.get(str(dbrow['ielectionid']) + '-shares')
        each_cost = request.form.get(str(dbrow['ielectionid']) + '-cost')  # cost of full sale
        each_date = request.form.get(str(dbrow['ielectionid']) + '-date')
        if each_shares != '' and each_cost != '' and each_date != '':
            each_ielectionid = int(request.form.get(str(dbrow['ielectionid']) + '-ielectionid'))
            each_fromid = int(request.form.get(str(dbrow['ielectionid']) + '-fromaccount'))
            each_action = request.form.get(str(dbrow['ielectionid']) + '-action')

            i_saveadd(
                ticker=dbrow['ticker'], transdate=each_date, shares=each_shares, cost=each_cost, fromacct=each_fromid,
                action=each_action, ielectionid=each_ielectionid, ielectionname=dbrow['ielectionname'], sweep=None
            )

    dbcon.close()


def i_entry_prepare_add():
    """I.ENTRY.ADD = generates body needed for "Investment Single Add" Section"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_invelections WHERE ielectionid=%s"
    cursor.execute(sqlstr, (request.args.get('ielectionid'),))
    entry = cursor.fetchone()
    dbcon.close()

    entry["mode"] = "add"
    entry["itransid"] = entry["btransid"] = entry["fundsorigin"] = 0
    entry["transdate"] = entry["action"] = entry["shares"] = entry["cost"] = ""
    entry["manuallyupdateprice"] = 'checked' if entry['fetchquotes'] == 0 else ''
    entry["account_select"] = b_makeselects(sweep=entry["sweep"])
    return entry


def i_entry_prepare_edit():
    """I.ENTRY.EDIT = generates body needed for "Investment Single Edit" Section"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT it.*, ie.ielectionname, ie.fetchquotes, ie.sweep FROM moneywatch_invtransactions it \
                INNER JOIN moneywatch_invelections ie ON it.ielectionid=ie.ielectionid WHERE it.itransid=%s"
    cursor.execute(sqlstr, (request.args.get('itransid'),))
    entry = cursor.fetchone()
    dbcon.close()

    entry["mode"] = "edit"
    entry["cost"] = "{:.2f}".format(float(entry['transprice']))
    entry["shares"] = "{:.3f}".format(float(entry['sharesamt']))
    entry["fundsorigin"] = entry['btransid']
    entry["manuallyupdateprice"] = 'checked' if entry['fetchquotes'] == 0 else ''
    bacctid = b_bacctidfrombtransid(entry["fundsorigin"]) \
        if entry["fundsorigin"] > 0 else 0
    entry["account_select"] = b_makeselects(bselected=bacctid, sweep=entry["sweep"])
    return entry


def i_edit_liveinvchart():
    return '''
           <!-- widget came from http://www.macroaxis.com/invest/widgets/native/intradaySymbolFeed?ip=true&s=VFIAX -->
                <iframe bgcolor='#ffffff' id='intraday_symbol_feed' name='intraday_symbol_feed' marginheight='0' \
                marginwidth='0' SCROLLING='NO' height='300px' width='300px' frameborder='0' \
                src='http://widgets.macroaxis.com/widgets/intradaySymbolFeed.jsp?\
                gia=t&tid=279&t=24&s=%s&_=1381101748535'></iframe>
    ''' % (request.args.get('ticker'))


def i_prepare_addupdate():

    # get form items
    in_job = request.form.get('job')
    in_ticker = request.form.get('ticker')
    in_transdate = request.form.get('tradedate')
    in_shares = request.form.get('shares')
    in_cost = request.form.get('cost')
    in_action = request.form.get('action')
    in_btransid = int(request.form.get('btransid'))  # updates only (hidden field)
    in_itransid = int(request.form.get('itransid'))  # updates only (hidden field)
    in_ielectionid = int(request.form.get('ielectionid'))
    in_ielectionname = request.form.get('ielectionname')
    in_fromacct = request.form.get('fromaccount')
    in_sweep = int(request.form.get('sweep'))

    if in_job == 'I.ENTRY.ADDSAVE':
        i_saveadd(ticker=in_ticker, transdate=in_transdate, shares=in_shares, cost=in_cost, fromacct=in_fromacct,
                  action=in_action, ielectionid=in_ielectionid, ielectionname=in_ielectionname, sweep=in_sweep)

    if in_job == 'I.ENTRY.EDITSAVE':
        i_saveupdate(ticker=in_ticker, transdate=in_transdate, shares=in_shares, cost=in_cost, fromacct=in_fromacct,
                     action=in_action, ielectionid=in_ielectionid, ielectionname=in_ielectionname,
                     btransid=in_btransid, itransid=in_itransid)


def i_saveadd(ticker, transdate, shares, cost, fromacct, action, ielectionid, ielectionname, sweep):
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)

    costpershare = "{:.3f}".format(float(cost) / float(shares))

    if action == 'SELL' or action == 'SELLX':
        updown = '-'
    else:  # BUY BUYX BUYE REINVDIV
        updown = '+'

    btransid = 0
    if fromacct == "sweep" and action == "BUY":
        # enter a sweep account sale transaction
        # look up sweep election
        sqlstr = "SELECT * FROM moneywatch_invelections WHERE active=1 AND ielectionid=%s"
        cursor.execute(sqlstr, (sweep,))
        dbrow = cursor.fetchone()
        # sell sweep shares
        sqlstr = "INSERT INTO moneywatch_invtransactions (ielectionid, btransid, transdate, ticker, updown, action, \
                  sharesamt, shareprice, transprice, totalshould) VALUES (%s, 0, %s, %s, '-', 'SELL', %s, 1, %s, 0)"
        # shares = cost
        cursor.execute(sqlstr, (dbrow["ielectionid"], transdate, dbrow["ticker"], cost, cost))
        h_logsql(cursor.statement)
        dbcon.commit()
        fromacct = 0
    else:
        fromacct = int(fromacct) # bacctid
        # do bank insert first, since we will need to learn the transaction id
        if fromacct > 0:  # was this bank funded?
            # enter bank transaction
            # Category: Buy Investment/CD: The Name Of Account
            # Buy: Mutual Fund Name 4.439 @ $22.754
            whom1 = 'Buy : ' + ticker + ' ' + shares + ' @ ' + h_showmoney(float(cost) / float(shares))
            whom2 = 'Buy Investment/CD: ' + ielectionname
            sqlstr = "INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, \
                      numnote, splityn, transferbtransid, transferbacctid, itransid) \
                      VALUES (%s, %s, 'w', '-', %s, %s, %s, 'INV', 0, 0, 0, 0)"
            cursor.execute(sqlstr, (fromacct, transdate, cost, whom1, whom2))
            h_logsql(cursor.statement)
            dbcon.commit()
            b_accounttally(fromacct)
            btransid = cursor.lastrowid

    # enter transaction in db
    sqlstr = "INSERT INTO moneywatch_invtransactions (ielectionid, btransid, transdate, ticker, updown, action, \
              sharesamt, shareprice, transprice, totalshould) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)"

    cursor.execute(sqlstr, (ielectionid, btransid, transdate, ticker, updown, action, shares, costpershare, cost))
    h_logsql(cursor.statement)
    dbcon.commit()

    if str(ielectionid) + '-updateprice' in request.form:  # update price based on new entry
        # update the elections price
        sqlstr = "UPDATE moneywatch_invelections SET manualoverrideprice=%s, quotedate=%s WHERE ielectionid=%s"
        cursor.execute(sqlstr, ("{:.3f}".format(float(cost) / float(shares)), h_todaydatetimeformysql(), ielectionid))
        h_logsql(cursor.statement)
        dbcon.commit()

    i_electiontally(ielectionid)

    if fromacct > 0:  # was this bank funded?
        # update the bank account to show investmentid
        sqlstr = """UPDATE moneywatch_banktransactions SET \
                    itransid=%s WHERE btransid=%s"""
        cursor.execute(sqlstr, (cursor.lastrowid, btransid))
        h_logsql(cursor.statement)
        dbcon.commit()

    dbcon.close()


def i_saveupdate(ticker, transdate, shares, cost, fromacct, action, ielectionid, ielectionname, btransid, itransid):
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)

    costpershare = "{:.3f}".format(float(cost) / float(shares))

    if action == 'SELL' or action == 'SELLX':
        updown = '-'
    else:  # BUY BUYX BUYE REINVDIV
        updown = '+'

    fromacct = int(fromacct) if fromacct != "sweep" else 0

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
        whom1 = 'Buy : ' + ticker + ' ' + shares + ' @ ' + h_showmoney(float(cost) / float(shares))
        whom2 = 'Buy Investment/CD: ' + ielectionname
        sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, \
                    numnote, splityn, transferbtransid, transferbacctid, itransid) \
                    VALUES (%s, %s, 'w', '-', %s, %s, %s, 'INV', 0, 0, 0, %s)"""
        cursor.execute(sqlstr, (fromacct, transdate, cost, whom1, whom2, itransid))
        h_logsql(cursor.statement)
        dbcon.commit()
        b_accounttally(fromacct)

        update_btransid = cursor.lastrowid  # use new btransid

    # (2) it was bank funded before, but it isn't anymore
    elif btransid > 0 and fromacct == 0:

        # -- [delete bank transaction]
        sqlstr = "SELECT bacctid FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (btransid,))
        h_logsql(cursor.statement)
        dbrow = cursor.fetchone()
        bacctid_lookup = dbrow['bacctid']  # need to parent bank acct for re-tally

        # not associated with a bank account anymore, delete the bank entry
        sqlstr = "DELETE FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (btransid,))
        h_logsql(cursor.statement)
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
        whom1 = 'Buy : ' + ticker + ' ' + shares + ' @ ' + h_showmoney(float(cost) / float(shares))
        whom2 = 'Buy Investment/CD: ' + ielectionname

        sqlstr = """UPDATE moneywatch_banktransactions SET \
            transdate=%s,
            type='w',
            amt=%s,
            whom1=%s,
            whom2=%s,
            itransid=%s WHERE btransid=%s"""

        cursor.execute(sqlstr, (transdate, cost, whom1, whom2, itransid, btransid))
        h_logsql(cursor.statement)
        dbcon.commit()

        b_accounttally(fromacct)

        sqlstr = "SELECT bacctid FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (btransid,))
        h_logsql(cursor.statement)
        dbrow = cursor.fetchone()
        bacctid_lookup = dbrow['bacctid']  # need to parent bank acct for re-tally

        if fromacct != bacctid_lookup:  # different bank account?
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
    h_logsql(cursor.statement)
    dbcon.commit()

    if str(ielectionid) + '-updateprice' in request.form:  # update price based on new entry
        # update the elections price
        sqlstr = "UPDATE moneywatch_invelections SET manualoverrideprice=%s, quotedate=%s WHERE ielectionid=%s"
        cursor.execute(sqlstr, ("{:.3f}".format(float(cost) / float(shares)), h_todaydatetimeformysql(), ielectionid))
        h_logsql(cursor.statement)
        dbcon.commit()

    i_electiontally(ielectionid)

    dbcon.close()


def i_entry_delete():
    """I.ENTRY.DELETE = removes an investment entry and possibly a transfer"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_invtransactions WHERE itransid=%s"
    cursor.execute(sqlstr, (request.args.get('itransid'),))
    dbrow = cursor.fetchone()

    # delete a bank transaction?
    if dbrow['btransid'] > 0:
        sqlstr = "DELETE FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (dbrow['btransid'],))
        h_logsql(cursor.statement)
        dbcon.commit()
        u_bank_totals()

    # delete inv transaction
    sqlstr = "DELETE FROM moneywatch_invtransactions WHERE itransid=%s"
    cursor.execute(sqlstr, (dbrow['itransid'],))
    h_logsql(cursor.statement)
    dbcon.commit()
    i_electiontally(dbrow['itransid'])

    dbcon.close()


# ================================================================================================================
# BANK
# ================================================================================================================


def b_accounttally(in_bacctid):
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_banktransactions WHERE bacctid=%s ORDER BY transdate,amt"
    cursor.execute(sqlstr, (in_bacctid,))
    dbrows = cursor.fetchall()
    ret = { 'total_all': Decimal('0'), 'total_up_to_today': Decimal('0'), 'total_reconciled': Decimal('0') }

    for dbrow in dbrows:
        if dbrow['updown'] == '+':
            ret['total_all'] += dbrow['amt']
            if dbrow['reconciled']:
                ret['total_reconciled'] += dbrow['amt']
            if not h_dateinfuture(dbrow['transdate']):
                ret['total_up_to_today'] += dbrow['amt']
        else:
            ret['total_all'] -= dbrow['amt']
            if dbrow['reconciled']:
                ret['total_reconciled'] -= dbrow['amt']
            if not h_dateinfuture(dbrow['transdate']):
                ret['total_up_to_today'] -= dbrow['amt']

    sqlstr = """UPDATE moneywatch_bankaccounts SET totalall=%s, totaluptotoday=%s,
             todaywas='%s', tallytime='%s' WHERE bacctid=%s""" % (
             ret['total_all'], ret['total_up_to_today'],
             h_todaydateformysql(), h_todaydatetimeformysql(), str(in_bacctid)
    )
    cursor.execute(sqlstr)
    dbcon.commit()
    dbcon.close()

    return ret

def b_makeselects(bselected=None, sweep=None):
    """bselected - optional pre-selected bacctid
       sweep - optional, shows investment election (ielectionid)
    """
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)

    markup = ''
    # sweep
    if sweep:
        sqlstr = "SELECT * FROM moneywatch_invelections WHERE active=1 AND ielectionid=%s"
        cursor.execute(sqlstr, (sweep,))
        dbrow = cursor.fetchone()
        selectedsay = ''
        markup += '<option value="sweep"' + selectedsay + '>[Sweep] ' + \
                  dbrow['ielectionname'] + '</option>'

    # bank accounts
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()
    for dbrow in dbrows:
        if bselected is not None and str(dbrow['bacctid']) == str(bselected):
            selectedsay = ' selected'
        else:
            selectedsay = ''
        markup += '<option value="' + str(dbrow['bacctid']) + '"' + selectedsay + '>[Bank] ' + \
                  dbrow['bacctname'] + '</option>'
    dbcon.close()
    return markup


def b_saybacctname(in_bacctid):
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT bacctname FROM moneywatch_bankaccounts WHERE bacctid=%s"
    cursor.execute(sqlstr, (in_bacctid,))
    dbrow = cursor.fetchone()
    dbcon.close()
    return dbrow['bacctname']


def b_bacctidfrombtransid(in_btransid):
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT bacctid FROM moneywatch_banktransactions WHERE btransid=%s"
    cursor.execute(sqlstr, (in_btransid,))
    dbrow = cursor.fetchone()
    dbcon.close()
    return dbrow['bacctid']


def b_reconciled_toggle():
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)

    mystate = 1 if request.args.get('state') == "true" else 0
    sqlstr = "UPDATE moneywatch_banktransactions SET reconciled=%s WHERE btransid=%s"
    cursor.execute(sqlstr, (mystate, request.args.get('btransid')))
    #h_logsql(cursor.statement)
    dbcon.commit()
    dbcon.close()
    return h_showmoney(b_accounttally(b_bacctidfrombtransid(request.args.get('btransid')))['total_reconciled'])


def b_reconciled_get():
    return h_showmoney(b_accounttally(request.args.get('bacctid'))['total_reconciled'])


# B.SUMMARY.GET = Shows Summary of Bank Accounts
def b_summary():
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)

    bank_summary = {}
    bank_summary["accounts"] = cursor.fetchall()
    bank_summary["last_tally"] = str(bank_summary["accounts"][0]['tallytime'].strftime("%A  %B %d, %Y %r"))

    total_mine_today = 0
    for account in bank_summary["accounts"]:
        if account['mine'] == 1:
            total_mine_today += account['totaluptotoday']
            account["own_value_today"] = h_showmoney(account['totaluptotoday'])
            account["own_value_extended"] = h_showmoney(account['totalall'])
        else:
            account["own_value_today"] = ''
            account["own_value_extended"] = ''

        account["total_all"] = h_showmoney(account['totalall'])

    dbcon.close()

    bank_summary["total_mine_today"] = h_showmoney(total_mine_today)
    bank_summary["total_mine_today_raw"] = total_mine_today

    return bank_summary


def b_account_get_transactions():
    """B.ACCOUNT.GET"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_banktransactions WHERE bacctid=%s ORDER BY transdate,numnote"
    cursor.execute(sqlstr, (request.args.get('bacctid'),))
    dbrows = cursor.fetchall()
    rtotal = Decimal('0')
    for dbrow in dbrows:
        dbrow["showamt"] = h_showmoney(dbrow["amt"])
        if dbrow['updown'] == '+':
            rtotal += dbrow['amt']
        else:
            rtotal -= dbrow['amt']
        dbrow["runningtotal"] = rtotal
        dbrow["showtotal"] = h_showmoney(rtotal)
        dbrow["future"] = True if h_dateinfuture(str(dbrow['transdate'])) else False

        if dbrow['type'] == 'ti' or dbrow['type'] == 'to':
            if dbrow['whom1'] == '':
                dbrow["showdetails"] = dbrow['whom2']
            else:
                dbrow["showdetails"] = dbrow['whom1']
            dbrow["whomclass"] = 'rwhomtrans'
        else:
            dbrow["showdetails"] = dbrow['whom1']
            dbrow["whomclass"] = 'rwhom'

    dbcon.close()
    return dbrows


def b_entry_prepare_add():
    """B.ENTRY.ADD = generates body needed for "Bank Single Add" Section"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT bacctid,bacctname FROM moneywatch_bankaccounts WHERE bacctid=%s"
    cursor.execute(sqlstr, (request.args.get('bacctid'),))
    entry = cursor.fetchone()
    dbcon.close()

    entry["mode"] = "add"
    entry["transdate"] = entry["whom1"] = entry["whom2"] = entry["numnote"] = entry["type"] = entry["amt"] = ""
    entry["btransid"] = entry["transferbtransid"] = entry["transferbacctid"] = 0

    entry["account_select"] = b_makeselects(bselected=entry["transferbacctid"])
    entry["autocomplete"] = b_autocomplete(entry["bacctid"])
    return entry


def b_entry_prepare_edit():
    """B.ENTRY.EDIT = generates body needed for "Bank Single Edit" Section"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = """SELECT bt.*, ba.bacctname FROM moneywatch_banktransactions bt \
                INNER JOIN moneywatch_bankaccounts ba ON bt.bacctid=ba.bacctid WHERE bt.btransid=%s"""
    cursor.execute(sqlstr, (request.args.get('btransid'),))
    entry = cursor.fetchone()
    dbcon.close()

    entry["amt"] = entry['amt']
    entry["mode"] = "edit"
    entry["account_select"] = b_makeselects(bselected=entry["transferbacctid"])
    entry["autocomplete"] = b_autocomplete(entry["bacctid"])
    return entry


def b_prepare_addupdate(in_job):
    # get form items
    in_date = request.form.get('transdate')
    in_numnote = request.form.get('numnote')
    in_amt = request.form.get('amt')
    in_type = request.form.get('ttype')
    in_whom1 = request.form.get('whom1')
    in_btransid = int(request.form.get('btransid'))  # (bank transaction id) updates only (hidden field)
    in_bacctid = int(request.form.get('bacctid'))
    in_transferbtransid = int(request.form.get('transferbtransid'))  # updates only (hidden field)
    in_transferbacctid = int(request.form.get('transferbacctid'))  # updates only (hidden field)

    if 'bacctid_transferselected' in request.form:  # bacctid_transferselected can be hidden and may not be included
        in_bacctid_transferselected = int(request.form.get('bacctid_transferselected'))
    else:
        in_bacctid_transferselected = 0

    if 'whom2' in request.form:  # was coming in as None
        in_whom2 = request.form.get('whom2')
    else:
        in_whom2 = ''

    if in_job == 'B.ENTRY.ADDSAVE':
        b_saveadd(
            bacctid=in_bacctid, transferbtransid=in_transferbtransid, transdate=in_date, ttype=in_type, amt=in_amt,
            numnote=in_numnote, whom1=in_whom1, whom2=in_whom2, bacctid_transferselected=in_bacctid_transferselected)

    if in_job == 'B.ENTRY.EDITSAVE':
        b_saveupdate(
            btransid=in_btransid, bacctid=in_bacctid, transferbtransid=in_transferbtransid,
            transferbacctid=in_transferbacctid, transdate=in_date, ttype=in_type, amt=in_amt,
            numnote=in_numnote, whom1=in_whom1, whom2=in_whom2, bacctid_transferselected=in_bacctid_transferselected)


def b_saveadd(bacctid, transferbtransid, transdate, ttype, amt, numnote, whom1,
              whom2, bacctid_transferselected):
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)

    updownother = ''
    transferaction = ''
    whom1trans = ''

    if ttype == 'w':  # withdrawal
        updown = '-'
    elif ttype == 'to':  # transfer out
        updown = '-'
        updownother = '+'
        transferaction = 'ti'
        whom1 = '[' + b_saybacctname(bacctid_transferselected) + ']'
        whom1trans = '[' + b_saybacctname(bacctid) + ']'
    elif ttype == 'ti':  # transfer in
        updown = '+'
        updownother = '-'
        transferaction = 'to'
        whom1 = '[' + b_saybacctname(bacctid_transferselected) + ']'
        whom1trans = '[' + b_saybacctname(bacctid) + ']'
    else:  # d = deposit
        updown = '+'

    # enter transaction in db
    sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, \
                whom2, numnote, splityn, transferbtransid, transferbacctid, itransid) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 0)"""

    cursor.execute(sqlstr, (bacctid, transdate, ttype, updown, amt, whom1, whom2, numnote, transferbtransid,
                            bacctid_transferselected))
    h_logsql(cursor.statement)
    dbcon.commit()
    btransid_learn1 = cursor.lastrowid
    b_accounttally(bacctid)

    if ttype == 'to' or ttype == 'ti':  # do the transfer part
        sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, \
                    numnote, splityn, transferbtransid, transferbacctid, itransid) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 0)"""

        cursor.execute(sqlstr, (bacctid_transferselected, transdate, transferaction, updownother, amt, whom1trans,
                                whom2, numnote, btransid_learn1, bacctid))
        h_logsql(cursor.statement)
        dbcon.commit()
        b_accounttally(bacctid_transferselected)
        btransid_learn2 = cursor.lastrowid

        # update the bank account to show transid
        sqlstr = """UPDATE moneywatch_banktransactions SET transferbtransid=%s WHERE btransid=%s"""
        cursor.execute(sqlstr, (btransid_learn2, btransid_learn1))
        h_logsql(cursor.statement)
        dbcon.commit()

    dbcon.close()


def b_saveupdate(btransid, bacctid, transferbtransid, transferbacctid, transdate, ttype, amt, numnote,
                 whom1, whom2, bacctid_transferselected):
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)

    # these are the previously saved values -> transferbtransid, transferbacctid

    updownother = ''
    transferaction = ''
    whom1trans = ''

    if ttype == 'w':  # withdrawal
        updown = '-'
    elif ttype == 'to':  # transfer out
        updown = '-'
        updownother = '+'
        transferaction = 'ti'
        whom1 = '[' + b_saybacctname(bacctid_transferselected) + ']'
        whom1trans = '[' + b_saybacctname(bacctid) + ']'
    elif ttype == 'ti':  # transfer in
        updown = '+'
        updownother = '-'
        transferaction = 'to'
        whom1 = '[' + b_saybacctname(bacctid_transferselected) + ']'
        whom1trans = '[' + b_saybacctname(bacctid) + ']'
    else:  # d = deposit
        updown = '+'

    # ---------  [update any bank transfers]  ---------
    if ttype == 'd' or ttype == 'w':
        # was it previously a transfer?
        if transferbtransid > 0:
            # delete the transfer, as this is no longer a transfer type
            # delete bank transaction
            sqlstr = "DELETE FROM moneywatch_banktransactions WHERE btransid=%s"
            cursor.execute(sqlstr, (transferbtransid,))
            h_logsql(cursor.statement)
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
            cursor.execute(sqlstr, (bacctid_transferselected, transdate, transferaction, updownother, amt, whom1trans,
                                    whom2, numnote, btransid, bacctid, transferbtransid))
            h_logsql(cursor.statement)
            dbcon.commit()
            b_accounttally(bacctid_transferselected)

        else:
            # insert a transfer
            sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, \
                        numnote, splityn, transferbtransid, transferbacctid, itransid)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s, 0)"""
            cursor.execute(sqlstr, (bacctid_transferselected, transdate, transferaction, updownother, amt, whom1trans,
                                    whom2, numnote, btransid, bacctid))
            h_logsql(cursor.statement)
            dbcon.commit()
            transferbtransid = cursor.lastrowid  # use new id
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
    cursor.execute(sqlstr, (transdate, ttype, updown, amt, whom1, whom2, numnote, transferbtransid,
                            transferbacctid, btransid))
    h_logsql(cursor.statement)
    dbcon.commit()
    b_accounttally(bacctid)


def b_entry_delete():
    """B.ENTRY.DELETE = removes a bank entry and possibly a transfer"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_banktransactions WHERE btransid=%s"
    cursor.execute(sqlstr, (request.args.get('btransid'),))
    dbrow = cursor.fetchone()

    # delete bank transaction
    sqlstr = "DELETE FROM moneywatch_banktransactions WHERE btransid=%s"
    cursor.execute(sqlstr, (dbrow['btransid'],))
    h_logsql(cursor.statement)
    dbcon.commit()
    b_accounttally(dbrow['bacctid'])

    if dbrow['splityn'] > 0:
        # delete any splits
        sqlstr = "DELETE FROM moneywatch_banktransactions_splits WHERE btransid=%s"
        cursor.execute(sqlstr, (dbrow['btransid'],))
        h_logsql(cursor.statement)
        dbcon.commit()

    if dbrow['transferbtransid'] > 0:
        # delete any transfers
        sqlstr = "DELETE FROM moneywatch_banktransactions WHERE btransid=%s"
        cursor.execute(sqlstr, (dbrow['transferbtransid'],))
        h_logsql(cursor.statement)
        dbcon.commit()
        b_accounttally(dbrow['transferbacctid'])

    dbcon.close()


def b_bulkinterest_edit():
    """B.BULKINTEREST.EDIT = generates body needed for "Interest Bulk Add" utility panel"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    bulkinterest = []
    for dbrow in dbrows:
        bulkinterest.append( {"id": dbrow['bacctid'], "name": dbrow['bacctname']})

    dbcon.close()
    return bulkinterest


def b_bulkinterest_save():
    """B.BULKINTEREST.SAVE = save "Interest Bulk Save" submission"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    in_date = request.form.get('bbulkinterest-date')

    for dbrow in dbrows:
        each_amt = request.form.get(str(dbrow['bacctid']) + '-amt')
        if each_amt != '' and in_date != '':
            sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, whom1, whom2, \
                        numnote, splityn, transferbtransid, transferbacctid, itransid) \
                        VALUES (%s, %s, 'd', '+', %s, 'Interest', '', 'INT', 0, 0, 0, 0)"""
            cursor.execute(sqlstr, (dbrow['bacctid'], in_date, each_amt))
            h_logsql(cursor.statement)
            dbcon.commit()
            b_accounttally(dbrow['bacctid'])

    dbcon.close()


def b_bulkbills_edit():
    """B.BULKBILLS.EDIT = generates controller data needed for "Bills Bulk Add" template"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_bankbills ORDER BY payeename"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    bulkbills = { "payees":[], "account_select": b_makeselects(bselected='8') }
    for dbrow in dbrows:
        bulkbills["payees"].append( {"id": dbrow['payeeid'], "name": dbrow['payeename']})
    dbcon.close()
    return bulkbills


def b_bulkbills_save():
    """B.BULKBILLS.SAVE = save "Bills Bulk SAVE" submission"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_bankbills ORDER BY payeename"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        each_fromacct = request.form.get(str(dbrow['payeeid']) + '-fromaccount')
        each_date = request.form.get('bbulkbillsedit-' + str(dbrow['payeeid']) + '-date')
        each_amt = request.form.get(str(dbrow['payeeid']) + '-amt')

        if each_amt != '' and each_date != '':
            sqlstr = """INSERT INTO moneywatch_banktransactions (bacctid, transdate, type, updown, amt, \
                        whom1, whom2, numnote, splityn, transferbtransid, transferbacctid, itransid) \
                        VALUES (%s, %s, 'w', '-', %s, %s, 'Bill', 'EBILLPAY', 0, 0, 0, 0)"""
            cursor.execute(sqlstr, (each_fromacct, each_date, each_amt, dbrow['payeename']))
            h_logsql(cursor.statement)
            dbcon.commit()
            b_accounttally(each_fromacct)

    dbcon.close()


def b_autocomplete(in_bacctid):
    """generates autocomplete possabilities, excludes fund purchases"""
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT DISTINCT whom1 FROM moneywatch_banktransactions WHERE bacctid=%s \
              AND whom1 NOT LIKE 'Buy : %%' ORDER BY whom1"
    cursor.execute(sqlstr, (in_bacctid,))
    dbrows = cursor.fetchall()
    whomlist = []

    for dbrow in dbrows:
        whomlist.append("'" + dbrow['whom1'] + "'")

    dbcon.close()
    return ', '.join(whomlist)


# ================================================================================================================
# UTILITIES
# ================================================================================================================


def u_fetch_quotes():
    """ U.UPDATEQUOTES - Pull stock quotes from Yahoo Finance
        http://finance.yahoo.com/d/quotes.csv?s=LLL+VFINX&f=snl1d1cjkyr1q
        "LLL","L-3 Communication",66.24,"12/2/2011","+0.23"
        "VFINX","VANGUARD INDEX TR",115.07,"12/1/2011","-0.21"
        stockstring = 'VBINX+LLL'
        0  = Ticker
        1  = Name
        2  = Price
        3  = Date of Price
        4  = Change
        5  = 52 week low
        6  = (k) 52 week high
        7  = (y) yield
        8  = (r1) dividend date (next)
        9  = (q) dividend date (prev)
        10 = (p) previous close
    """
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT DISTINCT ticker FROM moneywatch_invelections WHERE active=1 and fetchquotes=1"
    cursor.execute(sqlstr)

    dbrows = cursor.fetchall()
    stockstring = ""
    for dbrow in dbrows:
        if dbrow == dbrows[0]:
            stockstring = dbrow['ticker']
        else:
            stockstring += '+' + dbrow['ticker']

    # fetch from Yahoo
    response = requests.get('http://finance.yahoo.com/d/quotes.csv?s=' + stockstring + '&f=snl1d1cjkyr1qp&e=.csv')
    if response.status_code != 200:
        h_logsql('There was an error fetching quotes: http://finance.yahoo.com/d/quotes.csv?s=' +
                 stockstring + '&f=snl1d1cjkyr1qp&e=.csv')
        return

    csvdatalines = response.text.rstrip().split('\n')

    for line in csvdatalines:
        row = line.split(',')
        row[0] = str(row[0].replace('"', ''))
        row[3] = str(row[3].replace('"', ''))
        row[4] = str(row[4].replace('"', ''))
        row[7] = str(row[7].replace('"', ''))
        row[8] = str(row[8].replace('"', ''))
        row[9] = str(row[9].replace('"', ''))
        row[10] = str(row[10].replace('"', ''))

        sqlstr = "UPDATE moneywatch_invelections SET quoteprice=%s,lastcloseprice=%s, quotechange=%s, quotedate=%s,\
                yield=%s, divdatenext=%s, divdateprev=%s WHERE ticker=%s"
        cursor.execute(sqlstr, (row[2], row[10], row[4], h_todaydatetimeformysql(), row[7], row[8], row[9], row[0]))
        # h_logsql(cursor.statement)
        dbcon.commit()
    dbcon.close()
    i_electiontallyall()


def u_bank_totals():
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = "SELECT * FROM moneywatch_bankaccounts ORDER BY bacctname"
    cursor.execute(sqlstr)
    dbrows = cursor.fetchall()

    for dbrow in dbrows:
        b_accounttally(dbrow['bacctid'])
    dbcon.close()


def u_links_generate():
    """U.LINKS.GET"""
    markup = ''
    sets = 0
    for linksets in moneywatchconfig.uilinks:
        sets += 1
        for name, link in linksets:
            markup += '''<li><a tabindex="-1" href="%s" target="_blank"> \
                    <span class="glyphicon glyphicon-globe" aria-hidden="true"></span> %s</a></li>''' % (link, name)

        if sets != len(moneywatchconfig.uilinks):
            markup += '<li class="divider"></li>'
    return markup


def u_weathergenerate():
    """U.WEATHER.GET - grabs weather from forcast.io"""
    return '''<iframe id="forecast_embed" type="text/html" frameborder="0" height="245" width="100%%" /
              src="http://forecast.io/embed/#lat=%s&lon=%s&name=%s"> </iframe>''' % (
        moneywatchconfig.weather['latitude'], moneywatchconfig.weather['longitude'], moneywatchconfig.weather['title']
    )

# ================================================================================================================
# HELPER FUNCTIONS
# ================================================================================================================


def h_showmoney(in_num):
    return locale.currency(in_num, grouping=True)


def h_dateclean(in_date):
    """4/1'2008 or 12/31'2009 format in
       2009-12-31 returned"""
    sp1 = str(in_date).split("'")  # [0] = 4/1, [1] = 2008
    sp2 = sp1[0].split("/")  # [0] = 4(month), [1] = 1(day)
    return sp1[1] + '-' + sp2[0].zfill(2) + '-' + sp2[1].zfill(2)


def h_dateinfuture(in_date):
    """2009-12-31 format in
       boolean returned"""
    if in_date == '' or in_date is None:
        return False

    boom = str(in_date).split("-")  # [0] = year, [1] = month, [2] = day
    if len(boom) != 3:
        return False
    numdate = int(boom[0] + boom[1] + boom[2])

    # import time
    # time.strftime('%Y-%m-%d %H:%M:%S')

    todaydate = int(time.strftime('%Y%m%d'))
    if numdate > todaydate:
        return True
    else:
        return False


def h_todaydateformysql():
    """returns todays date as 2009-12-31
       import time"""
    return time.strftime('%Y-%m-%d')


def h_todaydatetimeformysql():
    """returns todays date as 2009-12-31 HH:MM:SS format
       requires: import time"""
    return time.strftime('%Y-%m-%d %H:%M:%S')


def h_dateqiftoint(in_date):
    """4/1'2008 or 12/31'2009 format in - 20091231 int out"""
    sp1 = str(in_date).split("'")  # [0] = 4/1, [1] = 2008
    sp2 = sp1[0].split("/")  # [0] = 4(month), [1] = 1(day)
    return int(sp1[1] + sp2[0].zfill(2) + sp2[1].zfill(2))


def h_datemysqltoint(in_date):
    """2009-12-31 format in
       20091231 int returned"""
    boom = str(in_date).split("-")  # [0] = year, [1] = month, [2] = day
    return int(boom[0] + boom[1] + boom[2])


def h_logsql(in_sqlstr):
    debugout = open(moneywatchconfig.dirlogs + 'sqllog.txt', 'a')
    debugout.write('Entered: ' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "\n" + in_sqlstr + "\n")
    debugout.close()


def h_loginfo(in_infostr):
    debugout = open(moneywatchconfig.dirlogs + 'infolog.txt', 'a')
    debugout.write('Entered: ' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "\n" + in_infostr + "\n")
    debugout.close()


# ================================================================================================================
# GRAPHING
# ================================================================================================================

def i_graph():
    dbcon = mysql.connector.connect(**moneywatchconfig.db_creds)
    cursor = dbcon.cursor(dictionary=True)
    sqlstr = """SELECT it.*, ie.ielectionname FROM moneywatch_invtransactions it \
                INNER JOIN moneywatch_invelections ie ON it.ielectionid=ie.ielectionid WHERE \
                it.ielectionid=%s ORDER BY it.transdate,it.action"""
    cursor.execute(sqlstr, (request.args.get('ielectionid'),))
    dbrows = cursor.fetchall()
    # ielectionid, transdate, ticker, updown, action, sharesamt, shareprice, transprice, totalshould
    data = {}
    data['start_year'] = str(dbrows[0]['transdate']).split("-")[0]
    data['election_name'] = dbrows[0]['ielectionname']
    data['ticker'] = dbrows[0]['ticker']
    shares_total = 0
    shares_list = []
    prices_list = []

    for dbrow in dbrows:
        datesplit = str(dbrow['transdate']).split("-")  # [0] = year, [1] = month, [2] = day
        if dbrow['updown'] == '+':
            shares_total += float(dbrow['sharesamt'])
        else:
            shares_total -= float(dbrow['sharesamt'])
        # Date.UTC(1971, 1, 24), 1.92],
        shares_list.append("[ Date.UTC({}, {}, {}), {:.3f} ]".format(
                datesplit[0], datesplit[1], datesplit[2], shares_total))

        prices_list.append("[ Date.UTC({}, {}, {}), {:.3f} ]".format(
                datesplit[0], datesplit[1], datesplit[2], float(dbrow['shareprice'])))

    data['shares'] = ', '.join(shares_list)
    data['prices'] = ', '.join(prices_list)
    dbcon.close()

    return data
