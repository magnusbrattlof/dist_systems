
class Server:
    def __init__(self, host, port, ip, vessels):
        self.vessels = vessels
        self.host = host
        self.port = port
        self.ip = ip
        self.sock = socket.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.sock.bind(self.host, self.port)
        self.neighbor_ip = self.ip % (len(self.vessels) + 1)
        self.token_id = random.randrange(1, 1025)
        self.is_leader = False
        self.leader = None
        self.client_sender = self.sock.connect(self.neighbor_ip, self.port)

    def run(self):
        self.sock.listen(1)
        while True:
            self.client_receiver, self.address_receiver = self.sock.accept()
            Thread(target=self.token_receive).start()
            Thread(target=self.token_send).start()

    def token_send(self):
        self.client_sender.send(self.token_id.encode())

    def token_receive(self):
        size = 1024
        try:
            data = self.client_receiver.recv(size)
            if data:
                neighbor_id = data
            else:
                raise error("Something went wrong")
        
        except Error as e:
            print e
            self.client_receiver.close()
            return False


""" 
            d = {}
            if data['entry_id'] in board:
                if data['node_id'] > board[data['entry_id']].keys()[0]:
                    d = {board[data['entry_id']].keys()[0]: board[data['entry_id']].values()[0]}
                    board.update({entry_id: d})

                    d = {data['node_id']: data['element']}
                    board.update({data['entry_id']: d})
                    print "Added {} from {}".format(data['element'], data['node_id'])

                else:
                    d = {data['node_id']: data['element']}
                    board.update({data['entry_id']+1: d})
                    print "Added {} from {}".format(data['element'], data['node_id'])
           
            else:
                d = {data['node_id']: data['element']}
                board.update({entry_id: d})
                print "Added {} from {}".format(data['element'], data['node_id'])
            #print board
            entry_id += 1

"""

""" 
                if neigh_lclock > lclock:
                    lclock = neigh_lclock
                    add_new_element_to_store(lclock, entry)
                
                elif neigh_lclock == lclock:
                    if node_id > body['node_id']: 
                        tmp = board[lclock]

                        print("Temp entry: " + tmp)
                        modify_element_in_store(lclock, entry)
                        lclock += 1
                        add_new_element_to_store(lclock, tmp)
                    else: 
                        lclock += 1
                        add_new_element_to_store(lclock, entry)
                else: 
                    lclock += 1
                    add_new_element_to_store(lclock, entry)




            if lclock in temp_board:
                d.update({neigh_id: element})
                temp_board = dict(temp_board, **{lclock: d})

            else:
                d = {}
                d.update({neigh_id: element})
                temp_board = dict(temp_board, **{lclock: d})


                            if lclock in temp_board:
                d.update({neigh_id: element})
                temp_board = dict(temp_board, **{lclock: d})

            else:
                d = {}
                d.update({neigh_id: element})
                temp_board = dict(temp_board, **{lclock: d})
                    
"""
