from environment.models import *


class SchedulerGrader:
    def __init__(self):
        pass

    def grade_easy_task(self,state):
        total_jobs = len(state.jobs)
        reward = 0.0
        for job in state.jobs:
            if job.status == JobStatus.SUCCESS:
                reward += 1.0
        if total_jobs>0:
            return SchedulerReward(score=reward/total_jobs, reason=f"{int(reward)}/{total_jobs} jobs completed successfully")
        return SchedulerReward(score=0.0, reason="No jobs in the system")
    
    def grade_medium_task(self,state):
        total_jobs = len(state.jobs)
        dependencyScore = 0.0
        retry_handling_score = 0.0
        resource_utilization_score = 0.0
        for job in state.jobs:
            if job.status == JobStatus.SUCCESS:
                dependencyScore+= self.isDependencySuccess(state, job)
            if job.status == JobStatus.FAILED:
                retry_handling_score+= self.checkRetryHandling(state, job)
            resource_utilization_score+= self.checkResourceUtilization(state,job)
        failed_jobs = sum(1 for job in state.jobs if job.status == JobStatus.FAILED)
        dependencyScore = dependencyScore / total_jobs if total_jobs > 0 else 0.0
        retry_handling_score = retry_handling_score / failed_jobs if failed_jobs > 0 else 1.0
        resource_utilization_score = resource_utilization_score / total_jobs if total_jobs > 0 else 0.0
        overall_score = (dependencyScore*0.4)+(retry_handling_score*0.3)+(resource_utilization_score*0.3)
        return SchedulerReward (score=overall_score, reason=f"Dependency Score: {dependencyScore:.2f}, Retry Handling Score: {retry_handling_score:.2f}, Resource Utilization Score: {resource_utilization_score:.2f}")


    def isDependencySuccess(self, state, job):
        jobs_with_deps_met = 0
        total_jobs_with_dependencies = 0
        for dep_id in job.dependencies:
            dep_job = next((j for j in state.jobs if j.job_id == dep_id), None)
            total_jobs_with_dependencies+=1
            if dep_job is not None and dep_job.status == JobStatus.SUCCESS:
                jobs_with_deps_met+=1
        return jobs_with_deps_met/total_jobs_with_dependencies if total_jobs_with_dependencies>0 else 1.0


    def checkRetryHandling(self, state, job):
        successAfterRetry = 0  
        failedAfterRetry = 0 
        if job.retry_count > 0 and job.status == JobStatus.SUCCESS:
            successAfterRetry+=1
        elif job.retry_count > 0 and job.status == JobStatus.FAILED:
            failedAfterRetry+=1
        return successAfterRetry/(successAfterRetry+failedAfterRetry) if (successAfterRetry+failedAfterRetry)>0 else 1.0
    
    def checkResourceUtilization(self, state, job):
        total_actions = len(state.execution_history)
        resource_mismanagement = 0
        for entry in state.execution_history:
            if "Not enough resources" in entry["reason"] and entry["job_id"] == job.job_id:
                resource_mismanagement+=1
        return 1.0 - (resource_mismanagement/total_actions) if total_actions>0 else 1.0
    
    def grade_hard_task(self,state):
        deadline_met = 0.0
        critical_score = 0.0
        casacading_effect_score = 0.0
        total_jobs = len(state.jobs)
        for job in state.jobs:
            deadline_met += self.isDeadLineMet(state,job)
            critical_score += self.isCriticalJobHandled(state, job)
            casacading_effect_score += self.checkCascadingEffects(state, job)
        deadline_met = deadline_met / total_jobs if total_jobs > 0 else 0.0
        critical_score = critical_score / total_jobs if total_jobs > 0 else 0.0
        casacading_effect_score = casacading_effect_score / total_jobs if total_jobs > 0 else 0.0
        overall_score = (deadline_met*0.4)+(critical_score*0.4)+(casacading_effect_score*0.2)
        return SchedulerReward(score=overall_score, reason=f"Deadline Met: {deadline_met:.2f}, Critical Jobs Handled: {critical_score:.2f}, Cascading Effects: {casacading_effect_score:.2f}")

    def isDeadLineMet(self,state,job):
        if job.deadline is not None and job.status == JobStatus.SUCCESS:
            if job.last_run <= job.deadline:
                return 1.0
            else: 
                return 0.0
        return 1.0
    
    def isCriticalJobHandled(self,state,job):
        if job.priority == Priority.HIGH:
            if job.status == JobStatus.SUCCESS:
                return 1.0
            else:
                return 0.0
        return 1.0
    
    def checkCascadingEffects(self, state, job):
        if job.status != JobStatus.FAILED:
            return 1.0
        dependent_jobs = []
        for j in state.jobs:
            if job.job_id in j.dependencies:
                dependent_jobs.append(j)
        if len(dependent_jobs) == 0:
            return 1.0
        properly_handled = 0
        for dep in dependent_jobs:
         if dep.status in [JobStatus.CANCELLED, JobStatus.SKIPPED]:
            properly_handled += 1
        return properly_handled / len(dependent_jobs)
