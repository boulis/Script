#! /usr/bin/python

import showisk

''' 
Create a show based on the functionality provided in showisk.py.
You can define 
'''

# names of the main characters, to make description of the plan and reporting easier
names = ['Actor1','Actor2','Actor3','Actor4','Actor5','Actor6']
# the phones that we can call from to begin the main show. Add as many as you like
triggerPhones = ['61439588446', '61413817002']

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
# 'Actor2': {'lineup':None},
# 'Actor3': {'lineup':None},
# 'Actor4': {'lineup':None},
# 'Actor5': {'lineup':None},
# 'Actor6': {'lineup':None},
 'Audience': {'lineup':None},
},
#Seated movements
{'Actor1': {'JScene1':{1:None}},

},
#Get headphones then start part 1
{'Actor1': {'JScene2':None},
}



]


# create a new show
show = showisk.Show(names, triggerPhones, audioPlan, audiencePhone='302721088776', username='admin', pswd='L1v3pupp3t5')

# set some configuration parameters. For example the audio directory or the full path for commonly
# played sounds like the beep or 'press 1'. No need to set everything, there are default values.
show.audiodir = '/audio/'

# begin the show. You can pass it a list of phones to bypass the requirement to collect phone # during preshow
#show.begin(['61296981940'])
show.begin(['61413817002'])