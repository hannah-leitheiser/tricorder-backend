from random import sample
import os

def deleteSample( directory, proportion):
    files = os.listdir(directory)
    for file in sample(files, int( len(files) * proportion)):
        os.remove(directory+file)
