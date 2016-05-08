#!/ usr/bin/env python3
#===============================================================================
# Copyright (c) 2016, James Ottinger. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# MoneyWatch - https://github.com/jamesottinger/moneywatch
#===============================================================================
from flask import Flask, abort, request
import sys
sys.path.append('./cgi-bin/')
import moneywatchengine

relay = Flask('relay', static_url_path='')
#===============================================================================

@relay.route('/', methods=['GET', 'POST'])
def index():
    return relay.send_static_file('moneywatch.html')

@relay.route('/action/<job>', methods=['GET', 'POST'])
def actionhandler(job):
    if job == 'I.SUMMARY.GET':
        return moneywatchengine.i_summary()
    elif job == 'I.ELECTION.GET':
        return moneywatchengine.i_electionget()
    elif job == 'I.BULKADD.EDIT':
        return moneywatchengine.i_bulkadd_edit()
    elif job == 'I.BULKADD.SAVE':
        moneywatchengine.i_bulkadd_save()
        return "ok"
    elif job == 'I.ENTRY.ADD':
        return moneywatchengine.i_entry_prepareadd()
    elif job == 'I.ENTRY.EDIT':
        return moneywatchengine.i_entry_prepareedit()
    elif job == 'I.ENTRY.ADDSAVE' or job == 'I.ENTRY.EDITSAVE':
        moneywatchengine.i_prepare_addupdate()
        return "ok"
    elif job == 'I.ENTRY.DELETE':
        moneywatchengine.i_entry_delete()
        return "ok"
    elif job == 'I.GRAPH.GET':
        return moneywatchengine.i_graph()
    elif job == 'B.SUMMARY.GET':
        return moneywatchengine.b_summary()
    elif job == 'B.ACCOUNT.GET':
        return moneywatchengine.b_accountget()
    elif job == 'B.ENTRY.ADD':
        return moneywatchengine.b_entry_prepareadd()
    elif job == 'B.ENTRY.EDIT':
        return moneywatchengine.b_entry_prepareedit()
    elif job == 'B.ENTRY.ADDSAVE' or job == 'B.ENTRY.EDITSAVE':
        moneywatchengine.b_prepare_addupdate(job)
        return "ok"
    elif job == 'B.ENTRY.DELETE':
        moneywatchengine.b_entry_delete()
        return "ok"
    elif job == 'B.BULKINTEREST.EDIT':
        return moneywatchengine.b_bulkinterest_edit()
    elif job == 'B.BULKINTEREST.SAVE':
        moneywatchengine.b_bulkinterest_save()
        return "ok"
    elif job == 'B.BULKBILLS.EDIT':
        return moneywatchengine.b_bulkbills_edit()
    elif job == 'B.BULKBILLS.SAVE':
        moneywatchengine.b_bulkbills_save()
        return "ok"
    elif job == 'U.IMPORTFILE.EDIT':
        return moneywatchengine.u_importfile_edit()
    elif job == 'U.IMPORTFILE.SAVE':
        return moneywatchengine.u_importfile_save()
    elif job == 'U.UPDATEQUOTES':
        moneywatchengine.u_fetchquotes()
        return "ok"
    elif job == 'U.UPDATEBANKTOTALS':
        moneywatchengine.u_banktotals()
        return "ok"
    elif job == 'U.LINKS.GET':
        return moneywatchengine.u_linksgenerate()
    elif job == 'U.WEATHER.GET':
        return moneywatchengine.u_weathergenerate()
    else:
        return ")(" # invalid, return ass cheeks

if __name__ == '__main__':
    relay.run(debug=True, port=5000, host='0.0.0.0')
