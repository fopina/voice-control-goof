voice-control-goof
==========
Simple library to goof around with voice control using Google unofficial speech-to-text and text-to-speech APIs.

Usage
-----

Playing with the echo_test.py

	git clone https://github.com/fopina/voice-control-goof
	cd voice-control-goof
	cp config.py.example config.py
	python echo_test.py

Goof!

	skmac:voice-control-goof fopina$ p echo_test.py 
	please speak into the microphone
	speech to text...
	hello world (confidence: 0.97335243)

	Winner: hello world

	text to speech...
	please speak into the microphone
	speech to text...
	please speak into the microphone
	speech to text...
	how are you (confidence: 0.95447284)
	are you

	Winner: how are you

	text to speech...


Dependencies
-----

- command line MP3 player for TTS (using [sox](http://sox.sourceforge.net/))
- command line wave2flac conversion tool (using [flac](http://xiph.org/flac/))

Links
-------
[google-speech-v2](https://github.com/gillesdemey/google-speech-v2) - Unofficial Google STT API "documentation"
[Chromium Developers](http://www.chromium.org/developers/how-tos/api-keys) - Get your own Google Speech API key
[ZeroKidz](http://zerokidz.com/ideas/?p=11035) - If you don't want to get your own key, maybe you'll find an active one here