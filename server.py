#!/usr/bin/env python
# coding: utf-8
# Copyright 2013 Abram Hindle
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You can start this by executing it in python:
# python server.py
#
# remember to:
#     pip install flask


import flask
from flask import Flask, request, redirect, make_response
import json
# import flask.cli    
# flask.cli.show_server_banner = lambda *args: None

# import logging
# logging.getLogger("werkzeug").disabled = True
app = Flask(__name__)
app.debug = True

# An example world
# {
#    'a':{'x':1, 'y':2},
#    'b':{'x':2, 'y':3}
# }

class World:     
    def __init__(self):
        self.clear()
        self.etag = "test"
        
    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry

    def set(self, entity, data):
        self.space[entity] = data

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self, etagTime=None):
        unfamiliarWorld = {}
        if etagTime:
            # print('etagTime', etagTime)
            for key, value in self.space.items():
                if key > etagTime and key != etagTime:
                    unfamiliarWorld[key] = value
            return unfamiliarWorld
        return {}#self.space

# you can test your webservice from the commandline
# curl -v   -H "Content-Type: application/json" -X PUT http://127.0.0.1:5000/entity/X -d '{"x":1,"y":1}' 

myWorld = World()          

# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])


def etagify(resp: flask.Response) -> flask.Response:
    resp.add_etag(overwrite=True)
    myWorld.etag = resp.get_etag()[0]
    return resp


@app.route("/")
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    return redirect("/static/index.html", code=302)


@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    # print('got request to update')
    update_data = flask_post_json()
    if type(update_data) == list:
        for thing in update_data:
            for k, v in thing[1].items():
                myWorld.update(thing[0], k, v)
    else:          
        for key, val in update_data.items():
            myWorld.update(entity, key, val)
    resp = make_response(myWorld.get(entity))
    resp = etagify(resp)
    # print('updated world', myWorld.etag)
    return resp


@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    etagTime = request.if_range.to_header()
    resp = make_response(myWorld.world(etagTime))
    resp.set_etag(myWorld.etag)
    resp = resp.make_conditional(request)
    # if resp.status_code == 200:
    #     print('sending world', myWorld.etag)
    return resp


@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    return myWorld.get(entity)


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    myWorld.clear()
    resp = make_response(myWorld.world())
    return etagify(resp)



if __name__ == "__main__":
    app.run()
