#! /usr/bin/python

import showisk

''' 
Create a show based on the functionality provided in showisk.py.
You can define 
'''

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
    # Hi to humans
    {'Actor1': {'ishuman':None},
     'Actor2': {'ishuman':None},
     'Actor3': {'ishuman':None},
     'Actor4': {'ishuman':None},
     #'Actor5': {'ishuman':None},
     #'Actor6': {'ishuman':None},
     'Audience': {'welcome':None},
     },
    #Get headphones then start part 1
    {'Actor1': {'Julietpart1':{1:None}},
     'Actor2': {'Andrewpart1':{1:None}},
     'Actor3': {'Susiepart1':{1:None}},
     'Actor4': {'Angelapart1':{1:None}},
    # 'Actor5': {'Albertpart1':{1:None}},
    # 'Actor6': {'Billpart1':{1:None}},
     'Audience': {'Audiencepart1':{1:None}},
     },
    {'Actor1': {'Julietpart2':None},
     'Actor2': {'Andrewpart2':None},
     'Actor3': {'Susiepart2':None},
     'Actor4': {'Angelapart2':None},
   #  'Actor5': {'Albertpart2':None},
    # 'Actor6': {'Billpart2':None},
     'Audience': {'Audiencepart2':None},
     },
    {'Actor1': {'Julietpart3':None},
     'Actor2': {'Andrewpart3':None},
     'Actor3': {'Susiepart3':None},
     'Actor4': {'Angelapart3':None},
  #   'Actor5': {'Albertpart3':None},
   #  'Actor6': {'Billpart3':None},
     'Audience': {'Audiencepart3':None},
     },
    {'Actor1': {'Julietpart4':None},
     'Actor2': {'Andrewpart4':None},
     'Actor3': {'Susiepart4':None},
     'Actor4': {'Angelapart4':None},
 #    'Actor5': {'Albertpart4':None},
 #    'Actor6': {'Billpart4':None},
     'Audience': {'Audiencepart4':None},
     },
    ]


# create a new show
show = showisk.Show(names, audioPlan, audiencePhone='', username='admin', pswd='L1v3pupp3t5')


# set some configuration parameters. For example the audio directory or the full path for commonly
# played sounds like the beep or 'press 1'. No need to set everything, there are default values.
show.audiodir = '/audio/'
show.whenReconnected = 'hello-world'
show.press1 = '/audio/press1'
show.register ='/audio/Register1'
show.nothuman = '/audio/nothuman'
show.register2 = '/audio/Register2'		# asked when calling in
show.triggerPreshow = '/audio/ShowStarter1'		# to be played at the trigger phone just before begin()
show.triggerDuringShow = '/audio/ShowStarter2' # to be played at the trigger phone during begin()
show.registerconf = '/audio/RegisterConf'

# the phones that we can call from to begin the main show. Add as many as you like
triggerPhones = ['']
# collect phones, you can also add an optional maximum delay in case no call from a trigger phone is made 
show.collectPhones(triggerPhones)
if input != contr-c:
    print "yeahhhh"
#show.begin(['61413817002', '61405585884', '61402337737', '61415732466'])
# we have collected phones. begin the show
show.begin()

