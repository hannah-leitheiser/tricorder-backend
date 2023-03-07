from generatemap import *
from readData import *
import datetime
import pytz
from metar import Metar
import csv

newMapDate = 1639900000
newEquipDate = 1658462830

startReadingData()
point = readNextData()

locationList = dict()

maxFreq = dict()
checkForBadContext = True

def altitude(pressure_actual, pressure_reference, height_reference, temperature):
    temperature = 288.15
    gravitational=9.80665                                    
    Molar = 0.0289644                                        
    R = 8.3144598                                            
    lapse = -0.0065                                          
    exponent = -gravitational*Molar/(R * lapse)              
    return ((((pressure_actual/pressure_reference) ** (1/exponent)) - 1) * temperature)/lapse + height_reference



pressure = list()
reference = list()
gps      = open("gps.txt", "w")

# Function to decode METAR data
def decode_metar(metar_str):
    try:
        obs = Metar.Metar(metar_str)
    except:
        print("Exception")
        return None
    # Your METAR decoding code goes here
    return obs

# Open the METAR data file
with open('metar_data.csv') as csvfile:
    # Read the CSV file
    csvreader = csv.reader(csvfile, delimiter=',')
    
    # Loop through each row in the file
    for row in csvreader:
        # Get the METAR string from the row
        metar_str = row[5]
        
        # Decode the METAR string
        decoded_metar = decode_metar(metar_str)
        
        if decoded_metar != None and decoded_metar.press != None and decoded_metar.temp != None:
            year = int(row[1][0:4])
            month = int(row[1][5:7])
            hour = int(row[1][8:10])
            minute = int(row[1][11:13])
            second = int(row[1][14:16])

            timestamp = pytz.utc.localize( datetime.datetime(year, month, hour, minute, second) ).timestamp()
            reference.append(( timestamp, row[0], decoded_metar.press.value("HPA")/1, decoded_metar.temp.value("K"), float(row[4])))
        # Print the decoded METAR data
        #print(decoded_metar)

presData = dict()
for record in reference:
    t = record[0] // 300
    if t not in presData.keys():
        presData[t] = {"p": [], "t": []}
    presData[ t ]["p"].append(record[2])
    presData[ t ]["t"].append(record[3])

for t in presData.keys():
    presData[t]["p"] = sum(presData[t]["p"]) / len(presData[t]["p"])
    presData[t]["t"] = sum(presData[t]["t"]) / len(presData[t]["t"])

alt = list()


colors = { "Pixel 3 XL" : (0.7,0,0),
           "Pixel 4"    : (0.5,0,0),
           "Pixel 3 XLg" : (0, 0.8,0),
           "Pixel 4g"    : (0, 0.3, 0),
           "BMP390"     : (1,0,0),
           "ZED-F9Pg"    : (0, 0.5, 0),
           "NEO-M9Ng"    : (0, 0.7, 0),
           "GT-U7g"      : (0,1,0),
           "specified"        : (0,0,1) }

while(point != dict() and len(pressure) < 10000000):
    for subpoint in point["subpoints"]:
        if subpoint["measurement type"] == "location - gps" and "accuracy, vertical" in subpoint["data"][0] and "altitude" in subpoint["data"][0] and float(subpoint["data"][0]["accuracy, vertical"]) < 12.0:
            s= str(subpoint["timestamp"]) + "," + subpoint["source"] + "," + str(subpoint["data"][0]["altitude"]) +"," + str( subpoint["data"][0]["accuracy, vertical"])
            alt.append( ( subpoint["timestamp"], subpoint["source"]+"g", subpoint["data"][0]["altitude"]))
            #print(s)
            if subpoint["source"]+"g" not in colors:
                exit()
            gps.write(s+"\n")
    
        if subpoint["measurement type"] == "specified location":
            name = subpoint["data"][0]["label"]
            context = subpoint["data"][0]["context"]
            location = resolveLocationLL( name, context, CenterTable)
            if context == "Apartment":
                uncert = 0.1
            else:
                uncert = 0.5
            s= str( subpoint["timestamp"])+",specified,"+str( location[2])+","+str( uncert)
            gps.write(s+"\n")
            alt.append( ( subpoint["timestamp"], "specified", location[2]))
            print(s)
        if subpoint["measurement type"] == "pressure":
            s= str( subpoint["timestamp"]) + "," + str(subpoint["source"]) + "," + str(subpoint["data"][0]["Value"])
            pressure.append( (subpoint["timestamp"], subpoint["source"], subpoint["data"][0]["Value"] ) )
            #print(s)
        if subpoint["measurement type"] == "altimeter":
            s= str( subpoint["timestamp"]) + "," + str(subpoint["source"]) + "," + str(subpoint["data"][0]["pressure"])
            pressure.append( (subpoint["timestamp"], subpoint["source"], subpoint["data"][0]["pressure"] ) )
            #print(s)

    point = readNextData()

import numpy as np
import matplotlib.pyplot as plt

x = list()
y = list()
color = list()
r=""
for p in pressure:
    if p[0] > 1676872800 and p[0] < 1676872800 + 86400*2:

        x.append(p[0] / 86400)
        t = p[0]//300
        y.append( altitude(float(p[2]), presData[t]["p"],0, presData[t]["t"]  ))
        if p[1] in colors:
            color.append( colors[ p[1] ] )
        else:
            print(p[1])
            exit()

for p in alt:
    if p[0] > 1676872800 and p[0] < 1676872800 + 86400*2:

        x.append(p[0] / 86400)
        y.append( p[2] )
        if p[1] in colors:
            color.append( colors[ p[1] ] )
        else:
            print(p[1])
            exit()

plt.scatter(x, y, c=color, s=0.05)
plt.show()
