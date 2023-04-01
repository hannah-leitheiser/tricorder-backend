from create_map import *
from read_data_file_library import *
import datetime
from pytz import timezone
import os
import json
import geopy.distance

newMapDate = 1639900000
newEquipDate = 1658462830

def readwifidata(data):
    wifidict=dict()
    for w in data:
        if "bssid" in w.keys():
            w["BSSID"] = w["bssid"]
        if "rssi" in w.keys():
            w["level"] = w["rssi"]
        if "ssid" in w.keys():
            w["SSID"] = w["ssid"]
        if "frequency_mhz" in w.keys():
            w["frequency"] = w["frequency_mhz"]
        if "BSSID" in w.keys() and "level" in w.keys():
            wifidict[ w["BSSID"]  ]=int(w["level"])
        else:
            print(w)
            exit()
    return wifidict

def makeHistogramBlur(l):
    numbers = dict()
    for i in l:
        i=int(i)
        # empirical paramaters, 300 inch goal
        Noise = 12
        guassianBlur = (-300 / (27.79 * 2.71828 ** (-0.0502 * i) * -0.0502)) + Noise
        guassianBlur = ((int(guassianBlur) // 2) * 2)
        # make sure low signal and no signal are blured together
        if i <= -75:
            guassianBlur = 26
        pdfSet = list()
        for x in range(-guassianBlur//2,guassianBlur//2+1):
            pdfSet.append( int(1000*scipy.stats.norm.pdf(x,0,guassianBlur/5)))

        #guassianBlur = 0
        #pdfSet = [1]
        for x in range(int(i)-(guassianBlur//2),int(i)+(guassianBlur//2)+1):
            if x < 0:
                ourNum = x
                if x < -100:
                    ourNum = -100
                if not ourNum in numbers.keys():
                    numbers[ourNum] = 0
                numbers[ourNum] = numbers[ourNum] + pdfSet[ x - i ]


    for num in numbers.keys():
        numbers[num] = numbers[num] / (len(l) * sum(pdfSet))
    return numbers


def makeHistogram(l):
    numbers = dict()
    for i in l:
        i=int(i)

        if not i in numbers.keys():
            numbers[i] = 0
        numbers[i] = numbers[i] + 1


    for num in numbers.keys():
        numbers[num] = numbers[num] / (len(l))
    return numbers

def createHistogram():

    startReadingData()
    point = readNextData()

    histogramData = dict()
    locationList = dict()

    wifiNames = dict()
    while(point != dict()):
        location = None
        for subpoint in point["subpoints"]:

            if subpoint["measurement type"] == "specified location":
                if ((subpoint["data"][0]["context"] == "The Home Depot" and subpoint["timestamp"] > newEquipDate) or
                     subpoint["data"][0]["context"] == "Apartment" ):
                    location = subpoint["data"][0]["label"]
                    context = subpoint["data"][0]["context"]
                    locationL = sorted(location.split(" "))
                    location = ""
                    for loc in locationL:
                        location = location + loc + " "
                    location = location[:-1].upper()
                    print((context, location))

        if location != None:
          for subpoint in point["subpoints"]:
              if subpoint["measurement type"] == "wifi scan":
                source = subpoint["source"]
                for t in subpoint["data"]:
                    if "bssid" in t.keys():
                        t["BSSID"] = t["bssid"]
                    if "ssid" in t.keys():
                        t["SSID"] = t["ssid"]
                    if "frequency_mhz" in t.keys():
                        t["frequency"] = t["frequency_mhz"]
                    if "SSID" not in t.keys():
                        t["SSID"] = ""
                    wifiNames [ t["BSSID"] ] = str(t["frequency"]) + " - " + t["SSID"]
                locationLL = resolveLocationLL(location, context, CenterTable)
                if len(locationLL) > 0:
                    if context not in histogramData:
                        histogramData[context] = dict()
                    if source not in histogramData[context]:
                        histogramData[context][source] = dict()
                    
                    if locationLL in locationList:
                        location = locationList[ locationLL ]
                    else:
                        locationList[ locationLL ] = location

                    for w in subpoint["data"]:
                        wifi = w["BSSID"]
                        if wifi in histogramData[context][source].keys():
                            locationIn = False
                            for l in histogramData[context][source][wifi].keys():
                                if location == l:
                                    locationIn = True
                            if locationIn:
                                histogramData[context][source][wifi][location].append(int(w["level"]))
                            else:
                                histogramData[context][source][wifi][location] = list()
                                histogramData[context][source][wifi][location].append(int(w["level"]))
                        else:
                            histogramData[context][source][wifi] = dict()
                            histogramData[context][source][wifi][location] = list()
                            histogramData[context][source][wifi][location].append(int(w["level"]))

                else:
                    notInTable.append(location)
        point = readNextData()



    for context in histogramData.keys():
        for source in histogramData[context].keys():
            listToDelete = list()
            for wifi in histogramData[context][source].keys():
                sampleCount = 0
                for loc in histogramData[context][source][wifi].keys():
                    sampleCount = sampleCount + len(histogramData[context][source][wifi][loc])
                if sampleCount < 100:
                    listToDelete.append(wifi)
            for d in set(listToDelete):
                print("Deleting from " + str(source) + " wifi " + str(d))
                histogramData[context][source].pop(d)

    histogramRaw = dict()
    histogramDataNew = dict()

    wifiList = dict()

    for context in histogramData.keys():

        if context not in histogramRaw:
            histogramRaw[context] = dict()
        if context not in histogramDataNew:
            histogramDataNew[context] = dict()

        for source in histogramData[context].keys():
            histogramRaw[context][source] = dict()
            histogramDataNew[context][source] = dict()
            for wifi in histogramData[context][source].keys():
                if context not in wifiList:
                    wifiList[context] = list() 
                wifiList[context].append(wifi)
                wifiList[context]= list(set(wifiList[context]))
                histogramRaw[context][source][wifi] = dict()
                histogramDataNew[context][source][wifi] = dict()
                print("Make Histogram: "+str(context)+":"+str(source)+":"+str(wifi))
                for loc in histogramData[context][source][wifi].keys():
                    histogramDataNew[context][source][wifi][loc] = makeHistogramBlur(histogramData[context][source][wifi][loc])
                    #histogramDataNew[context][source][wifi][loc] = makeHistogram(histogramData[context][source][wifi][loc])
                    histogramRaw[context][source][wifi][loc] =  makeHistogram(histogramData[context][source][wifi][loc])
         
        histogramData[context] = histogramDataNew[context]

        for source in histogramData[context].keys():
            for wifi in histogramData[context][source].keys():
                rSSIDDict = dict()
                for loc in histogramData[context][source][wifi].keys():
                    for rSSID in histogramData[context][source][wifi][loc].keys():
                        if not rSSID in rSSIDDict.keys():
                            rSSIDDict[rSSID] = dict()
                        rSSIDDict[rSSID][loc] = histogramData[context][source][wifi][loc][rSSID]
                histogramData[context][source][wifi] = rSSIDDict


        for source in histogramRaw[context].keys():
            for wifi in histogramRaw[context][source].keys():
                rSSIDDict = dict()
                for loc in histogramRaw[context][source][wifi].keys():
                    for rSSID in histogramRaw[context][source][wifi][loc].keys():
                        if not rSSID in rSSIDDict.keys():
                            rSSIDDict[rSSID] = dict()
                        rSSIDDict[rSSID][loc] = histogramRaw[context][source][wifi][loc][rSSID]
                histogramRaw[context][source][wifi] = rSSIDDict


    currentTS = datetime.datetime.now().timestamp()
    wifiDF = open("data_file_histogram/wifi_data_file_" + str(int(currentTS)) + ".txt", "w")
    wifiDF.write( json.dumps({"wifiList" : wifiList, "histogramData": histogramData } ) )
    wifiDF.close()
    return (histogramData, wifiList)


# -----------------------------------------------------


def findPoint(scan, method="histogram", discard="", timestamp=0, source=""):
    me=readwifidata(scan)
    checkForRepeats = []
    # ------------ use Histogram ----------

    if method=="histogram":
            for context in histogramData.keys():


                if len(set(wifiList[context]).intersection(me.keys())) > 40:
                    if (context not in histogramData or
                        source not in histogramData[context]):
                        return []

                    print("Attempting "+context+" Detection...")
                    placesList = []
                    places= []
                    for w in me.keys():
                        if w in histogramData[context][source].keys():
                            if me[w] in histogramData[context][source][w].keys():
                                placesList.append( histogramData[context][source][w][ me[w] ] )
                                places.append( set(histogramData[context][source][w][ me[w] ].keys()) )
                    weight=0
                    if len(placesList) > 0:
                        placesSet = places[0] 
                        for p in range(1,len(places)):
                            placesSet = placesSet.intersection(places[p])

                        if discard != "":
                            discardP = resolveLocationLL( discard, context, CenterTable)
                            for p in list(placesSet):
                                if resolveLocationLL(p, context, CenterTable) == discardP:
                                    placesSet.remove(p)
                        placesSetProbability = {}

                        for place in list(placesSet):
                            prob = 1e200
                            for ee in placesList:
                                prob = prob * ee[place]
                            placesSetProbability[place] = prob

                        #print("places:" + str(placesSetProbability))
                        x=0
                        y=0
                        z=0
                        highestWeight=0
                        mostProbableLocation=""
                        numberOfMatches = 0
                        for m in placesSetProbability.keys():
                            loc = resolveLocationLL( m, context, CenterTable )
                            if len(loc) >= 2:
                                w = (placesSetProbability[m])
                                if w > highestWeight:
                                    highestWeight = w
                                    mostProbableLocation = m
                                x=x+loc[0]*w
                                y=y+loc[1]*w
                                z=z+loc[2]*w
                                weight=weight+w
                                numberOfMatches = numberOfMatches+1



                        addUncertainty = 4
                        if numberOfMatches == 1:
                            addUncertainty = 12
                        if numberOfMatches == 2:
                            addUncertainty = 7
                        if weight > 0:
                            bestGuessPoint = {"x" : x/weight, "y" : y/weight, "z" : z/weight }


                            meanPosition = (x/weight, y/weight, z/weight)
                            delta = 0.00001
                            distanceNorth = geopy.distance.geodesic((meanPosition[0], meanPosition[1]), (meanPosition[0]+delta, meanPosition[1])).m
                            distanceEast = geopy.distance.geodesic((meanPosition[0], meanPosition[1]), (meanPosition[0], meanPosition[1]+delta)).m
                            meters_per_latitude = distanceNorth / delta
                            meters_per_longitude = distanceEast / delta

                            meanDist=0
                            weightDist = 0

                            for m in placesSetProbability.keys():
                                loc = resolveLocationLL( m, context, CenterTable )
                                if len(loc) >= 2:
                                    distance = ((  ( (loc[0] - bestGuessPoint["x"])*meters_per_latitude  )**2 +
                                                  ( (loc[1] - bestGuessPoint["y"]) * meters_per_longitude)**2 +
                                                  (loc[2] - bestGuessPoint["z"])**2 ) ** 0.5) 
                                    w = (placesSetProbability[m])
                                    meanDist = meanDist + w * distance
                                    weightDist = weightDist + w
                            print(" uncertainty computed: {:}, add uncertainty: {:}, num mat: {:}, label: {:}".format( (meanDist/weightDist), addUncertainty, numberOfMatches, mostProbableLocation))



                    if weight > 0:
                        main_label= mostProbableLocation 
                        return (x/weight,y/weight,z/weight,context,main_label,(meanDist/weightDist) + addUncertainty )
                    else:
                        print("  No WIFI match, " + context)
            

    return []



secondsOldAllowable = 7 * 86400
savedHistogramFileList = os.listdir("data_file_histogram/")
bestFile = None
for file in savedHistogramFileList:
    if "wifi_data_file_" in file:
        timestamp = int(file.split("wifi_data_file_")[1].split(".txt")[0])
        if bestFile != None:
            timestampBest = int(bestFile.split("wifi_data_file_")[1].split(".txt")[0])
            if timestamp > timestampBest:
                bestFile = file
        else:
            bestFile = file

currentTS = datetime.datetime.now().timestamp()
timestampBest = 0
if bestFile != None:
    timestampBest = int(bestFile.split("wifi_data_file_")[1].split(".txt")[0])
if currentTS - timestampBest > secondsOldAllowable:
    (histogramData, wifiList) = createHistogram()
else:
    data = json.loads( open( "data_file_histogram/"+bestFile).read() )
    histogramData = data["histogramData"]

    # we really need the level keys to be integers
    for context in histogramData:
        for source in histogramData[context].keys():
            for wifi in histogramData[context][source].keys():
                toPop = list()
                for level in histogramData[context][source][wifi].keys():
                    if type(level) != type(int()):
                        toPop.append( level)
                for p in toPop:
                    histogramData[context][source][wifi][ int(p) ] = histogramData[context][source][wifi].pop(p)

    wifiList = data["wifiList"]
