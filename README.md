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
We then use the `update`, `start_subtasks` and `start_numeric` of the Progress object to notify progress information.

The result is the following:

```python
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
p.set_handler(ProgressBar())
handle_files(p)
```





