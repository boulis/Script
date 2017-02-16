# Showisk
Showisk (Asterisk-enabled interactive show) enables someone to use Asterisk (open-source PBX) to place multiple calls to people (aka actors) and playback audio files in a synchronised way, while  allowing for choices to be made by the actors. One can create complicated audio plans with arbitrary many sync points, and decision trees of arbitrary depth. 

Created by Athanassios (Thanassis) Boulis in August-September 2013

## Requirements
Showisk relies on pyst and specifically the Python interface to the Asterisk Manager Interface (AMI). It also needs to connect to a machine that runs Asterisk and has setup a voip provider (or other way to make phone calls). 

## History and general scope
Showisk was develeoped to address technical challenges in Grant Moxom's honours project at UNSW, Australia. The central idea of the project was to create an audience-interactive show, where audience members volunteer to come on state and follow verbal instructions given to them through a headset. The instructions are prerecorded (no live guidance), and are very specific. For example: "put your right hand on the left part of your chest and look upwards". The main goal is to explore the performance opportunities that 'mindless actors' can create, actors that have no sense of the overarching performance (not even formal training in acting). What would the audience get out of this experiment?

A first iteration of the project included just one long audio track per actor. Actors (i.e., volunteers from the audience) would be provided with mp3 player and headsets to listen to the instructions. This meant that all actors had to synchronoysly press play at the beginning of the show and that the single audio track had to serve the whole show. There was little room for advanced interaction and no room for choice by the actors. The enhanced show was more ambitious. There was a need for: 
- Choice by the actors (to listen to different instructions at certain points)
- Synchronising the actors together since interactions between actors were important.

The solution chosen was to feed the audio to actors' phones via voip connections. A program would control the flow for the whole show and 
take care of synchronisation and choices by recognising key presses. Asterisk was chosen as a software PBX. However, it was not easy to control Asterisk via the standard scripting language provided to build phone plans. A program was needed to control the flows and other aspects of the show. Grant had setup Asterisk and a voip service and could make phone calls as well as repond to individual key presses, but had problems with the overall control and synchronisation. This is when I offered to help by building a Python script to take care of the control. I was excited to learn more about Asterisk and moreover this project was the perfect example to work with threads on Python. Threads were used to place multiple parallel calls and synchronise them. 

## Comments from Grant

After the first iteration was done (still a lot of testing was needed and several features added afterwards):

>Thanassis Boulis is possibly the greatest human ever. Making a heroic effort of writing the code for my ENTIRE show in pretty much ONE DAY! Sleeping only 4 hours. And not only is it done - but it is BEAUTIFUL! With logical comments, a stunningly attractive formatting and even more functions than I had needed. And to think that I thought I could do this myself... I couldn't... at all..."

After the first show in September:

>As for the show, first night went technically perfectly. Absolutely no problems someone even accidentally hung up and it called them back and set them RIGHT back to where they were. Very impressive.

After all shows:

>Once again, thanks SO much for doing all that Thanassis, it was AMAZING working with code that wasn't a massive mess. When I created those debugger files I thought I'd have to delete large sections of code. When I looked at it though I saw you'd put variables in there to do everything I wanted, eg. disable the "press1" and disable shuffle. This sort of foresight was SO impressive and a testament to someone who codes regularly.

>I would absolutely LOVE to work with you again one day on an extension of this.
