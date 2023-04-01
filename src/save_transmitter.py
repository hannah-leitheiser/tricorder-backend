import json
import os

def addToTransmitterData( transmitterType, name, position, level, source, timestamp ):
    if True:
        if not os.path.isdir("transmitter_data_"+transmitterType):
            os.mkdir("transmitter_data_"+transmitterType)
        if not os.path.isdir("transmitter_data_"+transmitterType+"/" + source):
            os.mkdir("transmitter_data_"+transmitterType + "/" + source)
        name = name.replace("/","|")
        data = { "name" : name, "position" : position, "level" : level, "timestamp" : timestamp  }
        outputFile = open("transmitter_data_"+transmitterType+"/" + source + "/" + transmitterType + "_" + name + ".json","a")
        outputFile.write(json.dumps(data,indent=3,sort_keys=True))
        outputFile.write("\n" + "*"*32 + "\n")
        outputFile.close()
