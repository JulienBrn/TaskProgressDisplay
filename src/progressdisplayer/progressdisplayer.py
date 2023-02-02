from __future__ import annotations
from typing import Dict, Any, List, Tuple
from taskprogress.taskprogress import Progress, Handler
from enum import Enum
import enlighten
import logging

logger=logging.getLogger(__name__)
manager = enlighten.get_manager()

class BasicProgressBars(Handler):
    
    # task_format =    '{depthpad}{desc:20s}{desc_pad}{percentage:3.0f}%|{bar}|{}'
    # numeric_format = '{depthpad}{desc:20s}{desc_pad}{percentage:3.0f}%|{bar}| {count:.2f}/{total:.2f}'
    numeric_format= '{depthpad}{desc:20s} {percentage:3.0f}%|{bar}|{count:4.0f}/{total:<3.0f} {unit:5s}  {rate:3.1f} {unit:5s}/s eta {eta}s spent {elapsed}s'
    task_format=    '{depthpad}{desc:20s} {percentage:3.0f}%|{bar}|{ndone:4.0f}/{ntask:<3.0f} {unit:18s} eta {eta}s spent {elapsed}s'
    # task_suffix=   '{finishedtasks}/{tottasks} subtasks'
    # numeric_suffix='{finishedtasks}/{tottasks} completed'
    
    class DisplayStrategy(Enum):
        LEAF = 0
        KEEP_SEQUENCE = 1
        REPLACE_SEQUENCE = 2
        PARRALLLEL_SEQUENCE = 3
        INLINE = 4 
        HIDDEN = 5
    
    dict: Dict[str, Tuple[Progress, BasicProgressBars.DisplayStrategy, int, enlighten.Counter | None]] ={}
    
    def compute_number_counters(self, task: Progress, strategy: BasicProgressBars.DisplayStrategy):
        (_, ds, v, _) = self.dict[task.parent.fullname] if task.parent else (None, BasicProgressBars.DisplayStrategy.KEEP_SEQUENCE, 1, None)
        (s, ns) = (list(task.parent.subtasks.keys()).index(task.name) , len(task.parent.subtasks)) if task.parent else (1,0)
        
        if ds == BasicProgressBars.DisplayStrategy.LEAF:
            return v
        if ds == BasicProgressBars.DisplayStrategy.HIDDEN:
            return v
        if task.type==Progress.Type.NUMERIC:
            return v
        if ds == BasicProgressBars.DisplayStrategy.REPLACE_SEQUENCE:
            if strategy == BasicProgressBars.DisplayStrategy.LEAF: return v
            if strategy == BasicProgressBars.DisplayStrategy.KEEP_SEQUENCE: return v+len(task.subtasks)
            if strategy == BasicProgressBars.DisplayStrategy.REPLACE_SEQUENCE: return v+1
            
        if ds == BasicProgressBars.DisplayStrategy.KEEP_SEQUENCE:
            if strategy == BasicProgressBars.DisplayStrategy.LEAF: return v-ns+s
            if strategy == BasicProgressBars.DisplayStrategy.KEEP_SEQUENCE: return v-ns+s+len(task.subtasks)
            if strategy == BasicProgressBars.DisplayStrategy.REPLACE_SEQUENCE: return v-ns+s+1
        raise NotImplementedError
    
    def compute_strategy(self, task: Progress):
        if task.parent:
            (_, ds, _, _) = self.dict[task.parent.fullname]
            if ds == BasicProgressBars.DisplayStrategy.LEAF:
                return BasicProgressBars.DisplayStrategy.HIDDEN
            if ds == BasicProgressBars.DisplayStrategy.HIDDEN:
                return BasicProgressBars.DisplayStrategy.HIDDEN
        if task.type==Progress.Type.NUMERIC:
            return  BasicProgressBars.DisplayStrategy.LEAF
        if self.compute_number_counters(task, BasicProgressBars.DisplayStrategy.KEEP_SEQUENCE) <= 5:
            return BasicProgressBars.DisplayStrategy.KEEP_SEQUENCE
        if self.compute_number_counters(task, BasicProgressBars.DisplayStrategy.REPLACE_SEQUENCE) <= 7:
            return BasicProgressBars.DisplayStrategy.REPLACE_SEQUENCE
        return BasicProgressBars.DisplayStrategy.LEAF
    
    def notify_numeric_started(self, task: Progress):
        strat = self.compute_strategy(task)
        if strat == BasicProgressBars.DisplayStrategy.HIDDEN:
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), None)
        else:
            unit=task.additional_info["unit"] if "unit" in task.additional_info else "elems"
            counter = manager.counter(total = task.max, desc=task.name, bar_format=self.numeric_format, unit=unit, fields={"depthpad":"  "*task.depth})
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), counter)
    def notify_subtasks_started(self, task: Progress):
        strat = self.compute_strategy(task)
        if strat == BasicProgressBars.DisplayStrategy.HIDDEN:
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), None)
        else:
            counter = manager.counter(total = 1.0, desc=task.name, bar_format=self.task_format, unit="subtasks completed", fields={"depthpad":"  "*task.depth, "ndone":0, "ntask":len(task.subtasks)})
            self.dict[task.fullname]=(task, strat, self.compute_number_counters(task, strat), counter)
    def notify_numeric_update(self, task: Progress):
        while task:
            # t=self.dict[task.fullname]
            # logger.debug("Updating task {}".format(task.fullname))
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
            if pds==BasicProgressBars.DisplayStrategy.REPLACE_SEQUENCE:
                self.remove_counter(task)
             
    def remove_counter(self, task: Progress):
        self.notify_numeric_update(task)
        (x, ds, y, counter) = self.dict[task.fullname]
        if counter:
            counter.leave=False
            counter.close()
            self.dict[task.fullname]=(x, ds, y, None)
            