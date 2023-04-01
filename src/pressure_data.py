from create_map import *
from read_data_file_library import *
import datetime
import pytz
from metar import Metar
import csv
import geopy.distance 

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

def altitudeFromSubpoint( timestamp, pressure, latitude, longitude ):
    distance = geopy.distance.geodesic((latitude, longitude), (44.9, -93.3)).m
    if distance < 50000:
        t = timestamp // 300
        if t in presData:
            return altitude( pressure, presData[t]["p"], 0, presData[t]["t"] )
    return None

