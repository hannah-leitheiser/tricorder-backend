import os
import json
import scipy.stats

data_file_library_directory = "/home/hannah/location_finder/data_file_library/"

dataFile = None
dataFileList = []
currentDataFile = ""
def startReadingData():
    global dataFileList
    global dataFile
    global currentDataFile
    dataFileList_ = os.listdir(data_file_library_directory)
    for f in dataFileList_:
        if "unsorted" not in f and ("2022" in f or "2023" in f):
            dataFileList.append(data_file_library_directory+f)
    dataFileList = sorted(dataFileList)
    currentDataFile = dataFileList[0]
    dataFile = open(dataFileList.pop(0), "r")


def readNextData():
    global dataFileList
    global dataFile
    global currentDataFile
    trackDataString=""
    line = ""
    while ( "*"*32 not in line):
        trackDataString = trackDataString + line
        line = dataFile.readline()
        if line == "":
            if len(dataFileList) > 0:
                currentDataFile = dataFileList[0]
                print(currentDataFile)
                dataFile = open(dataFileList.pop(0), "r")
                line = dataFile.readline()
            else:
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


