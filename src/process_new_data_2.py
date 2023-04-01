import datetime
import pytz
import json
import os
#import pynmea2
import datetime

# Find a file that needs processing.

files = os.listdir("data_file_library/")
fileToProcess = None
for f in files:
    if "unsorted" in f:
        fileToProcess = "data_file_library/"+f

if fileToProcess == None:
    print("Processing complete.")
    exit()

print("Processing file " + fileToProcess)

unsortedFile = open(fileToProcess, "r")
sortedFileName = fileToProcess[:-13] + ".txt"
if os.path.exists( sortedFileName):
    sortedFile = open(sortedFileName, "r")
else:
    sortedFile = None

def readNextData(dataFile):
    trackDataString=""
    line = ""
    while ( "*"*32 not in line):
        trackDataString = trackDataString + line
        line = dataFile.readline()
        if line == "":
            return dict()
    data = json.loads(trackDataString)
    data["timestamp"] = float(data["timestamp"])
    data["interval"] = int(data["interval"])
    for subpoint in data["subpoints"]:
        subpoint["timestamp"] = float(subpoint["timestamp"])
        floatKeys = [ "latitude", "longitude", "accuracy, horizontal", "accuracy, vertical", "altitude", "timestamp", "level" ]
        for d in subpoint["data"]:
            for key in floatKeys:
                if key in d.keys():
                    d[key] = float(d[key])


    return data


# load sorted file into memory

sortedData = []
if sortedFile:
    data = readNextData(sortedFile)
    while( data ):
        t = datetime.datetime.fromtimestamp( data["timestamp"], datetime.timezone.utc)

        print("Reading..."+ t.isoformat() )
        sortedData.append(data)
        data = readNextData(sortedFile)

def addToData(data, addNew=True):
    
    inData = False
    for d in sortedData:
        if d["timestamp"] == data["timestamp"]:
            # merge
            for subpoint in data["subpoints"]:
                repeat=False
                specified=False
                for dsub in d["subpoints"]:
                    if dsub["measurement type"] == "specified location":
                        print(" specified location in sorted: " + dsub["data"][0]["label"])
                        specified=True
                    if dsub==subpoint:
                        repeat=True
                        print("Found repeat in " + subpoint["measurement type"])
                if not repeat:
                    if subpoint["measurement type"] == "specified location" and specified:
                        print("Found different specified location: "+ subpoint["data"][0]["label"] +   ", not changing.")
                    else:
                        print(" Appending " + subpoint["measurement type"])
                        d["subpoints"].append(subpoint)
            inData=True
    if not inData and addNew:
        sortedData.append(data)


if unsortedFile:
    data = readNextData(unsortedFile)
    while( data ):
        t = datetime.datetime.fromtimestamp( data["timestamp"], datetime.timezone.utc)

        print("Unsorted: "+ t.isoformat() )
        addToData(data)
        data = readNextData(unsortedFile)




print("Writing Output")
outputFile = open(sortedFileName+ "_temp","w")

lastRecord = { "timestamp" : None }
for record in sorted(sortedData, key = lambda x:x["timestamp"]):
    if record["timestamp"] != lastRecord["timestamp"]:


        if lastRecord["timestamp"] != None:
            outputFile.write(json.dumps(lastRecord,indent=3,sort_keys=True))
            outputFile.write("\n" + "*"*32 + "\n")

        lastRecord = record
        

    else:
        print( " Record duplicate for " + str(pytz.timezone("UTC").localize(datetime.datetime.utcfromtimestamp(record["timestamp"]) ).astimezone(pytz.timezone("US/Central") )) )
        lastRecord["subpoints"] = lastRecord["subpoints"] + record["subpoints"]

if lastRecord:
        outputFile.write(json.dumps(lastRecord,indent=3,sort_keys=True))
        outputFile.write("\n" + "*"*32 + "\n")

outputFile.close()


#if everything went well

os.rename( sortedFileName + "_temp", sortedFileName)
os.remove( fileToProcess) 
