import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../src")

from taskprogress.taskprogress import Progress
from progressdisplayer.progressdisplayer import BasicProgressBars
from time import sleep
import beautifullogger
import logging

logger=logging.getLogger(__name__)
beautifullogger.setup() 

def conv(x : Progress):
    x.start_numeric(max=80, unit="frame")
    for i in range(0, 80):
        sleep(0.1)
        x.update()
    x.close()
        
def analyze(x : Progress):
    x.start_numeric(max=10, unit="frame")
    for i in range(0, 10):
        sleep(0.1)
        x.update()
    x.close()
      
def check(x : Progress):
    x.start_numeric(max=10, unit="frame")
    for i in range(0, 10):
        sleep(0.1)
        x.update()  
    x.close()
        
def handle_file(f, x : Progress):
    sub = x.start_subtasks({"Analyzing" : 1, "Converting": 8, "Checking" : 1})
    analyze(sub["Analyzing"])
    conv(sub["Converting"])
    check(sub["Checking"])
    x.close()
    
def handle_files(x : Progress):
    files = ["t.txt", "to.txt", "f.txt"]
    s=x.start_subtasks({("Handling " + f):1 for f in files})
    for f in files:
        handle_file(f, s["Handling " + f])
    x.close()


p = Progress("Compressing Files")
p.set_handler(BasicProgressBars())
handle_files(p)