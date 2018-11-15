import requests
from sys import argv

"""How to use:

$ python tests/single_client.py [action] [item]

where actions are either post, modify or delete
and item is an integer between 0 and N where N is 
the total element on your board"""

payload = {}

def main():

	if argv[1] == 'post':
		post("10.1.0.1", "/board", argv[2])

	elif argv[1] == 'modify':
		modify(argv[2], argv[3])

	elif argv[1] == 'delete':
		delete(argv[2])

def post(ip, path, items):

	for i in range(int(items)):
		payload['entry'] = "Message #{}".format(i)
		requests.post('http://{}{}'.format(ip, path), data=payload)

def delete(items):

	payload['delete'] = 1
	for i in items:
		requests.post('http://10.1.0.1/board/{}/'.format(i), data=payload)

def modify(items, element):

	payload['delete'] = 0
	payload['entry'] = element
	for i in items:
		requests.post('http://10.1.0.1/board/{}/'.format(i), data=payload)


if __name__ == '__main__':
	main()