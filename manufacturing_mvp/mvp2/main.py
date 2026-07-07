import asyncio
from agentscope.message import Msg, TextBlock
from .agents import (
    create_defect_accept_agent,
    create_data_retrieval_agent,
    create_root_cause_agent,
    create_doc_generation_agent
)
from configs.model_config import get_model

async def run_quality_analysis_demo():
    model = get_model()
    
    accept_agent = create_defect_accept_agent(model)
    retrieval_agent = create_data_retrieval_agent(model)
    analysis_agent = create_root_cause_agent(model)
    doc_agent = create_doc_generation_agent(model)
    
    user_input = "外观划痕，批次号B2026070601，B车间-1号工位，严重程度高"
    
    print("=" * 80)
    print("MVP2: 质检缺陷根因追溯Agent")
    print("=" * 80)
    print(f"缺陷上报: {user_input}")
    print("-" * 80)
    
    msg = Msg(name="user", content=[TextBlock(type="text", text=user_input)], role="user")
    
    print("[缺陷受理Agent] 处理中...")
    accept_result = await accept_agent.reply(msg)
    print(f"[缺陷受理Agent] 结果: {accept_result.content}")
    print("-" * 80)
    
    retrieval_msg = Msg(name="user", content=[TextBlock(type="text", text=f"缺陷报告信息：{accept_result.content}")], role="user")
    print("[数据检索Agent] 处理中...")
    retrieval_result = await retrieval_agent.reply(retrieval_msg)
    print(f"[数据检索Agent] 结果: {retrieval_result.content}")
    print("-" * 80)
    
    analysis_msg = Msg(name="user", content=[TextBlock(type="text", text=f"数据检索结果：{retrieval_result.content}")], role="user")
    print("[根因分析Agent] 处理中...")
    analysis_result = await analysis_agent.reply(analysis_msg)
    print(f"[根因分析Agent] 结果: {analysis_result.content}")
    print("-" * 80)
    
    doc_msg = Msg(name="user", content=[TextBlock(type="text", text=f"根因分析结果：{analysis_result.content}")], role="user")
    print("[单据生成Agent] 处理中...")
    doc_result = await doc_agent.reply(doc_msg)
    print(f"[单据生成Agent] 结果: {doc_result.content}")
    
    print("-" * 80)
    print("流程执行完成")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_quality_analysis_demo())