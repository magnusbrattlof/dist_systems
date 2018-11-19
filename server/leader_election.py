
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