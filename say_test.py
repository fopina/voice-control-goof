# coding=UTF-8

from voicecontrol.ttsstt import Conversation
import sys

try:
	from config import DEFAULT_LOCALE, API_KEY
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')

def main():
	conversation = Conversation(DEFAULT_LOCALE, API_KEY)

	print
	print 'Input: ',
	if len(sys.argv) > 1:
		input = ' '.join(sys.argv[1:])
		print input
	else:
		input = raw_input()
	conversation.say(input)

if __name__ == '__main__':
	main()