
import geopy.distance
import pyproj
from scipy.optimize import minimize 
import numpy

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


    def probForAddMeasurementLatLonAlt( self, time, latitude, longitude, altitude, uncertaintyHorizontal, uncertaintyVertical):
        p = self.inertialFunctionPredictionLatLonAlt( time )
        predictedLatLong = (p[0], p[1])
        predictedAlt     = p[2]
        distanceHorizontal = geopy.distance.geodesic((latitude, longitude), predictedLatLong).m
        distanceVertical = abs( altitude - predictedAlt)
        return -0.5 * ((distanceHorizontal / uncertaintyHorizontal)**2 + (distanceVertical / uncertaintyVertical ) ** 2)

    def addMeasurementLatLonAlt( self, time, latitude, longitude, altitude, uncertaintyHorizontal, uncertaintyVertical ):
        self.simpleData.append( (time, latitude, longitude, altitude, uncertaintyHorizontal ) )
        self.functionsForProbability.append( lambda s : s.probForAddMeasurementLatLonAlt(time, latitude, longitude, altitude, uncertaintyHorizontal, uncertaintyVertical ) )
        return

    def addMeasurementAlt      ( self, time, altitude, uncertainty ):
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

        return -0.5 * (  ((predVelDown - velocityDown) / uncertainty)**2 + 
                         ((predVelEast - velocityEast) / uncertainty)**2 +
                         ((predVelNorth - velocityNorth) / uncertainty) ** 2 )


    def addMeasurementVelocity ( self, time, velocityDown, velocityEast, velocityNorth, accuracy):
        self.functionsForProbability.append( lambda s : s.probForAddMeasurementVelocity(time, velocityDown, velocityEast, velocityNorth, accuracy ) )
        return

    def computeProb( self ):
        probSum = 0
        for fun in self.functionsForProbability:
            probSum += fun(self)
        return probSum

    def computeProbForOptimizer( self, x, vec_index1, vec_index2 ):
        self.parameters[vec_index1][vec_index2] = x
        return -self.computeProb()

    def optimizeParameters( self ):
        if self.parameters == None:
            times = list()
            for t in self.simpleData:
                times.append( t[0] )
            self.timeBias = sum(times) / len(times)

    
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

            if len(self.simpleData) < 10:
                DOF=0
            else:
                DOF=2
            polyFitX = numpy.polyfit( points_3D_Time, points_3D_X, DOF, w=points_3D_Accuracy )
            polyFitY = numpy.polyfit( points_3D_Time, points_3D_Y, DOF, w=points_3D_Accuracy )
            polyFitZ = numpy.polyfit( points_3D_Time, points_3D_Z, DOF, w=points_3D_Accuracy )
            self.parameters =  [ (list(reversed(list(polyFitX))) + [0,0])[:2], (list(reversed(list(polyFitY))) + [0,0])[:2], 
                        (list(reversed(list(polyFitZ))) + [0,0])[:2] ]


        print( (self.timeBias, self.parameters))
        for v in range(len(self.parameters)):
            for t in range(len(self.parameters[v])):
                parameterInitial = self.parameters[v][t]
                self.parameters[v][t] = float(minimize ( lambda x, self, v, t : self.computeProbForOptimizer(x, v, t), parameterInitial, (self, v, t)).x)
                                

        print(self.parameters)
        return

i = inertialModel()
for x in range(1):
    i.addMeasurementLatLonAlt( x, 45, -93, 400+x, 10, 20 )
i.addMeasurementVelocity( 5, -1, 0, 0, 0.01)
for x in range(10):
    i.optimizeParameters()
    for xx in range(7):
        print ( (xx,i.inertialFunctionPredictionLatLonAlt(xx)) )
