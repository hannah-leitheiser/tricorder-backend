def is_float(element: any) -> bool:
    #If you expect None to be passed:
    if element is None: 
        return False
    if element == "":
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False

def validateLocation( subpoint ):
    if "measurement type" in subpoint:
        if subpoint["measurement type"] == "location - gps" or subpoint["measurement type"] == "location - network":
            locationData = subpoint["data"][0]

            # validate latitude and longitude
            for a in ["latitude", "longitude"]:
                if a in locationData and is_float(locationData[a]):
                    locationData[a] = float(locationData[a])
                    if a=="latitude" and locationData[a] > 90 and locationData[a] < -90:
                        subpoint["validator response"] = "latitude invalid"
                        return subpoint
                    if a=="longutide" and locationData[a] > 180 and locationData[a] < -180:
                        subpoint["validator response"] = a+" invalid"
                        return subpoint
                else:
                    subpoint["validator response"] = "no "+a
                    return subpoint

            if "accuracy, horizontal" not in locationData or not is_float(locationData["accuracy, horizontal"]) or locationData["accuracy, horizontal"] == 0:
                    locationData["accuracy, horizontal"] = 10000
            else:
                    locationData["accuracy, horizontal"] = float(locationData["accuracy, horizontal"])
            if "accuracy, vertical" not in locationData or not is_float(locationData["accuracy, vertical"]) or locationData["accuracy, vertical"] == 0:
                    locationData["accuracy, vertical"] = 1000
            else:
                    locationData["accuracy, vertical"] = float(locationData["accuracy, vertical"])

            if ("altitude" in subpoint["data"][0] and is_float(subpoint["data"][0]["altitude"]) and float(subpoint["data"][0]["altitude"]) > 0 ):
                locationData["altitude"] = float(locationData["altitude"])
                locationData["validator reponse"] = "valid - altitude"
                subpoint["data"][0] = locationData
                return subpoint
            else:
                locationData["validator reponse"] = "valid"
                subpoint["data"][0] = locationData
                return subpoint
