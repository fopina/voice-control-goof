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
	if status == SKSTT.STATUS_WAITING:
		print "please speak into the microphone"
	elif status == SKSTT.STATUS_LISTENING:
		print "Listening..."
	elif status == SKSTT.STATUS_PROCESSING:
		print "speech to text..."

def main():
	stt = SKSTT(DEFAULT_LOCALE, API_KEY, callback = update_status)
	tts = SKTTS(DEFAULT_LOCALE)
	print 'Please, allow 10 seconds of silence to calibrate....'
	silence = stt.calculate_silence()
	stt.THRESHOLD = silence
	print "Silence threshold set to:", silence
	try:
		while 1:
			guesses = stt.listen_and_return()
			reply = None
			if guesses:
				print_guesses(guesses)
				print
				choice = choose_guess(guesses)
				print 'Winner:',choice
				reply = choice
			else:
				if DEFAULT_LOCALE[:2] == 'pt':
					reply = 'Não percebi, repete por favor.'
				else:
					reply = 'I did not understand, please repeat.'
			print
			print 'text to speech...'
			tts.read_out_loud(reply)
	except KeyboardInterrupt:
		print
		print 'Bye Bye'

if __name__ == '__main__':
	main()