# DAGScheduler-Env

An OpenEnv-compliant reinforcement learning environment that simulates a real-world **DAG-based job scheduler** — inspired by tools like Apache Airflow. An AI agent acts as a smart scheduler that must decide when to trigger jobs, handle failures, manage dependencies, and optimize resource usage.

---

## Motivation

Job scheduling is a critical real-world problem faced by every tech company. Tools like Apache Airflow, Prefect, and Dagster are used daily to manage complex pipelines. However, there is no standard RL environment that models this problem for AI agents to learn from.

DAGScheduler-Env fills this gap by providing a simulated scheduling environment where an AI agent can:
- Learn optimal scheduling strategies
- Handle real-world constraints like resource limits and deadlines
- Deal with failures, retries, and cascading effects
- Be evaluated and compared against other agents

---

## Project Structure

```
dagscheduler-env/
├── environment/
│   ├── __init__.py
│   ├── env.py          → Main environment logic (step, reset, state)
│   ├── models.py       → Pydantic data models (Job, State, Action, Reward)
│   └── graders.py      → Scoring logic for each task
├── tasks/
│   ├── __init__.py
│   ├── task_easy.py    → Easy task scenario (3 independent jobs)
│   ├── task_medium.py  → Medium task scenario (5 jobs with dependencies)
│   └── task_hard.py    → Hard task scenario (10 jobs, complex DAG)
├── inference.py        → Baseline AI agent script (coming soon)
├── openenv.yaml        → OpenEnv metadata (coming soon)
├── Dockerfile          → Container configuration (coming soon)
└── README.md           → You are here
```

---

## Architecture Overview

```
inference.py  (AI Agent)
      │
      │  SchedulerAction
      ▼
  env.py  (Environment)
      │
      ├── handle_trigger()
      ├── handle_retry()
      ├── handle_delay()
      ├── handle_cancel()
      ├── handle_reprioritize()
      └── handle_wait()
      │
      │  SchedulerState + SchedulerReward
      ▼
graders.py  (Scorer)
      │
      ├── grade_easy_task()
      ├── grade_medium_task()
      └── grade_hard_task()
```

---

## Data Models (`models.py`)

All models are Pydantic BaseModels for type safety and OpenEnv compliance.

### `Job`
Represents a single schedulable unit of work.

| Field | Type | Description |
|-------|------|-------------|
| job_id | str | Unique identifier |
| name | str | Human readable name |
| schedule | int | Run every N time units |
| dependencies | List[str] | job_ids that must succeed first |
| status | JobStatus | Current state of the job |
| priority | Priority | HIGH / MEDIUM / LOW |
| cpu_required | int | CPU units needed to run |
| memory_required | int | Memory units needed to run |
| retry_count | int | Number of retries attempted |
| max_retries | int | Maximum retries allowed |
| deadline | Optional[int] | Must complete by this time |
| last_run | Optional[int] | Last time job was triggered |

### `SchedulerState`
Snapshot of the entire environment at any point in time.

| Field | Type | Description |
|-------|------|-------------|
| current_time | int | Simulated clock |
| jobs | List[Job] | All jobs in the environment |
| available_cpu | int | Currently free CPU units |
| available_memory | int | Currently free memory units |
| execution_history | List[Dict] | Log of all past actions |
| episode_done | bool | Whether episode has ended |

### `SchedulerAction`
What the AI agent can do at each step.

| Field | Type | Description |
|-------|------|-------------|
| action_type | ActionType | One of 6 action types |
| job_id | Optional[str] | Target job for the action |
| delay_units | Optional[int] | Used with DELAY action |
| new_priority | Optional[Priority] | Used with REPRIORITIZE action |

**Available Actions:**
- `TRIGGER` — Start a job now
- `DELAY` — Postpone a job by N time units
- `RETRY` — Retry a failed job
- `CANCEL` — Cancel a pending or running job
- `REPRIORITIZE` — Change a job's priority
- `WAIT` — Do nothing, advance time by 1 unit

### `SchedulerReward`
Feedback given to the AI after each action.

| Field | Type | Description |
|-------|------|-------------|
| score | float | Between -1.0 and +1.0 |
| reason | str | Human readable explanation |
| details | Dict | Extra info if needed |

---

## Environment Logic (`env.py`)

### `reset()`
Initializes a fresh episode. Resets all jobs to PENDING, clears execution history, resets time to 0. Called at the start of every new episode.

### `step(action: SchedulerAction)`
Core method. Processes the agent's action, updates the environment state, logs to execution history, and returns the new state and reward.

**Reward signals per action:**

| Scenario | Score |
|----------|-------|
| Job triggered successfully | +1.0 |
| Smart retry after failure | +0.5 |
| Job delayed | -0.1 |
| Job not in correct state | -0.5 |
| Dependencies not met | -0.5 |
| Insufficient resources | -0.5 |
| Job not found | -0.5 to -1.0 |

### `state()`
Returns the current environment state without modifying anything.

---

## Tasks

### Task 1 — Easy (`task_easy.py`)
**3 independent jobs with no dependencies.**

The agent must trigger each job at the right time respecting schedule intervals. No failures, sufficient resources always available.

| Job | Name | Schedule | Priority | Deadline |
|-----|------|----------|----------|---------|
| job_1 | Send Daily Report | 12 | MEDIUM | 24 |
| job_2 | Backup Database | 6 | HIGH | 18 |
| job_3 | Clean Temp Files | 24 | LOW | 48 |

**Grading:** `successful_jobs / total_jobs`

---

### Task 2 — Medium (`task_medium.py`)
**5 jobs in a linear pipeline with dependencies.**

The agent must respect job ordering, handle occasional failures with smart retries, and manage limited resources.

```
job_1 → job_2 → job_3 → job_4 → job_5
```

| Job | Name | Depends On |
|-----|------|-----------|
| job_1 | Fetch Raw Data | None |
| job_2 | Validate Data | job_1 |
| job_3 | Transform Data | job_2 |
| job_4 | Load to Warehouse | job_3 |
| job_5 | Send Success Alert | job_4 |

**Grading:** Weighted combination of dependency order (40%), retry handling (30%), resource management (30%)

---

### Task 3 — Hard (`task_hard.py`)
**10 jobs forming a real DAG with multiple entry points, converging pipelines, tight deadlines, and limited resources.**

```
job_1 → job_4 → job_7 → job_9 → job_10
job_2 → job_5 ↗          ↑
job_3 → job_6 → job_8  ↗
```

All HIGH priority jobs have tight deadlines. Resources are very limited (4 CPU, 4 Memory). Agent must handle cascading failures gracefully.

**Grading:** Weighted combination of deadline compliance (40%), critical job completion (40%), cascading failure handling (20%)

---

## Grading Logic (`graders.py`)

All graders return a `SchedulerReward` with score between `0.0` and `1.0`.

### `grade_easy_task(state)`
```
score = successful_jobs / total_jobs
```

### `grade_medium_task(state)`
```
score = (dependency_score × 0.4) +
        (retry_score       × 0.3) +
        (resource_score    × 0.3)
```

### `grade_hard_task(state)`
```
score = (deadline_score   × 0.4) +
        (critical_score   × 0.4) +
        (cascading_score  × 0.2)
```

---

## Contributing

### Things already built:
- [x] `models.py` — All data models
- [x] `env.py` — Full environment logic
- [x] `graders.py` — All 3 graders
- [x] `task_easy.py` — Easy task scenario
- [x] `task_medium.py` — Medium task scenario
- [x] `task_hard.py` — Hard task scenario

### Things still to be built:
- [ ] `inference.py` — Baseline AI agent script
- [ ] `openenv.yaml` — OpenEnv metadata file
- [ ] `Dockerfile` — Container configuration
- [ ] How to run instructions in README

### How to contribute:
1. Fork the repository
2. Pick any pending item from the list above
3. Follow existing code patterns and naming conventions
4. All models must use Pydantic BaseModel
5. All scores must be between 0.0 and 1.0
6. Submit a pull request with a clear description

---

# DAGScheduler-Env

An OpenEnv-compliant reinforcement learning environment that simulates a real-world **DAG-based job scheduler** — inspired by tools like Apache Airflow. An AI agent acts as a smart scheduler that must decide when to trigger jobs, handle failures, manage dependencies, and optimize resource usage.

---

## Motivation

Job scheduling is a critical real-world problem faced by every tech company. Tools like Apache Airflow, Prefect, and Dagster are used daily to manage complex pipelines. However, there is no standard RL environment that models this problem for AI agents to learn from.

DAGScheduler-Env fills this gap by providing a simulated scheduling environment where an AI agent can:
- Learn optimal scheduling strategies
- Handle real-world constraints like resource limits and deadlines
- Deal with failures, retries, and cascading effects
- Be evaluated and compared against other agents

---

## Project Structure

```
dagscheduler-env/
├── environment/
│   ├── __init__.py
│   ├── env.py          → Main environment logic (step, reset, state)
│   ├── models.py       → Pydantic data models (Job, State, Action, Reward)
│   └── graders.py      → Scoring logic for each task
├── tasks/
│   ├── __init__.py
│   ├── task_easy.py    → Easy task scenario (3 independent jobs)
│   ├── task_medium.py  → Medium task scenario (5 jobs with dependencies)
│   └── task_hard.py    → Hard task scenario (10 jobs, complex DAG)
├── inference.py        → Baseline AI agent script (coming soon)
├── openenv.yaml        → OpenEnv metadata (coming soon)
├── Dockerfile          → Container configuration (coming soon)
└── README.md           → You are here
```

---

## Architecture Overview

```
inference.py  (AI Agent)
      │
      │  SchedulerAction
      ▼
  env.py  (Environment)
      │
      ├── handle_trigger()
      ├── handle_retry()
      ├── handle_delay()
      ├── handle_cancel()
      ├── handle_reprioritize()
      └── handle_wait()
      │
      │  SchedulerState + SchedulerReward
      ▼
graders.py  (Scorer)
      │
      ├── grade_easy_task()
      ├── grade_medium_task()
      └── grade_hard_task()
```

---

## Data Models (`models.py`)

All models are Pydantic BaseModels for type safety and OpenEnv compliance.

### `Job`
Represents a single schedulable unit of work.

| Field | Type | Description |
|-------|------|-------------|
| job_id | str | Unique identifier |
| name | str | Human readable name |
| schedule | int | Run every N time units |
| dependencies | List[str] | job_ids that must succeed first |
| status | JobStatus | Current state of the job |
| priority | Priority | HIGH / MEDIUM / LOW |
| cpu_required | int | CPU units needed to run |
| memory_required | int | Memory units needed to run |
| retry_count | int | Number of retries attempted |
| max_retries | int | Maximum retries allowed |
| deadline | Optional[int] | Must complete by this time |
| last_run | Optional[int] | Last time job was triggered |

### `SchedulerState`
Snapshot of the entire environment at any point in time.

| Field | Type | Description |
|-------|------|-------------|
| current_time | int | Simulated clock |
| jobs | List[Job] | All jobs in the environment |
| available_cpu | int | Currently free CPU units |
| available_memory | int | Currently free memory units |
| execution_history | List[Dict] | Log of all past actions |
| episode_done | bool | Whether episode has ended |

### `SchedulerAction`
What the AI agent can do at each step.

| Field | Type | Description |
|-------|------|-------------|
| action_type | ActionType | One of 6 action types |
| job_id | Optional[str] | Target job for the action |
| delay_units | Optional[int] | Used with DELAY action |
| new_priority | Optional[Priority] | Used with REPRIORITIZE action |

**Available Actions:**
- `TRIGGER` — Start a job now
- `DELAY` — Postpone a job by N time units
- `RETRY` — Retry a failed job
- `CANCEL` — Cancel a pending or running job
- `REPRIORITIZE` — Change a job's priority
- `WAIT` — Do nothing, advance time by 1 unit

### `SchedulerReward`
Feedback given to the AI after each action.

| Field | Type | Description |
|-------|------|-------------|
| score | float | Between -1.0 and +1.0 |
| reason | str | Human readable explanation |
| details | Dict | Extra info if needed |

---

## Environment Logic (`env.py`)

### `reset()`
Initializes a fresh episode. Resets all jobs to PENDING, clears execution history, resets time to 0. Called at the start of every new episode.

### `step(action: SchedulerAction)`
Core method. Processes the agent's action, updates the environment state, logs to execution history, and returns the new state and reward.

**Reward signals per action:**

| Scenario | Score |
|----------|-------|
| Job triggered successfully | +1.0 |
| Smart retry after failure | +0.5 |
| Job delayed | -0.1 |
| Job not in correct state | -0.5 |
| Dependencies not met | -0.5 |
| Insufficient resources | -0.5 |
| Job not found | -0.5 to -1.0 |

### `state()`
Returns the current environment state without modifying anything.

---

## Tasks

### Task 1 — Easy (`task_easy.py`)
**3 independent jobs with no dependencies.**

The agent must trigger each job at the right time respecting schedule intervals. No failures, sufficient resources always available.

| Job | Name | Schedule | Priority | Deadline |
|-----|------|----------|----------|---------|
| job_1 | Send Daily Report | 12 | MEDIUM | 24 |
| job_2 | Backup Database | 6 | HIGH | 18 |
| job_3 | Clean Temp Files | 24 | LOW | 48 |

**Grading:** `successful_jobs / total_jobs`

---

### Task 2 — Medium (`task_medium.py`)
**5 jobs in a linear pipeline with dependencies.**

The agent must respect job ordering, handle occasional failures with smart retries, and manage limited resources.

```
job_1 → job_2 → job_3 → job_4 → job_5
```

| Job | Name | Depends On |
|-----|------|-----------|
| job_1 | Fetch Raw Data | None |
| job_2 | Validate Data | job_1 |
| job_3 | Transform Data | job_2 |
| job_4 | Load to Warehouse | job_3 |
| job_5 | Send Success Alert | job_4 |

**Grading:** Weighted combination of dependency order (40%), retry handling (30%), resource management (30%)

---

### Task 3 — Hard (`task_hard.py`)
**10 jobs forming a real DAG with multiple entry points, converging pipelines, tight deadlines, and limited resources.**

```
job_1 → job_4 → job_7 → job_9 → job_10
job_2 → job_5 ↗          ↑
job_3 → job_6 → job_8  ↗
```

All HIGH priority jobs have tight deadlines. Resources are very limited (4 CPU, 4 Memory). Agent must handle cascading failures gracefully.

**Grading:** Weighted combination of deadline compliance (40%), critical job completion (40%), cascading failure handling (20%)

---

## Grading Logic (`graders.py`)

All graders return a `SchedulerReward` with score between `0.0` and `1.0`.

### `grade_easy_task(state)`
```
score = successful_jobs / total_jobs
```

### `grade_medium_task(state)`
```
score = (dependency_score × 0.4) +
        (retry_score       × 0.3) +
        (resource_score    × 0.3)
```

### `grade_hard_task(state)`
```
score = (deadline_score   × 0.4) +
        (critical_score   × 0.4) +
        (cascading_score  × 0.2)
```


### How to contribute:
1. Fork the repository
2. Pick any pending item from the list above
3. Follow existing code patterns and naming conventions
4. All models must use Pydantic BaseModel
5. All scores must be between 0.0 and 1.0
6. Submit a pull request with a clear description

---

## How to Run

### Prerequisites
- Python 3.10+
- Docker (optional, for containerized run)
- Hugging Face API key

---

### 1. Clone the Repository
```bash
git clone https://github.com/Dhhimanshu99580/openenv-scheduler-env.git
cd openenv-scheduler-env
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Activate on Mac/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Create a `.env` file in root folder:
```

# using Hugging Face
API_BASE_URL=https://router.huggingface.co/v1
MODEL_NAME=meta-llama/Meta-Llama-3-8B-Instruct
HF_TOKEN=your_huggingface_token
```

### 5. Run Inference Script
```bash
python inference.py
```

Expected output:
```
Step 1 | Action: TRIGGER | Reward: 1.00 | Reason: Job job_1 triggered successfully
Step 2 | Action: WAIT    | Reward: 0.10 | Reason: Time advanced by 1 unit
...
Task: easy   | Score: 0.85 | Reason: 3/3 jobs completed successfully
Task: medium | Score: 0.72 | Reason: Dependency Score: 0.80, ...
Task: hard   | Score: 0.61 | Reason: Deadline Met: 0.70, ...
```

---

### 6. Run with Docker
```bash
# Build
docker build -t dagscheduler-env .

# Run
docker run \
  -e API_BASE_URL=https://router.huggingface.co/v1 \
  -e MODEL_NAME=llama3-8b-8192 \
  -e HF_TOKEN=your_api_key \
  dagscheduler-env
```

---

### 7. Deploy to Hugging Face Spaces
```bash
# Add HF remote
git remote add hf https://YOUR_HF_USERNAME:YOUR_HF_TOKEN@huggingface.co/spaces/YOUR_HF_USERNAME/dagscheduler-env

# Push
git push hf main
```

Then add secrets in HF Space:
```
Settings → Variables and Secrets → New Secret
Add: API_BASE_URL, MODEL_NAME, HF_TOKEN
```
