"""
任務管理API端點
提供任務的創建、查詢、更新、刪除等功能
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4
import asyncio
import logging

# 導入任務執行器
from app.services.task_executor import get_task_executor, TaskExecutor

# 配置日誌
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ===== 請求/響應模型 =====

class TaskStatus(str, Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskType(str, Enum):
    """任務類型枚舉"""
    HEALTH_CHECK = "health_check"
    PROXY_TEST = "proxy_test"
    DATA_COLLECTION = "data_collection"
    SYSTEM_MAINTENANCE = "system_maintenance"
    CUSTOM = "custom"


class TaskCreate(BaseModel):
    """創建任務請求模型"""
    name: str = Field(..., description="任務名稱", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="任務描述", max_length=500)
    type: TaskType = Field(..., description="任務類型")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="任務配置")
    schedule: Optional[str] = Field(None, description="定時任務表達式")
    priority: int = Field(1, ge=1, le=10, description="優先級 (1-10)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="任務參數")


class TaskUpdate(BaseModel):
    """更新任務請求模型"""
    name: Optional[str] = Field(None, description="任務名稱", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="任務描述", max_length=500)
    config: Optional[Dict[str, Any]] = Field(None, description="任務配置")
    schedule: Optional[str] = Field(None, description="定時任務表達式")
    priority: Optional[int] = Field(None, ge=1, le=10, description="優先級 (1-10)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="任務參數")


class TaskResponse(BaseModel):
    """任務響應模型"""
    id: str = Field(..., description="任務ID")
    name: str = Field(..., description="任務名稱")
    description: Optional[str] = Field(None, description="任務描述")
    type: TaskType = Field(..., description="任務類型")
    status: TaskStatus = Field(..., description="任務狀態")
    config: Dict[str, Any] = Field(default_factory=dict, description="任務配置")
    schedule: Optional[str] = Field(None, description="定時任務表達式")
    priority: int = Field(1, description="優先級")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="任務參數")
    result: Optional[Dict[str, Any]] = Field(None, description="執行結果")
    error_message: Optional[str] = Field(None, description="錯誤信息")
    created_at: datetime = Field(..., description="創建時間")
    started_at: Optional[datetime] = Field(None, description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    duration: Optional[int] = Field(None, description="執行時長(秒)")
    created_by: Optional[str] = Field(None, description="創建者")


class TaskListResponse(BaseModel):
    """任務列表響應模型"""
    tasks: List[TaskResponse] = Field(..., description="任務列表")
    total: int = Field(..., description="總數")
    page: int = Field(1, description="當前頁碼")
    page_size: int = Field(20, description="每頁數量")


# ===== 全局任務存儲（內存存儲）=====
tasks_db: Dict[str, TaskResponse] = {}


def generate_task_id() -> str:
    """生成任務ID"""
    return str(uuid4())


# ===== API端點實現 =====

@router.get("", response_model=TaskListResponse)
async def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="任務狀態篩選"),
    type: Optional[TaskType] = Query(None, description="任務類型篩選"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量")
) -> TaskListResponse:
    """
    獲取任務列表
    
    Args:
        status: 任務狀態篩選
        type: 任務類型篩選
        page: 頁碼
        page_size: 每頁數量
        
    Returns:
        TaskListResponse: 任務列表響應
    """
    try:
        # 獲取所有任務
        all_tasks = list(tasks_db.values())
        
        # 應用篩選條件
        filtered_tasks = all_tasks
        if status:
            filtered_tasks = [task for task in filtered_tasks if task.status == status]
        if type:
            filtered_tasks = [task for task in filtered_tasks if task.type == type]
        
        # 分頁
        total = len(filtered_tasks)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_tasks = filtered_tasks[start:end]
        
        return TaskListResponse(
            tasks=paginated_tasks,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取任務列表失敗: {str(e)}")


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_request: TaskCreate) -> TaskResponse:
    """
    創建新任務
    
    Args:
        task_request: 任務創建請求
        
    Returns:
        TaskResponse: 創建的任務
    """
    try:
        # 創建任務
        task_id = generate_task_id()
        now = datetime.utcnow()
        
        task = TaskResponse(
            id=task_id,
            name=task_request.name,
            description=task_request.description,
            type=task_request.type,
            status=TaskStatus.PENDING,
            config=task_request.config or {},
            schedule=task_request.schedule,
            priority=task_request.priority,
            parameters=task_request.parameters or {},
            result=None,
            error_message=None,
            created_at=now,
            started_at=None,
            completed_at=None,
            duration=None,
            created_by="system"
        )
        
        # 存儲任務
        tasks_db[task_id] = task
        
        return task
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"創建任務失敗: {str(e)}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """
    獲取任務詳情
    
    Args:
        task_id: 任務ID
        
    Returns:
        TaskResponse: 任務詳情
    """
    try:
        # 查詢任務
        if task_id not in tasks_db:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        return tasks_db[task_id]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取任務詳情失敗: {str(e)}")


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate) -> TaskResponse:
    """
    更新任務
    
    Args:
        task_id: 任務ID
        task_update: 任務更新請求
        
    Returns:
        TaskResponse: 更新後的任務
    """
    try:
        # 查詢任務
        if task_id not in tasks_db:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        task = tasks_db[task_id]
        
        # 更新字段
        if task_update.name is not None:
            task.name = task_update.name
        if task_update.description is not None:
            task.description = task_update.description
        if task_update.config is not None:
            task.config = task_update.config
        if task_update.schedule is not None:
            task.schedule = task_update.schedule
        if task_update.priority is not None:
            task.priority = task_update.priority
        if task_update.parameters is not None:
            task.parameters = task_update.parameters
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新任務失敗: {str(e)}")


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str) -> None:
    """
    刪除任務
    
    Args:
        task_id: 任務ID
    """
    try:
        # 查詢任務
        if task_id not in tasks_db:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 刪除任務
        del tasks_db[task_id]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除任務失敗: {str(e)}")


@router.post("/{task_id}/start", response_model=TaskResponse)
async def start_task(
    task_id: str, 
    background_tasks: BackgroundTasks,
    executor: TaskExecutor = Depends(get_task_executor)
) -> TaskResponse:
    """
    開始任務
    
    Args:
        task_id: 任務ID
        background_tasks: 後台任務
        executor: 任務執行器
        
    Returns:
        TaskResponse: 任務詳情
    """
    try:
        # 查詢任務
        if task_id not in tasks_db:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        task = tasks_db[task_id]
        
        # 檢查任務狀態
        if task.status == TaskStatus.RUNNING:
            raise HTTPException(status_code=400, detail="任務已在運行中")
        
        # 更新任務狀態
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        # 在後台執行任務
        async def execute_task_async():
            try:
                logger.info(f"開始在後台執行任務 {task_id}")
                
                # 將任務數據轉換為執行器格式
                task_data = {
                    'id': task.id,
                    'type': task.type,
                    'config': task.config,
                    'parameters': task.parameters if task.parameters else {}
                }
                
                logger.info(f"任務數據: {task_data}")
                
                # 執行任務
                result = await executor.execute_task(task_data)
                
                logger.info(f"任務執行結果: {result}")
                
                # 更新任務結果
                if result['success']:
                    task.status = TaskStatus.COMPLETED
                    task.result = result.get('result', {})
                    completed_at_str = result.get('completed_at', datetime.utcnow().isoformat())
                    task.completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00') if 'Z' in completed_at_str else completed_at_str)
                    task.duration = int((task.completed_at - task.started_at).total_seconds())
                    logger.info(f"任務 {task_id} 執行成功")
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = result.get('error', 'Unknown error')
                    completed_at_str = result.get('completed_at', datetime.utcnow().isoformat())
                    task.completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00') if 'Z' in completed_at_str else completed_at_str)
                    logger.error(f"任務 {task_id} 執行失敗: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"任務 {task_id} 執行異常: {str(e)}", exc_info=True)
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
        
        # 添加到後台任務
        background_tasks.add_task(execute_task_async)
        
        logger.info(f"任務 {task_id} 已添加到後台執行隊列")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"開始任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"開始任務失敗: {str(e)}")


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: str) -> TaskResponse:
    """
    取消任務
    
    Args:
        task_id: 任務ID
        
    Returns:
        TaskResponse: 任務詳情
    """
    try:
        # 查詢任務
        if task_id not in tasks_db:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        task = tasks_db[task_id]
        
        # 更新任務狀態
        if task.status not in [TaskStatus.RUNNING, TaskStatus.PENDING]:
            raise HTTPException(status_code=400, detail="任務狀態不允許取消")
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        
        if task.started_at:
            task.duration = int((task.completed_at - task.started_at).total_seconds())
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任務失敗: {str(e)}")


@router.post("/{task_id}/rerun", response_model=TaskResponse)
async def rerun_task(task_id: str) -> TaskResponse:
    """
    重新運行任務
    
    Args:
        task_id: 任務ID
        
    Returns:
        TaskResponse: 新任務詳情
    """
    try:
        # 查詢原任務
        if task_id not in tasks_db:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        original_task = tasks_db[task_id]
        
        # 創建新任務（複製原任務配置）
        new_task_id = generate_task_id()
        now = datetime.utcnow()
        
        new_task = TaskResponse(
            id=new_task_id,
            name=f"{original_task.name} (重新運行)",
            description=original_task.description,
            type=original_task.type,
            status=TaskStatus.PENDING,
            config=original_task.config,
            schedule=original_task.schedule,
            priority=original_task.priority,
            parameters=original_task.parameters,
            result=None,
            error_message=None,
            created_at=now,
            started_at=None,
            completed_at=None,
            duration=None,
            created_by=original_task.created_by
        )
        
        # 存儲新任務
        tasks_db[new_task_id] = new_task
        
        return new_task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新運行任務失敗: {str(e)}")