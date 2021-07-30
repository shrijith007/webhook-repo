from flask import json
from flask import request
from flask import Flask,render_template
from pymongo import MongoClient
from bson import json_util
import datetime;


#Establishing connection with MongoDb 
cluster=MongoClient("mongodb+srv://shrij:liverpool3$@c1.nrqxg.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db=cluster["Webhook"]
collection=db["actiondata"]

#function to update from Db
def data_update():
    return list(collection.find({}))
    
#initializing Flask app
app=Flask(__name__,template_folder="template")

#Route to fetch data from db every 15seconds
@app.route("/fetchy",methods=["GET"])
def fetchy():
    data=data_update()
    d=json.loads(json_util.dumps(data))
    return {"d":d}

#route to home page
@app.route('/')
def api_root():
    d=data_update()
    return render_template("index.html",len=len(d), data=d)

#Route for fetching github webhook updates 
@app.route("/webhook/receiver",methods=["POST"])
def api_ghmessages():
    if request.headers["Content-Type"] =="application/json":
        my_inf= request.json
        timestamp='{:%Y-%b-%d %H:%M:%S}'.format(datetime.datetime.now())
        #sorting the webhook updates based on their action types
        
        if("pull_request" in my_inf.keys() ): #if pull request 
            if(my_inf["action"]!='closed'):
                collection.insert_one({
                    "request_id":my_inf["pull_request"]["id"],
                    "to_branch":my_inf['pull_request']['base']["ref"],
                    "author":my_inf['pull_request']['user']['login'],
                    "timestamp":timestamp+ "UTC",
                    "from_branch":my_inf["pull_request"]["head"]["ref"],
                    "action":"PULL"
                })
            elif(my_inf["action"]=='closed' and my_inf["pull_request"]["merged"]==True): #if merged the pull request
                 collection.insert_one({
                    "request_id":my_inf["pull_request"]["id"],
                    "to_branch":my_inf['pull_request']['base']["ref"],
                    "author":my_inf['pull_request']['user']['login'],
                    "timestamp":timestamp+"UTC",
                    "from_branch":my_inf["pull_request"]["head"]["ref"],
                    "action":"MERGE"
                })
        elif("pusher" in my_inf.keys() ): #if its pushing event
            s = my_inf["ref"]
            start = s.find("heads/") + len("heads/")
            substring = s[start:]
            collection.insert_one({
                "request_id":my_inf["commits"][0]["id"],
                "to_branch":substring,
                "author":my_inf['commits'][0]['author']['username'],
                "timestamp":timestamp+"UTC",
                "from_branch":"",
                "action":"PUSH"
                })
        return my_inf

#Running the app        
if __name__=="__main__":
    app.run(debug=True)


