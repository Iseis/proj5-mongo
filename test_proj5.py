"""
Tests for dates and db structure
"""


import arrow # Replacement for datetime, based on moment.js

#imports
from flask_main import get_memos
from flask_main import humanize_arrow_date
from flask_main import remove_memos


# Mongo database
from pymongo import MongoClient

import CONFIG
import sys

try:
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.memos
    collection = db.dated

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)

"""
Check and see if dates are being humanized correctly/also shows sorting since
get_memos() sorts date1 Which would be "Today" is pulled out of db in memos[1] position
where as date2 which would be "Yesterday" is pulled out of db in memos[0] position
Also no need to mess with times since I use date picker user can't select times
"""
def test_humanize_sort():
    collection.remove( {} )

    memo1 = "This is memo1"
    date1 = arrow.utcnow().to('local')
    isoDate1 = date1.isoformat()
    record = { "type": "dated_memo",
           "date":  isoDate1,
           "text": memo1
          }
    collection.insert(record)

    memo2 = "This is memo2"
    date2 = date1.replace(days=-1).isoformat()
    record = { "type": "dated_memo",
        "date":  date2,
        "text": memo2
    }

    collection.insert(record)

    memo3 = "This is memo2"
    date3 = date1.replace(days=1).isoformat()
    record = { "type": "dated_memo",
        "date":  date3,
        "text": memo3
    }
    collection.insert(record)

    memos = get_memos()
    assert humanize_arrow_date(memos[0]['date']) == "Yesterday"
    assert humanize_arrow_date(memos[0]['text']) == "This is memo2" #just to show sorting
    assert humanize_arrow_date(memos[1]['date']) == "Today"
    assert humanize_arrow_date(memos[2]['date']) == "Tomorrow"


"""
Test deletion
"""
def test_deletion():
    memos = get_memos()

    id = memos[0]['_id']
    #remove one entry from the collection
    remove_memos(id)
    #get number of entries left
    assert collection.count() == 2

    id = memos[1]['_id']
    #remove next
    remove_memos(id)
    assert collection.count() == 1

    id = memos[2]['_id']
    #remove next
    remove_memos(id)
    assert collection.count() == 0