# coding=UTF-8

from skspeech import SKSTT, SKTTS
from skspeech import STATUS_WAITING, STATUS_LISTENING, STATUS_PROCESSING
try:
	from config import API_KEY, DEFAULT_LOCALE
	from config import SPHINX_LM, SPHINX_DIC, SPHINX_HMM, SPHINX_TRIGGER
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')


def update_status(status):
	if status == STATUS_WAITING:
		print "please speak into the microphone"
	elif status == STATUS_LISTENING:
		print "Listening..."
	elif status == STATUS_PROCESSING:
		print "speech to text..."

def main():
	stt = SKSTT(DEFAULT_LOCALE, API_KEY, SPHINX_HMM, SPHINX_LM, SPHINX_DIC, update_status)
	tts = SKTTS(DEFAULT_LOCALE)

	print
	print 'Please, allow 2 seconds of silence to calibrate....'
	silence = stt.calculate_silence(2)
	stt.THRESHOLD = silence
	print "Silence threshold set to:", silence
	print

	try:
		while 1:
			reply = stt.listen()
			print 'You said:',reply
			if reply.find(SPHINX_TRIGGER) < 0:
				continue
			
			if DEFAULT_LOCALE[:2] == 'pt':
				reply = 'Sim?'
			else:
				reply = 'Yes?'

			tts.read_out_loud(reply)

			reply = stt.listen(use_google = True)
			
			if not reply:
				if DEFAULT_LOCALE[:2] == 'pt':
					reply = 'Não percebi, repete por favor.'
				else:
					reply = 'I did not understand, please repeat.'

			print
			print 'text to speech...'
			print 'Reply:', reply
			tts.read_out_loud(reply)

	except KeyboardInterrupt:
		stt.cleanup()
		print
		print 'Bye Bye'

if __name__ == '__main__':
	main()