import datetime
import pytz
import json
import os
#import pynmea2
import datetime

WIFIDup = 0
WIFILong = 0
WIFIGood = 0
interval = 6
NMEAGood = 0
NMEAExcept = 0


def parseGrandNewFile(fileName):
    data = list()
    dataFile = open(fileName, "r")

    trackDataString=""
    for line in dataFile:
        if "*"*32 not in line:
            trackDataString = trackDataString + line
        else:
            # is each record unique
            r = set()
            indexToPop = set()
            newRecord = json.loads(trackDataString)
            for recordIndex in range(len(newRecord["subpoints"])):
                record = newRecord["subpoints"][recordIndex]
                recordString = str(record["timestamp"]) + record["source"] + str(record.keys())
                if recordString in r:
                    indexToPop.append(recordIndex)
                    print("Duplicate for " + recordString)
            for num in sorted(list(indexToPop), reverse = True):
                newRecord["subpoints"].pop(num)


            data.append(json.loads(trackDataString))
            trackDataString = ""
    return data

tracking = {}
#tracking = parseGrandNewFile("tracking_raw_old.txt")


def addToData(subPoint, addNew=True):


    t = datetime.datetime.fromtimestamp( int(float(subPoint["timestamp"])), datetime.timezone.utc)
    dateString = "{:04}-{:02}-{:02}".format( t.year, t.month, t.day)
    if dateString not in tracking:
        tracking[dateString] = []


    inTracking=False
    for t in tracking[dateString]:
        if float(subPoint["timestamp"]) >= t["timestamp"] and float(subPoint["timestamp"]) < t["timestamp"] + interval:
            repeat=False
            for y in t["subpoints"]:
                if y==subPoint:
                    repeat=True
                    print("Found repeat in " + subPoint["measurement type"])
            if not repeat:
                t["subpoints"].append(subPoint)
            inTracking=True
            break
    if not inTracking and addNew:
        print("Adding new, interval: {}".format(interval))
        newTracking = { "timestamp" : None, "subpoints": None}
        newTracking["timestamp"] = (float(subPoint["timestamp"]) // interval) * interval
        newTracking["subpoints"] = list()
        newTracking["subpoints"].append(subPoint)
        newTracking["interval"] = interval
        tracking[dateString].append(newTracking)



files = os.listdir("data_files/") 

for f in range(len(files)):
    files[f] = "data_files/" + files[f] 

#for f in os.listdir("data_logger_data/"):
#    files.append( "data_logger_data/" + f )

for f in files:
    if "data_logger_data" in f:
        GPSfile = open(f)
        GPSfile.readline()
        currentData = { "timestamp" : -100 }

        for line in GPSfile:
            aaaa="""
            if line[0] == "$":
                try:
                    d = pynmea2.parse(line)
                except:
                    print("Exception! -- " + line)
                    NMEAExcept = NMEAExcept + 1
                else:
                    NMEAGood = NMEAGood + 1
                    if hasattr( d, "timestamp"):
                        if currentData["timestamp"] != d.timestamp:
                            if "datestamp" in currentData.keys() and currentData["timestamp"] != -100 and "accuracy, horizontal" in currentData.keys() and type(currentData["accuracy, horizontal"]) == type(float()) and currentData["accuracy, horizontal"] > 1 and "latitude" in currentData.keys() and "longitude" in currentData.keys() and not ( "satellites, used" in currentData.keys() and currentData["satellites, used"] < 4):
                                # save currentData
                                timestamp = (86400 * (-datetime.date(1970,1,1).toordinal() + currentData["datestamp"].toordinal()) + currentData["timestamp"].hour * 3600 +
                                             currentData["timestamp"].minute*60 + currentData["timestamp"].second)
                                currentData.pop( "datestamp" )
                                currentData["timestamp"] = timestamp

                                subPoint = {}
                                subPoint["timestamp"] = timestamp
                                subPoint["source"] = "GT-U7 gps module"
                                subPoint["measurement type"] = "location - gps"
                                subPoint["data"] = [ currentData ]
                                addToData(subPoint, addNew=False)
                                print(subPoint)
                            currentData = { "timestamp" : d.timestamp }


                    if hasattr( d, "datestamp") and d.datestamp and d.datestamp != "" and type(d.datestamp) == type(datetime.date(1970,1,1)):
                        currentData["datestamp"] = d.datestamp

                    if hasattr( d, "latitude") and d.latitude and d.latitude != "":
                        try:
                            currentData["latitude"] = float(d.latitude)
                        except:
                            print("lat except")

                    if hasattr( d, "longitude") and d.longitude and d.longitude != "":
                        try:
                            currentData["longitude"] = float(d.longitude)
                        except:
                            print("lon except")

                    if hasattr( d, "spd_over_grnd_kmph") and d.spd_over_grnd_kmph != None and d.spd_over_grnd_kmph != "":
                        try:
                            currentData["speed"] = float(d.spd_over_grnd_kmph) / 3.6
                        except:
                            print("speed except")

                    if hasattr( d, "num_sats") and d.num_sats and d.num_sats != "":
                        try:
                            currentData["satellites, used"] = int(d.num_sats)
                        except:
                            print("Exception, number of satellites:" + str(d.num_sats))
                            if "satellites, used" in currentData.keys():
                                currentData.pop("satellites, used")

                    if hasattr(d, "alt_ref") and d.alt_ref and d.alt_ref != "":
                        try:
                            currentData["altitude"] = float(d.alt_ref)
                        except: 
                            print("alt except")

                    if hasattr( d, "cog") and d.cog and d.cog != "":
                        try:
                            cog = float(d.cog)
                        except: 
                            print("cog except")
                        else:
                            if(float(cog) > 0):
                                currentData["bearing"] = float(d.cog)

                    if hasattr( d, "h_acc") and d.h_acc and d.h_acc != "":
                        try:
                            currentData["accuracy, horizontal"] = float(d.h_acc)
                        except:
                            print("h-a except")


                    if hasattr( d, "v_acc") and d.v_acc and d.v_acc != "":
                        try:
                            currentData["accuracy, vertical"] = float(d.v_acc)
                        except:
                            print("v_c except")"""



    if "PIXEL4" in f.upper() or "PIXEL 4" in f.upper():
        source = "Pixel 4"
    if "GALAXY" in f.upper():
        source = "Galaxy 5"
    if "PIXEL3XL" in f.upper() or "PIXEL 3 XL" in f.upper():
        source = "Pixel 3 XL"
    if False and "GPS" in f.upper():
        GPSfile = open(f)
        GPSfile.readline()
        for line in GPSfile:
            line = line.split(",")
            if len(line[1]) == 19:
                timestamp = datetime.datetime.strptime(line[1], "%Y-%m-%d %H:%M:%S")
            if len(line[1]) == 23:
                timestamp = datetime.datetime.strptime(line[1], "%Y-%m-%d %H:%M:%S.%f")
            timestamp = pytz.timezone("UTC").localize(timestamp)
            print( f + " " + str(pytz.timezone("UTC").localize(datetime.datetime.utcfromtimestamp(timestamp.timestamp()) ).astimezone(pytz.timezone("US/Central") ) ))
            subPoint = {}
            subPoint["timestamp"] = timestamp.timestamp()
            subPoint["source"] = source
            subPoint["measurement type"] = "location - gps"
            subPoint["data"] = [ { "latitude" : line[2],
                                    "longitude": line[3],
                                    "accuracy, horizontal" : line[4],
                                    "altitude" : line[5],
                                    "speed"    : line[7],
                                    "satellites, used" : line[9],
                                    "satellites, in view" : line[10] } ]
            addToData(subPoint)
        GPSfile.close()

    if False and "WIFI" in f.upper():
        WIFIfile = open(f)

        upTime = None
        wifiString=""
        lastWifi = None
        nowTime = None
        zeroScans = 0
        x=0
        for line in WIFIfile:
            x=x+1
            if wifiString[-2:] == "]\n":
                if upTime == None:
                    upTime = float(line)
                    line=""
                else:
                    if nowTime == None:
                        nowTime = float(line)
                        line=""
                    else:

                        #else:

                        try:
                            wifiData = json.loads(wifiString)
                        except json.JSONDecodeError:
                            print("JSONDecodeError -- line 113")
                            print(wifiString)
                        if len(wifiData) == 0:
                            zeroScan = zeroScan + 1
                        else:
                            zeroScan = 0
                        # we'll let it do 10 zero scans, otherwise it can get stuck on zero
                        if (len(wifiData) == 0 and zeroScan < 2000) or wifiData != lastWifi:

                            keyConverter = { "frequency_mhz": "frequency",
                             "channel_bandwidth_mhz": "bandwidth",
                             "center_frequency" : "frequency, center",
                             "ssid" : "SSID",
                             "bssid": "BSSID",
                             "rssi": "level" }

                            newWifiData = [] 

                            for w in wifiData:
                                element = {}
                                for ky in w.keys():
                                    if ky in keyConverter.keys():
                                        element[ keyConverter[ky] ] = w[ky]
                                    else:
                                        element[ ky ] = w[ky]
                                element["bandwidth"] = element["bandwidth"]+"Mhz"
                                newWifiData.append(element)

                            wifiData = newWifiData


                            lastWifi = wifiData
                            #find range
                            minStamp = 0
                            maxStamp = 1e100
                            for w in wifiData:
                                if int(w["timestamp"])//1000000 >= minStamp:
                                    minStamp = int(w["timestamp"])//1000000
                                if int(w["timestamp"])//1000000 <= maxStamp:
                                    maxStamp = int(w["timestamp"])//1000000

                            for i in range(len(wifiData)):
                                wifiData[i]["timestamp"] = int(wifiData[i]["timestamp"]) /1000000 + upTime
                            if minStamp - maxStamp < 15: 
                                subPoint = {}
                                subPoint["timestamp"] = upTime + minStamp
                                if len(wifiData) == 0:
                                    zeroScan = zeroScan + 1
                                    #subPoint["timestamp"] = float(line)
                                    subPoint["timestamp"] = nowTime


                                print( f + ":" + str(x) + " N=" + str(len(wifiData)) + " " +  str(pytz.timezone("UTC").localize(datetime.datetime.utcfromtimestamp(subPoint["timestamp"]) ).astimezone(pytz.timezone("US/Central") )) )
                                subPoint["source"] = source
                                subPoint["data"] = wifiData
                                subPoint["measurement type"] = "wifi scan"
                                WIFIGood = WIFIGood + 1


                                addToData(subPoint)
                            else:
                                print("WIFI Long")
                                WIFILong = WIFILong + 1
                        else:
                            print( f + " : Duplicate, Skip ")
                            WIFIDup = WIFIDup + 1
                        upTime = None
                        nowTime = None

                        wifiString=""

            wifiString = wifiString + line
        WIFIfile.close()

    if "SPECIFIED" in f.upper():
        locationsFile = open(f).readlines()
        locations = list()
        for x in range( len( locationsFile ) // 3 ):
            locations.append( { "name" : locationsFile[x*3][:-1],
                                "start time" : int( locationsFile[x*3 + 1] ),
                                "end time"   : int( locationsFile[x*3 + 2] ) } )
        for location in locations:
            for timestamp in range(  ((location["start time"] // interval) + 1) * interval,
                                     (location["end time"] // interval) * interval,
                                     interval ):
                location["context"] = location["name"].split(":")[0]
                location["label"] = location["name"].split(":")[1]

                print( f + " " + str(location["name"]) + " " + str(pytz.timezone("UTC").localize(datetime.datetime.utcfromtimestamp(timestamp) ).astimezone(pytz.timezone("US/Central") ) ))


                subPoint = {}
                subPoint["source"] = source
                subPoint["measurement type"] = "specified location"
                subPoint["data"] = [ { "label" : location["label"],
                                       "context" : location["context"] } ]
                subPoint["timestamp"] = timestamp

                addToData(subPoint)

    if "DATA" in f.upper() or "RASBERRY" in f.upper():
        DATAFile = open(f)
        JSONstring = ""
        line=DATAFile.readline()
        while len(line) > 0:
            if "*"*32 in line:
                Data = []
                try:
                    Data = json.loads(JSONstring)
                except json.JSONDecodeError:
                    print("JSONDecodeError -- DATA")
                    print(JSONstring)

                if len(Data) > 0:
                    if "sensor" in Data.keys():
                        measurementType = { "SCD30" : "science - air",
                                            "SHT40" : "science - air",
                                            "SGP30" : "science - air",
                                            "PM25AQI" : "science - air",
                                            "SCD40" : "science - air" }
                        measType = measurementType[Data["sensor"]]
                        ts = Data.pop("timestamp")
                        newData = { "source" : "Air Science Module",
                                    "timestamp" : ts,
                                    "measurement type" : measType,
                                    "data" : [ Data ] }
                        Data = newData



                    timestamp = int(float(Data["timestamp"]))
                    if "measurement type" not in Data.keys():
                        print("No measurement type.")
                        print(f)
                        print(Data)
                        exit()
                    print(f+ "" + str(pytz.timezone("UTC").localize(datetime.datetime.utcfromtimestamp(timestamp) ).astimezone(pytz.timezone("US/Central") )) + ":" + Data["measurement type"] + " n=" + str(len(Data["data"]))) 

                    if Data["measurement type"] == "specified location" and Data["data"][0]["label"].upper() != "TEST":

                        location = Data["data"][0]
                        if "start" in location.keys():
                            location["start time"] = location["start"]
                            location["end time"] = location["end"]


                        print(location)
                        for timestamp in range(  ((int(float(location["start time"])) // interval) + 1) * interval,
                                                 (int(float(location["end time"])) // interval) * interval,
                                                 interval ):

                            print( f + " " + str(location["context"]) + ":" + str(location["label"]) + " " + str(pytz.timezone("UTC").localize(datetime.datetime.utcfromtimestamp(timestamp) ).astimezone(pytz.timezone("US/Central") ) ))
                            subPoint = {}
                            subPoint["source"] = source
                            subPoint["measurement type"] = "specified location"
                            subPoint["data"] = [ { "label" : location["label"],
                                                   "context" : location["context"] } ]
                            subPoint["timestamp"] = timestamp

                            addToData(subPoint)
                    else:
                        subPoint = Data

                        addToData(subPoint)
                        timeStamp = None

                JSONstring=""
                line=DATAFile.readline()
            else:
                JSONstring = JSONstring + line
                line=DATAFile.readline()


print("Writing Output")

for date_key in tracking.keys():
    for record in sorted(tracking[date_key], key = lambda x:x["timestamp"]):

        data = record
        t = datetime.datetime.fromtimestamp( data["timestamp"], datetime.timezone.utc)
        print("Writing "+ t.isoformat() )
        fileName = "{:04}-{:02}-{:02}_unsorted.txt".format( t.year, t.month, t.day)

        outputFile = open("data_file_library/" + fileName,"a")
        outputFile.write(json.dumps(data,indent=3,sort_keys=True))
        outputFile.write("\n" + "*"*32 + "\n")
        outputFile.close()

        
print("---- NMEA ----\n {} GOOD, {} BAD".format(NMEAGood, NMEAExcept))
print("---- WIFI ----\n {} GOOD, {} LONG, {} DUP".format(WIFIGood, WIFILong, WIFIDup))
