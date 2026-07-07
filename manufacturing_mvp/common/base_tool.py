import logging
from datetime import datetime
from agentscope.tool import ToolBase, ToolChunk, ToolResponse
from agentscope.message import TextBlock
from agentscope.permission import PermissionContext, PermissionDecision, PermissionBehavior
from agentscope.tool._response import ToolResultState

logger = logging.getLogger(__name__)

class BaseTool(ToolBase):
    is_concurrency_safe: bool = True
    is_read_only: bool = False
    
    async def check_permissions(
        self,
        tool_input: dict,
        context: PermissionContext,
    ) -> PermissionDecision:
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="允许执行")
    
    async def __call__(self, **kwargs) -> ToolChunk:
        start_time = datetime.now()
        logger.info(f"[工具调用开始] {self.name} | 参数: {kwargs}")
        
        try:
            result = await self._call(**kwargs)
            
            duration = (datetime.now() - start_time).total_seconds()
            if isinstance(result, ToolResponse):
                status = result.state.value if hasattr(result.state, 'value') else str(result.state)
                logger.info(f"[工具调用成功] {self.name} | 耗时: {duration:.2f}s | 状态: {status}")
                return ToolChunk(content=result.content, state=result.state, is_last=True)
            elif isinstance(result, list):
                logger.info(f"[工具调用成功] {self.name} | 耗时: {duration:.2f}s | 返回 {len(result)} 条内容")
                return ToolChunk(content=result, state=ToolResultState.SUCCESS, is_last=True)
            else:
                logger.info(f"[工具调用成功] {self.name} | 耗时: {duration:.2f}s")
                return ToolChunk(content=[TextBlock(type="text", text=str(result))], state=ToolResultState.SUCCESS, is_last=True)
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"[工具调用失败] {self.name} | 耗时: {duration:.2f}s | 错误: {str(e)}")
            raise
    
    async def _call(self, **kwargs) -> ToolResponse:
        return ToolResponse(content=[TextBlock(type="text", text="Not implemented")])
