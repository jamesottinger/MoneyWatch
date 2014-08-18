#!/usr/bin/python


#===============================================================================
# Code written by James Ottinger
#===============================================================================
import sys
sys.path.append('/dirsomewhere/')
import moneywatchengine

#===============================================================================
'''
-- I.SUMMARY.GET
-- I.ELECTION.GET
-- I.BULKADD.EDIT
-- I.BULKADD.SAVE
I.TICKERS.EDIT
I.TICKERS.SAVE
-- I.ENTRY.ADD
I.ENTRY.EDIT
I.ENTRY.SAVE
I.ENTRY.DEL

-- B.SUMMARY.GET
-- B.ACCOUNT.GET
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

*- U.IMPORTFILE.EDIT
*- U.IMPORTFILE.SAVE
-- U.UPDATEQUOTES
'''
#===============================================================================

if moneywatchengine.g_formdata.getvalue('job') == 'I.SUMMARY.GET':
    print "Content-type: text/html\n\n"
    print moneywatchengine.i_summary()
elif moneywatchengine.g_formdata.getvalue('job') == 'I.ELECTION.GET':
    # requires: ?ticker=
    print "Content-type: text/html\n\n"
    print moneywatchengine.i_electionget()
elif moneywatchengine.g_formdata.getvalue('job') == 'I.BULKADD.EDIT':
    print "Content-type: text/html\n\n"
    print moneywatchengine.i_bulkadd_edit()
elif moneywatchengine.g_formdata.getvalue('job') == 'I.BULKADD.SAVE':
    print "Content-type: text/html\n\n"
    moneywatchengine.i_bulkadd_save()
    print "ok"
elif moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.ADD':
    # requires: ?ticker=
    print "Content-type: text/html\n\n"
    print moneywatchengine.i_entry_prepareadd()
elif moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.EDIT':
    # requires: ?id=&ticker=
    print "Content-type: text/html\n\n"
    print moneywatchengine.i_entry_prepareedit()
elif moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.ADDSAVE' or moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.EDITSAVE':
    print "Content-type: text/html\n\n"
    moneywatchengine.i_prepare_addupdate()
    print "ok"
elif moneywatchengine.g_formdata.getvalue('job') == 'I.ENTRY.DELETE':
    # requires: ?transid=
    print "Content-type: text/html\n\n"
    moneywatchengine.i_entry_delete()
    print "ok"
elif moneywatchengine.g_formdata.getvalue('job') == 'I.GRAPH.GET':
    # requires: ?ticker=
    print "Content-type: text/html\n\n"
    print moneywatchengine.i_graph()
elif moneywatchengine.g_formdata.getvalue('job') == 'B.SUMMARY.GET':
    print "Content-type: text/html\n\n"
    print moneywatchengine.b_summary()
elif moneywatchengine.g_formdata.getvalue('job') == 'B.ACCOUNT.GET': 
    # requires: ?parentid=
    print "Content-type: text/html\n\n"
    print moneywatchengine.b_accountget()
elif moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.ADD':
    # requires: ?bankacctid=
    print "Content-type: text/html\n\n"
    print moneywatchengine.b_entry_prepareadd()
elif moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.EDIT':
    # requires: ?transid=
    print "Content-type: text/html\n\n"
    print moneywatchengine.b_entry_prepareedit()
elif moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.ADDSAVE' or moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.EDITSAVE':
    print "Content-type: text/html\n\n"
    moneywatchengine.b_prepare_addupdate()
    print "ok"
elif moneywatchengine.g_formdata.getvalue('job') == 'B.ENTRY.DELETE':
    # requires: ?transid=
    print "Content-type: text/html\n\n"
    moneywatchengine.b_entry_delete()
    print "ok"
elif moneywatchengine.g_formdata.getvalue('job') == 'B.BULKINTEREST.EDIT':
    print "Content-type: text/html\n\n"
    print moneywatchengine.b_bulkinterest_edit()
elif moneywatchengine.g_formdata.getvalue('job') == 'B.BULKINTEREST.SAVE':
    print "Content-type: text/html\n\n"
    moneywatchengine.b_bulkinterest_save()
    print "ok"
elif moneywatchengine.g_formdata.getvalue('job') == 'B.BULKBILLS.EDIT':
    print "Content-type: text/html\n\n"
    print moneywatchengine.b_bulkbills_edit()
elif moneywatchengine.g_formdata.getvalue('job') == 'B.BULKBILLS.SAVE':
    print "Content-type: text/html\n\n"
    moneywatchengine.b_bulkbills_save()
    print "ok"
elif moneywatchengine.g_formdata.getvalue('job') == 'U.IMPORTFILE.EDIT':
    print "Content-type: text/html\n\n"
    print moneywatchengine.u_importfile_edit()
elif moneywatchengine.g_formdata.getvalue('job') == 'U.IMPORTFILE.SAVE':
    print "Content-type: text/html\n\n"
    print moneywatchengine.u_importfile_save()
elif moneywatchengine.g_formdata.getvalue('job') == 'U.UPDATEQUOTES':
    print "Content-type: text/html\n\n"
    moneywatchengine.u_fetchquotes()
    print "ok"
elif moneywatchengine.g_formdata.getvalue('job') == 'U.UPDATEBANKTOTALS':
    print "Content-type: text/html\n\n"
    moneywatchengine.u_banktotals()
    print "ok"
else:
    print "Content-type: text/html\n\n"
    print ")("# invalid, print ass cheeks
    #moneywatchengine.b_accounttally(1)
    #print moneywatchengine.i_entry_prepareedit()
