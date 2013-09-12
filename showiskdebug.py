#! /usr/bin/python

'''
Showisk (asterisk enabled interactive show) enables someone to use asterisk (open-source PBX) 
to place multiple calls to people (aka actors) and playback synchronized audio files, while 
allowing for choices to be made by the actors. One can create complicated audio plans with arbitrary
many sync points, and decision trees of arbitrary depth.
It relies on pyst and specififally the Python interface to the Asterisk Manager Interface (AMI)

Author: Thanassis Boulis, (aka Athanassios Boulis), August 2013
'''
import asterisk.manager
import sys
from datetime import datetime
from time import sleep, time
from random import shuffle
import threading


class Show:
	'''
	The class that does all the work by starting up the various threads and connection to the AMI.
	When creating a new object from this class, it initialises several variables and connects to
	the AMI. Then, by calling begin(), you start the show.
	'''
	def __init__(self, names, audioPlan, audiencePhone=None, server='127.0.0.1', username='admin', pswd=''):
		'''
		The constructor for this class needs the names of the actors in a list of strings, the special
		phone numbers (that give the signal to start the show) again as a list of strings, and the
		audio plan which should be list of dictionaries.
		'''
		self.names = names
		self.audiencePhone = audiencePhone
		self.audioPlan = audioPlan
		self.triggerPhones = []
		self.collectedPhones = []

		# configuration variables for common sounds. The audio dir is added ONLY to the filenames
		# in the audio plan, NOT the common sounds variables below.
		self.audiodir = ''					# a full path to be added to the files in the audio plan
		self.press1 = 'press-1'				# the press 1 sound
		self.beep = 'beep'					# the beep sound, after a button pressed
		self.tryAgain = 'please-try-again'	# the please try again sound
		self.whenReconnected = None			# audio to play when reconnecting after hangup
		self.nothuman = None				# an optional sound
		self.thankyou = 'auth-thankyou'		# saying thank you after establishing a call
		self.register ='/audio/Register1'
		self.register2 = '/audio/Register2'		# asked when calling in
		self.registerconf = '/audio/RegisterConf'
		self.registerfail = '/audio/RegisterFail'
		self.triggerPreshow = 'welcome'		# to be played at the trigger phone just before begin()
		self.triggerDuringShow = 'auth-thankyou'	# to be played at the trigger phone during begin()

		self.pathToTrunk = 'SIP/didlogic-trunk/'	# where do we place outgoing calls
		self.defaultOption = 1			# the option returned when no option is given by the user
										# you can have any key (e.g., 0,1,2,'default') just make
										# sure this key is always included in the audio plan
										# whenever the user has options to take


		# Dictionaries to hold important info on calls.
		self.channel = {}	# Referenced with actor name as key
		self.uniqueID = {}	# Referenced with actor name as key
		self.phoneNum = {}	# Referenced with actor name as key
		self.actor = {}		# Referenced with uniqueID as key
		self.actorFromChan = {} # Referenced with channel as key

		# events to signify when calls are answered, DTMF tones received, and ending of audiofile
		# playback. These are dictionaries because there are multiple events, one for each actor.
		self.eventsCallAnswer = {}
		self.eventsDTMF = {}
		self.eventsPlayEnd = {}
		# event to signify trigger phone to stop the collectPhones function
		self.eventTrigger = threading.Event()

		# a dictionary to hold the last DTMF pressed, one entry for each actor
		self.pressedDTMF = {}

		self.shuttingDown = False	# flag to inform handle_Hangup() not to try to reconnect

		# the AMI manager to interact with Asterisk
		self.manager = asterisk.manager.Manager()

		# connect to the manager
		try:
			self.manager.connect(server)
			self.manager.login(username, pswd)

			# register some callbacks
			self.manager.register_event('Shutdown', self.handle_shutdown) # shutdown
			self.manager.register_event('NewCallerid', self.handle_NewCallerID)		# the NewCallerid events help us find out the channel and unique id of our call
			self.manager.register_event('AGIExec', self.handle_AGIExec)				# to know the end of playback
			self.manager.register_event('DTMF', self.handle_DTMF)					# detected pressed keys
			self.manager.register_event('Hangup', self.handle_Hangup)				# react to hang ups
			#self.manager.register_event('*', self.handle_event)			# catch all, for debug purposes

		except asterisk.manager.ManagerSocketException, (errno, reason):
			print "Error connecting to the manager: %s" % reason
			self.manager.close()
			sys.exit(1)
		except asterisk.manager.ManagerAuthException, reason:
			print "Error logging in to the manager: %s" % reason
			self.manager.close()
			sys.exit(1)
		except asterisk.manager.ManagerException, reason:
			print "Error: %s" % reason
			self.manager.close()
			sys.exit(1)

	def collectPhones(self,triggerPhones=None, delay=None):
		'''
		A function to invoke preshow, in order to collect valid phone numbers. Stopped by a special
		phone(s) calling in and triggering the stop, or a timeout. Most of the work is done in the
		_testPhone() function invoked as multiple threads in handle_Newstate()
		'''
		# register an event to process phones calling in
		self.manager.register_event('Newstate', self.handle_Newstate)

		if triggerPhones is None and delay is None:
			delay = 300			# wait for 5 mins and then exit
		else:
			self.triggerPhones = triggerPhones

		print datetime.now(), 'Waiting for incoming calls to be registered, max delay:', delay, 'secs. List of trigger phones', self.triggerPhones
		self.eventTrigger.wait(delay)

		# check the reason for stopping to wait
		if self.eventTrigger.is_set():
			reason = 'trigger call'
		else:
			reason = 'timeout'
		print datetime.now(), '***** Collecting phones finished. Reason:', reason, '. List of collected phones', self.collectedPhones

		# no need to have this event registered anymore
		self.manager.unregister_event('Newstate', self.handle_Newstate)

	def begin(self, phones=None, randomShuffle=True):
		'''
		The main function to start the show. It first tries to originate the calls and then begins
		to execute the plan period by period.
		'''
		# the Newexten event help us know when an phone is answered. Used AFTER collectPhones()
		self.manager.register_event('Newexten', self.handle_NewExten)

		# if no explicit phone list is given, then use the list that collectPhoneNums() hopefully collected
		if phones is None: phones = self.collectedPhones
		# shuffle the order if needed
		if randomShuffle: shuffle(phones)

		print datetime.now(), 'Phones will be linked to actors in this way:', zip(phones, self.names)

		# First try to originate enough calls, and establish the connection is with a person
		actorThreads = []
		for phone, actorName in zip(phones, self.names):
			# the arguments
			t = threading.Thread(target=self._establishCall, args=(phone, actorName))
			t.start()
			actorThreads.append(t)

		# if an audience phone defined then establish a call for the special actor 'Audience'
		# no need to press 1 to establish the call, so the third argument is False
		if self.audiencePhone:
			t = threading.Thread(target=self._establishCall, args=(self.audiencePhone, 'Audience', False, 60))
			t.start()
			actorThreads.append(t)

		# wait for all threads to finish before proceeding
		for t in actorThreads:
			t.join()

		# TO DO: check if we have enough succesfull calls, and if not try to establish more
		#give some time for all the messages to arrive
		sleep(1)

		# Then execute the plan period by period, synchronising the calls before every new period start
		for period in self.audioPlan:
			# reset actor Thread to empty
			actorThreads = []
			for actorName in period:
				if actorName in self.channel:
					# create a thread to handle this period for this actor. _execute_plan() does all
					# the work and takes two arguments: the plan for this actor and the actorName
					t = threading.Thread(target=self._execute_plan, args=(period[actorName], actorName))
					t.start()
					actorThreads.append(t)
				else:
					print datetime.now(), "WARNING", actorName, "is in the plan but does not have an established call"

			# wait for all threads to finish before proceeding to the next period
			for t in actorThreads:
				t.join()

		# remember to clean up
		self.shuttingDown = True
		for actorName in self.channel:
			self.manager.hangup(self.channel[actorName])
		self.manager.close()


	def _establishCall(self, phone, actorName, press1needed=False, delay=30, reconnected=True):
		'''
		Multiple threads of this function are started in begin(). Originates a call and then waits
		for 1 to be pressed. If not pressed within <delay> secs, it hangs up the call.
		'''
		# originate calls asynchronously so that  multiple calls can be initiated in parallel.
		# Otherwise a call has to be answered for another one to start ringing, even if
		# the originate commands are given from different threads
		response = self.manager.originate(self.pathToTrunk + phone, caller_id=actorName, async=True, exten='callwait', context='testcall', priority='1')
		print datetime.now(), 'Originating call to', actorName, phone, 'Response:', response


		# wait for the call to be answered
		self.eventsCallAnswer[actorName] = threading.Event()
		self.eventsCallAnswer[actorName].wait(delay)
		if self.eventsCallAnswer[actorName].is_set():
			# if we do not need to press 1 print a success message and return.
			if not press1needed:
				print datetime.now(), 'Success establishing call to', actorName
				self.phoneNum[actorName] = phone  # associate phone number with actor
				self.playback(self.thankyou, actorName, dir='')
				return True
			sleep(1) # needs a small delay before the channel becomes valid for playback
			# if the call is answered, ask for the actor to press 1 (to confirm real interaction)
			self.playback(self.press1, actorName, dir='')
			if self.waitToPress1(actorName, delay=delay):
				print datetime.now(), 'Success establishing call to', actorName
				self.phoneNum[actorName] = phone  # associate phone number with actor
				self.playback(self.thankyou, actorName, dir='')
				if reconnected: self.playback(self.whenReconnected, actorName, dir='')
			else:
				if self.nothuman:
					self.playback(self.nothuman, actorName, dir='')
				self.manager.hangup(self.channel[actorName])
				print datetime.now(), 'Call answered but', actorName, 'did not press 1 within', delay, 'secs'
				print datetime.now(), '======================WARNING! PERFORMANCE MUST BE RESTARTED, Please press CTRL Z and run python debuggrantShow.py==========================='
				# remove this actor, channel, and unique ID from the corresponding dictionaries
				chan = self.channel[actorName]
				uniqID = self.uniqueID[actorName]
				del self.channel[actorName]
				del self.uniqueID[actorName]
				del self.actor[uniqID]
				del self.actorFromChan[chan]
		else:
			print datetime.now(), 'Call to', actorName, 'was NOT answered'


	def _execute_plan(self, plan, actorName):
		'''
		Multiple threads of this function are started in begin(): for each period we start the threads
		corresponding to the actors named in this period. The function parses the dict representing
		the plan. When parts of the plan are subplans (nested dictionaries) this function is
		called recursively. All the _execute_plan() threads started at begin, are joined (i.e. wait
		for all to finish) at the end of each period, and the cycle begins again for the next period.
		'''
		if type(plan) is not dict:
			print datetime.now(), '*** ERROR *** the following plan is not a dictionary', plan
			return

		# get the first key of the plan dictionary and check what kind of variable it is
		key = plan.__iter__().next()
		if type(key) is str:
			# key is an audio file and we have to play it. The method returns only when Playback is finished
			self.playback(key, actorName)

			# after playback is finished, go to the value of that key to decide on the next action
			nextAction = plan[key]
			if nextAction is None:
				return
			elif type(nextAction) is dict:
				self._execute_plan(nextAction, actorName)
			elif type(nextAction) is int:
				print datetime.now(), '*** ERROR *** Int is not a valid value for this key:value combo', key,':',nextAction
			elif type(nextAction) is str:
				print datetime.now(), '*** ERROR *** Str is not a valid value for this key:value combo', key,':',nextAction

		elif type(key) is int:
			# We have an option in our hands, we should wait for a DTMF. The following method waits
			# for a valid DTMF. If no valid, asks to try again. It keeps trying for 30 secs (default
			# but you can change it) and then returns the valid digit pressed or 1.
			digit = self.waitForDTMF(actorName, plan, 30)
			nextAction = plan[digit]

			if nextAction is None:
				return
			elif type(nextAction) is dict:
				self._execute_plan(nextAction, actorName)
			elif type(nextAction) is str:
				# nextAction is an audio file and we have to play it. Waits for the playback to finish
				self.playback(nextAction, actorName)
			elif type(nextAction) is int:
				print datetime.now(), '*** ERROR *** Int is not a valid value for this key:value combo', key,':',nextAction

		else:
			print datetime.now(), '*** ERROR *** No such key is allowed:', key


	def playback(self, filename, actorName, dir=None, waitToEnd=True):
		'''
		Plays back an audio file to the channel associated with <actorName>.
		Sends the proper AGI command, and then *waits* till it is notified that the playback has ended
		You can also call it so it does not wait, or with a different audio dir
		'''
		if dir is None: dir = self.audiodir
		cdict = {'Action':'AGI'}
		cdict['Channel'] = self.channel[actorName]
		cdict['Command'] = 'EXEC Playback ' + dir + filename
		cdict['CommandID'] = 'MyCommandID'
		response = self.manager.send_action(cdict)
		print datetime.now(), "Playing audio file", filename, "to", actorName, ". Start response:", response

		if response.headers['Response'] == 'Success' and waitToEnd:
			# Wait for the playback to finish. Create a new event to wait upon. The new event is
			# initially clear and we are waiting for the handle_AGIExec() method to set it.
			self.eventsPlayEnd[actorName] = threading.Event()
			self.eventsPlayEnd[actorName].wait()
			print datetime.now(), "Playing audio file", filename, "to", actorName, ". Finished"


	def waitForDTMF(self, actorName, plan, delay=8, defaultReturn=None):
		'''
 		Waits for a valid key pressed (DTMF tone) up to <delay> secs.
 		Valid options are taken from the keys of the given <plan>. If not valid option is given
 		within <delay> secs, the default options <defaultReturn> is returned
 		'''
 		if defaultReturn is None: defaultReturn = self.defaultOption
		start = end = time()
		while end - start < delay:
			self.eventsDTMF[actorName] = threading.Event()
			waitDuration = delay - (end-start)
			#print datetime.now(), "waiting for DTMF", actorName, plan, waitDuration
 			# block here waiting

 			self.eventsDTMF[actorName].wait(waitDuration)
			# when done, check whether the event was set, or expired
			if self.eventsDTMF[actorName].is_set():
				# check whether the pressed key is a valid option in our plan
				if self.pressedDTMF[actorName] in plan:
					return self.pressedDTMF[actorName]
				else:
					# a key was pressed but is not valid, ask again
					self.playback(self.tryAgain, actorName, dir='')
			else:
				# the wait period just expired, no valid key was pressed
				return defaultReturn
			# update
			end = time()
		return defaultReturn

	def waitToPress1(self, actorName, delay=30):
		return self.waitForDTMF(actorName, {1:None}, delay, defaultReturn=0)

	def _testPhone(self, phone, channel, uniqueID):
		'''
		Called in a thread by handle_Newstate(), this function tests whether an incoming call
		is answered by a human. If so, it stores the number in self.collectedPhones
		'''
		print datetime.now(), 'Received call from number:', phone, '. Testing suitability'
		sleep(0.5)
		# first update the dictionaries, using the phone as the actorName. This way we can use the
		# same waitForDTMF() and playback() as with the outgoing calls.
		self.channel[phone] = channel
		self.actor[uniqueID] = phone
		self.actorFromChan[channel] = phone

		if phone in self.triggerPhones:
			print datetime.now(), 'This is a TRIGGER phone. About to start show.'
			sleep(0.5)
			self.playback(self.triggerPreshow, phone, dir='')
			# notify the collectPhones() function/thread to exit
			self.eventTrigger.set()
			sleep(0.5)
			self.playback(self.triggerDuringShow, phone, dir='')
			return

		sleep(0.5)
		self.playback(self.register, phone, dir='')
		if not self.waitToPress1(phone): return
		self.playback(self.register2, phone, dir='')
		if not self.waitToPress1(phone): return


		# we have established that this phone number is suitable, add it to the list if not there
		if phone not in self.collectedPhones:
			print datetime.now(), 'Great, phone number:', phone, 'is suitable.'
			self.collectedPhones.append(phone)
			self.playback(self.registerconf, phone, dir='', waitToEnd=False) #Play the file AFTER the number is registered
		else:
			print datetime.now(), 'WARNING phone number:', phone, 'already in the list.'
			self.playback(self.registerfail, phone, dir='', waitToEnd=False) #Error File

		print datetime.now(), '*** Total collected phones so far: -===-', len(self.collectedPhones), '-===-  List:', self.collectedPhones

	# The rest are functions that we register with the pyst manager to handle AMI events

	def handle_NewCallerID(self, event, manager):
		actorName = event.headers['CallerIDName']
		self.channel[actorName] = event.headers['Channel']
		self.uniqueID[actorName] = event.headers['Uniqueid']
		self.actor[event.headers['Uniqueid']] = actorName
		self.actorFromChan[event.headers['Channel']] = actorName
		print  datetime.now(), "Registering", actorName, "with channel", self.channel[actorName], "and call uniqueID", self.uniqueID[actorName]

	def handle_NewExten(self, event, manager):
		if event.headers['Application'] == 'Answer':
			actorName = self.actor[event.headers['Uniqueid']]
			print datetime.now(), "Call Answered by", actorName
			if actorName in self.eventsCallAnswer and not self.eventsCallAnswer[actorName].is_set():
				self.eventsCallAnswer[actorName].set()
			else:
				print datetime.now(), "WARNING", actorName, "answered a call, which is not originated, or waiting to be answered"

	def handle_DTMF(self, event, manager):
		#print datetime.now(), event.name, event.headers
		if event.headers['Begin'] == 'Yes' and event.headers['Direction'] == 'Received':
			actorName = self.actor[event.headers['Uniqueid']]
			# store the pressed digit, so that other threads can find it
			self.pressedDTMF[actorName] = int(event.headers['Digit'])
			# notify the thread waiting for this by setting/trigering the right event
			# if the event is not there, or is already set, then a thread is not waiting for it
			if actorName in self.eventsDTMF and not self.eventsDTMF[actorName].is_set():
				# play the beep sound. Decided it's not needed
				# self.playback(self.beep, actorName, dir='', waitToEnd=False)
				self.eventsDTMF[actorName].set()
				print datetime.now(), actorName, "pressed key", event.headers['Digit']
			else:
				print datetime.now(), actorName, "pressed key", event.headers['Digit'], 'IGNORED'

	def handle_AGIExec(self, event, manager):
		# we are only issuing exec playback commands so if we receive an End Subevent
		# it means that the playback is over.
		if event.headers['SubEvent'] == 'End':
			actorName = self.actorFromChan[event.headers['Channel']]
			# notify the thread waiting for this by setting/trigering the right event
			if actorName in self.eventsPlayEnd and not self.eventsPlayEnd[actorName].is_set():
				self.eventsPlayEnd[actorName].set()
			else:
				print datetime.now(), "WARNING: playback ended for", actorName, "WITHOUT a thread waiting for it"

	def handle_shutdown(self, event, manager):
		print "Received shutdown event"
		manager.close()


	def handle_Hangup(self, event, manager):
		actorName = event.headers['CallerIDName']
		uniqID = event.headers['Uniqueid']
		# Try to reconect only if we are not shutting down and this is an established call
		if (not self.shuttingDown) and (actorName in self.phoneNum) and (actorName in self.uniqueID) and (self.uniqueID[actorName] == uniqID):
			print datetime.now(), actorName, '*Hangup*  Will try to call back.'
			# delete relevant entries from the dictionaries, keep only the phoneNum connection
			chan = self.channel[actorName]
			del self.channel[actorName]
			del self.uniqueID[actorName]
			del self.actor[uniqID]
			del self.actorFromChan[chan]
			# then set any events that the existing thread might be waiting on
			if actorName in self.eventsDTMF:
				self.eventsDTMF[actorName].set()
			if actorName in self.eventsPlayEnd:
				self.eventsPlayEnd[actorName].set()
			# we could wait for the thread to join (i.e., exit) but there is no need.
			sleep(0.5)
			# establish a new call. Start a new thread, we should not do any waiting in handlers
			# we are still waiting for 1 to be pressed, 30sec max delay, *and* playing the whenReconnected sound
			t = threading.Thread(target=self._establishCall, args=(self.phoneNum[actorName], actorName, True, 30, True))
			t.start()


	def handle_Newstate(self, event, manager):
		cid = event.headers['CallerIDNum']
		uniqID = event.headers['Uniqueid']
		chan = event.headers['Channel']

		# the call has been asnwered. It has to be an incoming call this handler is unregistered
		# before we run begin() which makes outgoing calls
		if event.headers['ChannelStateDesc'] == 'Up':
			# is it a valid number?
			try:
				val = int(cid)
			except ValueError:
				print datetime.now(), 'Call in:', cid, 'is not a valid phone number to keep'
				return
			# start a new thread to handle this call
			t = threading.Thread(target=self._testPhone, args=(cid, chan, uniqID))
			t.start()
	def handle_event(self, event, manager):
		# This is a catch-all handler for debugging. However, we can safely ignore some events.
		if (event.name == 'RTCPReceived') or (event.name == 'RTCPSent'):
			return
		print datetime.now(), "Received event: %s" % event.name
		print event.headers


# The class defines all we need. We can import this file in our own scripts and create audioplans
# and shows. We can also run this file on its own, and the following test code will run
if __name__ == "__main__":

	# names of the main characters, to make description of the plan and reporting easier
	names = ['Actor1','Actor2','Actor3','Actor4','Actor5','Actor6']

	'''
	The audio plan is structured as follows: It is a list of periods. A period is the sync checkpoint
	for all actors. All actors should complete their path of actions before starting the next period.
	A period is a list of trees, one for each actor (technically is a dict/map of trees)
	A tree is a tree of actions and possible options that an Actor has at a given period. An action
	is an audio file to be played. A tree is represented as a dictionary (of possibly nested
	dictionaries). Generally in Python, a dictionary, has  multiple entries of the form key:value
	separated with commas. In our tree representation, if a key has non-numeric value then it is
	interpreted as an audio filename to be played. The value of the key is the next action to take.
	'None' means that nothing happens and we are done. The value can also be another tree! If the key
	values are numeric, then the program interprets this as a choice that needs to be made by the user
	by pressing a number in the phone keypad (DTMF tones). Once the choice is made and is valid, then
	the value of the corresponding key is the action. It can be a simple filename (in which case the
	corresponding filename is played and we are done) or it can be another tree. This way we can
	build arbitrarily complex trees of actions and options. When creating options it is a good idea for
	the preceding audio file to explain these options and ask you to take them. For example if we have
	this tree {'blah':{1:'hi', 2:'bye'}} it will play the 'blah' and then just wait for a DTMF tone.
	So the valid options should be given and explained at the end of audio file 'blah'
	If the DTMF tone pressed is not one of the options given, it will 'say please try again'
	The program will try to get a correct input for x secs (x=30 by default). Giving an invalid
	input will not reset this timer. If no valid option is given, a default option will be taken by
	the program. Currenly th default option is 1, but you one can easily change this when calling
	the function waitForDTMF
	'''
	audioPlan = [
	# period0
	{'Actor1': {'welcome':{1:None}},
	 'Actor2': {'welcome':{1:None}},
	 'Actor3': {'welcome':{1:None}},
	 'Audience': {'welcome':{1:None}}
	},

	# period1
	{'Actor1': {'tt-monty-knights':{1:'priv-introsaved', 2:'priv-callpending', 3:'queue-minutes'}},
	 'Actor2': {'tt-monty-knights':{1:'good', 2:{'enter-num-blacklist':{1:'press-1', 2:'press-2'}}}},
	 'Actor3': {'different-file':None},
	 'Actor4': {'tt-monty-knights':{'play-another-file':None}},
	 'Audience': {'tt-monty-knights':None}
	},

	#pediod2
	{'Actor1': {'goodbye':None},
	 'Actor2': {'goodbye':None},
	 'Audience': {'goodbye':None},
	}

	]

	# create a new show
	show = Show(names, audioPlan, audiencePhone=None, username='admin', pswd='L1v3pupp3t5')

	# you can set several config parameters such as sound files. Look at the beginning of the class
	# definition to find all the configuration parameters as class attributes
	show.whenReconnected = 'hello-world'

	# define your trigger phone numbers in a list, run collectPhones(), with optional maximum delay
	# in secs, and then just begin the show
	triggerPhones = ['61413817002']
	show.collectPhones(triggerPhones, delay=150)
	show.begin()

	# if you do not want to collect them during preshow then do not call collectPhone() and pass
	# a list of phones as an arg to begin() e.g. show.begin(['302101000000', '61413000000'])
