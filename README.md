# kmtrein

This is a Python script written by Erik Tjong Kim Sang for
his participation in the 2017, 2019 and 2023 editions of the 
competition [kmtrein](https://www.kilometerkampioen.nl/).
The object of the competitions was to cover as many
kilometers by train traveling in The Netherlands on a single day.
The script computes the longest possible
route, given the train schedule for intercity trains and a
certain conditions.

## Installation

This is a Python script which runs on Apple Macs and Linux
machine. If you want to run it on Microsoft Windows, you
should check if you have
[Python](https://en.wikipedia.org/wiki/Python_(programming_language))
on your computer and install it on your system.

You can download the program and its five data files one by
one (copy and paste from raw view mode at this website) or
all at once with software git which is associated with the
website [github.com](http://github.com). Run the following
on the command line (in a terminal window):

```
git clone http://github.com/eriktks/kmtrein
```

This will create a directory kmtrein in the current folder
where you can find the program and its data files

## Updating the train schedule data

The train schedules are stored in the file [traintrips.txt](traintrips.txt).
It currently contains the schedule for 16-09-2023, the date
of the 2023 edition of the competition. The file can be updated
with any text editor. The rail network is divided in 
different small tracks. The tracks are stored in the file
on lines starting with a hash character (#). These lines
should be kept in future editions. They contain the length of 
the track, the name of the start station and the name of the 
end station, for example "# 54.5 groningen leeuwarden".

The rest of the file are blocks of four lines, of which the first
represents a departure time and the second an arrival time. The third
and the fourth line are not being used. The time blocks
should be removed for a next edition and be replaced with the 
new relevant times:

1. go to the website [ns.nl](https://ns.nl)
2. enter the departure station and the arrival station in the search fields
3. enter the relevant date in the search field and the start time of the competition, for example "00:00"
4. start the search for train trips
5. change the view style of the page to "No Style", in the browser Firefox: select "View" (top menu), then "Page Style" and then "No Style"
6. Press the button "Later" until the page contains all the departure times that you need plus those of two hours later
7. save the web page or copy all the text on a web page and store it in a file
8. run the program [convert_schedule.py](convert_schedule.py) on this file and store the results in a second file
9. edit the traintrips.txt file and replace the old travel times by the new times in the second file
10. manually remove all the blocks of four lines that you do not need: those with departure times before the start of the competition or departure times more than two hours later than the end of the competition
11. to search for times for other station pairs, you need to put the page back "Basic View Style" mode unless you just want to lookup the times of the reversed route

Note that some of the stations have changed name since 2017, for example "Arnhem" became "Arnhem Centraal". You can change the names in the traintrips.txt file (name convention: only lower case characters, no spaces or hyphens) or keep on using the 2017 station names.

In case you want to check the distances or add new tracks: the distances orginate from the Kilometer Tool at the [competition website](https://www.kilometerkampioen.nl). If you add new track you might want to check if they do not overlap with existing tracks. Information about this is stored in the file [partners](partners).

In the 2023 edition of the competition, slow trains that stop everywhere were counted differently from fast trains. Since Dutch Railways does not make a difference between the two in their train schedules, a trick was needed to make the difference for the program: some tracks on which both train types are running, have been included twice in traintrips.txt: directly for fast trains and with a via station for slow trains. For example, for Groningen-Leeuwarden we have Groningen-Leeuwarden and Groningen-Grijpskerk-Leeuwarden. Since only slow trains stop at Grijpskerk and since Grijpskerk only serves the two cities, Groningen-Grijpskerk-Leeuwarden is guaranteed to be served by a slow train. 

This scheme has only been used for the fastest tracks. Tracks without intermediate stations (like Eindhoven-Weert) and tracks which are served only by slow trains (like Zwolle-Kampen) have been included in the file [can_travel_back](can_travel_back) to indicate that they can be used twice in a route.


## Running the program

The program searches for the longest possible train routes
on a certain day. It is not perfect and it will not always
find the best solution. Your creativity in how to run the
program will determine how long the routes are that you will
find.

Let's start with looking for a new route. We want to start in
Groningen so we tell that to the program: our first station is
Groningen (-f groningen) and we are looking for a new route (-n):

```
./findRoute.py -n -f groningen < traintrips.txt
```

The program prefers all station names to be written in lower
case and without punctuation. So 's Hertogenbosch becomes
shertogenbosch. The option -f signals that the next word is
the first station. The file traintrips.txt contains the time
schedule (dienstregeling in Dutch). The option -n signals
that this is a new route and that no use should be made of
previously computed route information.

The program outputs the different routes that it finds with
the longest at the bottom:

```
24:55 25:25 00:04 35.7 0.0 71 leeuwarden grijpskerk
25:25 25:39 00:00 18.8 0.0 80 grijpskerk groningen
# largest distance : 1733.1
```

The bottom line shows the total distance covered by this
route. The other lines cover the different parts of the
route. For example, the line above the last line should be
read like this: *Take the train from Grijpskerk to
Groningen leaving at 25:25 (01:25) and arriving at 25:39 (01:39);
the transfer time from your previous train is 0 minutes. The length
of this train ride is 18.8 km. Distance difference of this
suggestion with the best suggestion at this time of the day
is 0.0 km, the speed of the train is 80 km per hour.*

## Finding longer routes

Checking all possible train routes in The Netherlands would
take a very very long time. The program uses a technique
called beam search for finding the longest route in a
reasonable time. At each point of the day, it only looks at
routes that are within a certain distance (the beam) of the
longest route known up until that point of the day. By doing
this, the program can find a long route quickly but it will
miss longer routes that only cover few kilometers early in
the day.

If you want the program to find a longer route, you can ask
it to examine more route by increasing its beam size. But
beware: the larger the beam size, the more time the program
will take to finish! The default beam size is 20 km. Lets try 
a beam size of 40 by using the option -b:

```
./findRoute.py -b 40 -f groningen < traintrips.txt
...
# largest distance : 1733.9
```

Excellent, now we get a slightly longer route. Try other beam sizes
and see what you get. You will notice that the program is
responding more slowly as the beam size increases. But
hopefully you will be rewarded with longer routes.

## Obtaining results more quickly

There are many possible train routes in The Netherlands and
it takes a lot of time to check them all, even with a
computer. One way to make the program find results quickly,
is to increase the beam slowly. For example, if you want to
test all possible first stations, then set the beam size at
zero first:

```
   ./findRoute.py -n -b 0 < traintrips.txt
```

Only when this run has finished, run the program with beam size 10:

```
   ./findRoute.py -b 10 < traintrips.txt
```

Note that this time we continue search for a route so we do
not use option -n here. Next, you run the program with beam
sizes 20, 30, 40 and so on until it takes too much time.

After this, look for the time 26:00 in the file
time-distance to find out the best stations and times to
start. The top four for beam size 20 in the year 2023 was:
Meppel (1746.3 km when starting at 00:04),
Leeuwarden (1742.1/00:55),
Akkrum (1733.9/00:36) and
Groningen (1733.0/01:44).
Rerun the program with a larger beam size, only for these 
first stations and starting times, for example:

```
   ./findRoute.py -b 40 -f meppel -s 00:31 < traintrips.txt
```

If this takes too much time, you can also start from a
partial route. For example, save the ten first lines of a
proposed route to a text file (with copy-and-paste), for 
example to "myfile.txt" and then run:

```
   ./findRoute.py -b 100 -H myfile.txt < traintrips.txt
```

The program will then look for a route that starts with the
trip specified in the file.

## Travelability

**Always check the routes suggested by  the program for
travelability!** It might suggest a transfer at station
Utrecht Centraal from platform 1 to platform 22 in zero
minutes, which is a bit hard to realize.

You can define minimum transfer times in the file
[transfers](transfers). The file contains lines with the format: 
minimum transfervtime (in minutes) and four stations: 
the station from which you left, the transfer station (twice) and 
the target station.
Optionally these are followed by the arrival time at the
transfer station. So;

```
00:04 amersfoort utrechtcentraal utrechtcentraal arnhem
```

means: *when you travel from Amersfoort to Arnhem and have a
transfer at Utrecht Centraal, allow for a transfer time of
at least four minutes*

In the tranfers file distributed here, all transfer times 
have been set at one minute. If this is too much for you,
please change the file.

For stations not mentioned in the transfers file, the program
uses a minimum transfer time of zero minutes. The reason for
this is that some direct routes have been split in the program
and therefore some transfers do not require changing trains.
For example, for Groningen-Grijpskerk-Leeuwarden, the program
assumes a transfer in Grijpskerk but since you would change
to the same train from Groningen, the transfer time here is
of no importance.

Use the option -i to ignore all transfer time restrictions:

```
   ./findRoute -i -b 90 -f shertogenbosch -s 00:48 < traintrips.txt
   ...
   # largest distance : 1995.8
```

