import asyncio
from agentscope.message import Msg, TextBlock
from .agents import (
    create_demand_decomposition_agent,
    create_inventory_query_agent,
    create_risk_alert_agent,
    create_report_generation_agent
)
from configs.model_config import get_model

async def run_material_kit_demo():
    model = get_model()
    
    decomposition_agent = create_demand_decomposition_agent(model)
    inventory_agent = create_inventory_query_agent(model)
    risk_agent = create_risk_alert_agent(model)
    report_agent = create_report_generation_agent(model)
    
    user_input = "产品PRD-001计划生产100件"
    
    print("=" * 80)
    print("MVP3: 物料齐套核算与交期预警Agent")
    print("=" * 80)
    print(f"生产计划: {user_input}")
    print("-" * 80)
    
    msg = Msg(name="user", content=[TextBlock(type="text", text=user_input)], role="user")
    
    print("[需求拆解Agent] 处理中...")
    decomposition_result = await decomposition_agent.reply(msg)
    print(f"[需求拆解Agent] 结果: {decomposition_result.content}")
    print("-" * 80)
    
    inventory_msg = Msg(name="user", content=[TextBlock(type="text", text=f"物料需求：{decomposition_result.content}")], role="user")
    print("[库存查询Agent] 处理中...")
    inventory_result = await inventory_agent.reply(inventory_msg)
    print(f"[库存查询Agent] 结果: {inventory_result.content}")
    print("-" * 80)
    
    risk_msg = Msg(name="user", content=[TextBlock(type="text", text=f"库存状况：{inventory_result.content}")], role="user")
    print("[风险预警Agent] 处理中...")
    risk_result = await risk_agent.reply(risk_msg)
    print(f"[风险预警Agent] 结果: {risk_result.content}")
    print("-" * 80)
    
    report_msg = Msg(name="user", content=[TextBlock(type="text", text=f"风险评估：{risk_result.content}")], role="user")
    print("[报表生成Agent] 处理中...")
    report_result = await report_agent.reply(report_msg)
    print(f"[报表生成Agent] 结果: {report_result.content}")
    
    print("-" * 80)
    print("流程执行完成")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_material_kit_demo())