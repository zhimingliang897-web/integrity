import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.config import settings
from services.agent_service import AgentService, global_search_progress

router = APIRouter(prefix="/api/agent", tags=["AI助手"])


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


@router.post("/chat")
async def chat(
    request: ChatRequest,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent_service = AgentService(db, user=user)
    result = await asyncio.to_thread(
        agent_service.chat, request.message, request.context
    )
    return result


@router.get("/test")
async def test_llm(user: str = Depends(get_current_user)):
    """测试 LLM 连接是否正常。"""
    if not settings.llm_api_key:
        return {"success": False, "message": "LLM API Key 未配置，请在设置页面填写"}
    try:
        import httpx
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=httpx.Timeout(15, connect=5)
        )
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": "回复 OK"}],
            max_tokens=10,
            temperature=0
        )
        reply = response.choices[0].message.content.strip()
        return {"success": True, "message": f"✅ LLM 连接正常，模型：{settings.llm_model}，响应：{reply}"}
    except Exception as e:
        err = str(e)
        if "authentication" in err.lower() or "api_key" in err.lower() or "401" in err:
            return {"success": False, "message": "❌ API Key 错误，请检查 API Key 是否正确"}
        return {"success": False, "message": f"❌ 连接失败：{err[:200]}"}


@router.get("/progress")
async def get_progress():
    def generate():
        import time
        last_msg = ""
        last_count = -1
        
        while True:
            current_status = global_search_progress["status"]
            current_msg = global_search_progress["message"]
            current_count = global_search_progress["found_count"]
            
            if current_status != "idle" or last_msg != current_msg or last_count != current_count:
                yield f"data: {json.dumps({'status': current_status, 'message': current_msg, 'found_count': current_count})}\n\n"
                last_msg = current_msg
                last_count = current_count
            
            if current_status == "idle" and last_msg != "":
                yield f"data: {json.dumps({'status': 'idle', 'message': '', 'found_count': 0})}\n\n"
                break
            
            time.sleep(0.5)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )