from skspeech import SKSTT
try:
	from config import API_KEY, DEFAULT_LOCALE
except:
	raise Exception('config.py not found, please copy config.py.example to config.py')

if __name__ == '__main__':
	stt = SKSTT(DEFAULT_LOCALE, API_KEY)
	try:
		while 1:
			print("please speak into the microphone")
			print stt.listen_and_return()
	except KeyboardInterrupt:
		print
		print 'Bye Bye'