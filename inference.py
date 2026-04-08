import os
import json
import re
import httpx
from openai import OpenAI
from environment.env import SchedulerEnv
from environment.models import *
from tasks.task_easy import get_easy_task
from tasks.task_medium import get_medium_task
from tasks.task_hard import get_hard_task
from environment.graders import SchedulerGrader
from dotenv import load_dotenv
load_dotenv() 

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
HF_TOKEN     = os.getenv("HF_TOKEN")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
    http_client=httpx.Client(verify=False)
)

def log_start(task: str, model: str) -> None:
    print(f"[START] task={task} env=openenv-scheduler model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error) -> None:
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: list) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

def action_str(action: SchedulerAction) -> str:
    if action.action_type in (ActionType.TRIGGER, ActionType.RETRY):
        return f"{action.action_type.value}({action.job_id})"
    return action.action_type.value

def run_episode(env, task_name: str, max_steps=50):
    env.reset()
    log_start(task=task_name, model=MODEL_NAME)
    rewards = []
    steps_taken = 0
    for step in range(max_steps):
        current_state = env.current_state

        last_events = current_state.execution_history[-3:] if current_state.execution_history else []
        running_jobs = [j.job_id for j in current_state.jobs if j.status == JobStatus.RUNNING]
        failed_jobs  = [j.job_id for j in current_state.jobs if j.status == JobStatus.FAILED]
        urgent_jobs  = [
            f"{j.job_id} (deadline={j.deadline}, time_left={j.deadline - current_state.current_time})"
            for j in current_state.jobs
            if j.status == JobStatus.PENDING and j.deadline is not None
               and j.deadline - current_state.current_time <= 5
        ]

        job_map = {j.job_id: j for j in current_state.jobs}
        triggerable_jobs = [
            j.job_id for j in current_state.jobs
            if j.status == JobStatus.PENDING
            and j.cpu_required <= current_state.available_cpu
            and j.memory_required <= current_state.available_memory
            and all(job_map[d].status == JobStatus.SUCCESS for d in j.dependencies if d in job_map)
        ]

        retry_actions = [f'{{"action_type": "retry", "job_id": "{jid}"}}' for jid in failed_jobs]

        if not triggerable_jobs and not failed_jobs:
            action = SchedulerAction(action_type=ActionType.WAIT)
        elif not triggerable_jobs and failed_jobs:
            action = SchedulerAction(action_type=ActionType.RETRY, job_id=failed_jobs[0])
        else:
            action = None 

        if action is not None:
            next_state, reward = env.step(action)
            steps_taken += 1
            rewards.append(reward.score)
            log_step(steps_taken, action_str(action), reward.score, next_state.episode_done, None)
            if next_state.episode_done:
                break
            continue

        prompt = f"""
        You are a DAG job scheduler agent.

        CRITICAL CONSTRAINTS — follow these exactly:
        1. You may ONLY trigger jobs from this list: {triggerable_jobs if triggerable_jobs else "NONE — do not trigger anything"}.
        2. If the triggerable list is NONE and there are no FAILED jobs, you MUST return {{"action_type": "wait"}}.
        3. FAILED jobs must be retried using RETRY action (not TRIGGER). Retry these now: {retry_actions if retry_actions else "NONE"}.
        4. Trigger ALL jobs in the triggerable list before using WAIT — maximize parallelism.

        Current State:
        {current_state.model_dump_json(indent=2)}

        Running jobs (waiting to complete on next WAIT): {running_jobs if running_jobs else "NONE"}
        {"URGENT jobs near deadline: " + ", ".join(urgent_jobs) if urgent_jobs else ""}

        Recent history:
        {json.dumps(last_events, indent=2)}

        Return ONLY a JSON like this:
        {{"action_type": "TRIGGER", "job_id": "job_1"}}
        """
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a scheduling assistant. Always respond with ONLY a valid JSON object. No explanations, no markdown, no code blocks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        content = response.choices[0].message.content
        try:
            match = re.search(r'\{.*?\}', content, re.DOTALL)
            if not match:
                raise ValueError("No JSON object found in response")
            action_dict = json.loads(match.group())
            action_dict["action_type"] = action_dict["action_type"].lower()
            action = SchedulerAction(**action_dict)
        except Exception as e:
            steps_taken += 1
            rewards.append(0.0)
            log_step(steps_taken, "parse_error", 0.0, False, str(e))
            break

        if action.action_type == "trigger" and action.job_id not in triggerable_jobs:
            if failed_jobs:
                action = SchedulerAction(action_type="retry", job_id=failed_jobs[0])
            else:
                action = SchedulerAction(action_type="wait")
        elif action.action_type == "retry" and (not hasattr(action, 'job_id') or action.job_id not in failed_jobs):
            if triggerable_jobs:
                action = SchedulerAction(action_type="trigger", job_id=triggerable_jobs[0])
            else:
                action = SchedulerAction(action_type="wait")

        next_state, reward = env.step(action)
        steps_taken += 1
        rewards.append(reward.score)
        log_step(steps_taken, action_str(action), reward.score, next_state.episode_done, None)
        if next_state.episode_done:
            break
    return rewards, steps_taken

if __name__ == "__main__":
    grader = SchedulerGrader()

    for task_name, get_task, grade_fn, max_steps in [
        ("easy",   get_easy_task,   grader.grade_easy_task,   50),
        ("medium", get_medium_task, grader.grade_medium_task, 100),
        ("hard",   get_hard_task,   grader.grade_hard_task,   200),
    ]:
        env = SchedulerEnv(get_task())
        rewards, steps_taken = run_episode(env, task_name=task_name, max_steps=max_steps)
        grade = grade_fn(env.current_state)
        score = max(0.0, min(1.0, grade.score))
        log_end(success=score > 0.0, steps=steps_taken, score=score, rewards=rewards)