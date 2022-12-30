import math

from contextorigins import contexts

def toRadians(num):
    return (num/360)*2*math.pi


#    /+\ y (north)
#     |
#     |
#     |----> x
#    /
#   / z


def translateToLL(origin, point, unit):
    #map points to 2-space meters

    conversions = { "meter" : 1,
                    "mm"    : 0.001,
                    "inch"  : 0.0254 }

    if "z" not in point.keys():
        point["z"] = 0.0

    altitude = point["z"] * conversions[unit] + origin["altitude"]

    point = { "x": point["x"] * conversions[unit],
              "y": point["y"] * conversions[unit],
              "z": point["z"] * conversions[unit] }

    #rotate by rotation

    point = { "x" : point["x"]*math.cos(toRadians(origin["angle"])) - point["y"]*math.sin(toRadians(origin["angle"])),
        "y" : point["x"]*math.sin(toRadians(origin["angle"])) + point["y"]*math.cos(toRadians(origin["angle"])),
        "z" : point["z"] }

    #translate origin to Earth center
    earthRadius=6371008.7714
    point = { "x" : point["x"],
              "y" : point["y"],
              "z" : earthRadius }

    #trim point to earthRadius from origin

    z = math.sqrt( earthRadius ** 2 /
         (  ( point["x"] / point["z"] )**2 +
            ( point["y"] / point["z"] )**2 +
              1 )  )

    point = { "x" : z * (point["x"] / point["z"]),
              "y" : z * (point["y"] / point["z"]),
              "z" : z }

    #   /+\ y (north)
    #    |
    #    |
    #    |----> x
    #   /
    #  / z

    # do latitude transform, around x axis in our case

    latRadians = math.pi * 2 * origin["latitude"] / 360

    point = { "z" : point["z"]*math.cos(latRadians) - point["y"]*math.sin(latRadians),
        "y" : point["z"]*math.sin(latRadians) + point["y"]*math.cos(latRadians),
        "x" : point["x"] }

    # to longitude transform, around y axis in our case

    longRadians = math.pi * 2 * origin["longitude"] / 360

    point = { "z" : point["z"]*math.cos(longRadians) - point["x"]*math.sin(longRadians),
        "x" : point["z"]*math.sin(longRadians) + point["x"]*math.cos(longRadians),
        "y" : point["y"] }

    # determine point latitude

    latitude = 360*math.asin(point["y"]/earthRadius) / (math.pi*2)
    longitude = 360*math.acos(point["z"]/math.sqrt( point["x"]**2+point["z"]**2)) / (math.pi*2)
    if point["x"] < 0:
        longitude = -longitude


    return { "longitude" : longitude,
             "latitude"  : latitude,
             "altitude"  : altitude  }


#    /+\ y (north)
#     |
#     |
#     |----> x
#    /
#   / z


def translateToPlot(origin, point, unit, scale):
    #map point to 3-space Earth

    conversions = { "meter" : 1,
                    "mm"    : 0.001,
                    "inch"  : 0.0254 }

    #Earth center
    earthRadius=6371008.7714

    #    /+\ y (north)
    #     |
    #     |
    #     |----> x
    #    /
    #   / z
    #  * -- 0 lat, 0 long


    point = { "y" : math.sin(toRadians(point["latitude"]))*earthRadius,
              "x" : math.cos(toRadians(point["latitude"]))*earthRadius * math.sin(toRadians(point["longitude"])),
              "z" : math.cos(toRadians(point["latitude"]))*earthRadius * math.cos(toRadians(point["longitude"])) }


    # to longitude transform, around y axis in our case

    longRadians = -math.pi * 2 * origin["longitude"] / 360

    point = { "z" : point["z"]*math.cos(longRadians) - point["x"]*math.sin(longRadians),
        "x" : point["z"]*math.sin(longRadians) + point["x"]*math.cos(longRadians),
        "y" : point["y"] }


    # to latitude transform, around x axis in our case

    latRadians = -math.pi * 2 * origin["latitude"] / 360

    point = { "z" : point["z"]*math.cos(latRadians) - point["y"]*math.sin(latRadians),
        "y" : point["z"]*math.sin(latRadians) + point["y"]*math.cos(latRadians),
        "x" : point["x"] }

    #place points on plane at z=earthRadius

    point = { "x" : earthRadius * (point["x"] / point["z"]),
              "y" : earthRadius * (point["y"] / point["z"]),
              "z" : earthRadius }

    #rotate by rotation, z no longer matters

    point = { "x" : point["x"]*math.cos(-toRadians(origin["angle"])) - point["y"]*math.sin(-toRadians(origin["angle"])),
        "y" : point["x"]*math.sin(-toRadians(origin["angle"])) + point["y"]*math.cos(-toRadians(origin["angle"])) }

    #scale point

    point = { "x" : (point["x"] / conversions[unit]) * scale,
              "y" : -(point["y"] / conversions[unit]) * scale }

    return  point


def translate(x, y, lat_origin, long_origin, angle, unit): 
    y=-y
    x=x
    earth_radius=6378000 #meter 
    unit_conversion = {  "inch" : 0.0254, 
                         "meter": 1.0,
                         "mm"   : 0.001 } 
    factor = unit_conversion[unit] 
    angle_radians = 2 * math.pi * (angle / 360) 
 
    new_lat = lat_origin + 360* (  (  y*factor*math.cos(angle_radians) + x*factor*math.sin(angle_radians)   )/(earth_radius * 2 * math.pi)) 
    new_lat_radians = 2 * math.pi * (new_lat / 360) 
    new_long = long_origin + 360 * (  (-y*factor*math.sin(angle_radians) + x*factor*math.cos(angle_radians)))/(earth_radius * math.cos(new_lat_radians)* 2 * math.pi) 
    
    plot_y = -plot_scale * (2 * math.pi * (new_lat - plot_origin_lat) / 360) * earth_radius * 2 * math.pi
    plot_x = plot_scale * (2 * math.pi * (new_long - plot_origin_long) / 360) * math.cos(new_lat_radians) * earth_radius * 2 * math.pi

    plot_rotation_radians = (plot_rotation / 360)*2*math.pi
    plot_x1 = math.cos(plot_rotation_radians)*plot_x - math.sin(plot_rotation_radians)*plot_y
    plot_y1 = math.sin(plot_rotation_radians)*plot_x + math.cos(plot_rotation_radians)*plot_y


    return (plot_x1, plot_y1)








def translate_ll(x, y, lat_origin, long_origin, angle, unit): 
    y=-y
    x=x
    earth_radius=6378000 #meter 
    unit_conversion = {  "inch" : 0.0254, 
                         "meter": 1.0,
                         "mm"   : 0.001 } 
    factor = unit_conversion[unit] 
    angle_radians = 2 * math.pi * (angle / 360) 
 
    new_lat = lat_origin + 360* (  (  y*factor*math.cos(angle_radians) + x*factor*math.sin(angle_radians)   )/(earth_radius * 2 * math.pi)) 
    new_lat_radians = 2 * math.pi * (new_lat / 360) 
    new_long = long_origin + 360 * (  (-y*factor*math.sin(angle_radians) + x*factor*math.cos(angle_radians)))/(earth_radius * math.cos(new_lat_radians)* 2 * math.pi) 
    
    return (new_lat, new_long)

