from generatemap import *
from readData import *
import datetime
from pytz import timezone


newMapDate = 1639900000
newEquipDate = 1658462830

startReadingData()
point = readNextData()

locationList = dict()

maxFreq = dict()
checkForBadContext = True

while(point != dict()):
    if True and float(point["timestamp"]) > newEquipDate: 
        GPSPoints = list()
        name = ""
        context = ""
        for subpoint in point["subpoints"]:
            if subpoint["measurement type"] == "specified location":
                name = subpoint["data"][0]["label"]
                context = subpoint["data"][0]["context"]

        if context == "The Home Depot":
            if checkForBadContext:
                for subpoint in point["subpoints"]: 
                    if "wifi scan" == subpoint["measurement type"] and len(subpoint["data"]) > 0:
                        for aaa in subpoint["data"]:
                            if "SSID" in aaa.keys() and "CenturyLink8151" in aaa["SSID"]:
                                print("CenturyLink8151 in The Home Depot")
                                print(subpoint)
                                exit()

            timeStamp = timezone('UTC').localize(  datetime.datetime.utcfromtimestamp(point["timestamp"]))
            timeStamp = timeStamp.astimezone( timezone("US/Central") )
            print( "Saving point: " + str(timeStamp) + " " + str(context) + " : " + str(name))

            l = (context, name)
            if l not in locationList.keys():
                locationList[l] = 0
            locationList[l] += 1
            if context not in maxFreq.keys():
                maxFreq[context] = 0
            if locationList[l] > maxFreq[context]:
                maxFreq[context] = locationList[l]


        if context == "Apartment":
            if checkForBadContext:
                for subpoint in point["subpoints"]: 
                    if "wifi scan" == subpoint["measurement type"] and len(subpoint["data"]) > 0:
                        for aaa in subpoint["data"]:
                            if "SSID" in aaa.keys() and "demopool" in aaa["SSID"]:
                                print("demopool in The Home Depot")
                                print(subpoint)
                                exit()
            timeStamp = timezone('UTC').localize(  datetime.datetime.utcfromtimestamp(point["timestamp"]))
            timeStamp = timeStamp.astimezone( timezone("US/Central") )
            print( "Saving point: " + str(timeStamp) + " " + str(context) + " : " + str(name))

            l = (context, name)
            if l not in locationList.keys():
                locationList[l] = 0
            locationList[l] += 1
            if context not in maxFreq.keys():
                maxFreq[context] = 0
            if locationList[l] > maxFreq[context]:
                maxFreq[context] = locationList[l]

    point = readNextData()




for context in svgMap.keys():
    svgMap[context] = svgMap[context][:-8]

for l in locationList.keys():
    (context, name) = l

    location = resolveLocationLL( name, context, CenterTable)
    thepointPlot = translateToPlot( contexts[context]["origin"],  {"latitude": location[0], "longitude" : location[1] }, contexts[context]["units"], 1)

    if context == "Apartment":
        r=40
    else:
        r=15

    svgMap[context]+= "<circle id=\""+str(name)+"\" cx=\""+str(thepointPlot["x"])+ "\" cy=\"" + str(thepointPlot["y"]) + "\" r=\""+str(r)+"\" fill=\"hsl(" + str(int( 230-230*(locationList[l] / maxFreq[context]))) + ",100%,50%)\" stroke-width=\"1\" stroke=\"black\" location=\"" + str(name) + "\"></circle>\n"


for context in svgMap.keys():
    f = open( context + "_map_coverage.svg", "w")
    f.write( svgMap[context]+ "\n\n</svg>" )
    f.close()
