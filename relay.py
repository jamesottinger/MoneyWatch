#!/ usr/bin/env python3
#===============================================================================
# Copyright (c) 2015, James Ottinger. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# MoneyWatch - https://github.com/jamesottinger/moneywatch
#===============================================================================
from flask import Flask, abort, request
import sys
sys.path.append('./cgi-bin/')
import moneywatchengine3

relay = Flask('relay')
#===============================================================================
@relay.route('/action/<job>')
def actionhandler(job):
    if job == 'I.SUMMARY.GET':
        return moneywatchengine3.i_summary()
    elif job == 'I.ELECTION.GET':
        return moneywatchengine3.i_electionget()
    elif job == 'I.BULKADD.EDIT':
        return moneywatchengine3.i_bulkadd_edit()
    elif job == 'I.BULKADD.SAVE':
        moneywatchengine3.i_bulkadd_save()
        return "ok"
    elif job == 'I.ENTRY.ADD':
        return moneywatchengine3.i_entry_prepareadd()
    elif job == 'I.ENTRY.EDIT':
        return moneywatchengine3.i_entry_prepareedit()
    elif job == 'I.ENTRY.ADDSAVE' or job == 'I.ENTRY.EDITSAVE':
        moneywatchengine3.i_prepare_addupdate()
        return "ok"
    elif job == 'I.ENTRY.DELETE':
        moneywatchengine3.i_entry_delete()
        return "ok"
    elif job == 'I.GRAPH.GET':
        return moneywatchengine3.i_graph()
    elif job == 'B.SUMMARY.GET':
        return moneywatchengine3.b_summary()
    elif job == 'B.ACCOUNT.GET':
        return moneywatchengine3.b_accountget()
    elif job == 'B.ENTRY.ADD':
        return moneywatchengine3.b_entry_prepareadd()
    elif job == 'B.ENTRY.EDIT':
        return moneywatchengine3.b_entry_prepareedit()
    elif job == 'B.ENTRY.ADDSAVE' or job == 'B.ENTRY.EDITSAVE':
        moneywatchengine3.b_prepare_addupdate()
        return "ok"
    elif job == 'B.ENTRY.DELETE':
        moneywatchengine3.b_entry_delete()
        return "ok"
    elif job == 'B.BULKINTEREST.EDIT':
        return moneywatchengine3.b_bulkinterest_edit()
    elif job == 'B.BULKINTEREST.SAVE':
        moneywatchengine3.b_bulkinterest_save()
        return "ok"
    elif job == 'B.BULKBILLS.EDIT':
        return moneywatchengine3.b_bulkbills_edit()
    elif job == 'B.BULKBILLS.SAVE':
        moneywatchengine3.b_bulkbills_save()
        return "ok"
    elif job == 'U.IMPORTFILE.EDIT':
        return moneywatchengine3.u_importfile_edit()
    elif job == 'U.IMPORTFILE.SAVE':
        return moneywatchengine3.u_importfile_save()
    elif job == 'U.UPDATEQUOTES':
        moneywatchengine3.u_fetchquotes()
        return "ok"
    elif job == 'U.UPDATEBANKTOTALS':
        moneywatchengine3.u_banktotals()
        return "ok"
    elif job == 'U.LINKS.GET':
        return moneywatchengine3.u_linksgenerate()
    elif job == 'U.WEATHER.GET':
        return moneywatchengine3.us_weathergenerate()
    else:
        return ")(" # invalid, return ass cheeks

if __name__ == '__main__':
    relay.run(debug=True)
