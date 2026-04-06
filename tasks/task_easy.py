from environment.models import *

def get_easy_task():
    jobs = [
        Job(
            job_id="job_1",
            name="Send Daily Report",
            schedule=12,
            dependencies=[],
            cpu_required=1,
            memory_required=1,
            status=JobStatus.PENDING,
            priority=Priority.MEDIUM,
            retry_count=0,
            max_retries=3,
            deadline=24,
            last_run=None
        ),
        Job(
            job_id="job_2",
            name="Backup Database",
            schedule=6,
            dependencies=[],
            cpu_required=2,
            memory_required=2,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=3,
            deadline=18,
            last_run=None
        ),
        Job(
            job_id="job_3",
            name="Clean Temp Files",
            schedule=24,
            dependencies=[],
            cpu_required=1,
            memory_required=1,
            status=JobStatus.PENDING,
            priority=Priority.LOW,
            retry_count=0,
            max_retries=3,
            deadline=48,
            last_run=None
        )
    ]
    return SchedulerState(
        current_time=0,
        jobs=jobs,
        available_cpu=5,
        available_memory=5,
        execution_history=[]
    )