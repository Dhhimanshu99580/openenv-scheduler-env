from environment.models import *

class SchedulerEnv:
    def __init__(self, initial_state: SchedulerState):
        self.current_state = initial_state

    def reset(self):
        self.current_state.current_time = 0
        for job in self.current_state.jobs:
            job.status = JobStatus.PENDING
            job.retry_count = 0
            job.last_run = None
        self.current_state.available_cpu=1
        self.current_state.available_memory=1
        self.current_state.execution_history = []
        self.current_state.episode_done = False
        return self.current_state
    
    def step(self, action: SchedulerAction):
        reward = SchedulerReward(score=0.0, reason="No action taken")
        if action.action_type == ActionType.TRIGGER:
            reward = self.handle_trigger(action)
        elif action.action_type == ActionType.DELAY:
            reward = self.handle_delay(action)
        elif action.action_type == ActionType.RETRY:
            reward = self.handle_retry(action)
        elif action.action_type == ActionType.CANCEL:
            reward = self.handle_cancel(action)
        elif action.action_type == ActionType.REPRIORITIZE:
            reward = self.handle_reprioritize(action)
        elif action.action_type == ActionType.WAIT:
            reward = self.handle_wait(action)

        self.current_state.execution_history.append({
        "time": self.current_state.current_time,
        "action": action.action_type,
        "job_id": action.job_id,
        "reward": reward.score,
        "reason": reward.reason  })
        return self.current_state, reward
    
    def handle_trigger(self, action):
        jobId = action.job_id
        for job in self.current_state.jobs:
            if job.job_id == jobId:
                if job.status != JobStatus.PENDING:
                    return SchedulerReward(score = - 0.5, reason = f"Job {jobId} is not in PENDING state")
                elif job.cpu_required > self.current_state.available_cpu or job.memory_required > self.current_state.available_memory:
                    return SchedulerReward(score = -0.5, reason = f"Not enough resources to trigger job {jobId}")
                elif job.last_run is not None and self.current_state.current_time - job.last_run < job.schedule:
                    return SchedulerReward(score = -0.5, reason = f"Job {jobId} cannot be triggered yet due to schedule constraint")
                for dep_id in job.dependencies:
                    dep_job = next((j for j in self.current_state.jobs if j.job_id == dep_id), None)
                    if dep_job is None or dep_job.status != JobStatus.SUCCESS:
                        return SchedulerReward(score = -0.5, reason = f"Job {jobId} cannot be triggered due to unmet dependency {dep_id}")
                job.status = JobStatus.RUNNING
                job.last_run = self.current_state.current_time
                self.current_state.available_cpu -= job.cpu_required
                self.current_state.available_memory -= job.memory_required
                return SchedulerReward(score = 1.0, reason = f"Job {jobId} triggered successfully")
        return SchedulerReward(score = -0.5, reason = f"Job {jobId} not found")
    
    def handle_retry(self, action):
        jobId = action.job_id
        for job in self.current_state.jobs:
            if job.job_id == jobId:
                if job.status != JobStatus.FAILED:
                    return SchedulerReward(score = -0.5, reason = f"Job {jobId} is not in FAILED state")
                elif job.retry_count >= job.max_retries:
                    return SchedulerReward(score = -0.5, reason = f"Job {jobId} has reached max retries")
                job.status = JobStatus.PENDING
                job.retry_count += 1
                self.current_state.available_cpu += job.cpu_required
                self.current_state.available_memory += job.memory_required
                return SchedulerReward(score = 0.5, reason = f"Job {jobId} set to retry (attempt {job.retry_count})")
        return SchedulerReward(score = -0.5, reason = f"Job {jobId} not found")
    
    def handle_delay(self,action):
        jobId = action.job_id
        delay_units = action.delay_units
        for job in self.current_state.jobs:
            if job.job_id == jobId:
                if job.status != JobStatus.PENDING:
                    return SchedulerReward(score = -0.1, reason = f"Job {jobId} is not in PENDING state")
                elif delay_units is None or delay_units <= 0:
                    return SchedulerReward(score = -0.1, reason = f"Invalid delay units for job {jobId}")
                job.schedule += delay_units
                return SchedulerReward(score = 0.5, reason = f"Job {jobId} delayed by {delay_units} time units")
        return SchedulerReward(score = -0.1, reason = f"Job {jobId} not found")
    
    def handle_cancel(self,action):
        jobId = action.job_id
        for job in self.current_state.jobs:
            if job.job_id == jobId:
                if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
                    if job.priority == Priority.HIGH:
                        score = -0.8
                    elif job.priority == Priority.MEDIUM:
                        score = -0.3
                    else:
                        score = 0.1 
                    return SchedulerReward(score = score, reason = f"Job {jobId} cannot be cancelled from its current state")
                job.status = JobStatus.CANCELLED
                self.current_state.available_cpu += job.cpu_required
                self.current_state.available_memory += job.memory_required
                return SchedulerReward(score = 0.5, reason = f"Job {jobId} cancelled successfully")
        return SchedulerReward(score = -0.1, reason = f"Job {jobId} not found")

    def handle_reprioritize(self,action):
        jobId = action.job_id
        new_priority = action.new_priority
        for job in self.current_state.jobs:
            if job.job_id == jobId:
                if job.status != JobStatus.PENDING:
                    return SchedulerReward(score = -0.1, reason = f"Job {jobId} is not in PENDING state")
                elif new_priority is None:
                    return SchedulerReward(score = -0.1, reason = f"New priority not provided for job {jobId}")
                job.priority = new_priority
                return SchedulerReward(score = 0.5, reason = f"Job {jobId} reprioritized to {new_priority}")
        return SchedulerReward(score = -0.1, reason = f"Job {jobId} not found")

    def handle_wait(self,action):
        self.current_state.current_time += 1
        all_done = all(
            job.status in [JobStatus.SUCCESS, JobStatus.CANCELLED, JobStatus.FAILED]
            for job in self.current_state.jobs
        )
        if all_done:
            self.current_state.episode_done = True
        for job in self.current_state.jobs:
            if job.status == JobStatus.RUNNING:
                job.status = JobStatus.SUCCESS
                self.current_state.available_cpu += job.cpu_required
                self.current_state.available_memory += job.memory_required
        return SchedulerReward(score = 0.1, reason = "Time advanced by 1 unit, running jobs completed")   
        
    
    def state(self):
        return self.current_state
        