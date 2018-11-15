from threading import Thread
import requests
import random

payload = {}

def main():
	for i in range(5):
		payload['entry'] = "A message from thread {}".format(i)
		Thread(target=post, args=("10.1.0.{}".format(random.randrange(1,8)), '/board', payload,)).start()

def post(ip, path, payload):
	requests.post('http://{}{}'.format(ip, path), data=payload)

if __name__ == '__main__':
	main()