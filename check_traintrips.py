#!/usr/bin/env python3
# check_traintrips.py: sanity checks for the file traintrips.txt
# usage: check_traintrips.py
# 20230913 erikt(at)xs4all.nl

import re
import sys

DATA_FILE_NAME = "traintrips.txt"

def subtract_times(start_time, end_time, track):
    try:
        start_hour, start_minute = start_time.split(":")
        end_hour, end_minute = end_time.split(":")
    except:
        sys.exit(f"time format error for:{start_time} {end_time} {track}")
    return 60 * (int(end_hour) - int(start_hour)) + int(end_minute) - int(start_minute)


def read_data(data_file_name=DATA_FILE_NAME):
    data_file = open(data_file_name, "r")
    track = ""
    travel_times = {}
    tracks = {}
    for line in data_file:
        if re.search("^#", line):
            fields = line.strip().split()
            track = f"{fields[2]} {fields[3]}"
        else:
            start_time = line.strip()
            end_time = data_file.readline().strip()
            nbr_of_minutes = subtract_times(start_time, end_time, track)
            data_file.readline()
            data_file.readline()
            travel_time = f"{start_time} {end_time}"
            if travel_time not in travel_times:
                travel_times[travel_time] = []
            travel_times[travel_time].append(track)
            if track not in tracks:
                tracks[track] = []
            if nbr_of_minutes not in tracks[track]:
                tracks[track].append(nbr_of_minutes)
    return travel_times, tracks


def show_travel_times(travel_times):
    pairs = {}
    for travel_time in travel_times:
        if len(travel_times[travel_time]) > 1:
            for track_1 in travel_times[travel_time]:
                for track_2 in travel_times[travel_time]:
                    if track_1 != track_2:
                        pair = f"{track_1} {track_2}"
                        if pair not in pairs:
                            pairs[pair] = 0
                        pairs[pair] += 1
    for pair in pairs:
        print(f"{pairs[pair]} {pair}")


def find_gaps():
    data_file = open(DATA_FILE_NAME, "r")
    last_start_time = "00:00"
    track = ""
    for line in data_file:
        if re.search("^#", line):
            last_hour = int(last_start_time.split(":")[0])
            if last_hour < 23:
                print(f"last hour is too small: {last_start_time} {track}")
            fields = line.strip().split()
            track = f"{fields[2]} {fields[3]}"
            last_start_time = "00:00"
        else:
            start_time = line.strip()
            end_time = data_file.readline().strip()
            data_file.readline()
            data_file.readline()
            this_hour = int(start_time.split(":")[0])
            last_hour = int(last_start_time.split(":")[0])
            if this_hour < last_hour:
                print(f"hour is too small: {last_start_time} {start_time} {track}")
            elif this_hour > last_hour + 1:
                print(f"hour is too large: {last_start_time} {start_time} {track}")
            last_start_time = start_time


# travel_times, tracks = read_data()

# show_travel_times()

# for track in tracks:
#     if len(tracks[track]) < 3:
#         print(track, tracks[track])

find_gaps()
