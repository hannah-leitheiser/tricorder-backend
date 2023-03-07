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
    parameters = None
    timeBias = None
    functionsForProbability = list()
    simpleData = list()
    times = list()
    sigmaVertical = list()
    sigmaHorizontal = list()
    sigmaVelocity = list()
    uncertainties = None
    stationary = False


    def inertialFunctionPrediction( self, time, derivativeDegree = 0 ):
        if self.parameters == None:
            print("inertialFunctionPrediction: no parameters.")
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
                result = result + factor*time**power
            ret.append(float(result))
        return ret

    def inertialFunctionPredictionLatLonAlt ( self, time ):
        trans = pyproj.Transformer.from_crs( "+proj=geocent", pyproj.crs.CRS("WGS84"))
        p3d = self.inertialFunctionPrediction(time)
        return trans.transform( p3d[0], p3d[1], p3d[2] )

    def probForAddMeasurementLatLon( self, time, latitude, longitude, uncertaintyHorizontal):
        p = self.inertialFunctionPredictionLatLonAlt( time )
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
        predictedLatLong = (p[0], p[1])
        predictedAlt     = p[2]
        distanceHorizontal = geopy.distance.geodesic((latitude, longitude), predictedLatLong).m
        distanceVertical = abs( altitude - predictedAlt)
        #return guassianPDF( distanceHorizontal, uncertaintyHorizontal) * guassianPDF( distanceVertical, uncertaintyVertical)
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
        p = self.inertialFunctionPredictionLatLonAlt( time  )
        p_v = self.inertialFunctionPrediction( time, 1 )
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

    def computeProb( self ):
        probSum = 0
        for fun in self.functionsForProbability:
            probSum += fun(self)
        return probSum


    def computeTstatistic( self ):
        t = 0
        for fun in self.functionsForProbability:
            t += (fun(self) / -0.5) ** 0.5
        return (t / len(self.functionsForProbability)**0.5, len(self.functionsForProbability))

    def computeProbForOptimizer( self, x, vec_index1, vec_index2 ):
        self.parameters[vec_index1][vec_index2] = x
        return -self.computeProb()

    def optimizeParameters( self, recompute = False ):
        if self.parameters == None or recompute:
            self.times = sorted(self.times)
            self.timeBias = (self.times[-1] + self.times[0]) / 2

    
            trans = pyproj.Transformer.from_crs( pyproj.crs.CRS("WGS84"), "+proj=geocent")
            points_3D_X = []
            points_3D_Y = []
            points_3D_Z = []
            points_3D_Accuracy = []
            points_3D_Time = []


            for p in self.simpleData:
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
            self.parameters =  [ (list(reversed(list(polyFitX))) + [0,0])[:2], (list(reversed(list(polyFitY))) + [0,0])[:2], 
                        (list(reversed(list(polyFitZ))) + [0,0])[:2] ]
        
        iter = 0
        paraChange = True
        while( iter < 3 and paraChange ):
            iter = iter + 1
            print( (self.timeBias, self.parameters))
            oldPara = self.parameters
            for v in range(len(self.parameters)):
                for t in range(len(self.parameters[v])):
                    parameterInitial = self.parameters[v][t]
                    self.parameters[v][t] = float(minimize ( lambda x, self, v, t : self.computeProbForOptimizer(x, v, t), parameterInitial, (self, v, t)).x)   
            if self.parameters == oldPara:
                paraChange = False
        return self.parameters

    def computeUncertainty(self, recompute = False):
        if self.uncertainties == None or recompute:
        
            t = self.computeTstatistic()
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
        print("Writing "+ t.isoformat() )
        fileName = "{:04}-{:02}-{:02}.txt".format( t.year, t.month, t.day)

        outputFile = open("data_file_library_inertial_models/" + fileName,"a")
        data = {"timestamp" : timestamp, "parameters" : self.optimizeParameters(), "time bias" : self.timeBias, "uncertainties" : self.computeUncertainty() }
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


