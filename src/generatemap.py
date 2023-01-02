import math
import json
import re

import contextorigins
from contexttranslations import translateToLL, translateToPlot
from contextorigins import contexts, plot

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
    for rec in rectangles:
        Feature = { "type"       : "Feature",
                    "properties" : {
                        "fill"   : "rgb"+department_colors[rec["department"]],
                        "label"  : rec["label"]
                    }
                    }
 
        coordinates = list()
        for point in rec["coordinates"]:
            
            pointLL = translateToLL( contexts[ rec["context"] ]["origin"],
                                                  { "x" : point[0], "y" : -point[1] },
                                                  contexts[ rec["context"] ]["units"] )
            coordinates.append( [ pointLL["longitude"], pointLL["latitude"] ] )

        Feature["geometry"] = { "type" : "Polygon",
                              "coordinates" : [ coordinates  ] }
        Features.append( Feature )
    return Features


def polygons_to_table ( Polygons ):
    centertable = list()
    for rec in rectangles:

        midpoint_r = midpoint( rec["coordinates"])  
        midpoint_LL = translateToLL( contexts[ rec["context"] ]["origin"],
                                                  {"x" : midpoint_r[0], "y" : -midpoint_r[1]},
                                                  contexts["The Home Depot"]["units"] )
        
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
CenterTable = polygons_to_table( rectangles ) 

open("mapGEO.json", "w").write(
     json.dumps( { "type" : "FeatureCollection",
                  "features" : JSONFeatures }, indent=4 ) )

def findInTable(bayName, context, table):

    conversions = { "meter" : 1,
                    "mm"    : 0.001,
                    "inch"  : 0.0254 }


    if re.search("^-?[0-9]+,-?[0-9]+,-?[0-9]+$",bayName):
        bayNameNumbers = bayName.split(",")

        LL = translateToLL( contexts[ context ]["origin"],
                                                  {"x" : int(bayNameNumbers[0]), "y" : -int(bayNameNumbers[1])},
                                                  contexts["The Home Depot"]["units"] )
        return (LL["latitude"],  LL["longitude"], contexts[context]["origin"]["altitude"] + int(bayNameNumbers[2]) * conversions[ contexts[ context ]["units"] ])

    if re.search("^-?[0-9]+,-?[0-9]+$",bayName):
        bayNameNumbers = bayName.split(",")
        return (int(bayNameNumbers[0]), int(bayNameNumbers[1]), 35)

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
                return ( l["latitude"], l["longitude"], l["altitude"] + z * conversions[ contexts[ l["context"] ]["units"] ])
    print( "Not found in table: {} : {}".format(bayName, context))

    pp=open("notintable.txt", "a")
    pp.write(str(currentDataFile) + ":" + str(context) + ":" + str(bayName) + "\n")
    pp.close()

    return tuple()

pointXYZDepotTable = {}
def resolveLocationLL(locationLabel, context, table):
    if (locationLabel, context) in pointXYZDepotTable.keys():
        return pointXYZDepotTable[locationLabel]
    lat=0
    lon=0
    alt=0
    n=0
    for part in locationLabel.split(" "):
        loc=findInTable(part, context, table)
        if len(loc) == 3:
            n=n+1
            lat=lat+loc[0]
            lon=lon+loc[1]
            alt=alt+loc[2]
    if n > 0:
        LL = (lat/n, lon/n, alt/n)
        pointXYZDepotTable[ (locationLabel, context)] = LL
        return LL
    else:
        return ()


