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
import random
import socket
import time
import json
import sys

try:
    # Initialize app object and create our board dictionary
    app = Bottle()
    board = {}

    """Board functions:
    Handles how the vessels are adding new elements, 
    how to modify elements and how to delete specified elements. 
    """
    def add_new_element_to_store(entry_sequence, element, is_propagated_call=False):
        
        global board, node_id
        success = False
        try:
            # Add new element with sequence number and element to board
            board[str(entry_sequence)] = element
            success = True
        except Exception as e:
            print e
        return success

    def modify_element_in_store(entry_sequence, modified_element, is_propagated_call = False):
        
        global board, node_id
        success = False
        try:
            # Update the board dictionary with the modified_element
            board[str(entry_sequence)] = modified_element
            success = True
        except Exception as e:
            print e
        return success

    def delete_element_from_store(entry_sequence, is_propagated_call = False):
        
        global board, node_id
        success = False
        try:
            # Pop entry from the board dictionary
            board.pop(str(entry_sequence), None)
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
                res = requests.post('http://{}{}'.format(vessel_ip, path), data=payload)
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
                print vessel_id
                t = Thread(target=contact_vessel, args=(vessel_ip, path, payload, req,))
                t.deamon = True
                t.start()
    
    """Prepare messages before sending to leader.
    Address will be leader ip which was determined in select_leader function.  
    """
    def propagate_to_leader(path, payload = None):
        global leader_ip

        address = "10.1.0.{}".format(leader_ip)
        try:
            contact_vessel(address, path, payload)
            return True

        except Exception as e:
            print e
        return False

    """This functions is only executed iff a node is receiving a message which it initated
    or it receives a message from another node which initiated its leader election round.
    The function receives a parameter 'data' which contains a dictionary with all nodes
    and their corresponding id.
    """
    def select_leader(data):
        global leader_is_elected, consensus, is_leader, leader_ip, leader_id

        leader_ip, leader_id = sorting(data)
        
        leader_is_elected = True
        consensus = True
        
        if leader_id == host_id:
            is_leader = True
        else:
            is_leader = False

        print "Leader is: {} with id: {}".format(leader_ip, leader_id)

    """"Sending payload to neighbor which contains all the nodes ids and your own id.
    """
    def send_id(neighbor_host_addr, host_id, payload):
        global node_id, leader_is_elected, consensus
        try:

            requests.post('http://10.1.0.{}/election/{}'.format(neighbor_host_addr, consensus), json=payload)

        except Exception as e:
            print e

    """Simple sorting algorithm which iterates through the received dictionary
    and returns the largest id and fetches the corresponding host-address (ip-address).
    """
    def sorting(data):
        largest = 0
        ip = 0
        for k, v in data.iteritems():
            if v > largest:
                largest = v
                ip = k
        return (ip, largest)

    """Function is executed by every node in the network. This function handles
    the creation of random id which is used for leader election. It also compute the neighbor
    address.
    """
    def init_election(host_addr, nodes):
        global host_id, neighbor_host_addr, node_id, consensus
        
        neighbor_host_addr = (host_addr % len(nodes)) + 1
        host_id = random.randrange(1, 1025)

        payload['initiator'] = node_id
        payload[node_id] = host_id
        
        print "My id: {}".format(host_id)
        
        time.sleep(2)
        send_id(neighbor_host_addr, host_id, payload)
        

    """Routing functions:
    Handles the index page plus the board page. 
    @app.post('/board') handles how new elements are added and calls
    correct functions for propagation to the other vessels in the system.
    """
    @app.route('/')
    def index():

        global board, node_id, leader_id, leader_ip
        print "Board: ", board
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()), members_name_string='Magnus Brattlof | brattlof@student.chalmers.se', leader_node=leader_ip, leader_id=leader_id)

    @app.get('/board')
    def get_board():

        global board, node_id, leader_id, leader_ip
        print board
        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems(), leader_node=leader_ip, leader_id=leader_id))
    # ------------------------------------------------------------------------------------------------------
    @app.post('/board')
    def client_add_received():
        '''Adds a new element to the board
        Called directly when a user is doing a POST request on /board'''
        global board, node_id, entry_id
        try:
            # Fetch new entry from the input form
            new_element = request.forms.get('entry')
            
            if is_leader != True:
                # Contact leader and send received data from client
                propagate_to_leader('/propagate/leader/add/{}'.format(None), payload=new_element)
            
            # This code is only executed by the leader
            else:
                add_new_element_to_store(entry_id, new_element)
                propagate_to_vessels("/propagate/others/add/{}".format(entry_id), payload=new_element)
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
            # Retreive appropiate data from HTML-form
            mod_element = request.forms.get('entry')
            delete = int(request.forms.get('delete'))

            # Check if you are leader or not then check if the action is delete or modify
            if is_leader != True:
                if delete == True:
                    propagate_to_leader("/propagate/leader/delete/{}".format(element_id), payload=None)
                
                else:
                    propagate_to_leader("/propagate/leader/modify/{}".format(element_id), payload=mod_element)
                
                return True
           
            # If you are the leader, first modify or delate to yourn own board
            # then propagate the changes to the other nodes in the network
            else:
                # This is only executed by the leader in the system
                if delete == True:
                    delete_element_from_store(element_id, None)
                    propagate_to_vessels("/propagate/others/delete/{}".format(element_id), payload=None)

                else:
                    modify_element_in_store(element_id, mod_element)
                    propagate_to_vessels("/propagate/others/modify/{}".format(element_id), payload=mod_element)

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
    @app.post('/propagate/<to>/<action>/<element_id>')
    def propagation_received(to, action, element_id):
        
        global entry_id
        try:
            # If the message are to the leader, then the following code is executed
            if to == 'leader':
                if action == 'add':
                    element = request.body.readlines()[0]
                    add_new_element_to_store(entry_id, element)
                    propagate_to_vessels("/propagate/others/add/{}".format(entry_id), payload=element)

                    entry_id += 1

                elif action == 'modify':
                    mod_element = request.body.readlines()[0]
                    modify_element_in_store(element_id, mod_element)
                    propagate_to_vessels("/propagate/others/modify/{}".format(element_id), payload=mod_element)

                elif action == 'delete':
                    delete_element_from_store(element_id, None)
                    propagate_to_vessels("/propagate/others/delete/{}".format(element_id), payload=None)

            # Else if the message is the the others, following code are executed
            elif to == 'others':
                # Action add, adding new element to our board, updating entry_id
                # to be consistent in our system
                if action == 'add':
                    # Updated here and in client_add_received function
                    element = request.body.readlines()[0]
                    add_new_element_to_store(element_id, element)
                
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
    
    """This is where the main logic of the leader election algorithm is implemented.
    The function receives a message with either True or False which indicates if it is 
    a concensus round or just a round where all nodes appends their id to the dictionary.
    """
    @app.post('/election/<message>')
    def receive_id(message):
        global host_id, leader_ip, leader_id, node_id, neighbor_host_addr, leader_is_elected, initiator
        try:
            # Fetch the data from the http-message
            data = json.load(request.body)

            # Determine if you are the initiator of the message
            if data['initiator'] == node_id:
                initiator = True
            else:
                initiator = False

            # Append your id to the dictionary and send to your neighbor
            if str(node_id) not in data:
                if host_id in data.values():
                    data[node_id] = host_id + node_id
                else:
                    data[node_id] = host_id

                Thread(target=send_id, args=(neighbor_host_addr, host_id, data)).start()

            # If you are the initiator and the message has traversed the ring
            # Select the leader with the highest id and then initiate the
            # consensus round. 
            elif str(node_id) in data and message == 'False' and initiator:
                print "First round done, init consensus round"
                select_leader(data)
                Thread(target=send_id, args=(neighbor_host_addr, host_id, data)).start()

            # If your consensus round has traversed the network ring
            # now there will be no more messages, terminate your election.
            elif str(node_id) in data and message == 'True' and initiator:
                # Terminate your election rounds
                print "My leader election is over"

            # If you are not the initiator, however another node is issuing a
            # leader election round you have to select a leader from this payload as well.
            elif str(node_id) in data and message == 'True' and not initiator:
                select_leader(data)
                Thread(target=send_id, args=(neighbor_host_addr, host_id, data)).start()

            else:
                print "Nothing matched. Error"

        except Exception as e:
            print e

    """Main execution starts from here:
    Initialization of variables and how to parse the cmd args.
    Booting up all webservers on the vessels.
    """
    def main():
        global vessel_list, node_id, app, entry_id, leader_ip, leader_id, leader_is_elected, payload, host_id, neighbor_host_addr, consensus, is_leader, initiator

        # Variables initialization
        neighbor_host_addr = None
        consensus = False
        is_leader = False
        initiator = False
        leader_ip = None
        leader_id = None
        host_id = None
        entry_id = 0
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
            # Start the web server application in another thread 
            # then we wait for two seconds and then executes the leader election
            Thread(target=run, kwargs=dict(app=app, host=vessel_list[str(node_id)], port=port)).start()
            time.sleep(2)
            init_election(int(node_id), vessel_list)

        except Exception as e:
            print e
    # ------------------------------------------------------------------------------------------------------
    if __name__ == '__main__':
        main()
except Exception as e:
        traceback.print_exc()
        while True:
            time.sleep(60.)