from environment.models import *

def get_hard_task():
    jobs = [
        Job(
            job_id="job_1",
            name="Ingest Customer Data",
            schedule=3,
            dependencies=[],
            cpu_required=2,
            memory_required=2,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=2,
            deadline=6,
            last_run=None
        ),
        Job(
            job_id="job_2",
            name="Ingest Transaction Data",
            schedule=3,
            dependencies=[],
            cpu_required=2,
            memory_required=2,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=2,
            deadline=6,
            last_run=None
        ),
        Job(
            job_id="job_3",
            name="Ingest Product Catalog",
            schedule=3,
            dependencies=[],
            cpu_required=1,
            memory_required=1,
            status=JobStatus.PENDING,
            priority=Priority.MEDIUM,
            retry_count=0,
            max_retries=2,
            deadline=8,
            last_run=None
        ),

        Job(
            job_id="job_4",
            name="Validate Customer Data",
            schedule=3,
            dependencies=["job_1"],
            cpu_required=1,
            memory_required=1,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=2,
            deadline=10,
            last_run=None
        ),
        Job(
            job_id="job_5",
            name="Validate Transaction Data",
            schedule=3,
            dependencies=["job_2"],
            cpu_required=1,
            memory_required=1,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=2,
            deadline=10,
            last_run=None
        ),
        Job(
            job_id="job_6",
            name="Enrich Product Data",
            schedule=3,
            dependencies=["job_3"],
            cpu_required=1,
            memory_required=2,
            status=JobStatus.PENDING,
            priority=Priority.MEDIUM,
            retry_count=0,
            max_retries=2,
            deadline=12,
            last_run=None
        ),

        Job(
            job_id="job_7",
            name="Join Customer & Transactions",
            schedule=3,
            dependencies=["job_4", "job_5"],  # needs both!
            cpu_required=2,
            memory_required=2,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=2,
            deadline=15,
            last_run=None
        ),
        Job(
            job_id="job_8",
            name="Calculate Product Metrics",
            schedule=3,
            dependencies=["job_6"],
            cpu_required=2,
            memory_required=2,
            status=JobStatus.PENDING,
            priority=Priority.MEDIUM,
            retry_count=0,
            max_retries=2,
            deadline=16,
            last_run=None
        ),

        Job(
            job_id="job_9",
            name="Generate Business Report",
            schedule=3,
            dependencies=["job_7", "job_8"],  # needs both!
            cpu_required=2,
            memory_required=2,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=2,
            deadline=20,
            last_run=None
        ),

        Job(
            job_id="job_10",
            name="Send Executive Dashboard Alert",
            schedule=3,
            dependencies=["job_9"],
            cpu_required=1,
            memory_required=1,
            status=JobStatus.PENDING,
            priority=Priority.HIGH,
            retry_count=0,
            max_retries=2,
            deadline=24,
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