from agentscope.model import OpenAIChatModel, DashScopeChatModel
from agentscope.credential import OpenAICredential, DashScopeCredential
from agentscope.message import Msg
import os
import logging
import time
from typing import Any, List, Dict

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoggingOpenAIChatModel(OpenAIChatModel):
    def __init__(self, **kwargs):
        self._model_name = kwargs.get("model", "")
        self._base_url = kwargs.get("credential", {}).base_url if hasattr(kwargs.get("credential"), "base_url") else ""
        super().__init__(**kwargs)
    
    def _log_request(self, messages: List[Msg], **kwargs):
        logger.info("=" * 80)
        logger.info(f"[LLM Request] Model: {self._model_name}")
        logger.info(f"[LLM Request] Base URL: {self._base_url}")
        logger.info(f"[LLM Request] Number of messages: {len(messages)}")
        for i, msg in enumerate(messages):
            content_preview = str(msg.content)[:200] + "..." if len(str(msg.content)) > 200 else str(msg.content)
            logger.info(f"[LLM Request] Message {i} - Role: {msg.role}, Content: {content_preview}")
        logger.info(f"[LLM Request] Additional kwargs: {kwargs}")
        logger.info("-" * 80)
    
    def _log_response(self, response, latency):
        if response is not None:
            logger.info(f"[LLM Response] Latency: {latency:.2f}s")
            logger.info(f"[LLM Response] Type: {type(response).__name__}")
            if hasattr(response, 'content'):
                content_preview = str(response.content)[:300] + "..." if len(str(response.content)) > 300 else str(response.content)
                logger.info(f"[LLM Response] Content preview: {content_preview}")
            if hasattr(response, 'usage') and response.usage is not None:
                logger.info(f"[LLM Response] Usage: {response.usage}")
        logger.info("=" * 80)
    
    def _log_error(self, error: Exception):
        logger.error("=" * 80)
        logger.error(f"[LLM Error] Type: {type(error).__name__}")
        logger.error(f"[LLM Error] Message: {str(error)}")
        logger.error(f"[LLM Error] Model: {self._model_name}")
        logger.error(f"[LLM Error] Base URL: {self._base_url}")
        logger.error("=" * 80, exc_info=True)
    
    async def reply(self, messages: List[Msg], **kwargs) -> Msg:
        self._log_request(messages, **kwargs)
        start_time = time.time()
        try:
            response = await super().reply(messages, **kwargs)
            latency = time.time() - start_time
            self._log_response(response, latency)
            return response
        except Exception as e:
            latency = time.time() - start_time
            self._log_error(e)
            logger.info(f"[LLM Error] Latency before error: {latency:.2f}s")
            raise

def get_model(model_type: str = "local"):
    if model_type == "dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if api_key:
            logger.info(f"[Model Config] Using DashScope model: qwen3.6-plus")
            credential = DashScopeCredential(api_key=api_key)
            return DashScopeChatModel(
                credential=credential,
                model="qwen3.6-plus",
            )
    elif model_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            logger.info(f"[Model Config] Using OpenAI model: gpt-4o-mini")
            credential = OpenAICredential(api_key=api_key)
            return OpenAIChatModel(
                credential=credential,
                model="gpt-4o-mini",
            )
    elif model_type == "local":
        api_key = os.getenv("LLM_LOCAL_API_KEY", "7d650bb4-00a6-4c00-a996-a39641c4215f")
        base_url = os.getenv("LLM_LOCAL_URL", "http://10.100.1.11:30978/v1")
        model_name = os.getenv("LLM_LOCAL_MODEL", "qwen3-coder")
        
        logger.info(f"[Model Config] Using Local model: {model_name}")
        logger.info(f"[Model Config] Base URL: {base_url}")
        logger.info(f"[Model Config] API Key: {api_key[:8]}***{api_key[-4:]}")
        logger.info(f"[Model Config] Logging enabled for debugging")
        
        credential = OpenAICredential(api_key=api_key, base_url=base_url)
        return LoggingOpenAIChatModel(
            credential=credential,
            model=model_name,
        )
    raise ValueError("No API key provided. Set OPENAI_API_KEY, DASHSCOPE_API_KEY or LLM_LOCAL_API_KEY environment variable.")
