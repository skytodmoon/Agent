import asyncio
from agentscope.message import Msg, TextBlock
from .agents import (
    create_reception_agent,
    create_diagnosis_agent,
    create_workflow_agent
)
from configs.model_config import get_model

async def run_fault_diagnosis_demo():
    model = get_model()
    
    reception_agent = create_reception_agent(model)
    diagnosis_agent = create_diagnosis_agent(model)
    workflow_agent = create_workflow_agent(model)
    
    user_input = "CNC-001设备主轴异响，A车间-1号工位"
    
    print("=" * 80)
    print("MVP1: 核心设备故障诊断与工单闭环助手")
    print("=" * 80)
    print(f"用户报修: {user_input}")
    print("-" * 80)
    
    msg = Msg(name="user", content=[TextBlock(type="text", text=user_input)], role="user")
    
    print("[故障受理Agent] 处理中...")
    reception_result = await reception_agent.reply(msg)
    print(f"[故障受理Agent] 结果: {reception_result.content}")
    print("-" * 80)
    
    diagnosis_msg = Msg(name="user", content=[TextBlock(type="text", text=f"故障报告信息：{reception_result.content}")], role="user")
    print("[故障诊断Agent] 处理中...")
    diagnosis_result = await diagnosis_agent.reply(diagnosis_msg)
    print(f"[故障诊断Agent] 结果: {diagnosis_result.content}")
    print("-" * 80)
    
    workflow_msg = Msg(name="user", content=[TextBlock(type="text", text=f"诊断结果：{diagnosis_result.content}")], role="user")
    print("[工单流转Agent] 处理中...")
    workflow_result = await workflow_agent.reply(workflow_msg)
    print(f"[工单流转Agent] 结果: {workflow_result.content}")
    
    print("-" * 80)
    print("流程执行完成")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_fault_diagnosis_demo())