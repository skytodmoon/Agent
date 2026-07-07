import asyncio
from agentscope.message import Msg, TextBlock
from .agents import (
    create_exception_detection_agent,
    create_scheduling_agent,
    create_approval_agent,
    create_execution_agent
)
from configs.model_config import get_model

async def run_reschedule_demo():
    model = get_model()
    
    detection_agent = create_exception_detection_agent(model)
    scheduling_agent = create_scheduling_agent(model)
    approval_agent = create_approval_agent(model)
    execution_agent = create_execution_agent(model)
    
    user_input = "LINE-A产线CNC-001设备故障，主轴异响，受影响工单PO-001，严重程度高"
    
    print("=" * 80)
    print("MVP4: 产线异常应急排程调度Agent")
    print("=" * 80)
    print(f"异常上报: {user_input}")
    print("-" * 80)
    
    msg = Msg(name="user", content=[TextBlock(type="text", text=user_input)], role="user")
    
    print("[异常感知Agent] 处理中...")
    detection_result = await detection_agent.reply(msg)
    print(f"[异常感知Agent] 结果: {detection_result.content}")
    print("-" * 80)
    
    scheduling_msg = Msg(name="user", content=[TextBlock(type="text", text=f"影响评估：{detection_result.content}")], role="user")
    print("[排程计算Agent] 处理中...")
    scheduling_result = await scheduling_agent.reply(scheduling_msg)
    print(f"[排程计算Agent] 结果: {scheduling_result.content}")
    print("-" * 80)
    
    approval_msg = Msg(name="user", content=[TextBlock(type="text", text=f"排程方案：{scheduling_result.content}")], role="user")
    print("[人工审批Agent] 处理中...")
    approval_result = await approval_agent.reply(approval_msg)
    print(f"[人工审批Agent] 结果: {approval_result.content}")
    print("-" * 80)
    
    execution_msg = Msg(name="user", content=[TextBlock(type="text", text=f"审批结果：{approval_result.content}")], role="user")
    print("[执行同步Agent] 处理中...")
    execution_result = await execution_agent.reply(execution_msg)
    print(f"[执行同步Agent] 结果: {execution_result.content}")
    
    print("-" * 80)
    print("流程执行完成")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_reschedule_demo())