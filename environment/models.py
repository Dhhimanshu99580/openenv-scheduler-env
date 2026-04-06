from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum

class JobStatus(str, Enum):
    PENDING   = "pending"    
    RUNNING   = "running"    
    SUCCESS   = "success"   
    FAILED    = "failed"     
    CANCELLED = "cancelled"  
    SKIPPED   = "skipped"   

class Priority(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"

class ActionType(str, Enum):
    TRIGGER      = "trigger"
    DELAY        = "delay"
    RETRY        = "retry"
    CANCEL       = "cancel"
    REPRIORITIZE = "reprioritize"
    WAIT         = "wait"

class Job(BaseModel):
    job_id:         str
    name:           str
    schedule:       int           
    dependencies:   List[str]     
    status:         JobStatus  = JobStatus.PENDING
    priority:       Priority   = Priority.MEDIUM
    cpu_required:   int        = 1  
    memory_required: int       = 1  
    retry_count:    int        = 0
    max_retries:    int        = 3
    deadline:       Optional[int] = None 
    last_run:       Optional[int] = None  

class SchedulerState(BaseModel):
    current_time:     int
    jobs:             List[Job]
    available_cpu:    int
    available_memory: int
    execution_history: List[Dict]  
    episode_done:     bool = False

class SchedulerAction(BaseModel):
    action_type: ActionType
    job_id:      Optional[str] = None   
    delay_units: Optional[int] = None   
    new_priority: Optional[Priority] = None  

class SchedulerReward(BaseModel):
    score:   float        
    reason:  str          
    details: Dict = {}   