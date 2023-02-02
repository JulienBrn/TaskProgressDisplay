from __future__ import annotations
from typing import Dict, Any, List, Tuple
from task_progress_api.task_progress_api import Progress, Handler
from enum import Enum
import enlighten
import logging

logger=logging.getLogger(__name__)


class ProgressBar(Handler):
    
    numeric_format= '{depthpad}{desc:20s} {percentage:3.0f}%|{bar}|{count:4.0f}/{total:<3.0f} {unit:5s}  {rate:3.1f} {unit:5s}/s eta {eta}s spent {elapsed}s'
    task_format=    '{depthpad}{desc:20s} {percentage:3.0f}%|{bar}|{ndone:4.0f}/{ntask:<3.0f} {unit:18s} eta {eta}s spent {elapsed}s'
    
    max_counters=7
    switch_replace=5
    
    manager = enlighten.get_manager()
    
    class DisplayStrategy(Enum):
        LEAF = 0
        KEEP_SEQUENCE = 1
        REPLACE_SEQUENCE = 2
        PARRALLLEL_SEQUENCE = 3
        INLINE = 4 
        HIDDEN = 5
    
    dict: Dict[str, Tuple[Progress, ProgressBar.DisplayStrategy, int, enlighten.Counter | None]] ={}
    
    def compute_number_counters(self, task: Progress, strategy: ProgressBar.DisplayStrategy):
        (_, ds, v, _) = self.dict[task.parent.fullname] if task.parent else (None, ProgressBar.DisplayStrategy.KEEP_SEQUENCE, 1, None)
        (s, ns) = (list(task.parent.subtasks.keys()).index(task.name) , len(task.parent.subtasks)) if task.parent else (1,0)
        
        if ds == ProgressBar.DisplayStrategy.LEAF:
            return v
        if ds == ProgressBar.DisplayStrategy.HIDDEN:
            return v
        if task.type==Progress.Type.NUMERIC:
            return v
        if ds == ProgressBar.DisplayStrategy.REPLACE_SEQUENCE:
            if strategy == ProgressBar.DisplayStrategy.LEAF: return v
            if strategy == ProgressBar.DisplayStrategy.KEEP_SEQUENCE: return v+len(task.subtasks)
            if strategy == ProgressBar.DisplayStrategy.REPLACE_SEQUENCE: return v+1
            
        if ds == ProgressBar.DisplayStrategy.KEEP_SEQUENCE:
            if strategy == ProgressBar.DisplayStrategy.LEAF: return v-ns+s
            if strategy == ProgressBar.DisplayStrategy.KEEP_SEQUENCE: return v-ns+s+len(task.subtasks)
            if strategy == ProgressBar.DisplayStrategy.REPLACE_SEQUENCE: return v-ns+s+1
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
            counter = self.manager.counter(total = task.max, desc=task.name, bar_format=self.numeric_format, unit=unit, fields={"depthpad":"  "*task.depth})
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), counter)
    def notify_subtasks_started(self, task: Progress):
        strat = self.compute_strategy(task)
        if strat == ProgressBar.DisplayStrategy.HIDDEN:
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), None)
        else:
            counter = self.manager.counter(total = 1.0, desc=task.name, bar_format=self.task_format, unit="subtasks completed", fields={"depthpad":"  "*task.depth, "ndone":0, "ntask":len(task.subtasks)})
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), counter)
    def notify_numeric_update(self, task: Progress):
        while task:
            (_, _, _, counter) = self.dict[task.fullname]
            if counter:
                if task.type==Progress.Type.NUMERIC:
                    counter.total=task.max
                    counter.count =task.value
                else:
                    counter.count=task.percentage
                    counter.fields["ndone"]=float(task.nb_completed)
                counter.refresh()
            task=task.parent
            
    def notify_close(self, task: Progress):
         if task.type==Progress.Type.TASK:
             for s in task.subtasks.values():
                 self.remove_counter(s)
         if task.parent:
            (_, pds, _, _) = self.dict[task.parent.fullname]
            if pds==ProgressBar.DisplayStrategy.REPLACE_SEQUENCE:
                self.remove_counter(task)
             
    def remove_counter(self, task: Progress):
        self.notify_numeric_update(task)
        (x, ds, y, counter) = self.dict[task.fullname]
        if counter:
            counter.leave=False
            counter.close()
            self.dict[task.fullname]=(x, ds, y, None)
            