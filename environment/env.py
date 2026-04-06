from environment.models import *

class SchedulerEnv:
    def __init__(self, initial_state: SchedulerState):
        self.state = initial_state

    def reset(self):
        self.state.current_time = 0
        for job in self.state.jobs:
            job.status = JobStatus.PENDING
            job.retry_count = 0
            job.last_run = None
        self.state.available_cpu=1
        self.state.available_memory=1
        self.state.execution_history = []
        self.state.episode_done = False
        return self.state
    
    def step(self, action: SchedulerAction):
        reward = SchedulerReward(score=0.0, reason="No action taken")
        # Implement logic to update state based on action
        # Update reward based on the outcome of the action
        # Check if episode is done (e.g., all jobs completed or failed)
        return self.state, reward
    
    def state(self):
        return self.state

        