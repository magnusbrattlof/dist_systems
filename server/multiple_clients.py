import requests
from threading import Thread
import random

payload = {}

def main():
	for i in range(10):
		payload['entry'] = "{}".format(i)
		Thread(target=post, args=("10.1.0.{}".format(random.randrange(1,8)), '/board', payload,)).start()

def post(ip, path, payload):
	requests.post('http://{}{}'.format(ip, path), data=payload)

if __name__ == '__main__':
	main()