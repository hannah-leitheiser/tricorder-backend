import math
import json
import re

import context_origins
from context_translations import translateToLL, translateToPlot
from context_origins import contexts, plot

def midpoint( points ):
    x=0
    y=0
    n=0
    for p in set(points):
        x+=p[0]
        y+=p[1]
        n+=1
    return (x/n, y/n)

def map_file_to_polygons( filename, context ):

    mapfile = open(filename, "r")
    rectangles=[]

    department="28"

    for line in mapfile.readlines():
        if line[0].upper()=='D':
            department=line[1]+line[2]
        else:
            print(line)
            linesplit = line.split()
            posx = int(linesplit[0])
            posy = int(linesplit[1])
            if linesplit[2].upper() == 'X':
                for x in range((len(linesplit)-4)//2):
                    rectangles.append( { "coordinates" : [ (posx, posy), 
                                         (posx, posy + int(linesplit[3])), 
                                         (posx+int(linesplit[x*2+4]), posy+int(linesplit[3])), 
                                         (posx + int(linesplit[x*2+4]), posy),
                                         (posx, posy) ],
                                         "label" : str(linesplit[x*2+5]), 
                                         "department" : department,
                                         "context"    : context } )
                    posx = posx + int(linesplit[x*2+4])
            
            if linesplit[3].upper() == 'X':
                for x in range((len(linesplit)-4)//2):
                    rectangles.append( {"coordinates" : [ (posx, posy), 
                                        (posx, posy + int(linesplit[x*2+4])), 
                                        (posx+int(linesplit[2]), posy+int(linesplit[x*2+4])), 
                                        (posx+int(linesplit[2]) , posy ),
                                        (posx, posy) ],
                                        "label" : str(linesplit[x*2+5]), 
                                        "department" : department,
                                        "context"    : context } )
                    posy = posy + int(linesplit[x*2+4])

            if linesplit[3].upper() != 'X' and linesplit[2].upper() != 'X':
                    rectangles.append( { "coordinates" : [(posx, posy), 
                                        (posx , posy + int(linesplit[3])), 
                                        (posx+int(linesplit[2]), posy+int(linesplit[3])), 
                                        (posx+int(linesplit[2]) , posy ),
                                        (posx, posy)],
                                        "label" : str(linesplit[4]), 
                                        "department" : department,
                                        "context"    : context }  )

        
    return rectangles


def polygons_to_geoJSON_features ( Polygons, DepartmentColors ):

    Features = list()
    for rec in Polygons:
        Feature = { "type"       : "Feature",
                    "properties" : {
                        "fill"   : "rgb"+department_colors[rec["department"]],
                        "label"  : rec["label"]
                    }
                    }
 
        coordinates = list()
        for point in rec["coordinates"]:
            
            pointLL = translateToLL( contexts[ rec["context"] ]["origin"],
                                                  { "x" : point[0], "y" : point[1] },
                                                  contexts[ rec["context"] ]["units"] )
            coordinates.append( [ pointLL["longitude"], pointLL["latitude"] ] )

        Feature["geometry"] = { "type" : "Polygon",
                              "coordinates" : [ coordinates  ] }
        Features.append( Feature )
    return Features


def polygons_to_svg ( Polygons, DepartmentColors ):
    svg = dict()
    ranges = dict()

    for rec in Polygons:
        if rec["context"] not in svg:
            svg[ rec["context"] ] = ""
            ranges[ rec["context"] ] = { "max X" : -1e100, "max Y" : -1e100, "min X" : 1e100, "min Y": 1e100 }


        svgAdd = '<polygon points="'

        xs = []
        ys = []
        pointSet = set()
        for point in rec["coordinates"]:
            if point not in pointSet:
                pointSet.add( point)
                if point[0] > ranges[ rec["context"] ]["max X"] :
                    ranges[ rec["context"] ]["max X"] = point[0]
                if point[0] < ranges[ rec["context"] ]["min X"] :
                    ranges[ rec["context"] ]["min X"] = point[0]
                if point[1] > ranges[ rec["context"] ]["max Y"] :
                    ranges[ rec["context"] ]["max Y"] = point[1]
                if point[1] < ranges[ rec["context"] ]["min Y"] :
                    ranges[ rec["context"] ]["min Y"] = point[1]
                xs.append( point[0])
                ys.append( point[1])
                svgAdd+= str(point[0]) + "," + str(point[1]) + " "

        svgAdd += '" fill="rgb'+DepartmentColors[ rec["department"] ]+'" stroke="black" stroke-width="1" />'

        if rec["context"] == "Apartment":
            fontSize = "100px"
        else:
            fontSize = "9px"
        svgAdd += '<text text-anchor="middle" dominant-baseline="middle" x="'+str( sum(xs)/len(xs)  -0) +'" y="'+str( sum(ys)/len(ys) +0 )+'" font-size="'+fontSize+'">'+rec["label"]+'</text>'
        svg[ rec["context"] ] += svgAdd + "\n\n"
    
    margin = 20
    for context in svg.keys():
        if context == "Apartment":
            percent = "100"
        else:
            percent = "100"
        svg[ context] = '<svg width="'+percent+'%" height="'+percent+'%" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="' + str(ranges[context]["min X"]-margin) + " " + str( ranges[context]["min Y"]-margin) + " " + str((ranges[context]["max X"]-ranges[context]["min X"])+margin*2) + " " + str((ranges[context]["max Y"] - ranges[context]["min Y"])+margin*2) + '" id="map">\n\n' + svg[context] + '\n</svg>'

    return svg



def polygons_to_table ( Polygons ):
    centertable = list()
    for rec in rectangles:

        midpoint_r = midpoint( rec["coordinates"])  
        midpoint_LL = translateToLL( contexts[ rec["context"] ]["origin"],
                                                  {"x" : midpoint_r[0], "y" : midpoint_r[1]},
                                                  contexts[ rec["context"]  ]["units"] )
        
        centertable.append( { "context" : rec["context"] , "label": rec["label"], "latitude":  midpoint_LL["latitude"], "longitude" : midpoint_LL["longitude"], 
                             "altitude": contexts[ rec["context"]]["origin"]["altitude"] } )
    return centertable




rectangles = map_file_to_polygons("map2.txt", "The Home Depot")
rectangles += map_file_to_polygons("map_apartment.txt", "Apartment")
department_colors= {
                    "00": "(100,100,100)",
                    "21": "(255,196,196)",
                    "22": "(225,225,196)",
                    "23": "(196,196,196)",
                    "24": "(255,255,128)",
                    "25": "(196,128,128)",
                    "26": "(128,128,255)",
                    "27": "(255,128,128)",
                    "28": "(128,192,128)",
                    "29": "(192,128,192)",
                    "30": "(255,192,128)" };
JSONFeatures = polygons_to_geoJSON_features( rectangles, department_colors)
svgMap =  polygons_to_svg( rectangles, department_colors) 
for context in svgMap.keys():
    f = open( context + "_map.svg", "w")
    f.write( svgMap[context] )
    f.close()
CenterTable = polygons_to_table( rectangles ) 

open("../tricorder-backend-map/data/mapGEO.json", "w").write(
     json.dumps( { "type" : "FeatureCollection",
                  "features" : JSONFeatures }, indent=4 ) )

def findInTable(bayName, context, table):

    conversions = { "meter" : 1,
                    "mm"    : 0.001,
                    "inch"  : 0.0254 }


    if re.search("^-?[0-9]+,-?[0-9]+,-?[0-9]+$",bayName):
        bayNameNumbers = bayName.split(",")

        LL = translateToLL( contexts[ context ]["origin"],
                                                  {"x" : int(bayNameNumbers[0]), "y" : int(bayNameNumbers[1]),"z" : int(bayNameNumbers[2]) },
                                                  contexts[ context ]["units"] )
        return LL

    if re.search("^-?[0-9]+,-?[0-9]+$",bayName):
        bayNameNumbers = bayName.split(",")

        LL = translateToLL( contexts[ context ]["origin"],
                                                  {"x" : int(bayNameNumbers[0]), "y" : int(bayNameNumbers[1]),"z" : 35 },
                                                  contexts[ context ]["units"] )
        return LL

    for l in table:
        if l["context"] == context:
            if (bayName).replace("\n","").replace("#","").replace("$","").replace("%","").split(",")[0].upper() == l["label"]:
                if len(bayName.split(",")) == 1:
                    z=35
                    if "%" in bayName:
                        z = (96+94+96)/3
                    if "#" in bayName:
                        z = (171+171+171)/3
                    if "$" in bayName:
                        z = (223+224+223)/3
                else:
                    z = int(bayName.split(",")[1])
                return { "latitude":l["latitude"], "longitude":l["longitude"], "altitude":l["altitude"] + z * conversions[ contexts[ l["context"] ]["units"] ] }
    print( "Not found in table: {} : {}".format(bayName, context))

    pp=open("notintable.txt", "a")
    pp.write(str(currentDataFile) + ":" + str(context) + ":" + str(bayName) + "\n")
    pp.close()

    return tuple()

pointXYZDepotTable = {}
def resolveLocationLL(locationLabel, context, table):
    if (locationLabel, context) in pointXYZDepotTable.keys():
        return pointXYZDepotTable[ (locationLabel, context) ]
    lat=0
    lon=0
    alt=0
    n=0
    for part in locationLabel.split(" "):
        loc=findInTable(part, context, table)
        if len(loc) == 3:
            n=n+1
            lat=lat+loc["latitude"]
            lon=lon+loc["longitude"]
            alt=alt+loc["altitude"]
    if n > 0:
        LL = (lat/n, lon/n, alt/n)
        pointXYZDepotTable[ (locationLabel, context)] = LL
        return LL
    else:
        return ()


