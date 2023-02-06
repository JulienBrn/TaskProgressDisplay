from __future__ import annotations
from typing import Dict, Any, List, Tuple
from task_progress_api.task_progress_api import Progress, Handler
from enum import Enum
import enlighten
import logging
import functools

logger=logging.getLogger("")

def monitor_results(func):
    @functools.wraps(func)
    def wrapper(*func_args, **func_kwargs):
        retval = func(*func_args,**func_kwargs)
        logger.debug('function ' + func.__name__ + '({})'.format(func_args) + 'returns ' + repr(retval))
        return retval
    return wrapper
    
import datetime
class ProgressBar(Handler):
    
    # numeric_format= '{depthpad}{desc:20s} {percentage:3.0f}%|{bar}|{count:4.0f}/{total:<3.0f} {unit:5s}  {rate:>4.1f} {unit:5s}/s eta {eta}s spent {elapsed}s'
    # task_format=    '{depthpad}{desc:20s} {percentage:3.0f}%|{bar}|{ndone:4.0f}/{ntask:<3.0f} {unit:19s} eta {eta}s spent {elapsed}s'
    numeric_format= '{depthpad}{desc:20s} {percentage:3.0f}%|{bar}|{errors} errors, {warnings} warnings, eta {eta}s'
    task_format=    '{depthpad}{desc:20s} {percentage:3.0f}%|{bar}|{errors} errors, {warnings} warnings, eta {eta}s'
    finished_format='{depthpad}{desc:20s} {bar} {ending} {duration:%M:%Ss}. {errors} errors, {warnings} warnings'
    
    def get_fields(self, task):
        dur=self.dict[task.fullname][3].elapsed if task.fullname in self.dict and self.dict[task.fullname][3] else 0
        return {
            "depthpad": "  "*task.depth,
            "errors": 0,
            "warnings": 0,
            "ending": "Task Completed in" if task.percentage==1.0 else "Stopped at {:2.0f}%. Duration".format(task.percentage*100.0),
            "duration":  datetime.time(second=int(dur))
        }
    
    max_counters=7
    switch_replace=5
    
    manager = enlighten.get_manager()
    def __repr__(self):
        return "ProgressBar(Handler)"
    
    class DisplayStrategy(Enum):
        LEAF = 0
        KEEP_SEQUENCE = 1
        REPLACE_SEQUENCE = 2
        PARRALLLEL_SEQUENCE = 3
        INLINE = 4 
        HIDDEN = 5
    
    dict: Dict[str, Tuple[Progress, ProgressBar.DisplayStrategy, int, enlighten.Counter | None]] ={}
    
    def __init__(self, max_counters=None, counter_margin=None, numeric_format=None, task_format=None):
        if max_counters:
            self.max_counters=max_counters
        if counter_margin:
            self.switch_replace=self.max_counters - counter_margin
        if numeric_format:
            self.numeric_format=numeric_format
        if task_format:
            self.task_format=task_format   
            
    def compute_number_counters(self, task: Progress, strategy: ProgressBar.DisplayStrategy):
        (_, ds, v, _) = self.dict[task.parent.fullname] if task.parent else (None, ProgressBar.DisplayStrategy.KEEP_SEQUENCE, 1, None)
        (s, ns) = (task.sibling_index, task.parent.nb_subtasks) if task.parent else (1,0)
        
        if ds == ProgressBar.DisplayStrategy.LEAF:
            return v
        if ds == ProgressBar.DisplayStrategy.HIDDEN:
            return v
        if task.type==Progress.Type.NUMERIC:
            return v
        if ds == ProgressBar.DisplayStrategy.REPLACE_SEQUENCE:
            if strategy == ProgressBar.DisplayStrategy.LEAF: return v
            if strategy == ProgressBar.DisplayStrategy.KEEP_SEQUENCE: return v+task.nb_subtasks
            if strategy == ProgressBar.DisplayStrategy.REPLACE_SEQUENCE: return v+1
            
        if ds == ProgressBar.DisplayStrategy.KEEP_SEQUENCE:
            if strategy == ProgressBar.DisplayStrategy.LEAF: return v-ns+s
            if strategy == ProgressBar.DisplayStrategy.KEEP_SEQUENCE: return v-ns+s+task.nb_subtasks-1
            if strategy == ProgressBar.DisplayStrategy.REPLACE_SEQUENCE: return v-ns+s
        raise NotImplementedError
    
    def compute_strategy(self, task: Progress):
        if task.parent:
            (_, ds, _, _) = self.dict[task.parent.fullname]
            if ds == ProgressBar.DisplayStrategy.LEAF:
                return ProgressBar.DisplayStrategy.HIDDEN
            if ds == ProgressBar.DisplayStrategy.HIDDEN:
                return ProgressBar.DisplayStrategy.HIDDEN
        if task.type==Progress.Type.NUMERIC:
            return  ProgressBar.DisplayStrategy.LEAF
        if self.compute_number_counters(task, ProgressBar.DisplayStrategy.KEEP_SEQUENCE) <= self.switch_replace:
            return ProgressBar.DisplayStrategy.KEEP_SEQUENCE
        if self.compute_number_counters(task, ProgressBar.DisplayStrategy.REPLACE_SEQUENCE) <= self.max_counters:
            return ProgressBar.DisplayStrategy.REPLACE_SEQUENCE
        return ProgressBar.DisplayStrategy.LEAF
    
    def notify_numeric_started(self, task: Progress):
        strat = self.compute_strategy(task)
        if strat == ProgressBar.DisplayStrategy.HIDDEN:
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), None)
        else:
            unit=task.additional_info["unit"] if "unit" in task.additional_info else "elems"
            desc=task.additional_info["desc"] if "desc" in task.additional_info else task.name
            logger.info("Creating counter for task {}".format(task.fullname))
            counter = self.manager.counter(total = task.max, desc=desc, bar_format=self.numeric_format, unit=unit, fields=self.get_fields(task))
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), counter)
    def notify_subtasks_started(self, task: Progress):
        strat = self.compute_strategy(task)
        if strat == ProgressBar.DisplayStrategy.HIDDEN:
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), None)
        else:
            unit=task.additional_info["unit"] if "unit" in task.additional_info else "subtasks completed"
            desc=task.additional_info["desc"] if "desc" in task.additional_info else task.name
            logger.info("Creating counter for task {}".format(task.fullname))
            counter = self.manager.counter(total = 1.0, desc=desc, bar_format=self.task_format, unit=unit, fields=self.get_fields(task))
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), counter)
    def notify_numeric_update(self, task: Progress):
        while task:
            (_, _, _, counter) = self.dict[task.fullname]
            if counter:
                if task.type==Progress.Type.NUMERIC:
                    if not isinstance(counter, enlighten._statusbar.StatusBar):
                        counter.total=task.max
                        counter.count =task.value
                else:
                    if not isinstance(counter, enlighten._statusbar.StatusBar):
                        counter.count=task.percentage
                        counter.fields["ndone"]=float(task.nb_completed)
                counter.refresh()
            task=task.parent
           
    def notify_close(self, task: Progress):
         if task.type==Progress.Type.TASK:
             for s, p in task.subtasks:
                 if p.status != Progress.Status.NOTSTARTED:
                    if p.fullname in self.dict:
                        self.remove_counter(p)
                    else:
                        logger.warning("SubCounter missing in notify close")
         if task.parent:
            (_, pds, _, _) = self.dict[task.parent.fullname]
            if pds==ProgressBar.DisplayStrategy.REPLACE_SEQUENCE:
                self.remove_counter(task)
            else:
                (x, ds, y, counter) = self.dict[task.fullname]
                if counter:
                    # st = self.manager.counter(replace=counter, desc=counter.desc, bar_format=self.finished_format, fields=self.get_fields(task))
                    counter.bar_format=self.finished_format
                    counter.series=" "
                    counter.fields=self.get_fields(task)
                    # st.refresh()
                    # logger.info("Transforming counter for task {} to status bar".format(task.fullname))
                    # st.update("  " * task.depth + task.name + "Finished")
                    # self.dict[task.fullname] = (x, ds, y, st) 
           
    def remove_counter(self, task: Progress):
        self.notify_numeric_update(task)
        (x, ds, y, counter) = self.dict[task.fullname]
        if counter:
            counter.leave=False
            logger.info("Closing counter for {}".format(task.fullname))
            counter.close()
            self.dict[task.fullname]=(x, ds, y, None)
            