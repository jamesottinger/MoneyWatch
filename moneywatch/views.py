from flask import current_app, Blueprint, render_template
from moneywatch import moneywatchengine
relay = Blueprint('relay', __name__, url_prefix='', static_folder='static')


@relay.route('/', methods=['GET', 'POST'])
def index():
    return relay.send_static_file('moneywatch.html')


@relay.route('/css/<file>', methods=['GET'])
def css(file):
    return relay.send_static_file('./css/{}'.format(file))


@relay.route('/js/<file>', methods=['GET'])
def js(file):
    return relay.send_static_file('./js/{}'.format(file))


@relay.route('/action/<job>', methods=['GET', 'POST'])
def actionhandler(job):
    if job == 'I.SUMMARY.GET':
        return moneywatchengine.i_summary()
    elif job == 'I.ELECTION.GET':
        return moneywatchengine.i_electionget()
    elif job == 'I.BULKADD.EDIT':
        return render_template('bulk_investments.html',
                               bulkinvestments=moneywatchengine.i_bulkadd_edit())
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
        return render_template('bank_edit.html',
                               entry=moneywatchengine.b_entry_prepare_add())
    elif job == 'B.ENTRY.EDIT':
        return render_template('bank_edit.html',
                               entry=moneywatchengine.b_entry_prepare_edit())
    elif job == 'B.ENTRY.ADDSAVE' or job == 'B.ENTRY.EDITSAVE':
        moneywatchengine.b_prepare_addupdate(job)
        return "ok"
    elif job == 'B.ENTRY.DELETE':
        moneywatchengine.b_entry_delete()
        return "ok"
    elif job == 'B.BULKINTEREST.EDIT':
        return render_template('bulk_interest.html',
                               bulkinterest=moneywatchengine.b_bulkinterest_edit())
    elif job == 'B.BULKINTEREST.SAVE':
        moneywatchengine.b_bulkinterest_save()
        return "ok"
    elif job == 'B.BULKBILLS.EDIT':
        return render_template('bulk_bills.html',
                               bulkbills=moneywatchengine.b_bulkbills_edit())
    elif job == 'B.BULKBILLS.SAVE':
        moneywatchengine.b_bulkbills_save()
        return "ok"
    elif job == 'U.IMPORTFILE.EDIT':
        return moneywatchengine.u_importfile_edit()
    elif job == 'U.IMPORTFILE.SAVE':
        return moneywatchengine.u_importfile_save()
    elif job == 'U.UPDATEQUOTES':
        moneywatchengine.u_fetch_quotes()
        return "ok"
    elif job == 'U.UPDATEBANKTOTALS':
        moneywatchengine.u_bank_totals()
        return "ok"
    elif job == 'U.LINKS.GET':
        return moneywatchengine.u_links_generate()
    elif job == 'U.WEATHER.GET':
        return moneywatchengine.u_weathergenerate()
    else:
        return ")("  # invalid, return ass cheek
