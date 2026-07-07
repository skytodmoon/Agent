from typing import AsyncGenerator, Callable, Dict, Any
from agentscope.tool import ToolResponse

async def logging_middleware(kwargs: Dict[str, Any], next_handler: Callable) -> AsyncGenerator[ToolResponse, None]:
    tool_call = kwargs.get("tool_call", {})
    print(f"[Middleware] Calling tool: {tool_call.get('name')}")
    print(f"[Middleware] Input: {tool_call.get('input')}")
    
    async for response in await next_handler(**kwargs):
        print(f"[Middleware] Response: {response.content}")
        yield response

    print(f"[Middleware] Tool {tool_call.get('name')} completed")

async def permission_middleware(kwargs: Dict[str, Any], next_handler: Callable) -> AsyncGenerator[ToolResponse, None]:
    tool_call = kwargs.get("tool_call", {})
    tool_name = tool_call.get("name", "")
    
    high_risk_tools = ["create_work_order", "modify_priority", "assign_engineer"]
    
    if tool_name in high_risk_tools:
        print(f"[Permission] High-risk tool detected: {tool_name}")
        print(f"[Permission] Requiring supervisor approval...")
    
    async for response in await next_handler(**kwargs):
        yield response

async def audit_middleware(kwargs: Dict[str, Any], next_handler: Callable) -> AsyncGenerator[ToolResponse, None]:
    tool_call = kwargs.get("tool_call", {})
    print(f"[Audit] Recording tool call: {tool_call.get('name')}")
    
    async for response in await next_handler(**kwargs):
        yield response
