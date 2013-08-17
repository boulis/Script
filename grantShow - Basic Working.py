#! /usr/bin/python

import asterisk.manager
import sys
from datetime import datetime
from time import sleep, time
import threading


class Show:
	"""
	The class that does all the work by starting up the various threads and connection to the AMI
	"""
	def __init__(self, names, specialPhones, audioPlan):
		self.names = names
		self.specialPhones = specialPhones
		self.audioPlan = audioPlan
				
		# Dictionaries to hold important info on calls.
		self.channel = {}	# Referenced with actor name as key
		self.uniqueID = {}	# Referenced with actor name as key
		self.actor = {}		# Referenced with uniqueID as key
		self.actorFromChan = {} # Referenced with channel as key
		
		self._enoughPhonesCollected = threading.Event()
		self._allActorsReady = threading.Event()
		
		# events to signify when calls are answered, DTMF tones received, and ending of audiofile 
		# playback These are dictionaries because there are multiple events, one for each actor.
		self.eventsCallAnswer = {}
		self.eventsDTMF = {}
		self.eventsPlayEnd = {}
		
		# a dictionary to hold the last DTMF pressed, one entry for each actor
		self.pressedDTMF = {}
		
		# the AMI manager to interact with Asterisk
		self.manager = asterisk.manager.Manager()

		# connect to the manager
		try:
			self.manager.connect('127.0.0.1')
			self.manager.login('admin', 'L1v3pupp3t5')
    
			# register some callbacks
			self.manager.register_event('Shutdown', self.handle_shutdown) # shutdown
			self.manager.register_event('NewCallerid', self.handle_NewCallerID)		# the NewCallerid events help us find out the channel and unique id of our call
			self.manager.register_event('Newexten', self.handle_NewExten)			# the Newexten event help us know when an phone is answered
			self.manager.register_event('AGIExec', self.handle_AGIExec)				# to know the end of playback
			self.manager.register_event('DTMF', self.handle_DTMF)					# detected pressed keys
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
		
		
	def begin(self, phones=[]):
				
		# First try to originate enough calls, and establish the connection is with a human
		actorThreads = []
		for phone, actorName in zip(phones, self.names):
			t = threading.Thread(target=self._establishCall, args=(phone, actorName))
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
		self.manager.close()
			
			
	def _establishCall(self, phone, actorName):
		# originate calls asynchronously so that  multiple calls can be initiated in parallel.
		# Otherwise a call has to be answered for another one to start ringing, even if 
		# the originate commands are given from different threads
		response = self.manager.originate('SIP/didlogic-trunk/'+ phone, caller_id=actorName, async=True, exten='callwait', context='testcall', priority='1')
		print datetime.now(), 'Originating call to', actorName, phone, 'Response:', response

		
		# wait for the call to be answered
		self.eventsCallAnswer[actorName] = threading.Event()
		self.eventsCallAnswer[actorName].wait(30)
		if self.eventsCallAnswer[actorName].is_set():
			sleep(1)
			# if the call is answered, ask for the actor to press 1, so we confirm is human
			self.playback('press-1', actorName)
			if self.waitToPress1(actorName, delay=30):
				print datetime.now(), 'Success establishing call to', actorName
			else:
				print datetime.now(), 'Call answered but', actorName, 'did not press 1 within 30 secs'
		else:
			print datetime.now(), 'Call to', actorName, 'was NOT answered'
		
	
	def _execute_plan(self, plan, actorName):
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


	def playback(self, filename, actorName):
		cdict = {'Action':'AGI'}
		cdict['Channel'] = self.channel[actorName]
		cdict['Command'] = 'EXEC Playback ' + filename
		cdict['CommandID'] = 'MyCommandID'
		response = self.manager.send_action(cdict)
		print datetime.now(), "Playing audio file", filename, "to", actorName, ". Start response:", response
		
		#print response.headers
		if response.headers['Response'] == 'Success':
			# Wait for the playback to finish. Create a new event to wait upon. The new event is 
			# initially clear and we are waiting for the handle_AGIExec() method to set it.
			self.eventsPlayEnd[actorName] = threading.Event()
			self.eventsPlayEnd[actorName].wait()
			print datetime.now(), "Playing audio file", filename, "to", actorName, ". Finished"
 
 	def waitForDTMF(self, actorName, plan, delay=30):
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
					self.playback('please-try-again', actorName)
			else:
				# the wait period just expired, no valid key was pressed
				return 1
			# update 
			end = time()
		return 1
							
  	def waitToPress1(self, actorName, delay=30):
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
				if self.pressedDTMF[actorName] == 1:
					return 1
				else:
					# a key was pressed but is not valid, ask again
					self.playback('please-try-again', actorName)
			else:
				# the wait period just expired, no valid key was pressed
				return 0
			# update 
			end = time()	
		return 0
 	
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
 
 
 	def handle_event(event, manager):
		if (event.name == 'RTCPReceived') or (event.name == 'RTCPSent'):
			return
		print datetime.now(), "Received event: %s" % event.name
		print event.headers
    	
    	
# names of the main characters, to make description of the plan and reporting easier
names = ['Actor1','Actor2','Actor3','Actor4','Actor5','Actor6'] 
# the phones that we can call from to begin the main show. Add as many as you like
specialPhones = ['61439588446', '61413817002']

'''
The audio plan is structured as follows: It is a list of periods. A period is the sync checkpoint for
all actors. All actors should complete their path of actions before starting the next period.
A period is a list of trees, one for each actor (technically is a dict/map of trees)
A tree is a tree of actions and possible options that an Actor has at a given period. An action  
is an audio file to be played. A tree is represented as a dictionary (of possibly nested 
dictionaries). In Python a dictionary in general has  multiple entries of the form key:value 
separated with commas. In our tree representation, if a key has non-numneric value then it is 
interpreted as an audio filename to be played. The value of the key is the next action to take.
'None' means that nothing happens and we are done. The value can also be another tree! If the key
values are numeric, then the program interprets this as a choice that needs to be made by the user
by pressing a number in the phone keypad (DTMF tones). Once the choice is made and is valid, then
the value of the corresponding key is the action. It can be a simple filename (in which case the
corresponding filename is played and we are done) or it can be another tree. This way we can 
build arbitrary complex trees of actions and options. When creating options it is a good idea for
the preceding audio file to explain these options and ask you to take them. For example if we have
this tree {'blah':{1:None, 2:None}} it will play the 'blah' and then just wait for a DTMF tone.
If the DTMF tone pressed is not one of the options given, it will 'say please try again'

'''
audioPlan = [
# period0
{'Actor1': {'welcome':{1:None}},
 'Actor2': {'welcome':{1:None}},
 'Actor3': {'welcome':{1:None}},
},

# period1
{'Actor1': {'tt-monty-knights':{1:'press-1', 2:'press-2', 3:'press-3'}},
 'Actor2': {'tt-monty-knights':{1:'good', 2:{'enter-num-blacklist':{1:'press-1', 2:'press-2'}}}},
 'Actor3': {'different-file':None},
 'Actor4': {'tt-monty-knights':{'play-another-file':None}}
},

#pediod2
{'Actor1': {'goodbye':None},
 'Actor2': {'goodbye':None},
}

]

# create a new show
show = Show(names, specialPhones, audioPlan)

# begin the show. You can pass it a list of phones to bypass the requirement to collect phone # during preshow
#show.begin(['61296981940'])
show.begin(['61296981940', '61439588446'])