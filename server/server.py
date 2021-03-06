# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID
# Student: Magnus Brattlof
# CID: brattlof
# Email {cid}@student.chalmers.se
# ------------------------------------------------------------------------------------------------------

from bottle import Bottle, run, request, template, HTTPResponse
from byzantine_behavior import *
from threading import Thread
import traceback
import argparse
import requests
import operator
import sys
import time
import json

try:
    # Initialize app object and create our board data structures
    app = Bottle()
    board = {}

    """How to propagate messages:
    The server that receives the post message from client calls this function
    from propagate_vessels function.
    """
    def contact_vessel(vessel_ip, path, payload=None, req='POST'):
        # Try to contact another server (vessel) through a POST or GET, once
        success = False
        
        try:
            if 'POST' in req:
                res = requests.post('http://{}{}'.format(vessel_ip, path), json=payload)
            elif 'GET' in req:
                res = requests.get('http://{}{}'.format(vessel_ip, path))

            if res.status_code == 200:
                success = True
        except Exception as e:
            print e
        return success

    def propagate_to_vessels(path, payload = None, req = 'POST', byz = False, step = None):
        
        global vessel_list, node_id
        v = {}
        if byz:

            for vessel_id, vessel_ip in vessel_list.items():
                if int(vessel_id) != node_id:

                    if step == '1':
                        d = {node_id: payload[int(vessel_id)-1]}

                    else:

                        v = {}
                        for n, i in enumerate(payload[int(vessel_id)-1]):
                            v.update({n+1: i})

                        d = v

                    t = Thread(target=contact_vessel, args=(vessel_ip, path, d, req))
                    t.deamon = True
                    t.start()
        else:
            # Create a thread for each vessel in vessel_list
            # Execute each thread with contact_vessel as target
            for vessel_id, vessel_ip in vessel_list.items():
                if int(vessel_id) != node_id:
                    t = Thread(target=contact_vessel, args=(vessel_ip, path, payload, req,))
                    t.deamon = True
                    t.start()

    def calculate_result(vector):
        global action

        attack = 0
        retreat = 0
        action = None
        print "Calculate"
        for k, v in vector.iteritems():
            if v == True:
                attack += 1
            elif v == False:
                retreat += 1

        if attack >= retreat:
            action = True
        else:
            action = False      

    """Routing functions:
    Handles the index page plus the board page. 
    @app.post('/board') handles how new elements are added and calls
    correct functions for propagation to the other vessels in the system.
    """
    @app.route('/')
    def index():

        global board, node_id, entry_id, temp_board, action

        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()), members_name_string='Magnus Brattlof | brattlof@student.chalmers.se', action=action)

    @app.get('/board')
    def get_board():

        global board, node_id, temp_board, action

        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()), action=action)
    # ------------------------------------------------------------------------------------------------------
    @app.post('/vote/<command>')
    def attack(command):
        global local_vector, node_id, vessel_list, honest

        try:
            if command == 'attack':
                honest = True
                d = {str(node_id): True}
                local_vector.update(d)
                propagate_to_vessels('/propagate/{}/1'.format(node_id), d)
            
            elif command == 'retreat':
                honest = True
                d = {str(node_id): False}
                local_vector.update(d)
                propagate_to_vessels('/propagate/{}/1'.format(node_id), d)

            elif command == 'byzantine':
                honest = False
                byz_vector = compute_byzantine_vote_round1(len(vessel_list) -1, len(vessel_list), True)
                propagate_to_vessels('/propagate/{}/1'.format(node_id), byz_vector, byz=True, step='1')
            
            else:
                print "Error!"

            # Check if we can proceed to step 2
            if len(local_vector) == len(vessel_list):
                propagate_to_vessels('/propagate/{}/2'.format(node_id), local_vector)

            return HTTPResponse(status=200)
        except Exception as e:
            print e
        return False

    @app.post('/propagate/<neigh_id>/<step>')
    def receive_vectors(step, neigh_id):
        global local_vector, node_id, vessel_list, system_vector, byz_counter, lv

        ip = request.environ.get('REMOTE_ADDR')
        try:
            received_vector = json.load(request.body)
            local_vector.update(received_vector)
            
            # Here we must wait until we have received all vectors from step 2
            if honest == False:
                byz_counter += 1
                if byz_counter == len(vessel_list) - 1:
                    byz_vector = compute_byzantine_vote_round2(len(vessel_list) -1, len(vessel_list), True)
                    
                    propagate_to_vessels('/propagate/{}/2'.format(node_id), byz_vector, byz=True)

            else:

                # Check if we have received all votes from all the nodes
                # If we have, we can proceed to step 2 where we send our local vector
                if step == '1' and len(local_vector) == len(vessel_list):
                    propagate_to_vessels('/propagate/{}/2'.format(node_id), local_vector)
                    system_vector.update({node_id: local_vector})
                
                elif step == '2':
                    system_vector.update({neigh_id: received_vector})

                    if len(system_vector) == len(vessel_list) - 1:       
                        step2()

            return HTTPResponse(status=200)
        except Exception as e:
            print e
        return False

    def step2():
        global action

        attack = 0
        retreat = 0
        for key, values in system_vector.iteritems():
            for k, v in values.iteritems():
                if v == True:
                    attack += 1
                elif v == False:
                    retreat += 1

        if attack >= retreat:
            action = True
        else:
            action = False

        print action
    """Main execution starts from here:
    Initialization of variables and how to parse the cmd args.
    Booting up all webservers on the vessels.
    """
    def main():
        global vessel_list, node_id, app, local_vector, action, system_vector, honest, byz_counter, lv

        local_vector = {}
        system_vector = {}
        lv = {}
        action = None
        honest = None
        byz_counter = 0

        port = 80
        parser = argparse.ArgumentParser(description='Your own implementation of the distributed blackboard')
        parser.add_argument('--id', nargs='?', dest='nid', default=1, type=int, help='This server ID')
        parser.add_argument('--vessels', nargs='?', dest='nbv', default=1, type=int, help='The total number of vessels present in the system')
        args = parser.parse_args()
        node_id = args.nid
        vessel_list = dict()
        # We need to write the other vessels IP, based on the knowledge of their number
        for i in range(1, args.nbv):
            vessel_list[str(i)] = '10.1.0.{}'.format(str(i))

        try:
            # Added a reloader to refresh the all servers with the changes 
            run(app, host=vessel_list[str(node_id)], port=port, reloader=True)

        except Exception as e:
            print e
    # ------------------------------------------------------------------------------------------------------
    if __name__ == '__main__':
        main()
except Exception as e:
        traceback.print_exc()
        while True:
            time.sleep(60.)