# kmtrein

This is a Python script written by Erik Tjong Kim Sang for
his participation in the 2017 competition kmtrein. The
object of the competition was to cover as many kilometers by
train travelling in The Netherlands on Saturday 24 June
2017. The script computes the longest possible route, given
the train schedule for intercity trains and a certain
conditions.

## Installation

This is a Python script which runs on Apple Macs and Linux
machine. If you want to run it on Microsoft Windows, you
should check if you have
[Python](https://en.wikipedia.org/wiki/Python_(programming_language))
Python on your computer and install it on your system.

You can download the program and its five data files one by
one (copy and paste from raw view mode at the website) or
all at once with software git which is associated with the
website [github.com](http://github.com). Run the following
on the command line (in a terminal window):

```
git clone http://github.com/eriktks/kmtrein
```

This will create a directory kmtrain in the current folder
where you can find the program and its data files

## Running the program

The program searches for the longest possible train routes
on a certain day. It is not perfect and it will not always
find the best solution. Your creativity in how to run the
program will determine how long the routes are that you will
find.

Let's start with looking for a new route. We want to start in
Groningen so we tell that to the program: our first station
is Groningen:

```
./findRoutes.py -n -f groningen < traintrips.txt
```

Note the program knows all station names written in lower
case characters and without punctuation. So 's Hertogenbosch
becomes shertogenbosch. The option -f signals that the next
word is the first station. The file traintrips.txt contain
the time schedule (dienstregeling in Dutch). The option -n
signals that this is a new route and that no use should be
made of previously computed route information.

The program outputs the different routes that it finds with
the longest at the bottom:

```
22:39 23:07 00:03 43.5 0.0 93 nijmegen shertogenbosch
23:23 23:51 00:16 46.6 0.0 103 shertogenbosch utrechtcentraal
# largest distance : 1853.0
```

The bottom line shows the total distance covered by this
route. The other lines cover the different parts of the
route. For example, the line above the last line should be
read like this: *Take the train from 's Hertogenbosch to
Utrecht Centraal leaving at 23:23 and arriving at 23:51;
waiting time after your previous train is 16 minutes. Length
of this train ride is 46.6 km. Distance difference of this
suggestion with the best suggestion at this time of the day
is 0.0 km.*

## Finding longer routes

Checking all possible train routes in The Netherlands would
take a very very long time. The program uses a technique
called *beam search* for finding the longest route in a
reasoble time. At each point of the day, it only looks at
routes that are within a certain distance (the beam) of the
longest route known. By doing this, the program can find a
longg route quickly but it will miss many possible routes
that only cover few kilometers early in the day.

If you want the program to find a longer route, you can ask
it to examine more route by increasing its beam size. But
beware: the larger the beam size, the more time the program
will take to finish! Lets try a beam size of 40 by using the
option -b:

```
./findRoutes.py -b 40 -f groningen < traintrips.txt
...
# largest distance : 1925.2
```

Execellent, now we get a longer route. Try other beam sizes
and see what you get. You will notice that the program is
responding more slowly as the beam size increases. But
hopefully you will be rewarded with longer routes.

## Travelabiliy

**Always check the routes suggested by  the program for
travelability!** It might suggest you a transfer at station
Utrecht Centraal from platform 1 to platform 22 in zero
minutes, which is a bit hard.

You can define minimum transfer times in the file transfers.
The file contains lines with on them: a time (in minutes)
and four stations: the station from which you left, the
transfer station (twice) and the target station. Optionally
these are followed by the arrival time at the transfer
station. So;

```
00:04 amersfoort utrechtcentraal utrechtcentraal arnhem
```

means: *when you travel from Amersfoort to Arnhem and have a
transfer at Utrecht Centraal, allow for a transfer time of
at least four minutes*

I have used conservative minimum transfer times for
transfers that included a platform change: four minutes at
large stations and three minutes at small ones. If you think
you can manage two-minute changes, you should change the
file transfers. Your reward will be longer routes but the
risk that you might miss a train connection will increase.

## Using this software in another edition

If you want to use this software for another edition of this
competition you will need to update train schedule. I
obtained the train schedule from the website
[rijdendetreinen.nl](https://www.rijdendetreinen.nl/reisplanner).
The track lengths were found on
[wiskunde123.nl](http://www.wiskunde123.nl/treingraaf/).

For other editions you also want to change the file
transfers to your needs (see previous section). You might
want to update the file stations, which currently contains
only a subset of the intercity stations. Examining the
partner file could also be useful: it contains the railway
sections which overlap and it is incomplete. The file
time-distance contains the longest distances per time of the
day and can be left alone.

