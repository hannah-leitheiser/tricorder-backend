import json
import random
import math
import geopy.distance
import pyproj
from scipy.optimize import minimize 
import scipy.stats
import numpy
import datetime
import os


inertialModelDirectory = "data_file_library_inertial_models/"

fileData = dict()

def guassianPDF(deviation, sigma):
    return (1/(sigma*(2*math.pi)**0.5))(math.e ** (-0.5 * (deviation/sigma)**2))

def normalized(a, axis=-1, order=2):
    l2 = numpy.atleast_1d(numpy.linalg.norm(a, order, axis))
    l2[l2==0] = 1
    return a / numpy.expand_dims(l2, axis)

def DownVector( latitude, longitude, altitude ):
    trans = pyproj.Transformer.from_crs( pyproj.crs.CRS("WGS84"),"+proj=geocent")
    p1 = trans.transform( latitude, longitude, altitude )
    p2 = trans.transform( latitude, longitude, altitude - 0.1 )
    return ( normalized( ( p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2] )  )[0] )

def EastVector( latitude, longitude, altitude ):
    trans = pyproj.Transformer.from_crs( pyproj.crs.CRS("WGS84"),"+proj=geocent")
    p1 = trans.transform( latitude, longitude, altitude )
    p2 = trans.transform( latitude, longitude + 0.0001, altitude )
    return ( normalized( ( p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2] ) )[0] )

def NorthVector( latitude, longitude, altitude ):
    trans = pyproj.Transformer.from_crs( pyproj.crs.CRS("WGS84"),"+proj=geocent")
    p1 = trans.transform( latitude, longitude, altitude )
    p2 = trans.transform( latitude+0.0001, longitude, altitude + 0.1 )
    return ( normalized( ( p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2] ) )[0]  )


class inertialModel:

    def __init__(self):
        self.parameters = None
        self.timeBias = None
        self.functionsForProbability = list()
        self.simpleData = list()
        self.times = list()
        self.sigmaVertical = list()
        self.sigmaHorizontal = list()
        self.sigmaVelocity = list()
        self.uncertainties = None
        self.stationary = False
        self.meters_per_lat = 1
        self.meters_per_lon = 1
        self.modelLatLonSimplified = True

    def inertialFunctionPrediction( self, time, derivativeDegree = 0 ):
        if self.parameters == None:
            #print("inertialFunctionPrediction: no parameters.")
            return None
        time = time - self.timeBias
        ret = []
        #print(terms)
        for vec in self.parameters:
            result=0
            for t in range(len(vec)):
                factor = vec[t]
                power = t
                for d in range(derivativeDegree):
                    factor = factor * power
                    power = power - 1
                    if power < 0:
                        power = 0
                        factor = 0
                result = result + factor*time**power
            ret.append(float(result))
        return ret

    def inertialFunctionPredictionLatLonAlt ( self, time ):
        p3d = self.inertialFunctionPrediction(time)
        if self.modelLatLonSimplified:
            return p3d
        trans = pyproj.Transformer.from_crs( "+proj=geocent", pyproj.crs.CRS("WGS84"))
        return trans.transform( p3d[0], p3d[1], p3d[2] )

    def probForAddMeasurementLatLon( self, time, latitude, longitude, uncertaintyHorizontal):
        p = self.inertialFunctionPredictionLatLonAlt( time )
        if p == None:
            return 0
        else:
            if self.modelLatLonSimplified:
                distanceHorizontal =  (( (latitude - p[0] ) * self.meters_per_lat) ** 2 +
                                       ( (longitude - p[1]) * self.meters_per_lon) ** 2 ) 
            else:
                predictedLatLong = (p[0], p[1])
                distanceHorizontal = geopy.distance.geodesic((latitude, longitude), predictedLatLong).m
            return -0.5 * ((distanceHorizontal / uncertaintyHorizontal)**2 )

    def addMeasurementLatLon( self, time, latitude, longitude, uncertaintyHorizontal):
        self.functionsForProbability.append( lambda s : s.probForAddMeasurementLatLon(time, latitude, longitude, uncertaintyHorizontal ) )
        self.sigmaHorizontal.append(uncertaintyHorizontal)
        self.times.append( time )
        return

    def probForAddMeasurementLatLonAlt( self, time, latitude, longitude, altitude, uncertaintyHorizontal, uncertaintyVertical):
        p = self.inertialFunctionPredictionLatLonAlt( time )
        predictedAlt     = p[2]
        distanceVertical = abs( altitude - predictedAlt)
        if self.modelLatLonSimplified:
            distanceHorizontal =  (( (latitude - p[0] ) * self.meters_per_lat) ** 2 +
                                   ( (longitude - p[1]) * self.meters_per_lon) ** 2 ) 
        else:
            predictedLatLong = (p[0], p[1])
            distanceHorizontal = geopy.distance.geodesic((latitude, longitude), predictedLatLong).m
        return -0.5 * ((distanceHorizontal / uncertaintyHorizontal)**2 + (distanceVertical / uncertaintyVertical ) ** 2)

    def addMeasurementLatLonAlt( self, time, latitude, longitude, altitude, uncertaintyHorizontal, uncertaintyVertical ):
        self.simpleData.append( (time, latitude, longitude, altitude, uncertaintyHorizontal ) )
        self.functionsForProbability.append( lambda s : s.probForAddMeasurementLatLonAlt(time, latitude, longitude, altitude, uncertaintyHorizontal, uncertaintyVertical ) )
        self.sigmaHorizontal.append(uncertaintyHorizontal)
        self.sigmaVertical.append(uncertaintyVertical)
        self.times.append( time )
        return

    def specifyStationary( self ):
        self.stationary = True
        if self.parameters != None and len(self.parameters[0]) != 1:
            for i in range(len(self.parameters)):
                self.parameters[i] = self.parameters[i][0:1]
            print("Stationary parameters:" + str(self.parameters))

    def probForAddMeasurementAlt( self, time, altitude, uncertaintyVertical):
        p = self.inertialFunctionPredictionLatLonAlt( time )
        predictedAlt     = p[2]
        distanceVertical = abs( altitude - predictedAlt)
        #return guassianPDF( distanceHorizontal, uncertaintyHorizontal) * guassianPDF( distanceVertical, uncertaintyVertical)
        return -0.5 * ((distanceVertical / uncertaintyVertical ) ** 2)

    def addMeasurementAlt      ( self, time, altitude, uncertaintyVertical ):
        self.functionsForProbability.append( lambda s : s.probForAddMeasurementAlt(time, altitude, uncertaintyVertical ) )
        self.sigmaVertical.append(uncertaintyVertical)
        self.times.append( time)
        return


    def probForAddMeasurementVelocity( self, time, velocityDown, velocityEast, velocityNorth, uncertainty):        
        p_v = self.inertialFunctionPrediction( time, 1 )
        if self.modelLatLonSimplified:
            predVelDown = -p_v[2]
            predVelEast = p_v[1] * self.meters_per_lon
            predVelNorth = p_v[0] * self.meters_per_lat
        else:
            p = self.inertialFunctionPredictionLatLonAlt( time  )
            predVelDown = numpy.dot( p_v, DownVector(p[0], p[1], p[2]))
            predVelEast = numpy.dot( p_v, EastVector(p[0], p[1], p[2]))
            predVelNorth = numpy.dot( p_v, NorthVector(p[0], p[1], p[2]))


        #print (  ("velocity", (predVelDown - velocityDown),
        #         (predVelEast - velocityEast),
        #          (predVelNorth - velocityNorth) ))
        #return guassianPDF( distance
        return -0.5 * (  ((predVelDown - velocityDown) / uncertainty)**2 + 
                         ((predVelEast - velocityEast) / uncertainty)**2 +
                         ((predVelNorth - velocityNorth) / uncertainty) ** 2 )


    def addMeasurementVelocity ( self, time, velocityDown, velocityEast, velocityNorth, accuracy):
        self.functionsForProbability.append( lambda s : s.probForAddMeasurementVelocity(time, velocityDown, velocityEast, velocityNorth, accuracy ) )
        self.sigmaVelocity.append(accuracy)
        self.times.append(time)
        return


    def probForAddMeasurementSpeedHorizontal( self, time, speed, uncertainty):        
        p_v = self.inertialFunctionPrediction( time, 1 )
        if self.modelLatLonSimplified:
            predVelEast = p_v[1] * self.meters_per_lon
            predVelNorth = p_v[0] * self.meters_per_lat
        else:
            p = self.inertialFunctionPredictionLatLonAlt( time  )
            predVelEast = numpy.dot( p_v, EastVector(p[0], p[1], p[2]))
            predVelNorth = numpy.dot( p_v, NorthVector(p[0], p[1], p[2]))

        predSpeed = (( predVelEast ** 2 ) + ( predVelNorth ** 2) ) ** 0.5
        #print (  ("velocity", (predVelDown - velocityDown),
        #         (predVelEast - velocityEast),
        #          (predVelNorth - velocityNorth) ))
        #return guassianPDF( distance
        return -0.5 * (  ((speed - predSpeed) / uncertainty)**2 )


    def addMeasurementSpeedHorizontal ( self, time, speed, accuracy):
        self.functionsForProbability.append( lambda s : s.probForAddMeasurementSpeedHorizontal(time, speed, accuracy ) )
        return



    def probForAddMeasurementHeading( self, time, heading, uncertainty): 
        if uncertainty == 0:
            return None
        p_v = self.inertialFunctionPrediction( time, 1 )
        if self.modelLatLonSimplified:
            predVelEast = p_v[1] * self.meters_per_lon
            predVelNorth = p_v[0] * self.meters_per_lat
        else:
            p = self.inertialFunctionPredictionLatLonAlt( time  )
            predVelEast = numpy.dot( p_v, EastVector(p[0], p[1], p[2]))
            predVelNorth = numpy.dot( p_v, NorthVector(p[0], p[1], p[2]))

        predHeading = math.degrees(math.atan2(predVelEast, predVelNorth) )
        predHeading = (predHeading + 360.0) % 360.0

        diff = predHeading - heading
        if abs(diff - 360) < abs(diff):
            diff = diff - 360
        if abs(diff + 360) < abs(diff):
            diff = diff + 360
        return -0.5 * (  ((diff) / uncertainty)**2 )


    def addMeasurementHeading ( self, time, heading, accuracy):
        self.functionsForProbability.append( lambda s : s.probForAddMeasurementHeading(time, heading, accuracy ) )
        return





    def computeProb( self ):
        probSum = 0
        for fun in self.functionsForProbability:
            probSum += fun(self)
        return probSum


    def computeTstatistic( self ):
        if len(self.functionsForProbability) == 0 or self.parameters == None:
            return None
        t = 0
        for fun in self.functionsForProbability:
            t += (fun(self) / -0.5) ** 0.5
        return (t / len(self.functionsForProbability)**0.5, len(self.functionsForProbability))

    def computeProbForOptimizer( self, x, vec_index1, vec_index2 ):
        self.parameters[vec_index1][vec_index2] = x
        return -self.computeProb()


    def metersPerLatLon(self):
            if self.modelLatLonSimplified and self.timeBias:
                meanPosition = self.inertialFunctionPredictionLatLonAlt(self.timeBias)
                if meanPosition:
                    #print( meanPosition )
                    delta = 0.00001
                    distanceNorth = geopy.distance.geodesic((meanPosition[0], meanPosition[1], meanPosition[2]), (meanPosition[0]+delta, meanPosition[1], meanPosition[2])).m
                    distanceEast = geopy.distance.geodesic((meanPosition[0], meanPosition[1], meanPosition[2]), (meanPosition[0], meanPosition[1]+delta, meanPosition[2])).m
                    self.meters_per_lat = distanceNorth / delta
                    self.meters_per_lon = distanceEast / delta
            else:
                    self.meters_per_lat = 1
                    self.meters_per_lon = 1



    def optimizeParameters( self, recompute = False, quick=False ):
        if self.parameters == None or recompute:
            if len(self.simpleData) == 0:
                return None
            self.times = sorted(self.times)
            print((self.times[0], self.times[-1]))
            self.timeBias = (self.times[-1] + self.times[0]) / 2

    
            if not self.modelLatLonSimplified:
                trans = pyproj.Transformer.from_crs( pyproj.crs.CRS("WGS84"), "+proj=geocent")
            points_3D_X = []
            points_3D_Y = []
            points_3D_Z = []
            points_3D_Accuracy = []
            points_3D_Time = []


            for p in self.simpleData:                
                if self.modelLatLonSimplified:
                    p_t = (p[1], p[2], p[3])
                else:
                    p_t = trans.transform(p[1], p[2], p[3])
                #print(p_t)
                points_3D_X.append( p_t[0])
                points_3D_Y.append( p_t[1])
                points_3D_Z.append( p_t[2])
                points_3D_Accuracy.append(1/(p[4]))
                points_3D_Time.append( p[0] - self.timeBias )

            if len(self.simpleData) < 10 or self.stationary:
                DOF=0
            else:
                DOF=1
            polyFitX, cov1 = numpy.polyfit( points_3D_Time, points_3D_X, DOF, w=points_3D_Accuracy, cov='unscaled')
            polyFitY, cov2 = numpy.polyfit( points_3D_Time, points_3D_Y, DOF, w=points_3D_Accuracy, cov='unscaled')
            polyFitZ, cov3 = numpy.polyfit( points_3D_Time, points_3D_Z, DOF, w=points_3D_Accuracy, cov='unscaled' )
            if len(cov1) > 1:
                self.sigmaVelocity.append(  numpy.sqrt(numpy.diag(cov1))[0] )
            self.parameters =  [ (list(reversed(list(polyFitX)))), (list(reversed(list(polyFitY)))), 
                        (list(reversed(list(polyFitZ)))) ]
            #print(self.parameters)
        
        self.metersPerLatLon()

        if quick == False:
            iter = 0
            paraChange = True
            while( iter < 3 and paraChange ):
                iter = iter + 1
                print( (self.timeBias, self.parameters))
                oldPara = self.parameters
                for v in range(len(self.parameters)):
                    for t in range(len(self.parameters[v])):
                        parameterInitial = self.parameters[v][t]
                        self.parameters[v][t] = float(minimize ( lambda x, self, v, t : self.computeProbForOptimizer(x, v, t), parameterInitial, (self, v, t), method='Nelder-Mead').x)   
                if self.parameters == oldPara:
                    paraChange = False

        speed = 0
        p_v = self.inertialFunctionPrediction( self.timeBias, 1 )
        if self.modelLatLonSimplified:
            if self.meters_per_lon == 1 or self.meters_per_lat == 1:
                print("meters_per = 1")
                exit()
            #print( " parameters: " + str(self.parameters))
            #print( " derivative: " + str(p_v))
            predVelDown = -p_v[2]
            predVelEast = p_v[1] * self.meters_per_lon
            predVelNorth = p_v[0] * self.meters_per_lat
            speed = ((predVelDown **2 ) + (predVelEast ** 2) + (predVelNorth ** 2)) ** 0.5
            #print( " speed    : " + str(speed))
            if speed > 60:
                print("Too fast, inertial_model!!!!")
                print("simpleData")
                print(self.simpleData)
                print("speed")
                print(speed)
                print( (p_v, predVelDown, predVelEast, predVelNorth))
                print(self.parameters)
                print(self.timeBias)
                print("Make stationary?", end="")
                response = input()
                if "Y" in response.upper():
                    self.specifyStationary()
                else:
                    exit()


        return self.parameters

    def computeUncertainty(self, recompute = False):
        if self.uncertainties == None or recompute:
        
            t = self.computeTstatistic()
            if t != None:
                t_goal = scipy.stats.t.ppf( 0.95, df=t[1]-1)
                print( "t: {:}, t_goal: {:}".format(t[0], t_goal))

            uncertainties = dict()
            for measure in [ ("horizontal",self.sigmaHorizontal), ("vertical",self.sigmaVertical), ("velocity",self.sigmaVelocity) ]:
                sigmaSum=0
                for m in measure[1]:
                    sigmaSum += 1/m**2
                if sigmaSum > 0:
                    uncertainties[ measure[0] ] = (1/sigmaSum)**0.5
                else:
                    uncertainties[ measure[0] ] = 0


            if len(self.times) == 0:
                return None
            self.times = sorted(self.times)
            duration = (self.times[-1] - self.times[0])/2
            velocityAdd = duration * uncertainties["velocity"]
            if self.stationary:
                velocityAdd = 0
            print(velocityAdd)

            self.uncertainties = {"horizontal" : uncertainties["horizontal"] + velocityAdd, "vertical": uncertainties["vertical"] + velocityAdd }
        return self.uncertainties

    def saveToFile(self, timestamp):
        t = datetime.datetime.fromtimestamp( timestamp, datetime.timezone.utc)
        fileName = "{:04}-{:02}-{:02}.txt".format( t.year, t.month, t.day)

        outputFile = open("data_file_library_inertial_models/" + fileName,"a")
        if self.parameters == None:
            self.optimizeParameters()
        data = {"timestamp" : timestamp, "parameters" : self.parameters, "time bias" : self.timeBias, "uncertainties" : self.computeUncertainty() }
        print(data)
        outputFile.write(json.dumps(data,indent=3,sort_keys=True))
        outputFile.write("\n" + "*"*32 + "\n")
        outputFile.close()

    def readFromData(self, timestamp, data):
        t = datetime.datetime.fromtimestamp( timestamp, datetime.timezone.utc)
        fileName = "{:04}-{:02}-{:02}.txt".format( t.year, t.month, t.day)
        if fileName in fileData.keys():
            if timestamp in fileData[fileName].keys():
                data = fileData[fileName][timestamp]
                self.parameters = data["parameters"]
                self.timeBias = data["time bias"]
                self.uncertainties = data["uncertainties"]
                return True
        return False
    def readFromFile(self, timestamp):
        global fileData
        t = datetime.datetime.fromtimestamp( timestamp, datetime.timezone.utc)
        fileName = "{:04}-{:02}-{:02}.txt".format( t.year, t.month, t.day)
        if fileName not in fileData.keys():
            dataFileList_ = os.listdir("data_file_library_inertial_models/")
            for f in dataFileList_:
                if fileName in f:
                    dataFile = open("data_file_library_inertial_models/" + f)
                    trackDataString=""
                    line = ""
                    done = False
                    fileData = { fileName : dict() }
                    while ( done == False ) :
                        while ( "*"*32 not in line and done == False):
                            trackDataString = trackDataString + line
                            line = dataFile.readline()
                            if line == "":
                                done=True
                        if len(line) > 0:
                            data = json.loads(trackDataString)
                            if data != None:
                                timestamp = data["timestamp"]
                                fileData[fileName][timestamp] = data
                        trackDataString=""
                        line=""
        return self.readFromData(timestamp, fileData )


