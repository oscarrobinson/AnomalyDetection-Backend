# run.py

# -*- encoding:utf8 -*-

import json
from flask import Flask, request, abort, make_response
from pymongo import MongoClient
from bson import json_util
from flask_cors import CORS
import time
import os
import datetime
import time

# Handling ObjectId: http://stackoverflow.com/questions/8409194/unable-to-deserialize-pymongo-objectid-from-json
# Handling spaces in URL: replace ' ' character with '%20', e.g. "Hello World" -> "Hello%20World"

# Flask
app = Flask(__name__)
#enable Cross Origin Support
cors = CORS(app)

# MongoDB connection
client = MongoClient("127.0.0.1", 27017)
db = client.tempdata
readingsCollection = db.temps
sensorsCollection = db.sensors


#-----------------------------#
#       ERROR HANDLERS        #
#-----------------------------#
@app.errorhandler(400)
def bad_request(error):
    resp = make_response("Bad Request", 400)
    return resp

#-----------------------------#
#       HELPER FUNCTIONS      #
#-----------------------------#

def createJsonList(listName):
    return "{\""+listName+"\":[]}"


def jsonListAppend(jList, listItem, comma=True):
    if comma:
        return jList[:-2]+","+(json.dumps(listItem, sort_keys=True, indent=4, separators=(',', ': '), default=json_util.default))+"]}"
    else:
        return jList[:-2]+(json.dumps(listItem, sort_keys=True, indent=4, separators=(',', ': '), default=json_util.default))+"]}"


def getReadings(startTime, endTime):
    result = createJsonList("readings")
    allReadings = readingsCollection.find({"time": {"$gt": str(startTime), "$lt": str(endTime)}})
    count = 0
    for reading in allReadings:
        if count==0:
            result = jsonListAppend(result, reading, False)
        else:
            result = jsonListAppend(result, reading)
        count+=1
    return result

#-----------------------------#
#      ROUTING FUNCTIONS      #
#-----------------------------#

#Used to get readings in certain time range
@app.route('/api/readings-unixtime', methods=['GET'])
def readingsUnixTime():
    startTime = request.args.get('start', '')
    endTime = request.args.get('end', '')
    if not startTime:
        startTime = time.time()-86400
    if not endTime:
        endTime = time.time()
    return getReadings(startTime, endTime)

@app.route('/api/readings', methods=['GET'])
def readings():
    #1-12-1994-12:12
    startTime = request.args.get('start', '')
    endTime = request.args.get('end', '')
    try:
        if startTime:
            startDateTime =  time.strptime(startTime, "%d-%m-%Y-%H:%M")
        else:
            startDateTime = time.strptime(time.ctime(time.time()-86400))
        if endTime:
            endDateTime = time.strptime(endTime, "%d-%m-%Y-%H:%M")
        else:
            endDateTime = time.strptime(time.ctime())
    except Exception:
        abort(400)

    print time.asctime(startDateTime)
    print time.asctime(endDateTime)

    return getReadings(time.mktime(startDateTime), time.mktime(endDateTime))

@app.route('/api/sensors', methods=['GET'])
def sensors():
    result = createJsonList('sensors')
    allSensors = sensorsCollection.find()
    count = 0
    for sensor in allSensors:
        if count==0:
            result = jsonListAppend(result, sensor, False)
        else:
            result = jsonListAppend(result,sensor)
        count+=1
    return result

@app.route('/api/thresholds/get', methods=['GET'])
def thresholdsGet():
    network = request.args.get('network', '')
    thresholdVals = db.thresholds.find({"network":network})
    for threshold in thresholdVals:    
        return json.dumps(threshold, sort_keys=True, indent=4, separators=(',', ': '), default=json_util.default)
    else:
        return "{}"

@app.route('/api/thresholds/set', methods=['POST'])
def thresholdsSet():
    dataToAdd = dict()
    json = request.get_json()
    try:
        json["network"]
    except:
        abort(400)
    try: 
        json["amber"]
        dataToAdd = {"amber": float(json["amber"])}
    except:
        pass
    try:
        json["red"]
        dataToAdd.update({"red": float(json["red"])})
    except:
        pass
    dataToAdd.update({"lastUpdated": int(time.time())})
    db.thresholds.update({"network": json["network"]}, {"$set": dataToAdd})
    return "Set Thresholds Successfully for "+str(json["network"])

#-----------------------------#
#           INIT API          #
#-----------------------------#

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
