from create_map import *
from read_data_file_library import *
import datetime
from pytz import timezone
from inertial_model import *
from measurement_grid import * 
from save_transmitter import *

newMapDate = 1639900000
newEquipDate = 1658462830

startReadingData(["2022","2023"])
point = readNextData()
earliestPoint = point["timestamp"]
wifis = 0
cells = 0


while(point != dict()):
    iModel = inertialModel()
    if iModel.readFromFile(point["timestamp"]):
        
        for subpoint in point["subpoints"]:
            if subpoint["measurement type"] == "wifi scan" or subpoint["measurement type"] == "cell scan":
                loc = iModel.inertialFunctionPredictionLatLonAlt( subpoint["timestamp"]  )
                uncertainty = iModel.computeUncertainty()
                if loc and uncertainty and "horizontal" in uncertainty:
                    uncertainty = iModel.computeUncertainty()["horizontal"] 
                    requiredUncertainty = 6
                    if (loc[0] > 44.976323 and 
                            loc[0] < 44.976732 and
                            loc[1] < -93.353022 and
                            loc[1] > -93.353655):
                            requiredUncertainty = 0.1
                    else:
                        if geopy.distance.geodesic( ( loc[0], loc[1] ),(44.9650269,-93.3526834) ).m < 100:
                            requiredUncertainty = 1
                    if uncertainty < requiredUncertainty:
                        if subpoint["measurement type"] == "wifi scan":
                            #print("  === Adding wifi transmitter === ")
                            for w in subpoint["data"]:
                                if "SSID" not in w:
                                    w["SSID"] = ""

                                wifis += 1
                                addToTransmitterData( "wifi", w["BSSID"] + "_" + str(w["frequency"])[0] + "G_" + w["SSID"], {"latitude":loc[0], "longitude":loc[1], "altitude":loc[2], "accuracy, horizontal":uncertainty }, w["level"], subpoint["source"], subpoint["timestamp"])

                        if ("cell scan" ==  subpoint["measurement type"]):
                            #print("  === Adding cell transmitter === ")
                            for w in subpoint["data"]:
                                name=""
                                for prop in sorted(w.keys()):
                                    if prop != "strength, asu" and prop != "timestamp" and prop != "strength, dbm" and prop != "strength, level" and prop != "LTE bandwidth, kHz" and prop != "operator, long" and prop != "timing advance":
                                        shortNames = { "LTE absolute RF channel number": "CH", "LTE cell identity" : "ID", "LTE mobile country code" : "CC", "LTE mobile network code": "NC", "LTE mobile network operator" : "NO", "LTE physical cell id": "PID", "LTE tracking area code" : "TAC", "operator, short" : "op" }
                                        if prop in shortNames.keys():
                                            name = name + "_" + shortNames[prop] + "=" + str(w[prop])
                                        else:
                                            name = name + "_" + prop + "=" + str(w[prop])
                                                    
                                if "strength, dbm" in w.keys():
                                    #print(name)
                                    cells+=1

                                    addToTransmitterData( "cell", name, {"latitude":loc[0], "longitude":loc[1], "altitude":loc[2], "accuracy, horizontal":uncertainty }, w["strength, dbm"], subpoint["source"], subpoint["timestamp"])







    if point["timestamp"] % 86400 == 0 and earliestPoint != point["timestamp"]:
        print( "Wifis : {:} Cells : {:}".format( wifis, cells))
        #if seconds == 0:
        #    break;
        wifis = 0
        cells = 0
    point = readNextData()

