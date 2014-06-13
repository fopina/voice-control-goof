import sys
import pjsua as pj
import time
import threading


try:
    from config import PJSIP_USERNAME, PJSIP_PASSWORD, PJSIP_REGISTAR, PJSIP_PROXY, PJSIP_ID
except:
    raise Exception('config.py not found, please copy config.py.example to config.py')

current_call = None
LOG_LEVEL=1

def log_cb(level, str, len):
    if level <= LOG_LEVEL:
        print level, str,

# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):

    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)

    # Notification when call state has changed
    def on_state(self):
        global current_call
        print "Call with", self.call.info().remote_uri,
        print "is", self.call.info().state_text,
        print "last code =", self.call.info().last_code, 
        print "(" + self.call.info().last_reason + ")"
        
        if self.call.info().state == pj.CallState.DISCONNECTED:
            current_call = None
            print 'Current call is', current_call

    # Notification when call's media state has changed.
    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Connect the call to sound device
            self.call_slot = self.call.info().conf_slot
            #pj.Lib.instance().conf_connect(0, 0)
            pj.Lib.instance().conf_connect(self.call_slot, 0)
            pj.Lib.instance().conf_connect(0, self.call_slot)
            print
            print
            print
            print pj.Lib.instance().get_snd_dev()
            print "Media is now active"
            print
            print
            print
        else:
            print "Media is inactive"

    def on_dtmf_digit(self, digits):
        print
        print
        print
        print 'DIGITS:'
        print digits
        print
        print
        print
        print

# Callback to receive events from account
class MyAccountCallback(pj.AccountCallback):

    def __init__(self, account=None):
        pj.AccountCallback.__init__(self, account)

    # Notification on incoming call
    def on_incoming_call(self, call):
        global current_call 
        if current_call:
            call.answer(486, "Busy")
            return
            
        print "Incoming call from ", call.info().remote_uri

        current_call = call

        call_cb = MyCallCallback(current_call)
        current_call.set_callback(call_cb)

        current_call.answer(200)


# Create library instance
lib = pj.Lib()

try:
    # Init library with default config and some customized
    # logging config.
    lib.init(log_cfg = pj.LogConfig(level=LOG_LEVEL, callback=log_cb))

    # Create UDP transport which listens to any available port
    transport = lib.create_transport(pj.TransportType.UDP, 
                                     pj.TransportConfig(0))
    print "\nListening on", transport.info().host, 
    print "port", transport.info().port, "\n"
    
    # Start the library
    lib.start()

    acc_cfg = pj.AccountConfig()
    acc_cfg.id = 'sip:' + PJSIP_ID
    acc_cfg.reg_uri = 'sip:' + PJSIP_REGISTAR
    acc_cfg.proxy = [ 'sip:' + PJSIP_PROXY ]
    acc_cfg.auth_cred = [ pj.AuthCred("*", PJSIP_USERNAME, PJSIP_PASSWORD) ]

    acc = lib.create_account(acc_cfg, cb=MyAccountCallback())

    my_sip_uri = "sip:" + transport.info().host + \
                 ":" + str(transport.info().port)

    # Menu loop
    while True:
        print "My SIP URI is", my_sip_uri
        print "Menu:  h=hangup call, q=quit"

        input = sys.stdin.readline().rstrip("\r\n")
        if input == "m":
            if current_call:
                print "Already have another call"
                continue
            print "Enter destination URI to call: ", 
            input = sys.stdin.readline().rstrip("\r\n")
            if input == "":
                continue
            lck = lib.auto_lock()
            current_call = make_call(input)
            del lck

        elif input == "h":
            if not current_call:
                print "There is no call"
                continue
            current_call.hangup()

        elif input == "a":
            if not current_call:
                print "There is no call"
                continue
            current_call.answer(200)

        elif input == "p":
            if not current_call:
                print "There is no call"
                continue
            wavplayer = lib.create_player('asd.wav')
            player_slot = lib.player_get_slot(wavplayer)
            lib.conf_connect(player_slot, current_call.info().conf_slot)
            time.sleep(2)
            lib.conf_disconnect(player_slot, current_call.info().conf_slot)
            lib.player_destroy(wavplayer)

        elif input == "r":
            if not current_call:
                print "There is no call"
                continue
            wavplayer = lib.create_recorder('asd2.wav')
            player_slot = lib.recorder_get_slot(wavplayer)
            lib.conf_connect(current_call.info().conf_slot, player_slot)
            time.sleep(2)
            lib.conf_disconnect(current_call.info().conf_slot, player_slot)
            lib.recorder_destroy(wavplayer)

        elif input == "q":
            if current_call : current_call.hangup()
            break

    # Shutdown the library
    transport = None
    acc.delete()
    acc = None
    lib.destroy()
    lib = None

except pj.Error, e:
    print "Exception: " + str(e)
    lib.destroy()
    lib = None