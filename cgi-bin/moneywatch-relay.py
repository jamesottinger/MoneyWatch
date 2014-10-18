#!/usr/bin/python
#===============================================================================
# Copyright (c) 2014, James Ottinger. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# MoneyWatch - https://github.com/jamesottinger/moneywatch
#===============================================================================
import sys
sys.path.append('/dirsomewhere/')
import moneywatchengine

#===============================================================================
'''
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
'''
#===============================================================================

def p_content():
    print "Content-type: text/html\n\n"

def main():
    if moneywatchengine.g_formdata.getvalue('job') == 'I.SUMMARY.GET':
        p_content()
        print moneywatchengine.i_summary()
    elif moneywatchengine.g_formdata.getvalue('job') == 'I.ELECTION.GET':
        p_content()
        print moneywatchengine.i_electionget()
    elif moneywatchengine.g_formdata.getvalue('job') == 'I.BULKADD.EDIT':
        p_content()
        print moneywatchengine.i_bulkadd_edit()
    elif moneywatchengine.g_formdata.getvalue('job') == 'I.BULKADD.SAVE':
        p_content()
        moneywatchengine.i_bulkadd_save()
        print "ok"
    elif moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.ADD':
        p_content()
        print moneywatchengine.i_entry_prepareadd()
    elif moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.EDIT':
        p_content()
        print moneywatchengine.i_entry_prepareedit()
    elif moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.ADDSAVE' or moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.EDITSAVE':
        p_content()
        moneywatchengine.i_prepare_addupdate()
        print "ok"
    elif moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.DELETE':
        p_content()
        moneywatchengine.i_entry_delete()
        print "ok"
    elif moneywatchengine.g_formdata.getvalue('job') == 'I.GRAPH.GET':
        p_content()
        print moneywatchengine.i_graph()
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.SUMMARY.GET':
        p_content()
        print moneywatchengine.b_summary()
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.ACCOUNT.GET':
        p_content()
        print moneywatchengine.b_accountget()
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.ADD':
        p_content()
        print moneywatchengine.b_entry_prepareadd()
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.EDIT':
        p_content()
        print moneywatchengine.b_entry_prepareedit()
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.ADDSAVE' or moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.EDITSAVE':
        p_content()
        moneywatchengine.b_prepare_addupdate()
        print "ok"
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.DELETE':
        p_content()
        moneywatchengine.b_entry_delete()
        print "ok"
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.BULKINTEREST.EDIT':
        p_content()
        print moneywatchengine.b_bulkinterest_edit()
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.BULKINTEREST.SAVE':
        p_content()
        moneywatchengine.b_bulkinterest_save()
        print "ok"
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.BULKBILLS.EDIT':
        p_content()
        print moneywatchengine.b_bulkbills_edit()
    elif moneywatchengine.g_formdata.getvalue('job') == 'B.BULKBILLS.SAVE':
        p_content()
        moneywatchengine.b_bulkbills_save()
        print "ok"
    elif moneywatchengine.g_formdata.getvalue('job') == 'U.IMPORTFILE.EDIT':
        p_content()
        print moneywatchengine.u_importfile_edit()
    elif moneywatchengine.g_formdata.getvalue('job') == 'U.IMPORTFILE.SAVE':
        p_content()
        print moneywatchengine.u_importfile_save()
    elif moneywatchengine.g_formdata.getvalue('job') == 'U.UPDATEQUOTES':
        p_content()
        moneywatchengine.u_fetchquotes()
        print "ok"
    elif moneywatchengine.g_formdata.getvalue('job') == 'U.UPDATEBANKTOTALS':
        p_content()
        moneywatchengine.u_banktotals()
        print "ok"
    else:
        p_content()
        print ")("# invalid, print ass cheeks

    #moneywatchengine.b_accounttally(1)
    #print moneywatchengine.i_entry_prepareedit()

if __name__ == '__main__':
    main()

