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

    """Board functions:
    Handles how the vessels are adding new elements, 
    how to modify elements and how to delete specified elements. 
    """
    def add_new_element_to_store(lclock, element, neigh_id):
        global board, node_id, entry_id, temp_board
        success = False
        try:
            
            # Append the logical clock, neighbor id and element to the temp board
            # After, we call sync_board which executes multiple checks and sorts the real board
            temp_board.append((lclock, neigh_id, element))
            sync_board()
            success = True
            
        except Exception as e:
            print e
        return success

    """Function that handles modification of messages.
    If the entry_sequence is in the board, the modification will take place.
    Else if it is not in the board, the entry_sequence will be added to mod_q
    """
    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call = False):
        global board, node_id, mod_q
        success = False
        try:
            if entry_sequence in board:
                # Update the board dictionary with the modified_element
                board[entry_sequence] = modified_element
            else:
                # Add the entry_sequence and element to modify queue
                mod_q[entry_sequence] = modified_element
                print "Element added to modify queue"

            success = True
        except Exception as e:
            print e
        return success

    """Function that handles deletion of elements in boards.
    If the sequence is in the board, the delete will take place.
    Else, must check if it is in the del_history or in the del_q.
    """
    def delete_element_from_store(entry_sequence, is_propagated_call = False):
        global board, node_id, del_q, temp_board, del_hist
        success = False
        try:
            # If the sequence is in board, delete it from real board and temprary board
            # Append to delete history, used for concurrent posts
            if entry_sequence in board:
                del_hist.append(entry_sequence)
                del board[entry_sequence]
                del temp_board[entry_sequence]
                
                success = True
            
            # Elese if there are concurrent deletes from two nodes
            # We check our delete history.
            elif entry_sequence in del_hist:
                print "Item already deleted"
            # Else add it to the delete queue which will be checked in sync_board function
            else:
                print "Item not in board, adding to delete queue"
                del_q.append(entry_sequence)

        except Exception as e:
            print e
        return success

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

    def propagate_to_vessels(path, payload = None, req = 'POST'):
        
        global vessel_list, node_id

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

        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()))
    # ------------------------------------------------------------------------------------------------------
    @app.post('/vote/<command>')
    def attack(command):
        global vector, node_id, vessel_list

        try:
            if command == 'attack':
                d = {str(node_id): True}
                vector.update(d)
                propagate_to_vessels('/propagate/1', d)
            
            elif command == 'retreat':
                d = {str(node_id): False}
                vector.update(d)
                propagate_to_vessels('/propagate/1', d)

            elif command == 'byzantine':
                print "Byzantine!"
            
            else:
                print "Error!"

            # Check if we can proceed to step 2
            if len(vector) == len(vessel_list):
                propagate_to_vessels('/propagate/2', vector)

            return HTTPResponse(status=200)
        except Exception as e:
            print e
        return False

    @app.post('/propagate/<step>')
    def receive_vectors(step):
        global vector, node_id, vessel_list
        ip = request.environ.get('REMOTE_ADDR')
        try:
            received_vector = json.load(request.body)
            vector.update(received_vector)                
            
            if step == '1' and len(vector) == len(vessel_list):
                propagate_to_vessels('/propagate/2', vector)
            
            elif step == '2':
                print "Step 2"
                print "Received vector {} from {}".format(received_vector, ip)
            
            return HTTPResponse(status=200)
        except Exception as e:
            print e
        return False


    """Main execution starts from here:
    Initialization of variables and how to parse the cmd args.
    Booting up all webservers on the vessels.
    """
    def main():
        global vessel_list, node_id, app, vector, action

        vector = {}
        action = None



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