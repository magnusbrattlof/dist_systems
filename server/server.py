# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID
# Student: John Doe
# ------------------------------------------------------------------------------------------------------
import traceback
import sys
import time
import json
import argparse
from threading import Thread

from bottle import Bottle, run, request, template
import requests
# ------------------------------------------------------------------------------------------------------
try:
    app = Bottle()

    board = {}

    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # Should nopt be given to the student
    # ------------------------------------------------------------------------------------------------------
    def add_new_element_to_store(entry_sequence, element, is_propagated_call=False):
        
        global board, node_id
        success = False
        try:
            # Add new element with sequence number and element
            board[entry_sequence] = element
            success = True
        except Exception as e:
            print e
        return success

    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call = False):
        
        global board, node_id
        success = False
        try:
            # Update the dictionary with the modified_element
            board[entry_sequence] = modified_element
            success = True
        except Exception as e:
            print e
        return success

    def delete_element_from_store(entry_sequence, is_propagated_call = False):
        
        global board, node_id
        success = False
        try:
            # Pop entry from dictionary
            board.pop(entry_sequence, None)
            success = True
        except Exception as e:
            print e
        return success

    # ------------------------------------------------------------------------------------------------------
    # DISTRIBUTED COMMUNICATIONS FUNCTIONS
    # should be given to the students?
    # ------------------------------------------------------------------------------------------------------
    def contact_vessel(vessel_ip, path, payload=None, req='POST'):
        # Try to contact another server (vessel) through a POST or GET, once
        success = False
        
        try:
            if 'POST' in req:
                res = requests.post('http://{}{}'.format(vessel_ip, path), data=payload)
            elif 'GET' in req:
                res = requests.get('http://{}{}'.format(vessel_ip, path))
            else:
                print 'Non implemented feature!'
            # result is in res.text or res.json()
            print(res.text)
            if res.status_code == 200:
                success = True
        except Exception as e:
            print e
        return success

    def propagate_to_vessels(path, payload = None, req = 'POST'):
        
        global vessel_list, node_id

        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id: # don't propagate to yourself
                t = Thread(target=contact_vessel, args=(vessel_ip, path, payload, req,))
                t.deamon = True
                t.start()
                # success = contact_vessel(vessel_ip, path, payload, req)
                # if not success:
                #     print "\n\nCould not contact vessel {}\n\n".format(vessel_id)


    # ------------------------------------------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------------------------------------------
    # a single example (index) should be done for get, and one for post
    # ------------------------------------------------------------------------------------------------------
    @app.route('/')
    def index():

        global board, node_id
        print "Board: ", board
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()), members_name_string='Magnus Brattlof | brattlof@student.chalmers.se')

    @app.get('/board')
    def get_board():

        global board, node_id
        print board
        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()))
    # ------------------------------------------------------------------------------------------------------
    @app.post('/board')
    def client_add_received():
        '''Adds a new element to the board
        Called directly when a user is doing a POST request on /board'''
        global board, node_id, entry_id
        try:
            # Fetch new entry from the input form
            new_element = request.forms.get('entry')
            # Add new entry to our dictionaty
            add_new_element_to_store(entry_id, new_element)
            propagate_to_vessels("/propagate/add/{}".format(entry_id), payload=new_element)
            # Increment entry id, to keep track of number of entries
            entry_id += 1

            return True
        except Exception as e:
            print e
        return False

    """The function client_action_received receives an element_id from the POST http-message.
    The value stored on the blackboard is stored in the 'mod_element' variable
    in 'delete' the value 0 or 1 is stored which we leverage to choose delete or modify
    we call the correct function and later propagates the changes to the rest vessels
    """
    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        
        try:
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
    @app.post('/propagate/<action>/<element_id:int>')
    def propagation_received(action, element_id):
        
        global entry_id
        try:
            # Action add, adding new element to our board, updating entry_id
            # to be consistent in our system
            if action == 'add':
                # Updated here and in client_add_received function
                entry_id += 1
                element = request.body.readlines()[0]
                add_new_element_to_store(element_id, element)
            
            elif action == 'modify':
                mod_element = request.body.readlines()[0]
                modify_element_in_store(element_id, mod_element)
            
            elif action == 'delete':
                delete_element_from_store(element_id, None)
            return True

        except Exception as e:
            print e
        return False
            
    # ------------------------------------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------------------------------------
    # a single example (index) should be done for get, and one for postGive it to the students-----------------------------------------------------------------------------------------------------
    # Execute the code
    def main():
        global vessel_list, node_id, app, entry_id
        entry_id = 0

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