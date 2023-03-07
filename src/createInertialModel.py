from generatemap import *
from readData import *
import datetime
from pytz import timezone
from inertialModel import *


newMapDate = 1639900000
newEquipDate = 1658462830

startReadingData()
point = readNextData()

while(point != dict()):
    iModel = inertialModel() 

    timeStamp = timezone('UTC').localize(  datetime.datetime.utcfromtimestamp(point["timestamp"]))
    timeStamp = timeStamp.astimezone( timezone("US/Central") )
    print( "Processing : " + str(timeStamp), end="")
    if not iModel.readFromFile(point["timestamp"]):
        print(" : not in file." )
        for subpoint in point["subpoints"]:

            if subpoint["measurement type"] == "specified location":
                uncertainties = { "The Home Depot" : [1, 2 ],
                                  "Apartment"      : [0.5, 2] }
                name = subpoint["data"][0]["label"]
                context = subpoint["data"][0]["context"]
                location = resolveLocationLL( name, context, CenterTable)
                iModel.addMeasurementLatLonAlt( subpoint["timestamp"], location[0], location[1], location[2], uncertainties[ context ]["The Home Depot"],
                             uncertainties[ context ] ["Apartment" ] )
                iModel.specifyStationary()
            if subpoint["measurement type"] == "location - gps" or subpoint["measurement type"] == "location - network":
                locationData = subpoint["data"][0]
                if "accuracy, horizontal" not in locationData or locationData["accuracy, horizontal"] == 0:
                        locationData["accuracy, horizontal"] = 1000
                if "accuracy, vertical" not in locationData or locationData["accuracy, vertical"] == 0:
                        locationData["accuracy, vertical"] = 1000

                if "altitude" in subpoint["data"][0] and subpoint["data"][0]["altitude"] != "" and float(subpoint["data"][0]["altitude"]) > 0:
                    iModel.addMeasurementLatLonAlt( subpoint["timestamp"], locationData["latitude"], locationData["longitude"], locationData["altitude"],
                             locationData["accuracy, horizontal"], locationData["accuracy, vertical"] )
                else:
                    iModel.addMeasurementLatLon( subpoint["timestamp"], locationData["latitude"], locationData["longitude"],
                             locationData["accuracy, horizontal"] )


            if "wifi scan" ==  subpoint["measurement type"]:
                if "WIFI histogram detection result" in subpoint.keys():
                    iModel.addMeasurementLatLonAlt( subpoint["timestamp"],
                              subpoint["WIFI histogram detection result"]["latitude"],
                              subpoint["WIFI histogram detection result"]["longitude"],
                              subpoint["WIFI histogram detection result"]["altitude"],
                              subpoint["WIFI histogram detection result"]["accuracy, vertical"],
                              subpoint["WIFI histogram detection result"]["accuracy, horizontal"])


        iModel.saveToFile(point["timestamp"])
    else:
        print(" : in file.")
    point = readNextData()



