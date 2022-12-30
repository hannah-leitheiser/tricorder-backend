import math
import json

import contextorigins
from contexttranslations import translateToLL, translateToPlot
from contextorigins import contexts, plot

svg=open("index.html", "w")
mapfile = open("map2.txt", "r")

offsetx=0
offset=offsetx

rectangles=[]

department="28"

# n - New
# h - no home
# H - New/NH

specials = [("03-013","n"),
            ("03-011","h"),

            ("51-001","H"),
            ("45-001","h"),
            ("45-003","n"),
            ("08-009","H"),
            ("09-008", "H"),
            ("11-012", "H"),
             ("36-002", "n"),
            ("36-004", "h"),
            ("33-012", "H"),
            ("18-020", "n"),
            ("18-018", "h"),
            ("25-002", "n"),
            ("25-004", "h")]

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


for x in range(len(rectangles)):
        rectangles[x] = rectangles[x]+(' ',)
        for special in specials:
            if rectangles[x][8] == special[0]:
                rectangles[x] = rectangles[x][:-1]+(special[1],)


departments = set()
for rec in rectangles:
    departments.add(rec[9])
departments.add("ALL")



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

afterFirst = False
for rec in rectangles:


    if afterFirst:
        geoJSONMapFile.write(",\n")

    afterFirst = True
    point1ll = translateToLL( contexts["The Home Depot"]["origin"],
                                              { "x" : rec[0], "y" : -rec[1] },
                                              contexts["The Home Depot"]["units"] )
    point2ll = translateToLL( contexts["The Home Depot"]["origin"],
                                              { "x" : rec[2], "y" : -rec[3] },
                                              contexts["The Home Depot"]["units"] )

    point3ll = translateToLL( contexts["The Home Depot"]["origin"],
                                              { "x" : rec[4], "y" : -rec[5]},
                                              contexts["The Home Depot"]["units"] )
    point4ll = translateToLL( contexts["The Home Depot"]["origin"],
                                              {"x" : rec[6], "y" : -rec[7]} ,
                                              contexts["The Home Depot"]["units"] )




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
    svg.write('<polygon points="'+str(point1[0])+','+
                                  str(point1[1])+' '+
                                  str(point2[0])+','+
                                  str(point2[1])+' '+
                                  str(point3[0])+','+
                                  str(point3[1])+' '+
                                  str(point4[0])+','+
                                  str(point4[1])+''+'"')

    midpoint = translateToLL( contexts["The Home Depot"]["origin"],
                                              {"x" : (rec[0]+rec[2]+rec[4]+rec[6])/4, "y" : -(rec[1]+rec[3]+rec[5]+rec[7])/4},
                                              contexts["The Home Depot"]["units"] )

    midpoint = translateToPlot( plot["origin"],  midpoint, plot["units"], plot["scale"])
    midpoint = (midpoint["x"],midpoint["y"] )


    #midpoint = translate((rec[0]+rec[2]+rec[4]+rec[6])/4-offset, (rec[1]+rec[3]+rec[5]+rec[7])/4, home_depot_origin_lat, home_depot_origin_long, home_depot_angle, "inch")


    svg.write( ' fill="rgb'+department_colors[rec[9]]+'" stroke="black" stroke-width="1" />')
    svg.write('<text x="'+str(  midpoint[0]-15) +'" y="'+str( midpoint[1]  )+'" font-size="9px">'+rec[8]+'</text>')

    #output.write("  \"" + rec[8] + "\", ")
    #output.write("  \"" + rec[9] + "\",")
    #output.write("   { " + str(  (rec[0] +rec[2] + rec[4] + rec[6])//4 ) + ", " +
    #                       str(  (rec[1]+rec[3]+rec[5]+rec[7])//4) + "}, \n")
    #output.write("   { " + str(rec[0]) + ", " + str(rec[2]) + ", " + str(rec[4]) + ", " + str(rec[6]) + ", " +
    #                       str(rec[1]) + ", " + str(rec[3]) + ", " + str(rec[5]) + ", " + str(rec[7]) + " },");
    #output.write("'" +rec[10]+"'},\n")


"""
pp=list()
pp = json.load(open("home_area.geojson"))["features"] + json.load(open("farm.geojson"))["features"]#+  json.load(open("grandpa_area.geojson"))["features"]

pp = pp+ json.load(open("home_area.geojson"))["features"]
#pp = list()

svg.write("<g id=\"osm geo data\">")
for feature in pp:
    if feature["geometry"]["type"] == "MultiPolygon":
        for polys in feature["geometry"]["coordinates"]:
            for poly in polys:

                svg.write('<polygon fill="none" stroke="#AAAAAA" stroke-width="10" class=\"geojson\" points="')
                for coord in poly:
                    point = translateToPlot( plot["origin"],  {"latitude":coord[1], "longitude" : coord[0] }, plot["units"], plot["scale"])
                    svg.write(" " + str(point["x"]) + "," + str(point["y"]))
                svg.write("\" />\n")


    if feature["geometry"]["type"] == "Polygon":
        for poly in feature["geometry"]["coordinates"]:
                svg.write('<polygon fill="none" stroke="#AAAAAA" stroke-width="10" class=\"geojson\" points="')
                for coord in poly:
                    point = translateToPlot( plot["origin"],  {"latitude":coord[1], "longitude" : coord[0] }, plot["units"], plot["scale"])
                    svg.write(" " + str(point["x"]) + "," + str(point["y"]))
                svg.write("\" />\n")

    if feature["geometry"]["type"] == "LineString":
        line = feature["geometry"]["coordinates"]
        for i in range(len(line) - 1):

            point1 = translateToPlot( plot["origin"],  {"latitude":line[i][1], "longitude" : line[i][0] }, plot["units"], plot["scale"])
            point2 = translateToPlot( plot["origin"],  {"latitude":line[i+1][1], "longitude" : line[i+1][0] }, plot["units"], plot["scale"])
            svg.write('<line fill="none" stroke="#AAAAFF" stroke-width="10" class=\"geojson\" ')
            svg.write(' x1=\"' + str(point1["x"]) + "\" ")
            svg.write(' y1=\"' + str(point1["y"]) + "\" ")
            svg.write(' x2=\"' + str(point2["x"]) + "\" ")
            svg.write(' y2=\"' + str(point2["y"]) + "\" ")
            svg.write("\" />\n")
svg.write("</g>\n")
svg.write("""


""")

"""


centertable = open("table.txt","w")
for rec in rectangles:
    centertable.write(rec[8]+":"+str(  (rec[0] +rec[2] + rec[4] + rec[6])//4) +':'+str( (rec[1]+rec[3]+rec[5]+rec[7])//4   )+"\n")
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


for x in range(len(rectangles)):
        rectangles[x] = rectangles[x]+(' ',)
        for special in specials:
            if rectangles[x][8] == special[0]:
                rectangles[x] = rectangles[x][:-1]+(special[1],)


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
    svg.write('<polygon points="'+str(point1[0])+','+
                                  str(point1[1])+' '+
                                  str(point2[0])+','+
                                  str(point2[1])+' '+
                                  str(point3[0])+','+
                                  str(point3[1])+' '+
                                  str(point4[0])+','+
                                  str(point4[1])+''+'"')



    midpoint = translateToLL( contexts["Apartment"]["origin"],
                                              {"x" : (rec[0]+rec[2]+rec[4]+rec[6])/4, "y" : -(rec[1]+rec[3]+rec[5]+rec[7])/4},
                                              contexts["Apartment"]["units"] )

    midpoint = translateToPlot( plot["origin"],  midpoint, plot["units"], plot["scale"])
    midpoint = (midpoint["x"],midpoint["y"] )

    svg.write( ' fill="rgb'+department_colors[rec[9]]+'" stroke="black" stroke-width="1" />')
    svg.write('<text x="'+str(  midpoint[0]-15) +'" y="'+str( midpoint[1]  )+'" font-size="9px">'+rec[8]+'</text>')

    #output.write("  \"" + rec[8] + "\", ")
    #output.write("  \"" + rec[9] + "\",")
    #output.write("   { " + str(  (rec[0] +rec[2] + rec[4] + rec[6])//4 ) + ", " +
    #                       str(  (rec[1]+rec[3]+rec[5]+rec[7])//4) + "}, \n")
    #output.write("   { " + str(rec[0]) + ", " + str(rec[2]) + ", " + str(rec[4]) + ", " + str(rec[6]) + ", " +
    #                       str(rec[1]) + ", " + str(rec[3]) + ", " + str(rec[5]) + ", " + str(rec[7]) + " },");
    #output.write("'" +rec[10]+"'},\n")
svg.write("""


""")


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


