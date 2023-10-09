#!/usr/bin/env python3
# convert_schedule.py: convert NS 2023 schedule to 2019 format
# usage: convert_schedule.py < text_data
# note: text_data copied and pasted from ns.nl (page style: none)
# 20230910 erikt(at)xs4all.nl

import re
import sys

def add_day(day_time):
    hours, minutes = day_time.split(":")
    hours = int(hours) + 24
    return f"{hours}:{minutes}"

next_day_started = False
lines = sys.stdin.readlines()
for i in range(0, len(lines)):
    line = lines[i]
    line = re.sub("^Alternatief\s+vervoer\s+", "", line)
    line = re.sub("^Werkzaamheden\s+", "", line)
    line = line.strip()
    if re.search("^vertrek\s", line) and not re.search("[bB]us", line):
        if i < len(lines) - 1 and not re.search("vertrek", lines[i+1]):
            line += lines[i+1].strip()
            i += 1
        if i < len(lines) - 1 and not re.search("vertrek", lines[i+1]):
            line += lines[i+1].strip()
            i += 1
        if i < len(lines) - 1 and not re.search("vertrek", lines[i+1]):
            line += lines[i+1].strip()
            i += 1
        if not re.search('\+', line):
            line_parts = line.split()
            start_time = line_parts[1]
            end_time = line_parts[3]
            if next_day_started:
                start_time = add_day(start_time)
                end_time = add_day(end_time)
            if end_time < start_time:
                end_time = add_day(end_time)
            nbr_of_transfers = 0
            if line_parts[6] == "met":
                nbr_of_transfers = line_parts[7]
            print(f"{start_time}\n{end_time}\n{nbr_of_transfers}\n0:00")
    if re.search("zondag", line):
        next_day_started = True
    if re.search("maandag", line):
        print(f"Warning: unexpected date! {line}", file=sys.stderr)
    if re.search("naar [A-Z]", line):
        print(line, file=sys.stderr)

