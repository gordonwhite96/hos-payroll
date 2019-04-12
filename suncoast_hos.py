#
#
# Sun Coast Resources HOS 
#
# 10 December 2018
# Gordon White / gordon@samsara.com
#
# Purpose: pull Samsara API HOS data and output CSV
#from datetime import timedelta, datetime, time
import datetime as dt
import time
from datetime import timedelta
import config
import requests
import json
import collections
import csv
import sys

debug=False

def get_times():
    midnight = dt.datetime.combine(dt.datetime.today() - timedelta(days=6), dt.time.min)
    yesterday_midnight = midnight - timedelta(days=1)
    startms =  int(time.mktime(yesterday_midnight.timetuple()) * 1000)+1
    endms = int(time.mktime(midnight.timetuple()) * 1000)-1
    #print startms, endms
    return (startms, endms)

def getdrivers(token, group):
    d={}
    params = ( ('access_token', token),)
    groupId = group
    postdata = '{"groupId":'+group+'}'
    driver = requests.post('https://api.samsara.com/v1/fleet/drivers',
           params=params, data=postdata)
    data = json.loads(driver.text)
    for driver in data['drivers']:
        driverid=driver['id']
        d[driverid]=driver['name']
    return d

def getdriverusername(token, driverid):
    d={}
    params = ( ('access_token', token),)
    driver = requests.get('https://api.samsara.com/v1/fleet/drivers/'+str(driverid),
           params=params)
    data = json.loads(driver.text)
    return data["username"]

def get_vehicles(token,group):
    d={}
    params = ( ('access_token', token),)
    groupId = group
    postdata = '{"groupId":'+group+'}'
    vehiclelist = requests.post('https://api.samsara.com/v1/fleet/list', 
            params=params, data=postdata)
    data = json.loads(vehiclelist.text)
    for vehicle in data['vehicles']:
        vid=str(vehicle['id'])
        d[vid]=vehicle['name']
    return d

def getlogs(token, group, driverid, startms, endms):
    d={}
    params = ( ('access_token', token),)
    groupId = group
    postdata = '{"groupId":'+group+',"driverID":'+str(driverid)+',\
    "startMs":'+str(startms)+',"endMs":'+str(endms)+'}'
    logs = requests.post('https://api.samsara.com/v1/fleet/hos_logs',
           params=params, data=postdata)
    if not logs.text:
        print "Error log", logs
        d=0
        return d
    try:
        data = json.loads(logs.text)
        i=0;
        for log in data['logs']:
            d[i]={"startms":log['logStartMs'],"status":log['hosStatusType'],\
            "vid":log['vehicleId']}
            i=i+1
        return d
    except:
        print "failed getting logs"
        return 0

def processlogs(logs,vehicles,fname,lname,username,drivew,commutew):
    oldstatus=''
    for k,log in logs.items():
        s = log['startms']/1000
        datestamp=dt.datetime.fromtimestamp(s).strftime('%Y-%m-%d')
        timestamp=dt.datetime.fromtimestamp(s).strftime('%H:%M:%S')
        vid=str(log['vid'])
        if vid=='0':
            vname=''
        else:
            try:
                vname=vehicles[vid]
            except KeyError as e:
                print "got an error"
                vname='UNKNOWN'
        if log['status']==oldstatus:
            pass
        elif len(logs)<2 and log['status']=='OFF_DUTY':
            pass
        elif log['status']=='ON_DUTY' and oldstatus=='DRIVING':
            pass
        elif log['status']=='DRIVING' and oldstatus=='ON_DUTY':
            pass
        elif log['status']=='OFF_DUTY' and oldstatus=='':
            pass
        else:
            vid=str(log['vid'])
            if vid=='0':
                vname=''
            else:
                try:
                    vname=vehicles[vid]
                except KeyError as e:
                    vname='UNKNOWN'
            if log['status']=='ON_DUTY' or log['status']=='DRIVING':
                # going on duty
                if vname == 'On Duty - Commuting':
                    csvfile=commutew
                else:
                    csvfile=drivew
                inout=1
            elif log['status']=='OFF_DUTY':
                # going off duty
                inout=2
            else:
                inout=3
            csvfile.writerow({'Punch Date': datestamp,\
            "Punch Time":timestamp,"First Name":fname,"Last Name":lname,\
            "In Out":inout,"Job Number":vname,"Card":username})
        oldstatus=log['status']

def main():
    times=get_times()
    vehicles=get_vehicles(config.token, config.group)
    alldrivers = getdrivers(config.token, config.group)
    print "Found: %d drivers" % len (alldrivers)
    drivefile= dt.datetime.strftime(dt.datetime.now() - timedelta(2), '%Y-%m-%d')+'.csv'
    commuterfile= dt.datetime.strftime(dt.datetime.now() - timedelta(2), '%Y-%m-%d')+'-commute.csv'
    outDrive=open(drivefile, 'w')
    outCommute=open(commuterfile, 'w')
    with outDrive, outCommute:
        myFields=["Punch Date","Punch Time","First Name","Last Name","Middle Name","Card","Download ID","In Out","Job Number"]
        drivewriter = csv.DictWriter(outDrive, fieldnames=myFields)
        commutewriter = csv.DictWriter(outCommute, fieldnames=myFields)
        drivewriter.writeheader()
        commutewriter.writeheader()
        for driverid,name in alldrivers.items():
            dname=name.split()
            fname=dname[0]
            if len(dname) == 1:
                lname = ' '
            elif len(dname)>2: 
                lname = dname[1]+' '+dname[2]
            else:
                lname=dname[1]
            username=getdriverusername(config.token, driverid)
            logs = getlogs(config.token, config.group, driverid, times[0], times[1])
            sortedlogs = collections.OrderedDict(sorted(logs.items()))
            processlogs(sortedlogs,vehicles,fname,lname,username,drivewriter,commutewriter)
if __name__ == "__main__":
    main()
