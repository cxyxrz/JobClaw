"""智能体管理接口：Agent 列表 / 模型用量 / 任务调度 / 职位信息管理操作。"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from ...core.permissions import require_perm
from ...core.response import ApiResponse
from ...modules.agents.base import all_agents
from ...modules.agents.jobinfo_agent import dedupe_jobs, expire_jobs, job_stats
from ...modules.agents.model_router import model_router
from ...modules.agents.scheduler_agent import (
    create_task,
    delete_task,
    list_tasks,
    run_scheduled_task,
    set_task_enabled,
)

router = APIRouter(prefix="/agents", tags=["agents"])


# ---------- Agent 注册表 ----------

class AgentInfo(BaseModel):
    name: str
    description: str
    admin_only: bool


@router.get("", response_model=ApiResponse[list[AgentInfo]])
async def list_agents(_: object = Depends(require_perm("agent:manage"))) -> ApiResponse:
    return ApiResponse(
        data=[
            AgentInfo(name=a.name, description=a.description, admin_only=a.admin_only)
            for a in all_agents()
        ]
    )


# ---------- 模型路由用量 ----------

@router.get("/model-usage", response_model=ApiResponse[list[dict]])
async def model_usage(_: object = Depends(require_perm("agent:manage"))) -> ApiResponse:
    return ApiResponse(data=await model_router.usage_stats())


# ---------- 任务调度 ----------

class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    task_type: str
    cron: str = Field(min_length=9, max_length=32)  # 标准 5 段 crontab
    params: dict = {}


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    task_type: str
    cron: str
    params: str
    enabled: int
    last_run_at: datetime | None = None
    last_status: str
    last_message: str
    heartbeat_at: datetime | None = None
    created_at: datetime


class TaskToggle(BaseModel):
    enabled: bool


@router.post("/tasks", status_code=201, response_model=ApiResponse[TaskOut])
async def create_scheduled_task(
    body: TaskCreate, subject=Depends(require_perm("agent:manage"))
) -> ApiResponse[TaskOut]:
    task = await create_task(
        name=body.name,
        task_type=body.task_type,
        cron=body.cron,
        params=body.params,
        created_by=subject.user_id,
    )
    return ApiResponse(data=TaskOut.model_validate(task))


@router.get("/tasks", response_model=ApiResponse[list[TaskOut]])
async def list_scheduled_tasks(_: object = Depends(require_perm("agent:manage"))) -> ApiResponse:
    return ApiResponse(data=[TaskOut.model_validate(t) for t in await list_tasks()])


@router.post("/tasks/{task_id}/toggle", response_model=ApiResponse[TaskOut])
async def toggle_scheduled_task(
    task_id: int, body: TaskToggle, _: object = Depends(require_perm("agent:manage"))
) -> ApiResponse[TaskOut]:
    task = await set_task_enabled(task_id, body.enabled)
    return ApiResponse(data=TaskOut.model_validate(task))


@router.post("/tasks/{task_id}/run", response_model=ApiResponse[dict])
async def run_task_now(
    task_id: int, _: object = Depends(require_perm("agent:manage"))
) -> ApiResponse[dict]:
    """手动触发一次（同时更新心跳/状态/推送）。"""
    return ApiResponse(data=await run_scheduled_task(task_id))


@router.delete("/tasks/{task_id}", response_model=ApiResponse[dict])
async def delete_scheduled_task(
    task_id: int, _: object = Depends(require_perm("agent:manage"))
) -> ApiResponse[dict]:
    await delete_task(task_id)
    return ApiResponse(data={"deleted": task_id})


# ---------- 校招信息管理操作（业务 Agent 能力直达）----------

class ExpireRequest(BaseModel):
    days: int = Field(default=90, ge=1, le=3650)


@router.get("/jobinfo/stats", response_model=ApiResponse[dict])
async def jobinfo_stats(_: object = Depends(require_perm("agent:manage"))) -> ApiResponse:
    return ApiResponse(data=await job_stats())


@router.post("/jobinfo/expire", response_model=ApiResponse[dict])
async def jobinfo_expire(
    body: ExpireRequest, _: object = Depends(require_perm("agent:manage"))
) -> ApiResponse:
    count = await expire_jobs(body.days)
    return ApiResponse(data={"offlined": count, "days": body.days})


@router.post("/jobinfo/dedupe", response_model=ApiResponse[dict])
async def jobinfo_dedupe(_: object = Depends(require_perm("agent:manage"))) -> ApiResponse:
    return ApiResponse(data={"offlined": await dedupe_jobs()})
