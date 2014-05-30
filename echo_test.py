# coding=UTF-8

from skspeech import SKSTT, SKTTS
try:
	from config import API_KEY, DEFAULT_LOCALE
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')


def print_guesses(guesses):
	for guess in guesses:
		print guess['transcript'],
		if 'confidence' in guess:
			print '(confidence: %s)' % guess['confidence'],
		print

def choose_guess(guesses):
	winner = None
	maxconf = -1
	for guess in guesses:
		conf = float(guess.get('confidence',0))
		if conf > maxconf:
			winner = guess['transcript']
			maxconf = conf
	return winner.encode('utf-8')

def update_status(status):
	if status == SKSTT.STATUS_LISTENING:
		print "please speak into the microphone"
	elif status == SKSTT.STATUS_UPLOADING:
		print "speech to text..."

def main():
	stt = SKSTT(DEFAULT_LOCALE, API_KEY)
	tts = SKTTS(DEFAULT_LOCALE)
	try:
		while 1:
			guesses = stt.listen_and_return(callback = update_status)
			if guesses:
				print_guesses(guesses)
				print
				choice = choose_guess(guesses)
				print 'Winner:',choice
				print
				print 'text to speech...'
				tts.read_out_loud(choice)
			else:
				if DEFAULT_LOCALE[:2] == 'pt':
					tts.read_out_loud('Não percebi, repete por favor.')
				else:
					tts.read_out_loud('I did not understand, please repeat.')
	except KeyboardInterrupt:
		print
		print 'Bye Bye'

if __name__ == '__main__':
	main()