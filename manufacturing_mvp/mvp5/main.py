import asyncio
from agentscope.message import Msg, TextBlock
from .agents import (
    create_inspection_accept_agent,
    create_classification_agent,
    create_tracking_agent,
    create_report_agent
)
from configs.model_config import get_model

async def run_safety_inspection_demo():
    model = get_model()
    
    accept_agent = create_inspection_accept_agent(model)
    classification_agent = create_classification_agent(model)
    tracking_agent = create_tracking_agent(model)
    report_agent = create_report_agent(model)
    
    user_input = "电气隐患，A车间配电箱未上锁，存在安全风险，报告人：王安全"
    
    print("=" * 80)
    print("MVP5: 车间安全巡检与隐患整改闭环Agent")
    print("=" * 80)
    print(f"隐患上报: {user_input}")
    print("-" * 80)
    
    msg = Msg(name="user", content=[TextBlock(type="text", text=user_input)], role="user")
    
    print("[巡检受理Agent] 处理中...")
    accept_result = await accept_agent.reply(msg)
    print(f"[巡检受理Agent] 结果: {accept_result.content}")
    print("-" * 80)
    
    classification_msg = Msg(name="user", content=[TextBlock(type="text", text=f"隐患信息：{accept_result.content}")], role="user")
    print("[分级判定Agent] 处理中...")
    classification_result = await classification_agent.reply(classification_msg)
    print(f"[分级判定Agent] 结果: {classification_result.content}")
    print("-" * 80)
    
    tracking_msg = Msg(name="user", content=[TextBlock(type="text", text=f"分类结果：{classification_result.content}")], role="user")
    print("[整改跟踪Agent] 处理中...")
    tracking_result = await tracking_agent.reply(tracking_msg)
    print(f"[整改跟踪Agent] 结果: {tracking_result.content}")
    print("-" * 80)
    
    report_msg = Msg(name="user", content=[TextBlock(type="text", text=f"整改跟踪：{tracking_result.content}")], role="user")
    print("[合规报表Agent] 处理中...")
    report_result = await report_agent.reply(report_msg)
    print(f"[合规报表Agent] 结果: {report_result.content}")
    
    print("-" * 80)
    print("流程执行完成")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_safety_inspection_demo())