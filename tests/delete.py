from threading import Thread
import requests
import random
import time

payload = {}

def delete(ip, path):
	payload['delete'] = '1'
	requests.post('http://{}{}'.format(ip, path), data=payload)

if __name__ == '__main__':
	Thread(target=delete, args=("10.1.0.1", '/board/0/')).start()
	#Thread(target=delete, args=("10.1.0.2", '/board/0/')).start()
