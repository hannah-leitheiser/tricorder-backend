import json

contexts = json.loads(open("contexts/origins.json").read())

e="""contexts = { "The Home Depot" : { "origin" : { "latitude"  :  44.965637,
                                               "longitude" : -93.352900,
                                               "altitude"  : 250.59900,
                                               "angle"     : -39 } ,
                                  "units":"inch",
                                  "accuracy, horizontal" : 0.5,
                                  "accuracy, vertical"   : 0.5},
        "Apartment" : { "origin" : { "latitude"  :  44.976594,
                                     "longitude" : -93.353482,
                                      "angle"    :   0,
                                      "altitude" : 240.492 },
                                  "units":"mm",
                                  "accuracy, horizontal" : 0.1,
                                  "accuracy, vertical"   : 0.1} 


                                  }
"""

def writeContexts():
    open("contexts/origins.json", "w").write(json.dumps(contexts,indent=3,sort_keys=True)) 

plot = { "origin" : { "latitude"  :  44.96564786787919,
                          "longitude" : -93.3529035169046,
                      "angle"     :  -39 },
        "units"   : "meter",
        "scale"   : 50 }

