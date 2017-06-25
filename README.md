# kmtrein

This is a Python script written by Erik Tjong Kim Sang for
his participation in the 2017 competition kmtrein. The
object of the competition was to cover as many kilometers by
train travelling in The Netherlands on Saturday 24 June
2017. The script computes the longest possible route, given
the train schedule for intercity trains and a certain
conditions.

## Platforms

This is a Python script which runs on Apple Macs and Linux
machine. If you want to run it on Microsoft Windows, you
should check if you have
[Python](https://en.wikipedia.org/wiki/Python_(programming_language))
Python on your computer and install it on your system.

## Running the program

The program searches for the longest possible train routes
on a certain day. It is not perfect and it will not always
find the best solution. Your creativity in how to run the
program will determine how long the routes are that you will
find.

Let's start with looking for a route. We want to start in
Groningen so we tell that to the program: our first station
is Groningen:

```
./findRoutes.py -f groningen < traintrips.txt
```

Note the program knows all station names written in lower
case characters and without punctuation. So 's Hertogenbosch
becomes shertogenbosch. The option -f signals that the next
word is the first station. The file traintrips.txt contain
the time schedule (dienstregeling in Dutch).


