from generatemap import *
from readData import *
import datetime
from pytz import timezone
from inertialModel import *
from pressureData import *
from createHistogram import *

newMapDate = 1639900000
newEquipDate = 1658462830

biases = { "The Home Depot": { "latitude sum" : 0,
                               "latitude weight": 0,
                               "longitude sum" : 0,
                               "longitude weight" : 0,
                               "altitude sum" : 0,
                               "altitude weight" : 0,
                               "count" : 0
                               },
         "Apartment": { "latitude sum" : 0,
                               "latitude weight": 0,
                               "longitude sum" : 0,
                               "longitude weight" : 0,
                               "altitude sum" : 0,
                               "altitude weight" : 0,
                               "count" : 0}}



startReadingData()
point = readNextData()

stationaryList = list()
iModel = inertialModel()
stationaryModel = None

while(point != dict()):
    isPointStationary = None
    specifiedLocation = False
    timeStamp = timezone('UTC').localize(  datetime.datetime.utcfromtimestamp(point["timestamp"]))
    timeStamp = timeStamp.astimezone( timezone("US/Central") )
    print( "Processing : " + str(timeStamp), end="")
    if len(stationaryList) > 0 or not iModel.readFromFile(point["timestamp"]):
        location = None
        for subpoint in point["subpoints"]:

            if subpoint["measurement type"] == "specified location" and subpoint["timestamp"] > newMapDate:
                uncertainties = { "The Home Depot" : [1, 2 ],
                                  "Apartment"      : [0.5, 2] }
                name = subpoint["data"][0]["label"]
                context = subpoint["data"][0]["context"]
                location = resolveLocationLL( name, context, CenterTable)
                iModel.addMeasurementLatLonAlt( subpoint["timestamp"], location[0], location[1], location[2], contexts[ context ]["accuracy, horizontal"],
                             contexts[ context ] ["accuracy, vertical" ] )
                iModel.specifyStationary()
                specifiedLocation = True
        for subpoint in point["subpoints"]:
            if subpoint["measurement type"] == "specified location" and subpoint["timestamp"] < newMapDate:
                data = subpoint["data"][0]
                specifiedLocation = True
                if ( "accuracy, horizontal" in data and
                     "accuracy, vertical"   in data and
                     "altitude"             in data and
                     "latitude"             in data and
                     "longitude"            in data ):
                    iModel.addMeasurementLatLonAlt( subpoint["timestamp"], data["latitude"], data["longitude"], data["altitude"], data["accuracy, horizontal"],
                             data["accuracy, vertical" ] )
                    iModel.specifyStationary()
                else:
                    if ( "accuracy, horizontal" in data and
                         "latitude"             in data and
                        "longitude"            in data ):
                        iModel.addMeasurementLatLon( subpoint["timestamp"], data["latitude"], data["longitude"], data["accuracy, horizontal"] )
                        iModel.specifyStationary()

            if subpoint["measurement type"] == "IMU":
                IMU = subpoint["data"][0]
                if "acceleration, x" in IMU and "acceleration, y" in IMU and "acceleration, z" in IMU:
                    totAcceleration = float(IMU["acceleration, x"])**2 + float(IMU["acceleration, y"])**2 + float(IMU["acceleration, z"])**2
                    totAcceleration = totAcceleration ** 0.5
                    if totAcceleration > 12 or totAcceleration < 8:
                        isPointStationary = False
                        print("IMU acceleration :{:}, not stationary".format(totAcceleration))
                    else:
                        print("IMU acceleration :{:}, stationary".format(totAcceleration))
                        if isPointStationary == None:
                            isPointStationary = True

            if subpoint["measurement type"] == "acceleration":
                IMU = subpoint["data"][0]
                if "x" in IMU and "y" in IMU and "z" in IMU:
                    totAcceleration = float(IMU["x"])**2 + float(IMU["y"])**2 + float(IMU["z"])**2
                    totAcceleration = totAcceleration ** 0.5
                    if totAcceleration > 0.05:
                        isPointStationary = False
                        print("acceleration :{:}, not stationary".format(totAcceleration))
                    else:
                        print("acceleration :{:}, stationary".format(totAcceleration))
                        if isPointStationary == None:
                            isPointStationary = True


            if subpoint["measurement type"] == "location - gps" or subpoint["measurement type"] == "location - network":
                locationData = subpoint["data"][0]
                if "accuracy, horizontal" not in locationData or locationData["accuracy, horizontal"] == 0:
                        locationData["accuracy, horizontal"] = 1000
                if "accuracy, vertical" not in locationData or locationData["accuracy, vertical"] == 0:
                        locationData["accuracy, vertical"] = 1000

                if "altitude" in subpoint["data"][0] and subpoint["data"][0]["altitude"] != "" and float(subpoint["data"][0]["altitude"]) > 0:
                    iModel.addMeasurementLatLonAlt( subpoint["timestamp"], locationData["latitude"], locationData["longitude"], locationData["altitude"],
                             locationData["accuracy, horizontal"], locationData["accuracy, vertical"] )
                    subPointDataElement = locationData
                    if location != None:
                        hWeight = 1 / subPointDataElement["accuracy, horizontal"]**2
                        vWeight = 1 / subPointDataElement["accuracy, vertical"]**2
                        biases[ context ]["latitude weight"] += hWeight
                        biases[ context ]["longitude weight"] += hWeight
                        biases[ context ]["altitude weight"] += vWeight
                        biases[ context ]["latitude sum"] -= (location[0] - subPointDataElement["latitude"]) * hWeight
                        biases[ context ]["longitude sum"] -= (location[1] - subPointDataElement["longitude"]) * hWeight
                        biases[ context ]["altitude sum"] -= (location[2] - subPointDataElement["altitude"]) * vWeight
                        biases[ context ]["count"] += 1

                        if (biases[context]["latitude weight"] > 0 and
                            biases[context]["longitude weight"] > 0 and
                            biases[context]["altitude weight"] > 0):
                            stri= "{:} -- lat bias: {:}, long bias: {:}, alt bias: {:}, count {:}". format(context, biases[context]["latitude sum"] / biases[context]["latitude weight"],
                                          biases[context]["longitude sum"] / biases[context]["longitude weight"], biases[context]["altitude sum"] / biases[context]["altitude weight"],
                                          biases[context]["count"] )
                            print(stri)

                else:
                    iModel.addMeasurementLatLon( subpoint["timestamp"], locationData["latitude"], locationData["longitude"],
                             locationData["accuracy, horizontal"] )

                if "velocity, down" in locationData and "velocity, east" in locationData and "velocity, north" in locationData:
                    iModel.addMeasurementVelocity( subpoint["timestamp"], locationData["velocity, down"], locationData["velocity, east"], locationData["velocity, north"], locationData["speed, accuracy"] )
                    if locationData["velocity, down"] ** 2 + locationData["velocity, east"]**2 + locationData["velocity, down"] ** 2 > locationData["speed, accuracy"] **2:
                        isPointStationary = False
                        print("vel sum: {:}, accuracy: {:} - moving".format( (locationData["velocity, down"] ** 2 + locationData["velocity, east"]**2 + locationData["velocity, down"] ** 2)**0.5, locationData["speed, accuracy"] ))
                    else:
                        print("vel sum: {:}, accuracy: {:} - stat".format( (locationData["velocity, down"] ** 2 + locationData["velocity, east"]**2 + locationData["velocity, down"] ** 2)**0.5, locationData["speed, accuracy"] ))
                if "speed" in locationData and "accuracy, speed" in locationData:
                    if locationData["speed"] > locationData["accuracy, speed"]:
                        isPointStationary = False
                        print("speed: {:}, accuracy: {:} - not stationary".format(locationData["speed"], locationData["accuracy, speed"]))
                    else:
                        print("speed: {:}, accuracy: {:} - stationary".format(locationData["speed"], locationData["accuracy, speed"]))
                        if isPointStationary == None:
                            isPointStationary == True

            if "wifi scan" ==  subpoint["measurement type"]:
                if "WIFI histogram detection result" in subpoint.keys():
                    if "altitude" in subpoint["WIFI histogram detection result"]:
                        iModel.addMeasurementLatLonAlt( subpoint["timestamp"],
                              subpoint["WIFI histogram detection result"]["latitude"],
                              subpoint["WIFI histogram detection result"]["longitude"],
                              subpoint["WIFI histogram detection result"]["altitude"],
                              subpoint["WIFI histogram detection result"]["accuracy, horizontal"],
                              subpoint["WIFI histogram detection result"]["accuracy, vertical"])
                    else:
                        iModel.addMeasurementLatLon( subpoint["timestamp"],
                              subpoint["WIFI histogram detection result"]["latitude"],
                              subpoint["WIFI histogram detection result"]["longitude"],
                              subpoint["WIFI histogram detection result"]["accuracy, horizontal"])
                else:
                    thepoint=findPoint(subpoint["data"], timestamp = subpoint["timestamp"], source= subpoint["source"])
                    if len(thepoint) == 5:
                        iModel.addMeasurementLatLonAlt( subpoint["timestamp"],
                                               thepoint[0],
                                               thepoint[1],
                                               thepoint[2],
                                               thepoint[5] )
        iModel.optimizeParameters(quick=True)
        for subpoint in point["subpoints"]:

            if "pressure" == subpoint["measurement type"]:
                pos = iModel.inertialFunctionPredictionLatLonAlt( subpoint["timestamp"] )
                if pos != None:
                    alt = altitudeFromSubpoint( subpoint["timestamp"], float(subpoint["data"][0]["Value"]), pos[0], pos[1] )
                    if alt != None:
                        iModel.addMeasurementAlt( subpoint["timestamp"], alt, 50)
            if "altimeter" == subpoint["measurement type"]:
                pos = iModel.inertialFunctionPredictionLatLonAlt( subpoint["timestamp"] )
                if pos != None:
                    alt = altitudeFromSubpoint( subpoint["timestamp"], float(subpoint["data"][0]["pressure"]), pos[0], pos[1] )
                    if alt != None:
                        iModel.addMeasurementAlt( subpoint["timestamp"], alt, 50)

        if (isPointStationary != None and isPointStationary == True) or specifiedLocation == True:
            iModel.specifyStationary()
            print("Stationary point")
            stationaryModel = iModel
            stationaryList.append( point["timestamp"])
        else:
            if stationaryModel != None:
                stationaryModel.optimizeParameters(recompute=True)
                stationaryModel.computeUncertainty()
                print( "stationary" + str(stationaryModel.uncertainties) )
                print("stationary set: {:}".format( len(stationaryList)))
                for t in stationaryList:
                    stationaryModel.saveToFile(t)
                stationaryModel = None
                stationaryList = list()

            iModel.optimizeParameters()
            iModel.computeUncertainty()
            print( "moving" + str(iModel.uncertainties) )
            iModel.saveToFile(point["timestamp"])
            iModel = inertialModel()
            stationaryList = list()
    else:
        pppp=8
        print(" : in file.")
    point = readNextData()


iModel.optimizeParameters()
iModel.computeUncertainty()
print( iModel.uncertainties )
if len(stationaryList) > 1:
    print("stationary set: {:}".format( len(stationaryList)))
for t in stationaryList:
    iModel.saveToFile(t)

b = open("biases.txt", "w")
for cont in biases.keys():
    if (biases[cont]["latitude weight"] > 0 and
        biases[cont]["longitude weight"] > 0 and
        biases[cont]["altitude weight"] > 0):
        stri= "{:} -- lat bias: {:}, long bias: {:}, alt bias: {:}, count {:}". format(cont, biases[cont]["latitude sum"] / biases[cont]["latitude weight"],
                          biases[cont]["longitude sum"] / biases[cont]["longitude weight"], biases[cont]["altitude sum"] / biases[cont]["altitude weight"],
                          biases[cont]["count"] )
        print(stri)
        b.write(stri+ "\n")

