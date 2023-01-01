import math
import json

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

def map_file_to_polygons( filename ):

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
                                         (posx + int(linesplit[x*2+4]), posy), 
                                         (posx+int(linesplit[x*2+4]), posy+int(linesplit[3])), 
                                         (posx , posy+int(linesplit[3])),
                                         (posx, posy) ],
                                         "label" : str(linesplit[x*2+5]), 
                                         "department" : department } )
                    posx = posx + int(linesplit[x*2+4])
            
            if linesplit[3].upper() == 'X':
                for x in range((len(linesplit)-4)//2):
                    rectangles.append( {"coordinates" : [ (posx, posy), 
                                        (posx, posy + int(linesplit[x*2+4])), 
                                        (posx+int(linesplit[2]), posy+int(linesplit[x*2+4])), 
                                        (posx+int(linesplit[2]) , posy),
                                        (posx, posy) ],
                                        "label" : str(linesplit[x*2+5]), 
                                        "department" : department } )
                    posy = posy + int(linesplit[x*2+4])

            if linesplit[3].upper() != 'X' and linesplit[2].upper() != 'X':
                    rectangles.append( { "coordinates" : [(posx, posy), 
                                        (posx, posy + int(linesplit[3])), 
                                        (posx+int(linesplit[2]), posy+int(linesplit[3])), 
                                        (posx+int(linesplit[2]) , posy),
                                        (posx, posy)],
                                        "label" : str(linesplit[4]), 
                                        "department" : department }  )

        
    return rectangles


rectangles = map_file_to_polygons("map2.txt")

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



geoJSONMapFile = open("data/" + "map"+"_GEO.json", "w")
geoJSONMapFile.write( """
      {"type" : "FeatureCollection",
         "features": [

         """)

centertable = open("table.txt","w")
afterFirst = False
for rec in rectangles:


    if afterFirst:
        geoJSONMapFile.write(",\n")

    afterFirst = True


    geoJSONMapFile.write( "{\n\"type\" : \"Feature\",\n")
    geoJSONMapFile.write( "\"properties\" : {\n")
    geoJSONMapFile.write( " \"fill\" : \"rgb"+department_colors[rec["department"]]+"\",\n")
    geoJSONMapFile.write( " \"label\" : \"" + rec["label"] + "\" },")

    geoJSONMapFile.write( "\"geometry\" : {\n  \"type\":\"Polygon\", \n \"coordinates\": [ \n \n")
    
    coordinates = list()
    for point in rec["coordinates"]:
        
        pointLL = translateToLL( contexts["The Home Depot"]["origin"],
                                              { "x" : point[0], "y" : -point[1] },
                                              contexts["The Home Depot"]["units"] )
        coordinates.append( [ str(pointLL["latitude"]), str(pointLL["longitude"]) ] )

    geoJSONMapFile.write( str( coordinates ) )
    geoJSONMapFile.write("] } }\n\n\n")

    midpoint_r = midpoint( rec["coordinates"])  
    midpoint_LL = translateToLL( contexts["The Home Depot"]["origin"],
                                              {"x" : midpoint_r[0], "y" : -midpoint_r[1]},
                                              contexts["The Home Depot"]["units"] )
    
    centertable.write(rec["label"]+":"+str( midpoint_LL["latitude"]) +':'+str( midpoint_LL["longitude"]   )+"\n")


centertable.close()



# ------------------- apartment --------------------------


mapfile = open("map_apartment.txt", "r")

offsetx = 0
offset=offsetx

rectangles=[]

department="28"

# n - New
# h - no home
# H - New/NH

for line in mapfile.readlines():
    if line[0].upper()=='D':
        department=line[1]+line[2]
    else:
        linesplit = line.split()
        posx = int(linesplit[0])
        posy = int(linesplit[1])
        if linesplit[2].upper() == 'X':
            for x in range((len(linesplit)-4)//2):
                rectangles.append( (posx+offsetx, posy,
                                    posx + int(linesplit[x*2+4])+offsetx, posy,
                                    posx+int(linesplit[x*2+4])+offsetx, posy+int(linesplit[3]),
                                    posx+offsetx , posy+int(linesplit[3]),
                                    str(linesplit[x*2+5]),department ) )
                posx = posx + int(linesplit[x*2+4])

        if linesplit[3].upper() == 'X':
            for x in range((len(linesplit)-4)//2):
                rectangles.append( (posx+offsetx, posy,
                                    posx+offsetx, posy + int(linesplit[x*2+4]),
                                    posx+int(linesplit[2])+offsetx, posy+int(linesplit[x*2+4]),
                                    posx+int(linesplit[2])+offsetx , posy,
                                    str(linesplit[x*2+5]), department ) )
                posy = posy + int(linesplit[x*2+4])

        if linesplit[3].upper() != 'X' and linesplit[2].upper() != 'X':
                rectangles.append( (posx+offsetx, posy,
                                    posx+offsetx, posy + int(linesplit[3]),
                                    posx+int(linesplit[2])+offsetx, posy+int(linesplit[3]),
                                    posx+int(linesplit[2])+offsetx , posy,
                                    str(linesplit[4]), department ) )




departments = set()
for rec in rectangles:
    departments.add(rec[9])
departments.add("ALL")

department_colors= {
                    "00": "(100,100,100)",
                    "21": "(255,196,196)",
                    "23": "(196,196,196)",
                    "24": "(255,255,128)",
                    "25": "(196,128,128)",
                    "26": "(128,128,255)",
                    "27": "(255,128,128)",
                    "28": "(128,192,128)",
                    "29": "(192,128,192)",
                    "30": "(255,192,128)" };


for rec in rectangles:


    if afterFirst:
        geoJSONMapFile.write(",\n")
    point1ll = translateToLL( contexts["Apartment"]["origin"],
                                              { "x" : rec[0], "y" : -rec[1] },
                                              contexts["Apartment"]["units"] )
    point2ll = translateToLL( contexts["Apartment"]["origin"],
                                              { "x" : rec[2], "y" : -rec[3] },
                                              contexts["Apartment"]["units"] )

    point3ll = translateToLL( contexts["Apartment"]["origin"],
                                              { "x" : rec[4], "y" : -rec[5]},
                                              contexts["Apartment"]["units"] )
    point4ll = translateToLL( contexts["Apartment"]["origin"],
                                              {"x" : rec[6], "y" : -rec[7]} ,
                                              contexts["Apartment"]["units"] )


    geoJSONMapFile.write( "{\n\"type\" : \"Feature\",\n")
    geoJSONMapFile.write( "\"properties\" : {\n")
    geoJSONMapFile.write( " \"fill\" : \"rgb"+department_colors[rec[9]]+"\",\n")
    geoJSONMapFile.write( " \"label\" : \"" + rec[8] + "\" },")

    geoJSONMapFile.write( "\"geometry\" : {\n  \"type\":\"Polygon\", \n \"coordinates\": [ \n \n")
    geoJSONMapFile.write('[ [ '+str(point1ll["longitude"])+','+
                                  str(point1ll["latitude"])+'], ['+
                                  str(point2ll["longitude"])+','+
                                  str(point2ll["latitude"])+'], ['+
                                  str(point3ll["longitude"])+','+
                                  str(point3ll["latitude"])+'], ['+
                                  str(point4ll["longitude"])+','+
                                      str(point4ll["latitude"])+'],[' +
                                      str(point1ll["longitude"])+','+
                                      str(point1ll["latitude"])+''+' ] ]\n')
    geoJSONMapFile.write("] } }\n\n\n")




    point1 = translateToPlot( plot["origin"],  point1ll, plot["units"], plot["scale"])
    point2 = translateToPlot( plot["origin"],  point2ll, plot["units"], plot["scale"])
    point3 = translateToPlot( plot["origin"],  point3ll, plot["units"], plot["scale"])
    point4 = translateToPlot( plot["origin"],  point4ll, plot["units"], plot["scale"])


    point1 = ( point1["x"], point1["y"] )
    point2 = ( point2["x"], point2["y"] )
    point3 = ( point3["x"], point3["y"] )
    point4 = ( point4["x"], point4["y"] )

    #point1 = translate(rec[0]-offset, rec[1], home_depot_origin_lat, home_depot_origin_long, home_depot_angle, "inch")
    #point2 = translate(rec[2]-offset, rec[3], home_depot_origin_lat, home_depot_origin_long, home_depot_angle, "inch")
    #point3 = translate(rec[4]-offset, rec[5], home_depot_origin_lat, home_depot_origin_long, home_depot_angle, "inch")
    #point4 = translate(rec[6]-offset, rec[7], home_depot_origin_lat, home_depot_origin_long, home_depot_angle, "inch")



    midpoint = translateToLL( contexts["Apartment"]["origin"],
                                              {"x" : (rec[0]+rec[2]+rec[4]+rec[6])/4, "y" : -(rec[1]+rec[3]+rec[5]+rec[7])/4},
                                              contexts["Apartment"]["units"] )

    midpoint = translateToPlot( plot["origin"],  midpoint, plot["units"], plot["scale"])
    midpoint = (midpoint["x"],midpoint["y"] )



geoJSONMapFile.write("] }")
geoJSONMapFile.close()

centertable = open("table_apartment.txt","w")
for rec in rectangles:
    centertable.write(rec[8]+":"+str(  (rec[0] +rec[2] + rec[4] + rec[6])//4) +':'+str( (rec[1]+rec[3]+rec[5]+rec[7])//4   )+"\n")
centertable.close()


offsetx = 0
offset=offsetx


DepotTable=open("table.txt","r").readlines()


def findInTable(bayName, context):

    if re.search("^-?[0-9]+,-?[0-9]+,-?[0-9]+$",bayName):
        bayNameNumbers = bayName.split(",")
        return (int(bayNameNumbers[0]), int(bayNameNumbers[1]), int(bayNameNumbers[2]))

    if re.search("^-?[0-9]+,-?[0-9]+$",bayName):
        bayNameNumbers = bayName.split(",")
        return (int(bayNameNumbers[0]), int(bayNameNumbers[1]), 35)

    if context == "The Home Depot":
        table=DepotTable
    if context == "Apartment":
        table=open("table_apartment.txt","r").readlines()
    for l in table:
        if (bayName).replace("\n","").replace("#","").replace("$","").replace("%","").split(",")[0].upper() in (l.split(":")[0]).upper().split(","):
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
            return ( int(l.split(":")[1]), int(l.split(":")[2]), z)
    print( "Not found in table: {} : {}".format(bayName, context))

    pp=open("notintable.txt", "a")
    pp.write(str(currentDataFile) + ":" + str(context) + ":" + str(bayName) + "\n")
    pp.close()

    return tuple()


