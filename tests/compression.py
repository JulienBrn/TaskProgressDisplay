import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../src")

from task_progress_api.task_progress_api import Progress
from task_progress_handlers.task_progress_handlers import ProgressBar
from time import sleep

import logging

try:
    import beautifullogger
    beautifullogger.setup() 
except ImportError as e:
    pass

logger=logging.getLogger(__name__)



def load(f, p: Progress):
    video={"nb_frames":100}#Assume video has 100 frames
    p.start_numeric(max=video["nb_frames"], unit="frame")
    for i in range(video["nb_frames"]):
        sleep(0.02) #simulates loading of video
        p.update()
    p.close()
    return video
    
def conv(video, p: Progress):
    p.start_numeric(max=video["nb_frames"], unit="frame")
    for i in range(video["nb_frames"]):
        sleep(0.1)#simulates conversion operations
        p.update(val=1.0)#We can pass a parameter to update
    p.close()
    return {}#In practice, something
        

      
def check(video, res, p: Progress):
    p.start_numeric(max=video["nb_frames"], unit="frame")
    for i in range(video["nb_frames"]):
        sleep(0.02)
        p.update()  
    p.close()
    return True
        
def handle_file(f, p : Progress):
    #We assume the conv operation takes 5 times the time of the other operations
    #You can provide None or simply a List if you want to set a task to average time of the tasks
    #Only indicative, serves to estimate end of tasks
    p.start_subtasks({"Loading" : 1, "Converting": 5, "Checking" : 1})
    video = load(f, p.subtasks["Loading"])
    res=conv(video, p.subtasks["Converting"])
    check(video, res, p.subtasks["Checking"])
    p.close()
    
def handle_files(p : Progress):
    files = ["t.txt", "to.txt", "f.txt"]
    p.start_subtasks({("Handling " + f):1 for f in files})
    for f in files:
        handle_file(f, p.subtasks["Handling " + f])
    p.close()


p = Progress("Compressing Files")
p.set_handler(ProgressBar())
handle_files(p)