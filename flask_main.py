"""
Flask web app connects to Mongo database.
Keep a simple list of dated memoranda.

Representation conventions for dates: 
   - We use Arrow objects when we want to manipulate dates, but for all
     storage in database, in session or g objects, or anything else that
     needs a text representation, we use ISO date strings.  These sort in the
     order as arrow date objects, and they are easy to convert to and from
     arrow date objects.  (For display on screen, we use the 'humanize' filter
     below.) A time zone offset will 
   - User input/output is in local (to the server) time.  
"""

import flask
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify # For AJAX transactions


import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we may still need time
from dateutil import tz  # For interpreting local times


# Mongo database
from pymongo import MongoClient


###
# Globals
###
import CONFIG

app = flask.Flask(__name__)

try: 
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.memos
    collection = db.dated

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)

import uuid
app.secret_key = str(uuid.uuid4())

###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Main page entry")
  flask.session['memos'] = get_memos()
  for memo in flask.session['memos']:
      app.logger.debug("Memo: " + str(memo))
  return flask.render_template('index.html')


# Just give the client the requested create.html file
@app.route("/create")
def create():
    app.logger.debug("Create")
    return flask.render_template('create.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('page_not_found.html',
                                 badurl=request.base_url,
                                 linkback=url_for("index")), 404


################
#
# Stores the memo in the db
#
###############
@app.route("/_store")
def store():
    """"
    Gets the memo and date from create.html
    then stores it in the db then returns
    """
    app.logger.debug("Entering db handling")
    text = request.args.get("text", type=str)
    date = request.args.get("date", type=str)
    app.logger.debug("text: " + text)
    app.logger.debug("date: " + date)

    #take date and localize it and store it in isoformat
    aDate = arrow.get(date, 'MM/DD/YYYY').replace(tzinfo='local')
    fDate = aDate.isoformat()
    record = { "type": "dated_memo",
           "date":  fDate,
           "text": text
          }

    collection.insert(record)
    rslt = True
    return jsonify(result=rslt)



###################
#
# Deletes the list of memos
#
##################
@app.route("/_delete")
def delete():
    """"
    Deletes all selected memos
    Expects a list memo _ids
    Then splits them
    """
    memos = request.args.get("memos", type=str)
    app.logger.debug("Memo Ids: " + memos)

    remove_memos(memos)
    #return garbage
    rslt = True
    return jsonify(result=rslt)


###########
#
# just removes memos from db
#
##########
def remove_memos(mems):
    """
    :param mems: list of memo ids
    :return: nothing
    """
    #Split it up so we can search for multiple _ids
    ids = mems.split(" ")
    for entry in collection.find():
        #Now delete if we find it
        if str(entry["_id"]) in ids:
            collection.remove(entry)
    return


#used to humanize the date within the client
@app.template_filter( 'humanize' )
def humanize_arrow_date( date ):
    """
    Date is internal UTC ISO format string.
    Output should be "today", "yesterday", "in 5 days", etc.
    Arrow will try to humanize down to the minute, so we
    need to catch 'today' as a special case. 
    """
    try:
        then = arrow.get(date).to('local')
        now = arrow.utcnow().to('local')
        tomorrow = now.replace(days=1)
        if then.date() == now.date():
            human = "Today"
        elif then.humanize(now) == "a day ago":
            human = "Yesterday"
        elif tomorrow.date() == then.date():
            human = "Tomorrow"
        else: 
            human = then.humanize(now)
            if human == "in a day":
                human = "Tomorrow"
    except: 
        human = date
    return human


#############
#
# Just gets all the memos in the db stores them in a dict sorts then and returns it
#
##############
def get_memos():
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = [ ]
    #if collection is empty return empty records
    if collection.count() == 0:
        return records

    for record in collection.find( { "type": "dated_memo" } ):
        record['date'] = arrow.get(record['date']).isoformat()

        #used for saving memos
        record['_id'] = str(record['_id'])
        records.append(record)

        #sort the memos
        sorted_records = sorted(records, key=lambda x: x["date"])
    return sorted_records


if __name__ == "__main__":
    # App is created above so that it will
    # exist whether this is 'main' or not
    # (e.g., if we are running in a CGI script)
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    # We run on localhost only if debugging,
    # otherwise accessible to world
    if CONFIG.DEBUG:
        # Reachable only from the same computer
        app.run(port=CONFIG.PORT)
    else:
        # Reachable from anywhere 
        app.run(port=CONFIG.PORT,host="0.0.0.0")

    
