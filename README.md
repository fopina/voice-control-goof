voice-control-goof
==========
Simple library to goof around with voice control using Google unofficial speech-to-text and text-to-speech APIs.  
A somewhat configurable module structure add functionality!  

Quickstart (OSX)
-----

- Install [Homebrew](http://brew.sh)

- Install [sox](http://sox.sourceforge.net/), [portaudio](http://www.portaudio.com), [flac](http://xiph.org/flac/) and [pocketsphinx](http://cmusphinx.sourceforge.net)

		brew install sox
		brew install portaudio
		brew install flac
		brew install cmu-pocketsphinx

- If it's the first time you install a brew package that includes a python module, be sure to follow the warning that brew showed when installing cmu-pocketsphinx

		If you need Python to find the installed site-packages:
		mkdir -p ~/Library/Python/2.7/lib/python/site-packages
		echo '/usr/local/lib/python2.7/site-packages' > ~/Library/Python/2.7/lib/python/site-packages/homebrew.pth

- Install pip and PyAudio

		sudo easy_install pip
		sudo pip install --allow-external PyAudio --allow-unverified PyAudio PyAudio

- Clone this

		git clone https://github.com/fopina/voice-control-goof

- Copy config.py.example to config.py and download [Jasper](http://jasperproject.github.io/) language model and dictionary

		cd voice-control-goof
		cp config.py.example config.py
		curl -O https://raw.githubusercontent.com/jasperproject/jasper-client/master/client/languagemodel_persona.lm
		curl -O https://raw.githubusercontent.com/jasperproject/jasper-client/master/client/dictionary_persona.dic

- Goof!

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
- command line tool to downsample WAVE when input rate is above 16k (using [sox](http://sox.sourceforge.net/))  

Links
-------
[CMU Sphinx](http://cmusphinx.sourceforge.net) - Open Source Toolkit For Speech Recognition  
[google-speech-v2](https://github.com/gillesdemey/google-speech-v2) - Unofficial Google STT API "documentation"  
[Chromium Developers](http://www.chromium.org/developers/how-tos/api-keys) - Get your own Google Speech API key  
[Jasper Project](http://jasperproject.github.io/) - Control anything with your voice  
[ZeroKidz](http://zerokidz.com/ideas/?p=11035) - If you don't want to get your own key, maybe you'll find an active one here  