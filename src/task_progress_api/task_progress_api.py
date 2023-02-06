from __future__ import annotations
from typing import Dict, Any, List, Tuple
from enum import Enum
import logging

logger=logging.getLogger(__name__)

class Progress:
    class Type(Enum):
        PROXY=1
        NUMERIC=2
        TASK=3
    class Status(Enum):
        NOTSTARTED=1
        RUNNING=2
        CLOSED=3
        
    def __init__(self, name: str, extra: Dict[str, Any]={}):
        self.__name = name
        self.additional_info = extra
        self.__handler = None
        self.__status=Progress.Status.NOTSTARTED
        self.__type=Progress.Type.PROXY
        self.__parent=None
        self.__parent_contrib=1.0
    def __repr__(self):
            return 'Progress {}'.format(self.fullname) 
    # Common methods for all "Progress"
    @property
    def name(self) -> str: 
        return self.__name
    @property
    def parent(self) -> Progress|None: 
        return self.__parent
    
    @property
    def sibling_index(self) -> int:
        return list(self.parent.__subtasks.keys()).index(self.__name) if self.parent else 0
       
    @property
    def depth(self) -> int: 
        return 1 + self.__parent.depth if self.__parent else 0
    @property
    def namechain(self) -> List[str]:
        return self.__parent.namechain + [self.name] if self.__parent else [self.name]
    @property
    def fullname(self) -> str:
        return '.'.join(self.namechain)
    @property
    def root(self) -> Progress:
        return self.__parent.root if self.__parent else self
    @property 
    def handler(self) -> Handler | None:
        return self.__handler
    @property
    def type(self) -> Type:
        return self.__type
    @property
    def status(self) -> Status:
        return self.__status
    @property
    def percentage(self) -> float:
        if self.type == Progress.Type.PROXY:
            return 0.
        elif self.type == Progress.Type.NUMERIC:
            return self.value/self.max
        elif self.type == Progress.Type.TASK:
            return sum([s.percentage*s.parent_contrib for s in self.__subtasks.values()])
    @property
    def parent_contrib(self) -> float:
        return self.__parent_contrib
    @property
    def root_contrib(self)-> float:
        return self.parent_contrib * self.__parent.root_contrib if self.__parent else 1.0
    
    def set_handler(self, handler: Handler):
        self.__handler=handler
    def get_used_handler(self) -> Handler | None:
        if self.handler:
            return self.handler
        elif self.parent:
            return self.parent.get_used_handler()
        else:
            return default_handler
        
    def close(self) -> None: 
        self.__status = Progress.Status.CLOSED
        self.get_used_handler().notify_close(self)
        
    def __enter__(self):pass
    def __exit__(self, *args):
        self.close()
        
    # Methods available only on Proxy Type
    def start_numeric(self, max: float, unit: str | None = None) ->  Progress:
        self.__value = 0
        self.__max = max
        self.__type=Progress.Type.NUMERIC
        self.__status=Progress.Status.RUNNING
        if unit:
            self.additional_info["unit"]=unit
        self.get_used_handler().notify_numeric_started(self)
        return self
        
    def start_subtasks(self, subtasks: List[str] | Dict[str, float | None], extra: Dict[str, Any] = {}) ->  Progress:
        if isinstance(subtasks, List):
            subtasks={n:None for n in subtasks}
        if len(subtasks)==0:
            logger.warning("Creating 0 subtasks for progress {}.".format(self.fullname))
            return {}
        for n,v in subtasks.items():
            if v <0:
                logger.error("Setting contribution value of subtask {} in progress {} under zero ({}), continuing with zero".format(n, self.fullname, v))
                subtasks[n]=0
        filtered=list(filter(None, subtasks.values()))
        msum=sum(filtered)
        if msum==0:
            subtasks={s:1.0/float(len(subtasks)) for s,v in subtasks.items()}
        else:
            finalsum=msum*float(len(subtasks))/float(len(filtered))
            subtasks={s:v/finalsum if v else 1.0/float(len(subtasks)) for s,v in subtasks.items()}
        def create_progress(n ,v):
            p = Progress(n, extra[n] if n in extra else {})
            (p.__parent, p.__parent_contrib) = (self, v)
            return p
        self.__subtasks={n:create_progress(n,v) for n,v in subtasks.items()}    
        self.__type=Progress.Type.TASK
        self.__status=Progress.Status.RUNNING
        self.get_used_handler().notify_subtasks_started(self)
        return self
        
    #Methods only available on Numeric Type
    @property 
    def max(self):
        return self.__max
    
    @property 
    def value(self):
        return self.__value
    
    def update(self, val: float = 1.0):
        self.set_value(self.value+val)
    def set_value(self, val: float):
        if val <0:
            logger.error("Setting value of progress {} under zero ({}), continuing with zero".format(self.fullname, val))
            val=0
        if val>self.max:
            logger.error("Setting value of progress {} to {} with is above max ({}), setting value to max".format(self.fullname, val, self.max))
            val=self.max
        self.__value=val
        self.get_used_handler().notify_numeric_update(self)
    
    #Methods only available on Task Type
    @property 
    def subtasks(self) -> List[Tuple[str, Progress]]:
        return self.__subtasks.items()
        # return {n:p for n,p in self.__subtasks.items()}

    def __getitem__(self, subtask: str) -> Progress:
        return self.__subtasks[subtask]
    
    @property 
    def nb_subtasks(self):
        return len(self.__subtasks)
    
    @property
    def nb_completed(self) -> int:
        return len(list(filter(lambda x: x.status == Progress.Status.CLOSED, self.__subtasks.values())))
    
    __name: str
    __parent: Progress | None
    __handler: Handler | None
    __type: Progress.Type
    __status: Progress.Status
    __parent_contrib: float
    additional_info: Dict[str, Any]
    
class Handler:
    def notify_numeric_started(self, task: Progress):
        raise NotImplementedError
    def notify_subtasks_started(self, task: Progress):
        raise NotImplementedError
    def notify_numeric_update(self, task: Progress):
        raise NotImplementedError
    def notify_close(self, task: Progress):
        raise NotImplementedError
    
class DummyHandler(Handler):
    def notify_numeric_started(self, task: Progress):
        pass
    def notify_subtasks_started(self, task: Progress):
        pass
    def notify_numeric_update(self, task: Progress):
        pass
    def notify_close(self, task: Progress):
        pass

default_handler=DummyHandler()