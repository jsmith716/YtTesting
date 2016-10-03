'''
This is just practice stuff. 

Video quality testing script. 

Standalone script: 
    python 1.ux.py

With controller script: 
    python 1.ux.py -d ANDROID_DEVICE_ID -v VIDEO_ID -t DURATION_OF_VIDEO -o STATS_FILE -dir FILE_DIR
'''




'''
START ARGUMENTS  

These allow the script to either be a stand along script, or callable from another "controller" type script. 

Put this before the rest of the imports so it loads faster

TODO: These arguments weren't really thought out too well so I should revisit them.
'''
import argparse

parser = argparse.ArgumentParser(description='Video test script that plays through videos and calculates quality and bitrates for each test.  It can be used as a stand alone script w/out arguments, or called on from a controller scipt with arguments')

parser.add_argument('-d', action="store", dest="device_id", default="NONE", required=False,
                    help="Android device ID. You can get this from running 'adb devices'.  If not used, script will look for single device connected. ")

parser.add_argument('-v', action="store", dest="video_id", default="NONE", required=False,
                    help="The ID of the video to run.  If not used, script will use a default set of 3 videos that are hard coded w/in the script")

parser.add_argument('-t', action="store", dest="duration", default="NONE", required=False,
                    help="The time you want the video to run.  This is only necessary if you specify video_id.  If not used, script will a default of 60 seconds.")

parser.add_argument('-o', action="store", dest="output", default="NONE", required=False,
                    help="The name of the output file to save the stats to.  This is only necessary if a controller script is used so you don't get a bunch of individual files created each time it is run.")

parser.add_argument('-dir', action="store", dest="directory", default="NONE", required=False,
                    help="The subdirectory to save the files to.  This is only necessary if a controller script is used so you don't get a bunch of individual directories created each time it is run.")

# TODO: I don't know if we shoud implement this here or in the main script. 
#parser.add_argument('-video_list', action="store", dest="video_file", default="NONE", required=False,
#                    help="The name of the file with a list of videos.  The format should be video_id,duration.  If not used, we use a default set of 3 from w/in the script")

results = parser.parse_args() 
'''
END ARGUMENTS
'''



'''
START IMPORTS
'''
import subprocess
import os
import time
from sys import exit
import pandas as pd
import matplotlib.pyplot as plt
pd.options.mode.chained_assignment = None # use this to exclude warnings when adding column to dataframe
'''
END IMPORTS
'''




''' 
START QUALITY DICT

These are the qualities I see in testing.  There are a bunch more, but they aren't used for mobile so I haven't included them here.

TODO:  Ended up not using percent so should remove if we don't find a use for it
'''
quality_dict = {
    # H.264
    '133': {'resolution': '240P', 'count': 0, 'percent': 0.0},
    '134': {'resolution': '360P', 'count': 0, 'percent': 0.0},
    '135': {'resolution': '480P', 'count': 0, 'percent': 0.0},
    '136': {'resolution': '720P', 'count': 0, 'percent': 0.0}, 
    '137': {'resolution': '1080P', 'count': 0, 'percent': 0.0},
    # VP9
    '242': {'resolution': '240P', 'count': 0, 'percent': 0.0},
    '243': {'resolution': '360P', 'count': 0, 'percent': 0.0},
    '244': {'resolution': '480P', 'count': 0, 'percent': 0.0},
    '247': {'resolution': '720P', 'count': 0, 'percent': 0.0}, 
    '248': {'resolution': '1080P', 'count': 0, 'percent': 0.0},
    '264': {'resolution': '1440P', 'count': 0, 'percent': 0.0}, # H.264
    '271': {'resolution': '1440P', 'count': 0, 'percent': 0.0}
}
'''
END QUALITY DICT
'''




'''
START SUBPROCESS FUNCTION

Subprocess for any command.  Prefer this over writing the same thing every time

TODO: split this up so we don't need if - e.g. 2 subprocess functions depending on command requirement
'''
def subprocess_command(cmd):
    if "exo" not in cmd and "youtube" not in cmd and "devices" not in cmd and "ifconfig" not in cmd: 
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return process
    else: 
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        proc_out  = process.communicate()[0]
        proc_out = proc_out.split('\n')
        return proc_out
'''
END SUBPROCESS FUNCTION
'''




'''
START ARG PARSE


Check to see if arguments are used.  If they aren't, then use default values hard coded w/in the scipt.

Video ARG
Duration ARG 
Device ARG
Directory ARG
Output ARG

'''
# Run COUNT

# Video ARG
if results.video_id == "NONE": 
    video_list = ['v_HVmFA47w0, 61', 'z4UDNzXD3qA, 71', 'GzZezqJ9VgI, 39']
    run_count = 0 # Controls number of runs in main loop - 0 = run until killed
else: 
    if results.duration == "NONE": # Duration ARG - only needed if video_id isn't used
        duration = 60
    else: 
        duration = results.duration
    run_count = 1 # Controls number of runs in main loop - 1 = 1 run
    video_list = [results.video_id, duration] 

# Device ARG
if results.device_id == "NONE": 
    device_list = []
    get_devices = 'adb devices'
    device_list = subprocess_command(get_devices)
    device_list = device_list[1].split('\t')[0]
    device_id = device_list 
else: 
    device_id = results.device_id
    run_count = 1 # Controls number of runs in main loop - 1 = 1 run

# Directory ARG
if results.directory == "NONE":
    dir_name = str(int(time.time())) + "\\" + device_id

else: 
    dir_name = results.directory + "\\" + device_id

# Output ARG
if results.output == "NONE":
    out_file = str(int(time.time())) + "." + device_id + '.csv'
else: 
    out_file = results.output

'''
END ARG PARSE
'''




'''
START SHELL SCRIPT FUNCTION

Creates shell script that can be executed on any android device to collect network usage per app UID

TODO: There is another way of collecting these stats from android that we should look into in the event that this changes
'''
def create_xtag_script(count, uid, duration, int_type):
    duration = str(duration)
    with open('xt_qtag.sh', 'wb') as f: # Needed b since WIN uses \r\n line endings rather than just \n
        f.write('count=-5\n')
        f.write('while [ "$count" -lt "' + duration + '" ]\n')
        f.write('do\n')
        f.write('        tStat=$(cat /proc/net/xt_qtaguid/stats | grep "' + int_type + ' 0x0 ' + uid + ' 1" | egrep -v "v4-rmnet_data0")\n')
        f.write('        tDate=$(date +%s)\n')
        f.write('        echo $tDate " " $tStat >>  /sdcard/' + count + '.xt_qtag\n')
        f.write('        sleep .95\n') # need to do a better job here.  Using .95 as a temp hack
        f.write('        let count=count+1\n')
        f.write('done\n')
    f.close()
'''
END SHELL SCRIPT FUNCTION
'''




'''
START SCRIPT PREP - RUN ONCE

UID:  Gets the UID for the android app we are testing.  This can be any app, but we're hard coding YouTube for now

DIR:  Checks if output directory exists, and then creates it if it doesn't.  output directory determined above in ARG PARSE 

BASE:  Sets youtube base URL

CACHE:  Sets YouTube cache directory.  This is required so we can see what qualities played

INT_CHECK:  Checks of rmnet0 or rmnet_data0 is used w/in the device.  This is required since some devices alternate
'''
# UID
uid = []
get_uid = 'adb -s ' + device_id + ' shell dumpsys package com.google.android.youtube'
uid.extend(subprocess_command(get_uid))
for line in uid:
    if 'userId' in line:
        uid = line.split('=')[1].strip('\r')

# DIR
if not os.path.exists(dir_name):
    os.makedirs(dir_name)

# BASE
video_base_url = 'https://www.youtube.com/watch?v='

# CACHE
get_cache_dir = 'adb -s ' + device_id + ' shell ls -R /sdcard/ | grep "cache/exo"'
cache_dir = subprocess_command(get_cache_dir)[0].strip(':\r') + '/'

# INT_CHECK
check_uid = 'adb -s ' + device_id + ' shell ifconfig rmnet_data0'
uid_type = subprocess_command(check_uid)
if "No such device" in uid_type[0]:
    int_type = 'rmnet0'
else: 
    int_type = 'rmnet_data0'
'''
END SCRIPT PREP - RUN ONCE
'''




'''
START EXO ANALYSIS FUNCTION

EXO is youtube's cache.  The file names of EXO tell you the size, timestamp and quality of each video segment.

Goes through each line of exo file and counts the quality.  Once it has counted each line, it calculates the percent

Note that EXO only exists in YT so we'll need to ignore if we extend to NF or another app.  NF has a diff way to get quality
'''
def analyze_exo(dir_name, count):
    with open(dir_name + '\\' + str(count) + '.exo', 'rU') as f:
        temp_count = 0
        for line in f:
            if 'exo' in line:
                itag = line.split('.')[1]
                file_size = line.split('.')[3] # Corrects quality count     q
                for key in quality_dict.keys():
                    if itag == key and file_size > 1000:
                        quality_dict[key]['count'] += 1 # Counts the number of times each quality is seen from cache dump
                        temp_count += 1

    for key in quality_dict.keys():
        quality_count = quality_dict[key]['count']
        if quality_count > 0:
            #quality_dict[key]['percent'] = quality_count / float(temp_count) * 100 # Calculates the % for each quality seen
            percent = str(quality_count / float(temp_count) * 100) # Calculates the % for each quality seen
            quality = quality_dict[key]['resolution']
            q.append(quality + ": " + percent + '%')
            quality_dict[key]['count'] = 0 # resets quality_dict items to 0 for next run
'''
END EXO ANALYSIS FUNCTION
'''




'''
START XT ANALYSIS FUNCTION

xt_qtag is a way of seeing how much data is being transferred per the app's UID.

There is another way of getting this that is much simpler, but I need to find it.

Note that I split EXO and XT into two functions since EXO is YT specific, but XT is not
'''
def analyze_xt(dir_name, count, video_id, device_id, duration):
    file_ =  dir_name + "\\" + str(count) + ".xt_qtag"
    df = pd.read_csv(file_, delim_whitespace=True, usecols=[0,6]) # Only need timestamp and DL bytes.  Aren't actually using TS, but may in the future 
    df.columns = ['epoch', 'dl_bytes']
    df['mbps'] = ((df['dl_bytes'] - df['dl_bytes'].shift()) * 8.0 / 1000/1000) # Adds another column  to the dataframe
    avg_mbps = round(df.mbps[df.mbps > .1].mean(), 2)
    max_mbps = round(df.mbps[df.mbps > .1].max(), 2)
    title_quality = '/'.join(q) # Joins all the qualities seen from the EXO directory separated by a / into a single variable 
    df = df.mbps
    if avg_mbps > 0.1:  # Ignore tests that fail
        df.plot()
        plt.ylabel('mbps')
        plt.xlim([0, duration])
        # Added this to add some sort of consistancy to the graphs. 
        for mbps in 10, 20, 30, 40, 50, 70, 90, 110:
            if max_mbps <= mbps:
                plt.ylim([0, mbps])
                break
            elif max_mbps > 110: 
                plt.ylim([0, max_mbps])
                break
        plt.xlabel('time in seconds')
        plt.title('Video: ' + video_id + ' / AVG Mbps: ' + str(avg_mbps) + '\n' + title_quality)
        filename = file_ + '.' + video_id + '.' + device_id + '.IMG.png'
        plt.savefig(filename)
        plt.close()
    with open(out_file, 'a') as f:
        if count == 0:
            f.write("count,device_id,video_id,quality1,quality2\n")
        f.write(str(count) + ',' + device_id + ',' + video_id + ',' + title_quality.replace('/', ',') + '\n')
    f.close()

'''
END XT ANALYSIS FUNCTION
'''




'''
START TEST FUNCTION

'''
def run_test(device_id, cache_dir, dir_name, uid, count, duration, video_id, test_url, int_type):
    count = str(count)
    get_cache = 'adb -s ' + device_id + ' shell ls ' + cache_dir
    del_cache_v = 'adb  -s ' + device_id + ' shell rm ' + cache_dir + video_id + '.2*'
    del_cache_h = 'adb  -s ' + device_id + ' shell rm ' + cache_dir + video_id + '.13*'
    push_xtag = 'adb -s ' + device_id + ' push xt_qtag.sh /sdcard/'
    start_xtag = 'adb -s ' + device_id + ' shell sh /sdcard/xt_qtag.sh'
    pull_xtag = 'adb -s ' + device_id + ' pull /sdcard/' + count + '.xt_qtag ' + dir_name + '\\' + count + '.xt_qtag'
    remove_xtag = 'adb -s ' + device_id + ' shell rm /sdcard/' + count + '.xt_qtag'
    close_app = 'adb -s ' + device_id + ' shell input keyevent 4'
    start_video = 'adb -s ' + device_id + ' shell am start -a android.intent.action.VIEW -d ' + test_url

    subprocess_command(remove_xtag)
    subprocess_command(del_cache_v)
    subprocess_command(del_cache_h)
    create_xtag_script(count, uid, duration, int_type)
    subprocess_command(push_xtag)
    subprocess_command(close_app)
    time.sleep(1)
    subprocess_command(start_xtag)
    time.sleep(2)
    subprocess_command(start_video)
    time.sleep(duration)
    subprocess_command(close_app)
    subprocess_command(close_app)
    subprocess_command(pull_xtag)
    time.sleep(1)
    video_cache = []
    video_cache.extend(subprocess_command(get_cache))
    with open(dir_name + '\\' + count + '.exo', 'w') as f:
        for lines in video_cache:
            if video_id + '.2' in lines or video_id + '.13' in lines:
                f.write(lines)
'''
END TEST FUNCTION
'''




'''
START MAIN LOOP
'''
count = 0
while True: 
    for lines in video_list:
        q = []
        line = lines.split(',')
        try: 
            duration = line[1].strip(' ')
            duration = int(duration)
        except:
            duration = int(duration)
        video_id = line[0]
        test_url = video_base_url + video_id
        run_test(device_id, cache_dir, dir_name, uid, count, duration, video_id, test_url, int_type)
        analyze_exo(dir_name, count)
        analyze_xt(dir_name, count, video_id, device_id ,duration)
        time.sleep(10)
        count+=1
        if run_count == 1:
            exit(0)
'''
END MAIN LOOP
'''
