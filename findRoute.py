#!/usr/bin/python -W all
"""
   findRoute.py: find longest route with an index of the available train rides
   usage: findRoute.py [-b beam-size] [-f firstStation] [-h] [-H history-file] [-i] [-n] [-s time] [-S] < traintrips.txt
   note: expected input line formats: 
   1. hash sign distance start-station end-station
   2. (often on 4 separate lines) start-time end-time transfers travel-time
   -b: beam size
   -f: first station: start all routes here
   -h: show help message and exit
   -H history-file: file with partial journey; like output format:
      startTime endTime waitingTime distance speed startStation endStation
   -i: ignore transfer safety times
   -n: create new route/delete old route information
   -s: start time of search, format: HH:MM (hours and minutes)
   -S: show the speeds of the various trips
   20170617 erikt(at)xs4all.nl developed for my 2017 kmkampioen participation
"""

import getopt
import re
import sys

# constants
COMMAND = sys.argv.pop(0)
TIMEZERO = "06:00" # start time of competition
DAYTIME = "18:00" # duration of competition
MAXWAIT = "00:29" # do not stay at any station longer than this
MINRETURNWAITINGTIME = "00:02" # need at least 2 minutes to catch train back
CENTERNAME = "utrechtcentraal" # visit this station...
CENTERSTARTTIME = "11:00" # between this time and...
CENTERENDTIME = "15:00" # this time and...
CENTERWAITTIME = "00:05" # stay there at least this many minutes
MAXTIMERESERVE = "00:00" # number of last minute(s) of 24 hours as reserve
MINUTESPERHOUR = 60.0
PARTNERFILE="partners" # tracks with overlapping parts
STATIONSFILE="stations" # list of station names
TRANSFERSFILE="transfers" # minimum required time per transfer
TIMEDISTANCEFILE = "time-distance" # best distance covered per time of earlier runs
HELP="""usage: findRoute.py [-b beam-size] [-f firstStation] [-h] [-H history-file] [-i] [-n] [-s time] [-S] < traintrips.txt
-b: beam size
-f: first station: start all routes here
-h: show help message and exit
-H history-file: file with partial journey; like output format:
   startTime endTime waitingTime distance speed startStation endStation
-i: ignore transfer safety times
-n: create new route/delete old route information
-s: start time of search, format: HH:MM (hours and minutes)
-S: show the speeds of the various trips"""

# variables modifiable by arguments 
beamSize = 20
historyFile = ""
firstStation = ""
globalStartTime = TIMEZERO # start the journey at this time (or a little bit later)
doShowSpeeds = False
resetBestDistances = False
ignoreTransferSafetyTimes = False
# internal variables
index = {}
partners = {}
stations = {}
transfers = {}
trainTrips = []
maxDistance = 0
timeDistance = {}

def help():
    print(HELP)
    sys.exit()

def reverseTrack(track):
    startStation,endStation = track.split()
    return(endStation+" "+startStation)

def readStations():
    try: inFile = open(STATIONSFILE,"r")
    except: sys.exit(COMMAND+": cannot read file "+STATIONSFILE+"\n")
    stations = {}
    for line in inFile:
        line = line.rstrip()
        stations[line] = True
    return(stations)

# read minimal transfer times
def readTransfers():
    transfers = {}
    try: inFile = open(TRANSFERSFILE,"r")
    except: return(transfers) 
    for line in inFile:
        line = line.rstrip()
        fields = line.split()
        if len(fields) < 5: sys.exit(COMMAND+": unexpected line in file "+TRANSFERSFILE+": "+line+"\n")
        time = fields.pop(0)
        for i in range(0,4):
            if not fields[i] in stations:
                sys.exit(COMMAND+": unknown station "+fields[i]+" on line: "+line+"\n")
        line = " ".join(fields)
        transfers[line] = time
    return(transfers)

# read time-distance file
def readTimeDistance():
    timeDistance = {}
    try: inFile = open(TIMEDISTANCEFILE,"r")
    except: return(timeDistance)
    patternHashStart = re.compile("^#")
    for line in inFile:
        line = line.rstrip()
        if patternHashStart.match(line): continue
        fields = line.split()
        if len(fields) == 3: return({}) # old format
        if len(fields) != 4: sys.exit(COMMAND+": unexpected line in file "+TIMEDISTANCEFILE+": "+line+"\n")
        station,startTime,time,distance = fields
        timeDistance[station+" "+startTime+" "+time] = float(distance)
    return(timeDistance)

# write time-distance file
def writeTimeDistance(timeDistance):
    try: outFile = open(TIMEDISTANCEFILE,"w")
    except: sys.exit(COMMAND+": cannot write file "+TIMEDISTANCEFILE+"\n")
    startStationsTimes = {}
    for keyTD in timeDistance:
        fields = keyTD.split()
        if len(fields) != 3: sys.exit(COMMAND+": invalid time-distance key: "+keyTD+"\n")
        station,startTime,time = keyTD.split()
        startStationsTimes[station+" "+startTime] = True
    for stationTime in startStationsTimes:
        lastDistance = 0
        for minutes in range(0,time2minutes("25:01")):
            thisTime = minutes2time(minutes)
            keyTD = stationTime+" "+thisTime
            if not keyTD in timeDistance or timeDistance[keyTD] <= lastDistance:
                outFile.write(keyTD+" "+str(lastDistance)+"\n")
            else:
                outFile.write(keyTD+" "+str(timeDistance[keyTD])+"\n")
                lastDistance = timeDistance[keyTD]
    outFile.close()

def averageSpeed(distance,startTime,endTime):
    averageSpeed = MINUTESPERHOUR*distance/(time2minutes(endTime)-time2minutes(startTime))
    return(averageSpeed)

def readTrainTrips():
    # regular expressions
    patternHashStart = re.compile("^#")
    patternIsTime = re.compile("^\d\d:\d\d$")
    patternIsNumber = re.compile("^\d+(\.\d+)?$")
    # variables
    trainTrips = []
    startStation = ""
    endStation = ""
    distance = 0
    lines = [] # contain train trip information (spread over several lines)
    for line in sys.stdin:
        line = line.rstrip()
        # line with route meta data start with a hash sign
        # example: # 39 amsterdamcentraal utrechtcentraal
        if patternHashStart.match(line):
            fields = line.split()
            # sanity checks
            if len(fields) != 4: 
                sys.exit(COMMAND+": unexpected line in data file: "+line+"\n")
            if not patternIsNumber.match(fields[1]): 
                sys.exit(COMMAND+": missing distance on line: "+line+"\n")
            distance = float(fields[1])
            startStation = fields[2]
            endStation = fields[3]
            for station in fields[2:4]:
                if not station in stations:
                    sys.exit(COMMAND+": unknown station on stdin: "+station+"\n")
            lines = []
        else:
        # lines with train trip information are grouped in sets of four
        # 1. start time, 2. end time, 3. number of transfers, 4. travel time
            fields = line.split()
            lines.extend(fields)
            if len(lines) > 4: 
                sys.exit(COMMAND+": unexpected schedule data (quantity): "+str(lines)+"\n")
            if len(lines) == 4:
                startTime = lines[0]
                endTime = lines[1]
                if not patternIsTime.match(startTime) or \
                   not patternIsTime.match(endTime):
                    sys.exit(COMMAND+": unexpected schedule data (times): "+str(lines)+"\n")
                # do not allow travelling over the day end
                if startTime >= endTime:
                    sys.exit(COMMAND+": unexpected start and end time: "+str(lines)+"\n")
                speed = averageSpeed(distance,startTime,endTime)
                trainTrips.append({"startStation":startStation,"endStation":endStation,"startTime":startTime,"endTime":endTime,"distance":distance,"averageSpeed":speed})
                # clear lines buffer
                lines = []
    return(trainTrips)

def time2minutes(time):
    chars = list(time)
    minutes = 600*int(chars[0])+60*int(chars[1])+10*int(chars[3])+int(chars[4])
    return(minutes)

def minutes2time(minutes):
    hours = int(float(minutes)/MINUTESPERHOUR)
    minutes = int(minutes-hours*MINUTESPERHOUR)
    if hours < 10: hours = "0"+str(hours)
    else: hours = str(hours)
    if minutes < 10: minutes = "0"+str(minutes)
    else: minutes = str(minutes)
    return(hours+":"+minutes)

def computeTimes(startTime,waitingTime):
    startMinutes = time2minutes(startTime)
    waitingMinutes = time2minutes(waitingTime)
    times = []
    for minutes in range(startMinutes-waitingMinutes,startMinutes+1):
        if minutes >= 0:
            time = minutes2time(minutes)
            if time >= globalStartTime: times.append(time)
    return(times)
    
def makeIndex(trainTrips,transfers):
    index = {}
    # first check at which stations we can be at what times
    for i in range(0,len(trainTrips)):
        key = trainTrips[i]["endStation"]+" "+trainTrips[i]["endTime"]
        # we need follow-up routes for any station a trip finishes at
        if not key in index: index[key] = {}
        # keep the start station as well
        index[key][trainTrips[i]["startStation"]] = {}
        # we need follow-up routes for any station we can start the day
        if trainTrips[i]["startTime"] <= MAXWAIT:
            key = trainTrips[i]["endStation"]+" "+globalStartTime
            if not key in index: index[key] = {}
            # no start station: use the end station as start staion
            index[key][trainTrips[i]["endStation"]] = {}
    # next look for appropriate places to use a train trip
    for i in range(0,len(trainTrips)):
        for time in computeTimes(trainTrips[i]["startTime"],MAXWAIT):
            startStation = trainTrips[i]["startStation"]
            key = startStation+" "+time
            if key in index:
                for prevStartStation in index[key]:
                    # we keep only the time closest to now
                    # this causes a problem when the station requires a longer waiting time:
                    # the next time is missing
                    endStation = trainTrips[i]["endStation"]
                    trackPair = prevStartStation+" "+startStation+" "+startStation+" "+endStation
                    trackPairTime = trackPair+" "+time
                    waitingTime = minutes2time(time2minutes(trainTrips[i]["startTime"])-time2minutes(time)) 
                    nextTrip = {"startTime":trainTrips[i]["startTime"],"endTime":trainTrips[i]["endTime"],"distance":trainTrips[i]["distance"],"averageSpeed":trainTrips[i]["averageSpeed"]}
                    # collect all relevant trips for the start of the route
                    if time == TIMEZERO:
                        if not endStation in index[key][prevStartStation]: index[key][prevStartStation][endStation] = []
                        index[key][prevStartStation][endStation].append(nextTrip)
                    # for continuing a route, just keep the best time for each destination; consider the minimal transfer times
                    elif (not endStation in index[key][prevStartStation] or \
                        trainTrips[i]["endTime"] < index[key][prevStartStation][endStation][0]["endTime"]) and \
                       (prevStartStation != endStation or waitingTime >= MINRETURNWAITINGTIME or ignoreTransferSafetyTimes) and \
                       (not trackPair in transfers or waitingTime >= transfers[trackPair] or ignoreTransferSafetyTimes) and \
                       (not trackPairTime in transfers or waitingTime >= transfers[trackPairTime] or ignoreTransferSafetyTimes):
                        if not endStation in index[key][prevStartStation]: index[key][prevStartStation][endStation] = [nextTrip]
                        else: index[key][prevStartStation][endStation][0] = nextTrip
    return(index)

def centerVisited(route):
    if len(route) == 0: return(True)
    if route[-1]["endTime"] < CENTERENDTIME or ignoreTransferSafetyTimes: return(True)
    for i in range(1,len(route)):
        # did we arrive at the center station in the time frame, waitin 5 mins
        if route[i]["startStation"] == CENTERNAME and route[i]["waitingTime"] >= CENTERWAITTIME and \
           ((route[i]["startTime"] >= CENTERSTARTTIME and route[i]["startTime"] <= CENTERENDTIME) or
            (route[i-1]["endTime"] >= CENTERSTARTTIME and route[i-1]["endTime"] <= CENTERENDTIME)): return(True)
    return(False)

def printRoute(route):
    for trainTrip in route:
        print("%s %s %s %0.1f %0.1f %d %s %s" % (trainTrip["startTime"],trainTrip["endTime"],trainTrip["waitingTime"],trainTrip["distance"],trainTrip["lessThanBest"],int(trainTrip["averageSpeed"]),trainTrip["startStation"],trainTrip["endStation"]))

# compute the maximum (end) time for a given start time
def computeMaxTime(startTime):
    minutes = time2minutes(startTime)+time2minutes(DAYTIME)
    if not ignoreTransferSafetyTimes: minutes -= time2minutes(MAXTIMERESERVE)
    return(minutes2time(minutes))

def fillTimeDistance(startStation,startTime,endTime,distance):
    global timeDistance

    for minutes in range(0,time2minutes("25:01")):
        thisTime = minutes2time(minutes)
        if thisTime > endTime:
            keyTD = startStation+" "+startTime+" "+thisTime
            if not keyTD in timeDistance or timeDistance[keyTD] <= distance: timeDistance[keyTD] = distance
            else: return()

def findRoute(index,route,travelled,distance):
    global maxDistance,maxTime,timeDistance

    if distance > 0:
        keyTD = route[0]["startStation"]+" "+route[0]["startTime"]+" "+route[-1]["endTime"]
        if keyTD not in timeDistance or timeDistance[keyTD] < distance:
            timeDistance[keyTD] = distance
            fillTimeDistance(route[0]["startStation"],route[0]["startTime"],route[-1]["endTime"],distance)
            route[-1]["lessThanBest"] = 0.0
        if distance >= maxDistance: 
            maxDistance = distance
            printRoute(route)
            print("# largest distance : %0.1f" % (maxDistance))
    # start of route: check all stations at start time
    if len(route) == 0:
        for key in index:
            fields = key.split()
            if len(fields) < 2: 
                sys.exit(COMMAND+": incorrect key in index: "+key+"\n")
            startStation = fields[0]
            if fields[1] == globalStartTime and (firstStation == "" or startStation == firstStation):
                for endStation in index[key][startStation]:
                    for i in range(0,len(index[key][startStation][endStation])):
                        startTime = index[key][startStation][endStation][i]["startTime"]
                        if globalStartTime == TIMEZERO or startTime == globalStartTime:
                            endTime = index[key][startStation][endStation][i]["endTime"]
                            distance = index[key][startStation][endStation][i]["distance"]
                            averageSpeed = index[key][startStation][endStation][i]["averageSpeed"]
                            waitingTime = minutes2time(time2minutes(startTime)-time2minutes("00:00"))
                            maxTime = computeMaxTime(startTime)
                            track = startStation+" "+endStation
                            travelled = {track:True,reverseTrack(track):True}
                            findRoute(index,[{"startStation":startStation,"endStation":endStation,"startTime":startTime,"endTime":endTime,"distance":distance,"averageSpeed":averageSpeed,"waitingTime":waitingTime,"lessThanBest":0.0}],travelled,distance)
                    # store new time-distance data for this start station
                    writeTimeDistance(timeDistance)
    # continue a route
    else:
        prevStartStation = route[-1]["startStation"]
        startStation = route[-1]["endStation"]
        time = route[-1]["endTime"]
        key = startStation+" "+time
        for endStation in index[key][prevStartStation]:
            track = startStation+" "+endStation
            endTime = index[key][prevStartStation][endStation][0]["endTime"]
            if endTime <= maxTime:
                repeatedTrack = track in travelled
                startTime = index[key][prevStartStation][endStation][0]["startTime"]
                if len(route) == 1 and route[-1]["distance"] == 0.0:
                    maxTime = computeMaxTime(startTime)
                waitingTime = minutes2time(time2minutes(startTime)-time2minutes(route[-1]["endTime"]))
                if endStation != route[-1]["startStation"] or waitingTime >= MINRETURNWAITINGTIME or ignoreTransferSafetyTimes:
                    # add track
                    lastTrackPair = route[-1]["startStation"]+" "+route[-1]["endStation"]+" "+track
                    lastTrackPairEndTime = lastTrackPair+" "+time
                    thisDistance = 0.0
                    if not repeatedTrack:
                        travelled[track] = True
                        travelled[reverseTrack(track)] = True
                        thisDistance = index[key][prevStartStation][endStation][0]["distance"]
                        if track in partners:
                            for i in range(0,len(partners[track])):
                                if partners[track][i]["partner"] in travelled:
                                    thisDistance -= partners[track][i]["distance"]
                    distance += thisDistance
                    averageSpeed = index[key][prevStartStation][endStation][0]["averageSpeed"]
                    keyTD = route[0]["startStation"]+" "+route[0]["startTime"]+" "+endTime
                    lessThanBest = 0.0
                    if keyTD in timeDistance: lessThanBest = timeDistance[keyTD]-distance
                    route.append({"startStation":startStation,"endStation":endStation,"startTime":startTime,"endTime":endTime,"distance":thisDistance,"averageSpeed":averageSpeed,"waitingTime":waitingTime,"lessThanBest":lessThanBest})
                    # continue search
                    if centerVisited(route) and lessThanBest <= beamSize and \
                       (not lastTrackPair in transfers or waitingTime >= transfers[lastTrackPair] or ignoreTransferSafetyTimes) and \
                       (not lastTrackPairEndTime in transfers or waitingTime >= transfers[lastTrackPairEndTime] or ignoreTransferSafetyTimes):
                        findRoute(index,route,travelled,distance)
                    # delete track
                    if not repeatedTrack:
                        del travelled[track]
                        del travelled[reverseTrack(track)]
                        distance -= thisDistance
                    route.pop(-1)

def readRoute(fileName):
    global maxTime

    try: inFile = open(fileName,"r")
    except: sys.exit(COMMAND+": cannot read file "+fileName+"\n")
    route = []
    travelled = {}
    totalDistance = 0
    patternHashStart = re.compile("^#")
    patternNumberChar = re.compile("^[0-9][0-9a-z]*")
    for line in inFile:
        line = line.rstrip()
        if patternHashStart.match(line): continue
        fields = line.split()
        # expected line format: 00:02 00:15 00:02 20 0 92 rotterdamcentraal dordrecht 0
        if len(fields) < 8: sys.exit(COMMAND+": unexpected line in file "+fileName+": "+line+"\n")
        # remove final number from list (make its presence optional)
        while len(fields) > 0 and patternNumberChar.match(fields[-1]): fields.pop(-1)
        startTime = fields[0]
        if len(route) == 0: maxTime = computeMaxTime(startTime)
        endTime = fields[1]
        waitingTime = fields[2]
        distance = float(fields[3])
        totalDistance += distance
        lessThanBest = float(fields[4])
        averageSpeed = int(fields[5])
        startStation = fields[-2]
        endStation = fields[-1]
        for station in fields[-2:]:
            if not station in stations:
                sys.exit(COMMAND+": unknown station in file "+fileName+" : "+station+"\n")
        track = startStation+" "+endStation
        travelled[track] = True
        travelled[reverseTrack(track)] = True
        route.append({"startStation":startStation,"endStation":endStation,"startTime":startTime,"endTime":endTime,"distance":distance,"waitingTime":waitingTime,"averageSpeed":averageSpeed,"lessThanBest":lessThanBest})
    inFile.close()
    return({"travelled":travelled, "route":route, "distance":totalDistance})

def showSpeeds(index):
    speeds = {}
    for key1 in index:
        startStation,time = key1.split()
        for prevStartStation in index[key1]:
            for endStation in index[key1][prevStartStation]:
                key2 = startStation+" "+endStation
                if not key2 in speeds: speeds[key2] = {}
                speeds[key2][int(index[key1][prevStartStation][endStation][0]["averageSpeed"])] = True
    for key2 in speeds:
        for speed in sorted(speeds[key2],reverse=True): sys.stdout.write(str(speed)+" ")
        print(key2)

# read track pairs that share a section
def readPartners():
    partners = {}
    patternHashStart = re.compile("^#")
    try: inFile = open(PARTNERFILE,"r")
    except: sys.exit(COMMAND+": cannot read file "+PARTNETFILE+"\n")
    for line in inFile:
        line = line.rstrip()
        if patternHashStart.match(line): continue
        fields = line.split()
        if len(fields) < 5: sys.exit(COMMAND+": unexpected line in file "+PARTNERFILE+": "+line+"\n")
        station1,station2,station3,station4,distance = fields
        distance = float(distance)
        for station in fields[0:4]:
            if not station in stations:
                sys.exit(COMMAND+": unknown station in file "+PARTNERFILE+": "+station+"\n")
        if not station1+" "+station2 in partners: partners[station1+" "+station2] = []
        if not station2+" "+station1 in partners: partners[station2+" "+station1] = []
        if not station3+" "+station4 in partners: partners[station3+" "+station4] = []
        if not station4+" "+station3 in partners: partners[station4+" "+station3] = []
        partners[station1+" "+station2].append({"partner":station3+" "+station4,"distance":distance})
        partners[station2+" "+station1].append({"partner":station4+" "+station3,"distance":distance})
        partners[station3+" "+station4].append({"partner":station1+" "+station2,"distance":distance})
        partners[station4+" "+station3].append({"partner":station2+" "+station1,"distance":distance})
    inFile.close()
    return(partners)

def main(argv):
    global beamSize,doShowSpeeds,firstStation,globalStartTime,historyFile,ignoreTransferSafetyTimes,resetBestDistances
    global index,partners,stations,transfers,trainTrips,maxDistance,timeDistance,maxTime

    stations = readStations()
    options,args = getopt.getopt(argv,"b:f:hH:ins:S")
    if len(args) > 0: sys.exit(COMMAND+": unexpected extra argument: "+args[0])
    for option,value in options:
        if option == "-b": beamSize = float(value)
        elif option == "-f": firstStation = value
        elif option == "-h": help()
        elif option == "-H": historyFile = value
        elif option == "-i": 
           ignoreTransferSafetyTimes = True
        elif option == "-n": resetBestDistances = True
        elif option == "-s": globalStartTime = value
        elif option == "-S": doShowSpeeds = True
    if firstStation != "" and not firstStation in stations:
        sys.exit(COMMAND+": unknown first station: "+firstStation+"\n")
    patternTime = re.compile("^\d\d:\d\d$")
    if not patternTime.match(globalStartTime):
        sys.exit(COMMAND+": unexpected start time argument value for -s: "+globalStartTime+"\n")
    
    maxTime = computeMaxTime(globalStartTime) # needs function to be computed
    if not resetBestDistances: timeDistance = readTimeDistance()
    trainTrips = readTrainTrips()
    transfers = readTransfers()
    index = makeIndex(trainTrips,transfers)
    partners = readPartners()
    if doShowSpeeds: 
        showSpeeds(index)
        sys.exit()
       
    if historyFile == "": 
        findRoute(index,[],{},0)
    else:
        readRouteResults = readRoute(historyFile)
        findRoute(index,readRouteResults["route"],readRouteResults["travelled"],readRouteResults["distance"])
    writeTimeDistance(timeDistance)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
