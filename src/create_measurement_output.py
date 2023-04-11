from create_map import *
from read_data_file_library import *
import datetime
from pytz import timezone
from inertial_model import *
from measurement_grid import * 

dataDirectory = "/media/hannah/Tricorder/tricorder/tricorder-backend-map/data/" 

newMapDate = 1639900000
newEquipDate = 1658462830

startReadingData()
point = readNextData()
earliestPoint = point["timestamp"]
seconds = 0

def getMeasurements( data, measurement):
    measurements = list()
    for subpoint in data["subpoints"]:
        for d in subpoint["data"]:
            if measurement in d.keys():
                measurements.append( (d[measurement], subpoint["timestamp"]))
    return measurements

while(point != dict()):
    iModel = inertialModel()
    if iModel.readFromFile(point["timestamp"]):
        for x in range(point["interval"]):
            loc = iModel.inertialFunctionPredictionLatLonAlt( point["timestamp"] + x )
            if loc and iModel.computeUncertainty():
                seconds = seconds + 1
                #if loc[0] > 50:
                #    print("lat high")
                #    print(loc)
                #    print(point["timestamp"])
                #    print(x)
                #    print(iModel.parameters)
                #    exit()
                addToGrid( loc[0], loc[1], "Histogram", 1, iModel.computeUncertainty()["horizontal"])
        measurements = ["CO2","TVOC", "Part>0.3", "Part>0.5", "Part>1.0",
                                    "Part>1.0", "Part>2.5", "Part>5.0", "Part>10.0", "eCO2"]
        
        for subpoint in point["subpoints"]:
            if subpoint["measurement type"] == "wifi scan":
                wifiCount = len(subpoint["data"])
                loc = iModel.inertialFunctionPredictionLatLonAlt( subpoint["timestamp"]  )
                if loc and iModel.computeUncertainty():
                    addToGrid( loc[0], loc[1], "WifiCount", wifiCount, iModel.computeUncertainty()["horizontal"])



        meass = dict()
        for m in measurements:
            for p in getMeasurements( point, m):
                if m == "TVOC" and p[0] > 50000:
                    print("Too high TVOC, " + str(p[0]))
                else:
                    if m == "CO2" and p[0] == 0:
                        print("CO2 is zero")
                    else:
                        predictedLocation = iModel.inertialFunctionPredictionLatLonAlt( p[1])
                        if predictedLocation and iModel.computeUncertainty():
                            if m in meass:
                                meass[m]+=[p[0],]
                            else:
                                meass[m] = [p[0],1]
                            addToGrid( predictedLocation[0], predictedLocation[1], m, p[0], iModel.computeUncertainty()["horizontal"])



    if point["timestamp"] % 86400 == 0 and earliestPoint != point["timestamp"]:
        print( "Percentage found: {:}".format( (100 * seconds) / (point["timestamp"] - earliestPoint)))
        earliestPoint = point["timestamp"]
        if seconds == 0 and point["timestamp"] > datetime.datetime(2022,1,1).timestamp():
            break;
            "fff"
        seconds = 0
    point = readNextData()

determineMeasurementGridRanges()


for r in gridResolutions:
    gridResolution = r
    if r == gridResolutions[-1]:
        drawSVG = True
    else:
        drawSVG = False
    for measurement in measurementGrid[r].keys():
        afterFirst = False
        geoJSONFile = open(dataDirectory + measurement+"_"+ "{:06}".format(gridResolution) + "_GEO.json", "w")
        geoJSONFile.write( """
          {"type" : "FeatureCollection",
             "features": [

             """)
        print("Producing measurement: " + str(measurement) + " at resolution 1/" + str(gridResolution))
        print("  Max: " + str(measurementGrid[r][measurement]["max"]) + "  Min:"+ str(measurementGrid[r][measurement]["min"]))

        #if drawSVG:
        #    svg.write("<g id=\"" + measurement + "\">")
        for x in measurementGrid[r][measurement].keys():
            if x != "min" and x != "max":
                for y in measurementGrid[r][measurement][x].keys():

                    if measurement == "Histogram" or (len(measurementGrid[r][measurement][x][y]) > 3 and scipy.stats.sem( measurementGrid[r][measurement][x][y]) < semRequired[measurement]):
                        if afterFirst:
                            geoJSONFile.write(",\n")
                        afterFirst = True
                        value = statistics.mean(measurementGrid[r][measurement][x][y])

                        if measurementGrid[r][measurement]["max"] - measurementGrid[r][measurement]["min"] > 0:
                            proportion = (value -measurementGrid[r][measurement]["min"])  / (measurementGrid[r][measurement]["max"] - measurementGrid[r][measurement]["min"])
                        else:
                            proportion = 0
                        point1 = translateToPlot( plot["origin"],  {"latitude":x/gridResolution, "longitude":y/gridResolution}, plot["units"], plot["scale"])
                        point2 = translateToPlot( plot["origin"],  {"latitude":(x+1)/gridResolution, "longitude":y/gridResolution}, plot["units"], plot["scale"])
                        point3 = translateToPlot( plot["origin"],  {"latitude":(x+1)/gridResolution, "longitude":(y-1)/gridResolution}, plot["units"], plot["scale"])
                        point4 = translateToPlot( plot["origin"],  {"latitude":(x)/gridResolution, "longitude":(y-1)/gridResolution}, plot["units"], plot["scale"])

                        #if drawSVG:
                        #    svg.write('<polygon class="histogram" points="'+str(point1["x"])+','+
                        #                              str(point1["y"])+' '+
                        #                              str(point2["x"])+','+
                        #                              str(point2["y"])+' '+
                        #                              str(point3["x"])+','+
                        ##                              str(point3["y"])+' '+
                        #                              str(point4["x"])+','+
                        #                              str(point4["y"])+''+'" fill="hsl('+str(int( 260- (260 * proportion)   ))+',50%,50%)" fill-opacity="0.5" value="' + str(value)+'±'+str( scipy.stats.sem( measurementGrid[r][measurement][x][y]) * 2 ) + '" />')



                        point1ll = {"la":x/gridResolution, "lo":y/gridResolution}
                        point2ll = {"la":(x+1)/gridResolution, "lo":y/gridResolution}
                        point3ll = {"la":(x+1)/gridResolution, "lo":(y-1)/gridResolution}
                        point4ll = {"la":(x)/gridResolution, "lo":(y-1)/gridResolution}

                        geoJSONFile.write( "{\n\"type\" : \"Feature\",\n")
                        geoJSONFile.write( "\"properties\" : {\n")
                        geoJSONFile.write( "\"label\" : \"" + str(int(value)) + "\",\n")
                        geoJSONFile.write( " \"fill\" : \"hsl("+str(int( 260- (260*proportion)))+',50%,50%)" },')

                        geoJSONFile.write( "\"geometry\" : {\n  \"type\":\"Polygon\", \n \"coordinates\": [ \n \n")
                        geoJSONFile.write('[ [ '+str(point1ll["lo"])+','+
                                                      str(point1ll["la"])+'], ['+
                                                      str(point2ll["lo"])+','+
                                                      str(point2ll["la"])+'], ['+
                                                      str(point3ll["lo"])+','+
                                                      str(point3ll["la"])+'], ['+
                                                      str(point4ll["lo"])+','+
                                                      str(point4ll["la"])+'],[' +
                                                      str(point1ll["lo"])+','+
                                                      str(point1ll["la"])+''+' ] ]\n')
                        geoJSONFile.write("] } }\n\n\n")

                        midpoint = { "x" : (point1["x"] + point2["x"] + point3["x"] + point4["x"])/4,
                                     "y" : (point1["y"] + point2["y"] + point3["y"] + point4["y"])/4 }
                        #if drawSVG:
                        #    svg.write('<text class="' + measurement + '" x="'+str(  midpoint["x"]-0) +'" y="'+str( midpoint["y"]  )+'" font-size="120px" fill="hsl('+str(int( 260- (260*proportion)   ))+',50%,20%)" text-anchor="middle" dominant-baseline="central">'+str(int(value))+'</text>\n')


                        #    svg.write("\n")


        #if drawSVG:
        #    svg.write("</g>\n")
        geoJSONFile.write("] }")

#svg.write("</svg>\n</html>")
#svg.close()

