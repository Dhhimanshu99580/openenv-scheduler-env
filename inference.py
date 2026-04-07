import os
import json
from openai import OpenAI
from environment.env import SchedulerEnv
from environment.models import *
from tasks.task_easy import get_easy_task
from tasks.task_medium import get_medium_task
from tasks.task_hard import get_hard_task
from environment.graders import SchedulerGrader
from dotenv import load_dotenv
load_dotenv() 

API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME   = os.getenv("MODEL_NAME")
HF_TOKEN     = os.getenv("HF_TOKEN")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

def run_episode(env, max_steps=50):
    state = env.reset()
    for step in range(max_steps):
        current_state = env.current_state
        prompt = f"""
        You are a DAG job scheduler agent.

        Current State:
        {current_state.model_dump_json(indent=2)}

        Available actions: TRIGGER, DELAY, RETRY, CANCEL, REPRIORITIZE, WAIT

        Return ONLY a JSON like this:
        {{"action_type": "TRIGGER", "job_id": "job_1"}}
        """
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a scheduling assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        content = response.choices[0].message.content
        try:
            action_dict = json.loads(content)
            action_dict["action_type"] = action_dict["action_type"].lower()
            action = SchedulerAction(**action_dict)
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"LLM response was: {content}")
            break
        next_state, reward = env.step(action)
        print(f"Step {step+1} | Action: {action.action_type} | Reward: {reward.score:.2f} | Reason: {reward.reason}")
        if next_state.episode_done:
            break
    return env

if __name__ == "__main__":
    grader = SchedulerGrader()
    
    for task_name, get_task, grade_fn in [
        ("easy",   get_easy_task,   grader.grade_easy_task),
        ("medium", get_medium_task, grader.grade_medium_task),
        ("hard",   get_hard_task,   grader.grade_hard_task),
    ]:
        env = SchedulerEnv(get_task())
        run_episode(env)
        score = grade_fn(env.current_state) 
        print(f"Task: {task_name} | Score: {score.score:.2f} | Reason: {score.reason}")