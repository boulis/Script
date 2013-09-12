#! /usr/bin/python

import showisk



''' 
Create a show based on the functionality provided in showisk.py.
You can define 
'''

# names of the main characters, to make description of the plan and reporting easier
names = ['Juliet','Andrew','Susie','Angela','Albert','Bill']

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
    {'Juliet': {'ishuman':None},
     'Andrew': {'ishuman':None},
     'Susie': {'ishuman':None},
     'Angela': {'ishuman':None},
     'Albert': {'ishuman':None},
     'Bill': {'ishuman':None},
     'Audience': {'':None},
    },
   # Get headphones then start part 1
    {'Juliet': {'Julietstart':{1:None}},
     'Andrew': {'Andrewstart':{1:None}},
     'Susie':  {'Susiestart':{1:None}},
     'Angela': {'Angelastart':{1:None}},
     'Albert': {'Albertstart':{1:None}},
     'Bill':   {'Billstart':{1:None}},
     'Audience': {'Audiencestart':None},
    },
    {'Juliet': {'Juliet01':None},
     'Andrew': {'Andrew01':None},
     'Susie':  {'Susie01':None},
     'Angela': {'Angela01':None},
     'Albert': {'Albert01':None},
     'Bill':   {'Bill01':None},
     'Audience': {'Audience01':None},
    },
    {'Juliet': {'Juliet02':None},
     'Andrew': {'Andrew02':None},
     'Susie':  {'Susie02':None},
     'Angela': {'Angela02':None},
     'Albert': {'Albert02':None},
     'Bill':   {'Bill02':None},
     'Audience': {'Audience02':None},
    },
    {'Juliet': {'Juliet03':None},
     'Andrew': {'Andrew03':None},
     'Susie':  {'Susie03':None},
     'Angela': {'Angela03':None},
     'Albert': {'Albert03':None},
     'Bill':   {'Bill03':None},
     'Audience': {'Audience03':None},
    },
    {'Juliet': {'Juliet04':None},
     'Andrew': {'Andrew04':None},
     'Susie':  {'Susie04':None},
     'Angela': {'Angela04':None},
     'Albert': {'Albert04':None},
     'Bill':   {'Bill04':None},
     'Audience': {'Audience04':None},
    },
    {'Juliet': {'Juliet05':None},
     'Andrew': {'Andrew05':None},
     'Susie':  {'Susie05':None},
     'Angela': {'Angela05':None},
     'Albert': {'Albert05':None},
     'Bill':   {'Bill05':None},
     'Audience': {'Audience05':None},
    },
    {'Juliet': {'Juliet06':None},
     'Andrew': {'Andrew06':None},
     'Susie':  {'Susie06':None},
     'Angela': {'Angela06':None},
     'Albert': {'Albert06':None},
     'Bill':   {'Bill06':None},
     'Audience': {'Audience06':None},
    },
    {'Juliet': {'Juliet07':None},
     'Andrew': {'Andrew07':None},
     'Susie':  {'Susie07':None},
     'Angela': {'Angela07':None},
     'Albert': {'Albert07':None},
     'Bill':   {'Bill07':None},
     'Audience': {'Audience07':None},
    },
    {'Juliet': {'Juliet08':None},
     'Andrew': {'Andrew08':None},
     'Susie':  {'Susie08':None},
     'Angela': {'Angela08':None},
     'Albert': {'Albert08':None},
     'Bill':   {'Bill08':None},
     'Audience': {'Audience08':None},
    },
    {'Juliet': {'Juliet09':None},
     'Andrew': {'Andrew09':None},
     'Susie':  {'Susie09':None},
     'Angela': {'Angela09':None},
     'Albert': {'Albert09':None},
     'Bill':   {'Bill09':None},
     'Audience': {'Audience09':None},
    },
    {'Juliet': {'Juliet10':None},
     'Andrew': {'Andrew10':None},
     'Susie':  {'Susie10':None},
     'Angela': {'Angela10':None},
     'Albert': {'Albert10':None},
     'Bill':   {'Bill10':None},
     'Audience': {'Audience10':None},
    },
    {'Juliet': {'Juliet11':None},
     'Andrew': {'Andrew11':None},
     'Susie':  {'Susie11':None},
     'Angela': {'Angela11':None},
     'Albert': {'Albert11':None},
     'Bill':   {'Bill11':None},
     'Audience': {'Audience11':None},
    },
    {'Juliet': {'Juliet12':None},
     'Andrew': {'Andrew12':None},
     'Susie':  {'Susie12':None},
     'Angela': {'Angela12':None},
     'Albert': {'Albert12':None},
     'Bill':   {'Bill12':None},
     'Audience': {'Audience12':None},
    },
    {'Juliet': {'Juliet13':None},
     'Andrew': {'Andrew13':None},
     'Susie':  {'Susie13':None},
     'Angela': {'Angela13':None},
     'Albert': {'Albert13':None},
     'Bill':   {'Bill13':None},
     'Audience': {'Audience13':None},
    },
    {'Juliet': {'Juliet14':None},
     'Andrew': {'Andrew14':None},
     'Susie':  {'Susie14':None},
     'Angela': {'Angela14':None},
     'Albert': {'Albert14':None},
     'Bill':   {'Bill14':None},
     'Audience': {'Audience14':None},
    },
    ]


# create a new show
show = showisk.Show(names, audioPlan, audiencePhone='61412591161', username='admin', pswd='L1v3pupp3t5')
#show = showisk.Show(names, audioPlan, audiencePhone='', username='admin', pswd='L1v3pupp3t5')


# set some configuration parameters. For example the audio directory or the full path for commonly
# played sounds like the beep or 'press 1'. No need to set everything, there are default values.
show.audiodir = '/audio/'
show.press1 = '/audio/Press1'
show.register ='/audio/Register1'
show.nothuman = '/audio/nothuman'
show.register2 = '/audio/Register2'		# asked when calling in
show.triggerPreshow = '/audio/ShowStart1'		# to be played at the trigger phone just before begin()
show.triggerDuringShow = '/audio/ShowStart2' # to be played at the trigger phone during begin()
show.registerconf = '/audio/RegisterConf'
show.tryAgain = '/audio/please-try-again'
show.whenReconnected = '/audio/reconnected'
show.thankyou = '/audio/thankyou'

# the phones that we can call from to begin the main show. Add as many as you like
#triggerPhones = ['61431034289']
#show.collectPhones(triggerPhones)
# collect phones, you can also add an optional maximum delay in case no call from a trigger phone is made
# we have collected phones. begin the show#
#show.begin()
show.begin(['61413817002'])