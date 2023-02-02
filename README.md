# TaskProgressDisplay
A Python module to 1) Correctly notify progress of application based on tasks 2) Suggest a nice display

Main issues: 
- @multitasking/async routines:
    The current handler to display progress bars does not correctly handle non depth first search progression of task. Simply put, you may experience problems with the order of counters if using async/dask.delayed or any other form of multitasking. On the progress API, no effort has yet been put to create thread safe updates.

- @terminals: displaying progress bars depends on the enlighten package which has issues with some terminals. Currently seems to work in most linux terminals and in VSCode terminal. Problems noticed in terminals of PyCharm (view [this issue](https://github.com/Rockhopper-Technologies/enlighten/issues/32) and Spyder)

# Using the progress api
## A first example

Consider an application that handles multiple video files and calls the function `handle_file` for each of them. `handle_file` is then decomposed into three subtasks (here three functions):
- `analyze`: the function that analyzes the video
- `conv`: the function that does the main work.
- `check`: the function that checks the result.

In order to notify progress information in each task, each function is passed an additional parameter: the "Progress" object.
We then use the `update`, `start_subtasks` and `start_numeric` of the Progress object to notify progress information (where `sleep` is used as a replacement for the actual work).

The result is the following:

```python
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
p.set_handler(ProgressBar()) #For the display part
handle_files(p)
```





