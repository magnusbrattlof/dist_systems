from threading import Thread
import requests
import random
import time

payload = {}

def modify(ip, path):
	payload = {
	'delete': '0',
	'entry': 'modified'
	}
	requests.post('http://{}{}'.format(ip, path), data=payload)

if __name__ == '__main__':
	Thread(target=modify, args=("10.1.0.1", '/board/0/')).start()
