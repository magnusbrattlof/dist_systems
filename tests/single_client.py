import requests
from sys import argv

payload = {}

def main():
	if argv[1] == 'post':
		post("10.1.0.1", "/board", argv[2])
	elif argv[1] == 'delete':
		delete(argv[2])


def post(ip, path, items):
	for i in range(int(items)):
		payload['entry'] = "Message #{}".format(i)
		requests.post('http://{}{}'.format(ip, path), data=payload)

def delete(items):
	payload['delete'] = 1
	for i in range(int(items)):
		requests.post('http://10.1.0.1/board/{}/'.format(i), data=payload)


def modify():
	pass


if __name__ == '__main__':
	main()