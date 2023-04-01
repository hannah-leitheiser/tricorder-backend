from generatemap import *
from readData import *
import contextorigins
import datetime
from pytz import timezone
import geopy.distance

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

while(point != dict()):

    location = None
    timeStamp = timezone('UTC').localize(  datetime.datetime.utcfromtimestamp(point["timestamp"]))
    timeStamp = timeStamp.astimezone( timezone("US/Central") )
    
    if point["timestamp"] % 86400 == 0:
        print( "Processing : " + str(timeStamp))

        for cont in biases.keys():
            if (biases[cont]["latitude weight"] > 0 and
                biases[cont]["longitude weight"] > 0 and
                biases[cont]["altitude weight"] > 0):

                cont = context
                latitude_bias = biases[cont]["latitude sum"] / biases[cont]["latitude weight"]
                longitude_bias = biases[cont]["longitude sum"] / biases[cont]["longitude weight"]
                altitude_bias = biases[cont]["altitude sum"] / biases[cont]["altitude weight"]


                stri= "{:} -- lat bias: {:}, long bias: {:}, alt bias: {:}, count {:}". format(cont, latitude_bias,
                                  longitude_bias, altitude_bias,
                                  biases[cont]["count"] )
                print(stri)

                new_lat = contexts[cont]["origin"]["latitude"] + latitude_bias
                new_lon = contexts[cont]["origin"]["longitude"] + longitude_bias
                new_alt = contexts[cont]["origin"]["altitude"] + altitude_bias
                print( cont + " : distance change : " + str(geopy.distance.geodesic((new_lat, new_lon, new_alt  ), ( contexts[cont]["origin"]["latitude"],
                             contexts[cont]["origin"]["longitude"], new_alt)).m) + " alt :" + str( new_alt - contexts[cont]["origin"]["altitude"]))

    for subpoint in point["subpoints"]:

            if subpoint["measurement type"] == "specified location" and subpoint["timestamp"] > newMapDate:
                uncertainties = { "The Home Depot" : [1, 2 ],
                                  "Apartment"      : [0.5, 2] }
                name = subpoint["data"][0]["label"]
                context = subpoint["data"][0]["context"]
                location = resolveLocationLL( name, context, CenterTable)
    if location != None:
        for subpoint in point["subpoints"]:
            if subpoint["measurement type"] == "location - gps":
                locationData = subpoint["data"][0]

                if "altitude" in subpoint["data"][0] and subpoint["data"][0]["altitude"] != "" and float(subpoint["data"][0]["altitude"]) > 0 and "accuracy, horizontal" in locationData and locationData["accuracy, horizontal"] > 0 and "accuracy, vertical" in locationData and locationData["accuracy, vertical"] > 0:
                    subPointDataElement = locationData
                    if subpoint["measurement type"] == "location - gps" and location != None:
                        hWeight = 1 / subPointDataElement["accuracy, horizontal"]**2
                        vWeight = 1 / subPointDataElement["accuracy, vertical"]**2
                        biases[ context ]["latitude weight"] += hWeight
                        biases[ context ]["longitude weight"] += hWeight
                        biases[ context ]["altitude weight"] += vWeight
                        biases[ context ]["latitude sum"] -= (location[0] - subPointDataElement["latitude"]) * hWeight
                        biases[ context ]["longitude sum"] -= (location[1] - subPointDataElement["longitude"]) * hWeight
                        biases[ context ]["altitude sum"] -= (location[2] - subPointDataElement["altitude"]) * vWeight
                        biases[ context ]["count"] += 1



    point = readNextData()


for cont in biases.keys():
    if (biases[cont]["latitude weight"] > 0 and
        biases[cont]["longitude weight"] > 0 and
        biases[cont]["altitude weight"] > 0):
        latitude_bias = biases[cont]["latitude sum"] / biases[cont]["latitude weight"]
        longitude_bias = biases[cont]["longitude sum"] / biases[cont]["longitude weight"]
        altitude_bias = biases[cont]["altitude sum"] / biases[cont]["altitude weight"]
        new_lat = contexts[cont]["origin"]["latitude"] + latitude_bias
        new_lon = contexts[cont]["origin"]["longitude"] + longitude_bias
        new_alt = contexts[cont]["origin"]["altitude"] + altitude_bias
        print( cont + " : distance change : " + str(geopy.distance.geodesic((new_lat, new_lon, new_alt  ), ( contexts[cont]["origin"]["latitude"],
                                         contexts[cont]["origin"]["longitude"], new_alt)).m) + " alt :" + str( new_alt - contexts[cont]["origin"]["altitude"]))
        contexts[cont]["origin"]["latitude"] = new_lat 
        contexts[cont]["origin"]["longitude"] = new_lon
        contexts[cont]["origin"]["altitude"] = new_alt

contextorigins.writeContexts()
