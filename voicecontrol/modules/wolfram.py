# coding=UTF-8

try:
	import wolframalpha
	from config import WOLFRAM_API_KEY
	wolfclient = wolframalpha.Client(WOLFRAM_API_KEY)
except:
	print 'Failed to load wolfram module, remove it from config.py if you don''t want to use it'
	wolfclient = None

def valid_input(conversation, input):
	# handle any input in english
	# module should be the last one in the brain modules list

	if not wolfclient:
		return False

	if conversation.lang_code == 'en-US':
		return True

	return False

def process_input(conversation, input):
	# really needs some work!
	processed = False

	res = wolfclient.query(' '.join(input))

	if len(res.pods) < 2:
		return (False, None)

	return (True, res.pods[1].text)
