from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.tools.models import Tool
from app.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])

class ToolCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    category: str = "general"
    input_schema: dict = {}
    output_schema: dict = {}
    is_enabled: bool = True
    requires_auth: bool = False
    required_env_keys: list = []
    safe_mock_mode: bool = True

class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    is_enabled: Optional[bool] = None
    requires_auth: Optional[bool] = None
    required_env_keys: Optional[list] = None
    safe_mock_mode: Optional[bool] = None

@router.get("")
async def list_tools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tool).order_by(Tool.name))
    return result.scalars().all()

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_tool(payload: ToolCreate, db: AsyncSession = Depends(get_db)):
    slug_res = await db.execute(select(Tool).where(Tool.slug == payload.slug))
    if slug_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Tool with slug '{payload.slug}' already exists.")
    
    tool = Tool(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        category=payload.category,
        input_schema=payload.input_schema,
        output_schema=payload.output_schema,
        is_enabled=payload.is_enabled,
        requires_auth=payload.requires_auth,
        required_env_keys=payload.required_env_keys,
        safe_mock_mode=payload.safe_mock_mode
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return tool

@router.get("/{tool_id}")
async def get_tool(tool_id: int, db: AsyncSession = Depends(get_db)):
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool

@router.patch("/{tool_id}")
async def update_tool(tool_id: int, payload: ToolUpdate, db: AsyncSession = Depends(get_db)):
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tool, key, value)
        
    await db.commit()
    await db.refresh(tool)
    return tool

@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(tool_id: int, db: AsyncSession = Depends(get_db)):
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    await db.delete(tool)
    await db.commit()

@router.post("/{tool_slug}/run")
async def run_tool(tool_slug: str, payload: dict, db: AsyncSession = Depends(get_db)):
    tool_res = await db.execute(select(Tool).where(Tool.slug == tool_slug))
    tool = tool_res.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found in database")
    
    from app.tools.registry import tool_registry
    registry_tool = tool_registry.get_tool(tool_slug)
    
    if registry_tool:
        try:
            result = await registry_tool.run(**payload)
            return {"status": "success", "output": result}
        except Exception as e:
            return {"status": "error", "output": str(e)}
    else:
        if tool.safe_mock_mode:
            return {"status": "success", "output": f"[MOCK MODE] Tool '{tool.name}' executed successfully with payload: {payload}"}
        else:
            raise HTTPException(status_code=501, detail="Tool not fully implemented in backend registry and mock mode is disabled.")
