from create_map import *
from read_data_file_library import *
import datetime
from pytz import timezone
from inertial_model import *
from pressure_data import *
from create_histogram import *
from validate_location import *
from delete_sample import deleteSample

deleteSample( inertialModelDirectory, 0.05)

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

lastPrediction = {"timestamp":None, "loc" : None }

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
                        #print("acceleration :{:}, stationary".format(totAcceleration))
                        if isPointStationary == None:
                            isPointStationary = True


            if ((subpoint["measurement type"] == "location - gps" or subpoint["measurement type"] == "location - network") and 
                      subpoint["source"] != "GT-U7 gps module"):
                accuracyFactor = 1
                if subpoint["measurement type"] == "location - network":
                    accuracyFactor = 5
                subpoint = validateLocation(subpoint)
                locationData = subpoint["data"][0]

                if locationData["validator reponse"] == "valid - altitude":
                    iModel.addMeasurementLatLonAlt( subpoint["timestamp"], locationData["latitude"], locationData["longitude"], locationData["altitude"],
                             locationData["accuracy, horizontal"]*accuracyFactor, locationData["accuracy, vertical"]*accuracyFactor )
                    subPointDataElement = locationData

                else:
                    if locationData["validator reponse"] == "valid" and point["timestamp"] > datetime.datetime(2021,1,1).timestamp():
                        iModel.addMeasurementLatLon( subpoint["timestamp"], locationData["latitude"], locationData["longitude"],
                             locationData["accuracy, horizontal"] * accuracyFactor )
                    else:
                        if locationData["validator reponse"] == "valid" and point["timestamp"] <= datetime.datetime(2021,1,1).timestamp():
                            iModel.addMeasurementLatLonAlt( subpoint["timestamp"], locationData["latitude"], locationData["longitude"],
                             250, locationData["accuracy, horizontal"] * accuracyFactor, 250 )
                        else:
                            print(subPoint)
                            exit()
                if "bearing" in locationData and "accuracy, bearing" in locationData and float(locationData["accuracy, bearing"]) > 0:
                    iModel.addMeasurementHeading( subpoint["timestamp"], float(locationData["bearing"]), float(locationData["accuracy, bearing"]))

                if "velocity, down" in locationData and "velocity, east" in locationData and "velocity, north" in locationData:
                    iModel.addMeasurementVelocity( subpoint["timestamp"], locationData["velocity, down"], locationData["velocity, east"], locationData["velocity, north"], locationData["speed, accuracy"] )
                    if locationData["velocity, down"] ** 2 + locationData["velocity, east"]**2 + locationData["velocity, down"] ** 2 > locationData["speed, accuracy"] **2:
                        isPointStationary = False
                        print("vel sum: {:}, accuracy: {:} - moving".format( (locationData["velocity, down"] ** 2 + locationData["velocity, east"]**2 + locationData["velocity, down"] ** 2)**0.5, locationData["speed, accuracy"] ))
                    else:
                        tttt=3
                        #print("vel sum: {:}, accuracy: {:} - stat".format( (locationData["velocity, down"] ** 2 + locationData["velocity, east"]**2 + locationData["velocity, down"] ** 2)**0.5, locationData["speed, accuracy"] ))
                if "speed" in locationData and "accuracy, speed" in locationData and float(locationData["accuracy, speed"]) > 0:
                    iModel.addMeasurementSpeedHorizontal( subpoint["timestamp"], float(locationData["speed"]), float(locationData["accuracy, speed"]))
                    if locationData["speed"] > locationData["accuracy, speed"]:
                        isPointStationary = False
                        print("speed: {:}, accuracy: {:} - not stationary".format(locationData["speed"], locationData["accuracy, speed"]))
                    else:
                        #print("speed: {:}, accuracy: {:} - stationary".format(locationData["speed"], locationData["accuracy, speed"]))
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
                    thepoint=None
                    thepoint=findPoint(subpoint["data"], timestamp = subpoint["timestamp"], source= subpoint["source"])
                    if thepoint and len(thepoint) == 5:
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
                newLastPrediction = {"timestamp": point["timestamp"], "loc" : stationaryModel.inertialFunctionPredictionLatLonAlt( point["timestamp"] ) }
                if lastPrediction["timestamp"] != None:
                    distance = geopy.distance.geodesic(newLastPrediction["loc"], lastPrediction["loc"]).m
                    speed = distance / (newLastPrediction["timestamp"] - lastPrediction["timestamp"] )
                    if speed > 100:
                        print("Too fast!!!!!!!!!!!!!")
                        print(speed)
                        print(point)
                        exit()
                    lastPrediction = newLastPrediction
                stationaryModel = None
                stationaryList = list()

            iModel.optimizeParameters()
            iModel.computeUncertainty()
            print( "moving" + str(iModel.uncertainties) )

            newLastPrediction = {"timestamp": point["timestamp"], "loc" : iModel.inertialFunctionPredictionLatLonAlt( point["timestamp"] ) }
            if lastPrediction["timestamp"] != None:
                    distance = geopy.distance.geodesic(newLastPrediction["loc"], lastPrediction["loc"]).m
                    speed = distance / (newLastPrediction["timestamp"] - lastPrediction["timestamp"] )
                    if speed > 100:
                        print("Too fast!!!!!!!!!!!!!")
                        print(speed)
                        print(point)
                        exit()
                    lastPrediction = newLastPrediction
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

