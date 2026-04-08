from environment.models import *

def get_medium_task():
    jobs = [
        Job(
            job_id="job_1",
            name="Fetch Raw Data from API",
            schedule=5,
            dependencies=[],
            cpu_required=1,
            memory_required=1,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=3,
            deadline=10,
            last_run=None
        ),
        Job(
            job_id="job_2",
            name="Validate Data",
            schedule=5,
            dependencies=["job_1"],  
            cpu_required=1,
            memory_required=1,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=3,
            deadline=15,
            last_run=None
        ),
        Job(
            job_id="job_3",
            name="Transform Data",
            schedule=5,
            dependencies=["job_2"],  
            cpu_required=2,
            memory_required=2,
            status=JobStatus.PENDING,
            priority=Priority.MEDIUM,
            retry_count=0,
            max_retries=3,
            deadline=20,
            last_run=None
        ),
        Job(
            job_id="job_4",
            name="Load Data to Warehouse",
            schedule=5,
            dependencies=["job_3"],  
            cpu_required=2,
            memory_required=2,
            status=JobStatus.PENDING,
            priority=Priority.MEDIUM,
            retry_count=0,
            max_retries=3,
            deadline=25,
            last_run=None
        ),
        Job(
            job_id="job_5",
            name="Send Pipeline Success Alert",
            schedule=5,
            dependencies=["job_4"],
            cpu_required=1,
            memory_required=1,
            status=JobStatus.PENDING,
            priority=Priority.LOW,
            retry_count=0,
            max_retries=3,
            deadline=30,
            last_run=None
        ),
        Job(
            job_id="job_6",
            name="Archive Old Logs",
            schedule=5,
            dependencies=[],
            cpu_required=1,
            memory_required=1,
            status=JobStatus.FAILED,
            priority=Priority.LOW,
            retry_count=0,
            max_retries=3,
            deadline=35,
            last_run=None
        ),
    ]
    return SchedulerState(
        current_time=0,
        jobs=jobs,
        available_cpu=4,
        available_memory=4,
        execution_history=[]
    )