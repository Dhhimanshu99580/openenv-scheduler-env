from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from environment.env import SchedulerEnv
from environment.models import SchedulerAction
from tasks.task_easy import get_easy_task
from tasks.task_medium import get_medium_task
from tasks.task_hard import get_hard_task

app = FastAPI(title="DAG Scheduler OpenEnv")

TASKS = {
    "easy":   get_easy_task,
    "medium": get_medium_task,
    "hard":   get_hard_task,
}

_envs: dict = {}


@app.get("/")
def ping():
    return {"status": "ok"}


@app.post("/reset")
def reset(task: str = "easy"):
    if task not in TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown task '{task}'. Choose from {list(TASKS)}")
    _envs[task] = SchedulerEnv(TASKS[task]())
    state = _envs[task].reset()
    return JSONResponse(content=state.model_dump())


@app.post("/step")
def step(action: SchedulerAction, task: str = "easy"):
    if task not in _envs:
        raise HTTPException(status_code=400, detail="Call /reset first")
    next_state, reward = _envs[task].step(action)
    return JSONResponse(content={"state": next_state.model_dump(), "reward": reward.model_dump()})


@app.get("/state")
def state(task: str = "easy"):
    if task not in _envs:
        raise HTTPException(status_code=400, detail="Call /reset first")
    return JSONResponse(content=_envs[task].state().model_dump())


def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
