import geopy.distance
import math
import random
import json
#import matplotlib.pyplot as plt
import statistics
import os

deviceDirectories = []
for dd in os.listdir("."):
    if "transmitter_data_" in dd:
        for d in os.listdir(dd+"/"):
            deviceDirectories.append(dd+"/" + d + "/")
wifiFiles = []
for d in deviceDirectories:
    for f in os.listdir(d):
        if "_SOLUTION.txt" not in f:
            if not os.path.exists((d+f)[:-5]+"_SOLUTION.txt"):
                wifiFiles.append(d + f)


def extractSSID(wifiFile):
    return wifiFile.split("/")[-1][:17]
wifiFiles = sorted(wifiFiles, key=extractSSID)


meterL = 360/ 40e6


pValueRange = 0.90

def meanLL(l):
    sumLat=0
    sumLon = 0
    for ll in l:
        sumLat = sumLat + ll[0]
        sumLon = sumLon + ll[1]
    return ( sumLat / len(l), sumLon / len(l) )

def stdDevLL(l):
    mean = meanLL(l)
    var2=0
    for ll in l:
        r = geopy.distance.geodesic( mean, ll).m
        var2 = var2 + r**2
    return math.sqrt( var2 / len(l) )

def convertToLinearLevel(sig):
    if sig > 0:
        print(sig)
    return 10 ** (sig / 10)

# l = c / r^2
# l * r^2 = c
# c / l = r^2
def predicted(sig, c):
    return math.sqrt(  c / convertToLinearLevel(sig) ) 
def predictedUncertainty(sig, c):
    plusMinus = 5
    mean = predicted(sig, c)
    deviation_low = (mean - predicted( sig-plusMinus, c)) ** 2
    deviation_high = (mean - predicted(sig+plusMinus, c)) ** 2
    if deviation_low > deviation_high:
        return math.sqrt( deviation_low)
    return math.sqrt(deviation_high)



def makeData():
    latitude = 45
    longitude = -93
    data=[]
    name="MyWifi"
    for x in range(-50,-20,1):
        for y in range(-50,10,5):
            accuracy = random.random() * 40 + 5
            #accuracy = 1
            la = latitude + 1/100000 * x + 1*accuracy*(random.random()-0.5)*meterL
            lo = longitude + 1/10000 * y + 1*accuracy*(random.random()-0.5)*meterL
            r = geopy.distance.geodesic( (la, lo), (latitude, longitude) ).m
            if r > 0:
                sig = 10 * (math.log(1 / r**2) / math.log(10)) + 1*(random.random()-0.5)*3
                data.append( {   "name" : name,
                                "position" : {
                                 "latitude" :la,
                                 "accuracy, horizontal" :accuracy,
                                 "longitude" : lo },
                                 "level" : sig
                                  } )
    return data

def startReadingData(fileName):
    #global dataFileList
    global dataFile
    #idataFileList_ = os.listdir("data_file_library/")
    #for f in dataFileList_:
    #    if "unsorted" not in f:
    #        dataFileList.append("data_file_library/"+f)
    #dataFileList = sorted(dataFileList)
    #dataFile = open(dataFileList.pop(0), "r")
    dataFile = open(fileName, "r")


def readNextData():
    #global dataFileList
    global dataFile
    levelNotGood = True
    while( levelNotGood):
        trackDataString=""
        line = ""
        while ( "*"*32 not in line):
            trackDataString = trackDataString + line
            line = dataFile.readline()
            if line == "":
                #if len(dataFileList) > 0:
                #    dataFile = open(dataFileList.pop(0), "r")
                #    line = dataFile.readline()
                #else:
                return dict()
        data = json.loads(trackDataString)
        data["level"] = int(data["level"])
        if data["level"] < 1:
            levelNotGood = False
    return data

for f in wifiFiles:

    if f.split("/")[-1][:5] == "cell_":
        transmitterType = "cell"
    else:
        transmitterType = "wifi"
    data = []
    startReadingData(f)
    newData = readNextData()
    while ( newData != dict() ):
        #if "accuracy, horizontal" in newData:
        data.append(newData)
        newData = readNextData()
    #data= makeData()
    print( f + " : " + str(len(data)))
    minimumPoints = 300
    if transmitterType == "wifi":
        minimumPoints = 200


    if(len(data) > minimumPoints):
        origData = data
        #if len(data) > 50000:
        #    data = data[::  len(data) // 50000]


        # c/r^2 = l

        # find mean C
        latSum = 0
        latWeightSum = 0
        lonSum = 0
        lonWeightSum = 0
        for d in data: 
            
            if d["position"]["accuracy, horizontal"] > 0:
                latWeight = 1/(d["position"]["accuracy, horizontal"]**2)  +  convertToLinearLevel(d["level"])
                latSum = latSum + latWeight*d["position"]["latitude"]
                latWeightSum = latWeightSum + latWeight
                lonWeight = (1/d["position"]["accuracy, horizontal"]**2) * convertToLinearLevel(d["level"])
                lonSum = lonSum + lonWeight*d["position"]["longitude"]
                lonWeightSum = lonWeightSum + lonWeight
            else:
                print("accuracy, horizontal = 0")


        guesses = []

        la =latSum/latWeightSum
        lo =lonSum/lonWeightSum

        guesses.append( (la, lo) )

        print((la, lo))

        # c = l * r^2

        # c/l = r^2
        # sqrt( c/l) = r_p

        # minimum of (r_p - r_a) ** 2 / (r_accuracy) ** 2
        #  (r_p - (r_a+(p*x)))**2 / (r_accuracy) ** 2
        # (r_p - r_a - px ) **2 / (r_acc ** 2) = 0
        # p * (r_p - r_a - px) / (r_acc ** 2) = 0
        # p* (r_p - r_a - px) / (r_acc ** 2) = 0
        # x * sum [ p^2/ r_acc**2 ] = sum [ p*r_p / r_acc**2 - p*r_a / r_acc**2 ] 


        # minimum (r_p - (r_a + ax))^2 = 0
        # a2 * (r_p - r_a - ax) = 0
        # a*r_p - a*r_a = a*a*x
        # (sum(a*r_p) - sum(a*r_a)) / sum(a^2) = x



        Delta = 1/500000
        increasing = 0
        decreasing = 0
        cont=True
        it=0
        c_list = []

        if len(data) > 10000:
            data = data[::  len(data) // 10000]
        while(it < 1 and cont):
            it=it+1
            for u in ["la", "lo"]:


                cMin = 10e10
                cSum = 0
                cWeight = 0
                cData = []
                rlist= []

                for d in data:
                    r = geopy.distance.geodesic( (la, lo), (d["position"]["latitude"], d["position"]["longitude"])).m
                    rlist.append(r)
                maxDistance = sorted(rlist)[ int( len(rlist) * pValueRange)-1 ]
                if maxDistance < 30: 
                    maxDistance = 40
                print( "Max Distance: " + str(maxDistance))
                for d in data:
                    r = geopy.distance.geodesic( (la, lo), (d["position"]["latitude"], d["position"]["longitude"])).m
                    
                    if r < maxDistance and r > 0:
                        val = convertToLinearLevel( d["level"] ) * r**2
                        uncertaintyLinearLevel = -(convertToLinearLevel( d["level"] ) - convertToLinearLevel( d["level"] + 5 ))
                        reluncertaintyr = d["position"]["accuracy, horizontal"] / r
                        uncertainty = math.sqrt( (uncertaintyLinearLevel / convertToLinearLevel(d["level"]) )**2 + 2 * reluncertaintyr**2) * val
                        cData.append( (  convertToLinearLevel( d["level"] ) * r**2,
                                                 uncertainty ))



                sumC = 0
                sumWeight = 0
                for dd in cData:
                    weight_c = 1/ dd[1]**2
                    sumC = sumC + weight_c * dd[0]
                    sumWeight = sumWeight + weight_c

                cNew = sumC / sumWeight 
                print( "c: {}".format(cNew))
                #if cNew*2 > c:
                #    exit()
                c_list.append(cNew)
                if len(c_list) > 5:
                    c_list = c_list[-5:]
                c = statistics.mean(c_list)
                #c=1
                #if c > 0.0001:
                #    c = 0.0001

                r_p_sum = 0
                p2_sum = 0

                for d in data:
                    r = geopy.distance.geodesic( (la, lo), (d["position"]["latitude"], d["position"]["longitude"])).m
                    if r < maxDistance:
                        if u == "la":
                            r2 = geopy.distance.geodesic( (la+Delta, lo), (d["position"]["latitude"], d["position"]["longitude"])).m
                        if u == "lo":
                            r2 = geopy.distance.geodesic( (la, lo+Delta), (d["position"]["latitude"], d["position"]["longitude"])).m
                        p = (r2- r)/ Delta
                        sigma = (predictedUncertainty( d["level"], c) ** 2 + d["position"]["accuracy, horizontal"]**2)

                        r_p_sum = r_p_sum + ((
                            p*predicted( d["level"],c ) / 
                                sigma

                            ) - (
                            (p * r) / sigma ))
                        p2_sum = p2_sum  + (((p*p) / sigma))

                x=(r_p_sum / p2_sum)*0.5
                print( "x = " + str((2*x)/meterL) + " " + u)

                """
                plot1=[]
                plot2=[]
                for d in data:
                    r = geopy.distance.geodesic( (la, lo), (d["position"]["latitude"], d["position"]["longitude"])).m
                    if r < maxDistance:
                        rp = predicted( d["level"],c )
                        if rp > 1000 or r > 1000:
                            print((c, rp, r, d))
                        plot1.append(r)
                        plot2.append(rp)
                plt.figure()
                plt.figure(figsize=(8, 6), dpi=160)
                plt.scatter(plot1, plot2, s=0.1)
                plt.ylabel('some numbers')
                plt.savefig( "{:04}.png".format(it)) 
                plt.close()"""

                #print( ( r_p_sum, p2_sum, x ) )
                if transmitterType == "cell":
                    maxMovement = 20
                else:
                    maxMovement = 5
                if x > meterL*maxMovement:
                    x = meterL*maxMovement
                if x < -meterL*maxMovement:
                    x = -meterL*maxMovement

                theTest=""" 
                if u == "la" and it > 3:
                    for oo in range(50):
                        dev = 0
                        for d in data:
                            r = geopy.distance.geodesic( (la, lo), (d["position"]["latitude"], d["position"]["longitude"])).m
                            if r < maxDistance:
                                x_dev = x + (oo-25)*0.00001
                                r = geopy.distance.geodesic( (la, lo), (d["position"]["latitude"], d["position"]["longitude"])).m
                                if u == "la":
                                    r2 = geopy.distance.geodesic( (la+Delta, lo), (d["position"]["latitude"], d["position"]["longitude"])).m
                                if u == "lo":
                                    r2 = geopy.distance.geodesic( (la, lo+Delta), (d["position"]["latitude"], d["position"]["longitude"])).m
                                p = (r2- r)/ Delta

                                r_predicted = predicted( d["level"] ,c) 
                                r_predicted_uncertainty = predictedUncertainty(d["level"],c) 

                                if u == "lo":
                                    r_updated = geopy.distance.geodesic( (la, lo+x_dev), (d["position"]["latitude"], d["position"]["longitude"])).m

                                if u == "la":
                                    r_updated = geopy.distance.geodesic( (la+x_dev, lo), (d["position"]["latitude"], d["position"]["longitude"])).m
                                #r_updated = r + p*x_dev
                                r_updated_uncertainty = d["position"]["accuracy, horizontal"]
                                #print( (r_updated_g, r_updated))
                                dev = dev + (r_predicted - r_updated)**2/(( r_predicted_uncertainty**2 + r_updated_uncertainty**2))
                        print( "{},{},{}".format(oo, la+x_dev, dev) )
                    exit()
                    """




                if u == "la":
                    la = la + x
                    #print(" la: {}, d: {}".format( la, geopy.distance.geodesic( (la, lo), (45,-93)).m))
                if u == "lo":
                    lo = lo + x
                    #print(" lo: {}, d: {}".format( lo, geopy.distance.geodesic( (la, lo), (45,-93)).m))
                    guesses.append( (la, lo, cNew) )
                    print( "guess" + str ( (la, lo)) )


            if len(guesses) > 10:
                print( "delta: {}, stdDev: {} ".format(x, stdDevLL(guesses[-10:])))
            if len(guesses) > 20:
                if stdDevLL( guesses[-10:] ) < stdDevLL( guesses[-20:] ):
                    decreasing = decreasing + 1
                else:
                    increasing = increasing + 1
            if increasing > 20:
                print("increasing too much, breaking.")
                cont=False
            if transmitterType == "cell":
                stdDev = 5
            else:
                stdDev = 0.5
            if len(guesses) > 10 and stdDevLL( guesses[-10:] ) < stdDev:
                print("down to 50 cm, breaking.")
                cont=False


        print(guesses)
        o = open(f[:-5]+"_SOLUTION.txt","w")
        o.write("{ \"latitude\" : " + str(guesses[-1][0]) + ", \"longitude\" : " + str(guesses[-1][1]) + ", \"power\" : " + str( int(10*(  math.log(guesses[-1][2]) / math.log(10)))) + ", \"n\" : " + str(len(data)) +"  }\n")


        if f.split("/")[-1][:4] == "cell":
            geoFileName =  "data/xmtr_cell_" + f.split("/")[-1][6:-5]+"_GEO.json"
        else:
            geoFileName =  "data/xmtr_" + f.split("/")[-1][0:22]+"_GEO.json"
        if os.path.exists(geoFileName):
            geoJSON = json.loads( open(geoFileName).read() )
        else:
            geoJSON = { "type" : "FeatureCollection",
                        "features" : [] }
        

        distanceMultiple = 0.1 # meters
        center = (guesses[-1][0], guesses[-1][1])

        delta = 0.000001
        dLat = distanceMultiple * (delta/((geopy.distance.geodesic( center, (center[0] + delta, center[1]))).m))
        dLon = distanceMultiple * (delta/((geopy.distance.geodesic( center, (center[0] , center[1] + delta))).m))

        pointSet = set()
        for d in origData:
            pointSetPoint = (int(   (d["position"]["latitude"] - center[0]) / dLat), int( (d["position"]["longitude"] - center[1]) / dLon))
            if pointSetPoint not in pointSet:
                pointSet = pointSet.union( { pointSetPoint } )
                geoJSON["features"].append( {

                         "type": "Feature",
                         "properties": {
                           "level" : d["level"],
                           "uncertainty" : d["position"]["accuracy, horizontal"]},
                          "geometry" : { 
                                "type": "Point",
                                "coordinates": [
                        d["position"]["longitude"], d["position"]["latitude"] ]
                          } } )


        line = ""
        line = line + (" {\n\"type\":\"Feature\",\n\"properties\":\n")
        line = line +(" { \"level\":" + str(d["level"]) + "},\n")
        line = line +(" \"geometry\": { \n\"type\":\"LineString\",\n\"coordinates\": [")
        notFirst = False
        for g in guesses: 
            if notFirst:
                line=line+(",")

            notFirst = True
            line = line + ("["+ str(g[1]) + ","+ str(g[0]) + "] ")

        line = line + ("\n\n] }}")

        geoJSON["features"].append( json.loads( line ) )

        open(geoFileName, "w").write( json.dumps( geoJSON ))







