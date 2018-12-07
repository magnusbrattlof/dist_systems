# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID
# Student: Magnus Brattlof
# CID: brattlof
# Email {cid}@student.chalmers.se
# ------------------------------------------------------------------------------------------------------

from bottle import Bottle, run, request, template
from threading import Thread
import traceback
import argparse
import requests
import operator
import sys
import time
import json

try:
    # Initialize app object and create our board dictionary
    app = Bottle()
    board = {}
    temp_board = []
    
    """Board functions:
    Handles how the vessels are adding new elements, 
    how to modify elements and how to delete specified elements. 
    """
    def sort_board(temp_board):
        global board
        
        d = sorted(temp_board, key=lambda element: (element[0], element[1]))
        
        for n, i in enumerate(d):
            board[n] = i[2]

        return board

    def add_new_element_to_store(lclock, element, neigh_id):
        
        global board, node_id, entry_id, temp_board
        success = False
        try:
            
            # Add the time-stamp (lclock) and neighbor id and element to temp list
            # This list will be sorted when clients refresh their pages
            temp_board.append((lclock, neigh_id, element))

            success = True
            
        except Exception as e:
            print e
        return success

    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call = False):
        
        global board, node_id
        success = False
        try:
            # Update the board dictionary with the modified_element
            board[entry_sequence] = modified_element
            success = True
        except Exception as e:
            print e
        return success

    def delete_element_from_store(entry_sequence, is_propagated_call = False):
        
        global board, node_id
        success = False
        try:
            # Pop entry from the board dictionary
            board.pop(entry_sequence, None)
            success = True
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

    """Routing functions:
    Handles the index page plus the board page. 
    @app.post('/board') handles how new elements are added and calls
    correct functions for propagation to the other vessels in the system.
    """
    @app.route('/')
    def index():

        global board, node_id, entry_id, temp_board
        board = sort_board(temp_board)
        #print "Board: ", board
        #print "Entry id: ", entry_id
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()), members_name_string='Magnus Brattlof | brattlof@student.chalmers.se')

    @app.get('/board')
    def get_board():

        global board, node_id, temp_board
        board = sort_board(temp_board)
        #print board
        #print "Entry id: ", entry_id
        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()))
    # ------------------------------------------------------------------------------------------------------
    @app.post('/board')
    def client_add_received():
        '''Adds a new element to the board
        Called directly when a user is doing a POST request on /board'''
        global board, node_id, lclock
        try:
            # Fetch new entry from the input form
            new_element = request.forms.get('entry')
            # Prepare data to send to other vessels
            body = {
                'element': new_element,
                'lclock': lclock,
                'node_id': node_id,
                'action': 'add'
            }

            # Add new entry to our dictionaty
            add_new_element_to_store(lclock, new_element, node_id)
            propagate_to_vessels("/propagate/add", payload=body)
            lclock += 1
            
            return True
        except Exception as e:
            print e
        return False

    def sortBoard(board): 
        integerParsedBoard = {int(float(k)): v for k, v in board.items()}
        return sorted(integerParsedBoard.iteritems())

    """The function client_action_received receives an element_id from the POST http-message.
    The value stored on the blackboard is stored in the 'mod_element' variable
    in 'delete' the value 0 or 1 is stored which we leverage to choose delete or modify
    we call the correct function and later propagates the changes to the rest vessels
    """
    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        
        try:
            # Retreive appropiate data from HTML-form
            mod_element = request.forms.get('entry')
            delete = int(request.forms.get('delete'))

            if delete == True:
                delete_element_from_store(element_id, None)
                propagate_to_vessels("/propagate/delete/{}".format(element_id), payload=None)
            else:
                modify_element_in_store(element_id, mod_element)
                propagate_to_vessels("/propagate/modify/{}".format(element_id), payload=mod_element)
            return True
       
        except Exception as e:
            print e
        return False

    """Propagation_received takes two arguments, action and element_id
    this POST http-message is issued by some vessel which has been posted with som changes
    here we have the global variable entry_id which every vessel in the system will update accordingly
    if there are a new element added. 

    Three actions are available, add, modify or delete. 
    The element are fetched from the http-messages body    
    """
    @app.post('/propagate/<action>')
    def propagation_received(action):
        
        global entry_id, lclock
        try:

            body = json.load(request.body)
            entry = body['element']
            neigh_lclock = body['lclock']
            neigh_id = body['node_id']

            # Action add, adding new element to our board, updating entry_id
            # to be consistent in our system
            if action == 'add':
                add_new_element_to_store(neigh_lclock, entry, neigh_id)
                lclock += 1
    
            # Fetch modified element from the http-body message and modify it.
            elif action == 'modify':
                mod_element = request.body.readlines()[0]
                modify_element_in_store(element_id, mod_element)
            
            # Deletes the element with element_id
            elif action == 'delete':
                delete_element_from_store(element_id, None)
            return True

        except Exception as e:
            print e
        return False
            
    """Main execution starts from here:
    Initialization of variables and how to parse the cmd args.
    Booting up all webservers on the vessels.
    """
    def main():
        global vessel_list, node_id, app, lclock, payload

        # Initialize entry_id to 0 for all vessels
        lclock = 0
        payload = {}

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