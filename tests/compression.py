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
    with p.start_numeric(max=video["nb_frames"], unit="frame"):
        for i in range(video["nb_frames"]):
            sleep(0.02) #simulates loading of video
            p.update()
    return video
    
def conv(video, p: Progress):
    with p.start_numeric(max=video["nb_frames"], unit="frame"):
        for i in range(video["nb_frames"]):
            sleep(0.1)#simulates conversion operations
            p.update(val=1.0)#We can pass a parameter to update
    return {}#In practice, something
        

      
def check(video, res, p: Progress):
    with p.start_numeric(max=video["nb_frames"], unit="frame"):
        for i in range(video["nb_frames"]):
            sleep(0.02)
            p.update()  
    return True
        
def handle_file(f, p : Progress):
    #We assume the conv operation takes 5 times the time of the other operations
    #You can provide None or simply a List if you want to set a task to average time of the tasks
    #Only indicative, serves to estimate end of tasks
    with p.start_subtasks({"Loading" : 1, "Converting": 5, "Checking" : 1}):
        video = load(f, p["Loading"])
        res=conv(video, p["Converting"])
        check(video, res, p["Checking"])
    
def handle_files(p : Progress):
    #Let's create some dummy files. In practice ths might just be the result of getting all files in current folder
    files = ["t{}.mp4".format(i) for i in range(4)]
    with p.start_subtasks({f:1 for f in files}):
        for f in files:
            p[f].additional_info["desc"] = "Handling " + f
            handle_file(f, p[f])


if __name__ =="__main__":
    p = Progress("Compressing Files")
    with p:
        p.set_handler(ProgressBar(max_counters=10, counter_margin=0))
        try:
            handle_files(p)
        except KeyboardInterrupt:
            pass
    p.close()
    logger.info("END")