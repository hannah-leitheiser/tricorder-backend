from measurementGrid import *


measurements = ["CO2","TVOC", "Part>0.3", "Part>0.5", "Part>1.0",
                                    "Part>1.0", "Part>2.5", "Part>5.0", "Part>10.0", "eCO2"]
                    meass = dict()
                    for m in measurements:
                        for p in getMeasurements( point, m):
                            if m == "TVOC" and p[0] > 50000:
                                print("Too high TVOC, " + str(p[0]))
                            else: 
                                if m == "CO2" and p[0] == 0:
                                    print("CO2 is zero")
                                else:
                                    predictedLocation = predict( p[1], poly )
                                    if m in meass:
                                        meass[m]+=[p[0],]
                                    else:
                                        meass[m] = [p[0],1]
                                    addToGrid( predictedLocation[0], predictedLocation[1], m, p[0])
                    aaa=" "
                    for m in meass.keys():
                        aaa += "{:}: {:.1f} ".format(m, sum(meass[m])/len(meass[m]))
                    if aaa != " ":
                        print( aaa )

