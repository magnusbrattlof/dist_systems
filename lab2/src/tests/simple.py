from threading import Thread
import requests
import random

payload = {}

def post(ip, path, d):
	payload['entry'] = d
	requests.post('http://{}{}'.format(ip, path), data=payload)

if __name__ == '__main__':
	Thread(target=post, args=("10.1.0.1", '/board', 'm1',)).start()
	Thread(target=post, args=("10.1.0.2", '/board', 'm2',)).start()