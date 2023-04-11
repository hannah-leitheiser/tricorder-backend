import geopy.distance
import math
import random
import json
#import matplotlib.pyplot as plt
import statistics
import os

dataDirectory = "/media/hannah/Tricorder/tricorder/tricorder-backend-map/data/"

deviceDirectories = []
for dd in os.listdir("."):
    if "transmitter_data_" in dd:
        for d in os.listdir(dd+"/"):
            deviceDirectories.append(dd+"/" + d + "/")
wifiFiles = {}
for d in deviceDirectories:
    for f in os.listdir(d):
        if "_SOLUTION.txt" in f:
            if f[:5] == "cell_": 
                if f in wifiFiles:
                    wifiFiles[f[:-13]].append(d + f)
                else:
                    wifiFiles[f[:-13]] = [ d+f ]
            else:
                if f[0:22] in wifiFiles:
                    wifiFiles[f[0:22]].append(d + f)
                else:
                    wifiFiles[f[0:22]] = [ d+f ]


wifiCount=0
for xmtrType in ["wifi", "cell"]:


    geo = open("data/xmtrs_"+xmtrType+ "_GEO.json", "w")
    geo.write( " {\n\"type\":\"FeatureCollection\",\n\"features\":[\n\n")


    notFirst = False
    for w in wifiFiles.keys(): 
        if w[:4] == xmtrType:
            print(w)

            meanLat = 0
            meanLon = 0
            meanPower=0
            weight = 0
            wifiNames = []
            for d in wifiFiles[w]:
                fileData = open(d, "r").read()
                print( (d, open(d, "r").read() ))
                if len(fileData) > 10:
               
                    data = json.loads( open(d, "r").read() )
                    if "n" in data:
                        weight_ = data["n"]
                    else:
                        weight_ = 1
                    meanLat = meanLat + weight_*data["latitude"]
                    meanLon = meanLon + weight_*data["longitude"]
                    meanPower= meanPower + weight_*data["power"]
                    weight=weight+weight_

                    wifiName_current = wifiFiles[w][0].split("/")[-1][23:-13]
                    if len(wifiName_current) > 0 and wifiName_current[-1] == "_":
                        wifiName_current = wifiName_current[:-1]

                    wifiNames.append(wifiName_current)
            if weight > 0:
                wifiCount = wifiCount + 1

                wifiName = ""
                for name in wifiNames:
                    if name not in wifiName:
                        wifiName = wifiName + name
                if w[:4] == "cell":
                    wifiName = "xmtr_cell_" + w[6:]

                if notFirst:
                    geo.write(",")

                notFirst = True

                if xmtrType == "cell":
                    geoFileName =  "data/xmtr_cell_" + w[6:]+"_GEO.json"
                    wifiName = w[6:]
                if xmtrType == "wifi":
                    geoFileName = "data/xmtr_" + w + "_GEO.json"

                geo.write(" {\n\"type\":\"Feature\",\n\"properties\":\n")
                geo.write(" { \"name\":\"" + wifiName  + "\",")

                geo.write(" \"filename\":\"" + geoFileName  + "\",")
                geo.write("   \"bssid\" : \"" + w + "\",")
                geo.write("    \"power\" : " + str( int ( meanPower/weight)) + "},\n")
                geo.write(" \"geometry\": { \n\"type\":\"Point\",\n\"coordinates\": [")
                geo.write( str(meanLon / weight) + ","+ str(meanLat/weight) + "] } }")
                if os.path.exists(geoFileName):
                    geoJSON = json.loads( open(geoFileName).read() )
                    points = []
                    for i in range(len(geoJSON["features"])):
                        if "bssid" in geoJSON["features"][i]["properties"].keys():
                            points.append(i)
                    for i in points[-1::-1]:
                        geoJSON["features"].pop(i)

                        
                    string = " {\n\"type\":\"Feature\",\n\"properties\":\n"
                    string=string+(" { \"name\":\"" + wifiName  + "\",")
                    string=string+(" \"filename\":\"" + geoFileName  + "\",")
                    string=string+("   \"bssid\" : \"" + w  + "\",")
                    string=string+("    \"power\" : " + str( int ( meanPower/weight)) + "},\n")
                    string=string+(" \"geometry\": { \n\"type\":\"Point\",\n\"coordinates\": [")
                    string=string+( str(meanLon / weight) + ","+ str(meanLat/weight) + "] } }")
                    newFeature = json.loads(string)

                    print(newFeature)
                    geoJSON["features"].append( newFeature )

                    open(geoFileName, "w").write( json.dumps( geoJSON ))








    geo.write("\n\n] }")


print( "Wifi Count: {}".format(wifiCount))


