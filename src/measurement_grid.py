gridResolutions=[ 50000,20000, 15000, 10000, 5000, 2500, 1000, 500, 250, 100, 50, 25, 10, 5, 2, 1 ]
#gridResolution= 10

measurementGrid = dict()
for r in gridResolutions:
    measurementGrid[r] = dict()
import statistics
import math

def addToGrid(x_orig, y_orig, measurementType, measurement):


    for r in gridResolutions:
        x = x_orig
        y = y_orig
        gridResolution = r
        #init Grid, if necessary
        if measurementType not in measurementGrid[r].keys():
            measurementGrid[r][measurementType] = dict()
        
        x=int(x*gridResolution)
        y=int(y*gridResolution)

        if x not in measurementGrid[r][measurementType].keys():
            measurementGrid[r][measurementType][x] = dict()

        if y not in measurementGrid[r][measurementType][x].keys():
            measurementGrid[r][measurementType][x][y] = list()

        if type(measurement) == type(list()):
            for m in measurement:
                measurementGrid[r][measurementType][x][y].append(m)
        else:
                measurementGrid[r][measurementType][x][y].append(measurement)


import scipy.stats

semRequired = { "Geiger": 1*1.96,
                "WifiCount": 1*1.96,
                "CO2" : 50*1.96,
                "TVOC" : 50*1.96,
                "Part>0.3" : 100*1.96,
                "Part>0.5" : 100*1.96,
                "Part>1.0" : 100*1.96,
                "Part>2.5" : 100*1.96,
                "Part>5.0" : 100*1.96,
                "Part>10.0" : 100*1.96,
                "eCO2" : 100*1.96 }

def determineMeasurementGridRanges():

    for r in gridResolutions:
        gridResolution = r
        total=0
        measurement = "Histogram"
        for x in measurementGrid[r][measurement].keys():
            for y in measurementGrid[r][measurement][x].keys():
                total = total + len(measurementGrid[r][measurement][x][y] )

        for x in measurementGrid[r][measurement].keys():
            for y in measurementGrid[r][measurement][x].keys():
                measurementGrid[r][measurement][x][y] = [ 10*math.log( ((len(measurementGrid[r][measurement][x][y])) / total)) / math.log(10) ]


        for measurement in measurementGrid[r].keys():
            minV = 1e100
            maxV = -1e100
            for x in measurementGrid[r][measurement].keys():
                for y in measurementGrid[r][measurement][x].keys():
                    if measurement == "Histogram" or (len(measurementGrid[r][measurement][x][y]) > 3 and scipy.stats.sem( measurementGrid[r][measurement][x][y]) < semRequired[measurement]):
                        value = statistics.mean( measurementGrid[r][measurement][x][y] )
                        if value < minV:
                            minV = value
                        if value > maxV:
                            maxV = value
            measurementGrid[r][measurement]["max"] = maxV
            measurementGrid[r][measurement]["min"] = minV
