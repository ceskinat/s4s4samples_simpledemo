#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 09:33:00 2023

@author: cem
"""

from flask import Flask, render_template, request, redirect, session, jsonify
# from flask_socketio import SocketIO
# from routeX import app, socketio, session
# from sampleintfcs import object_list, client

from flask_session import Session


app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'KeB932okfjc'
Session(app)

S4S4_ADDRESS = 'http://localhost:5010/routing_form'
#S4S4_ADDRESS = 'http://akvaryum.solusmart.com:5010/routing_form'
API_CLIENTID = "s4s4demo"
API_KEY = "s4s4password" 



# from config import MONGO_CONN_STRING

from pymongo import MongoClient
# client = MongoClient(MONGO_CONN_STRING)
client = MongoClient()




# app = Flask(__name__)

# app.register_blueprint(routeX_app)

import re 
def object_list(inp):
    # returns a sample list of objects
    db = client.routeX_demo
    lst = list(db.objects.find({"oname": re.compile(inp, re.I)}))

    return lst


def object_name(otype, oid):
    for obj in object_list(""):
        if obj["otype"] == otype and obj["oid"] == oid:
            return obj["oname"]
    return None


def all_users():
    db = client.routeX_demo
    return list(db.users.find())



@app.route('/', methods = ['GET', 'POST'])
def index():
    ol = object_list("")
    types = list(set([k["otype"] for k in ol]))
    return render_template('demoindex.html', objs=ol, otypes=types, s4s4address=S4S4_ADDRESS)

@app.route('/add_object', methods=['POST'])
def add_object():
    from random import randint
    db = client.routeX_demo
    if request.form.get("newtype"):
        otype = request.form["newtype"]
    else:
        otype = request.form["slct-type"]
    
    if db.objects.find_one({"otype": otype, "oname": request.form["newname"]}):
        return "Object already defined"
    
    oid = randint(1e6, 1e7 -1) # generate a random 7 digit integer
    while db.objects.find_one({"otype": otype, "oid": oid}):
        oid = randint(1e6, 1e7 -1) 
        
    db.objects.insert_one({"otype": otype,
                           "oid": oid,
                           "oname": request.form["newname"] })
    return redirect('/')


@app.route('/login', methods=["POST"])
def login():
    db = client.routeX_demo
    usr = db.users.find_one({"username": request.form["username"]})
    if not usr:
        db.users.insert_one({"username": request.form["username"], "email": request.form.get("email")})
        usr = db.users.find_one({"username": request.form["username"]})
    elif request.form.get("email"):
        db.users.update_one({"username": request.form["username"]},
                            {"$set": {"email": request.form["email"]}})
        
    session["user"] = {"userid": usr["_id"],
                       "username": request.form["username"]}
    if request.form.get("email"):
        session["user"]["email"] = request.form["email"]
    elif usr.get("email"):
        session["user"]["email"] = usr["email"]
        

    ol = object_list("")
    types = list(set([k["otype"] for k in ol]))
    return render_template('demoindex.html', objs=ol, otypes=types, s4s4address=S4S4_ADDRESS)
    
@app.route('/logout', methods=["GET"])
def logout():
    session.pop("user", None)
    return render_template('demoindex.html')

@app.route('/get-auth-code', methods=['GET'])
def api_code():
    return jsonify({"api_key": API_KEY,
                    "client_id": API_CLIENTID})



import requests

@app.route('/routing_form', methods=['GET'])
def routing_form():
    # proxy for posting to s4s4
    ret = requests.post("http://localhost:5010/routing_form", data=request.args)
    return ret.content


@app.route('/interfaces/object_list', methods=['POST'])
def obj_list():
    # returns a sample list of objects
    inp = request.form.get("inp", "")
    db = client.routeX_demo
#    lst = list(db.objects.find({"oname": re.compile(inp, re.I)}))
    lst = []
    for obj in db.objects.find({"oname": re.compile(inp, re.I)}):
        lst.append({"id": {"id": [obj["otype"], str(obj["oid"])], "name": obj["oname"]},
                    "name": obj["otype"] + ":" + obj["oname"]})


    return lst

@app.route('/interfaces/object_name', methods=['POST'])
def obj_name():
    otype = request.form["otype"]
    oid = int(request.form["oid"])

    db = client.routeX_demo
    obj = db.objects.find_one({"otype": otype,
                               "oid": oid  })
    if obj:
        return obj["oname"]
    else:
        return ""

"""
    for obj in object_list(""):
        if obj["id"]["id"][0] == otype and str(obj["id"]["id"][1]) == oid:
            return obj["id"]["name"]
    return None
"""

@app.route('/interfaces/authorized_users', methods=['POST'])
def all_users():
    # returns in the form of {"id": id, "name": username}
    db = client.routeX_demo
    
    return [{"id": str(x["_id"]), "name": x["username"], "email": x.get("email", "") } for x in db.users.find()]


@app.route('/routing_proxy', methods=['GET'])
def routing_proxy():

    
    url = "http://localhost:5010/routing_form?otype=" + request.args.get("otype")   
    url +="&oid=" + request.args.get('oid') + "&username=" + session["user"]["username"]
    if session["user"].get("email"): 
        url += "&email=" + session["user"]["email"]
    ret = requests.get(url)
    return ret.content
    



if __name__ == '__main__':
    app.run(debug = True, host = "0.0.0.0", port=5015)
    # socketio.run(app, debug = True, host = "0.0.0.0", port=5010)   
