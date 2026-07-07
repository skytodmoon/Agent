from agentscope.agent import Agent, ReActConfig
from agentscope.tool import Toolkit
from .tools import (
    DefectAcceptTool,
    ProcessDataQueryTool,
    EquipmentDataQueryTool,
    MaterialBatchQueryTool,
    RootCauseAnalysisTool,
    CreateQualityExceptionOrderTool
)

def create_defect_accept_agent(model):
    sys_prompt = """你是缺陷受理Agent。你的职责是：
1. 从输入中提取缺陷类型、批次号、工位、严重程度等信息
2. 标准化并保存缺陷报告
3. 输出完整的缺陷信息供下游Agent使用

处理流程：
- 必须从输入中提取缺陷类型（defect_type）和批次号（batch_no）
- 调用缺陷受理工具（defect_accept）保存报告
- 输出时必须包含：缺陷ID、缺陷类型、批次号、工位、严重程度
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[DefectAcceptTool()])
    
    return Agent(
        name="缺陷受理Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_data_retrieval_agent(model):
    sys_prompt = """你是数据检索Agent。你的职责是：
1. 从输入中提取批次号和工位信息
2. 使用工具查询该批次的工艺参数
3. 使用工具查询相关设备的运行数据
4. 使用工具查询该批次使用的物料批次信息

处理逻辑：
- 必须从输入中提取批次号（batch_no）和工位（location/workstation）
- 优先调用工艺参数查询工具（process_data_query）
- 然后调用物料批次查询工具（material_batch_query）
- 将获取的所有数据整理后传递给根因分析Agent
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[
        ProcessDataQueryTool(),
        EquipmentDataQueryTool(),
        MaterialBatchQueryTool()
    ])
    
    return Agent(
        name="数据检索Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_root_cause_agent(model):
    sys_prompt = """你是根因分析Agent。你的职责是：
1. 从输入中提取缺陷类型、批次号等信息
2. 调用根因分析工具匹配质量知识库
3. 输出可能的根因列表和整改建议
4. 将分析结果传递给单据生成Agent

处理流程：
- 必须从输入中提取缺陷类型（defect_type）
- 调用根因分析工具（root_cause_analysis）进行分析
- 输出根因列表和整改建议
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[RootCauseAnalysisTool()])
    
    return Agent(
        name="根因分析Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_doc_generation_agent(model):
    sys_prompt = """你是单据生成Agent。你的职责是：
1. 从输入中提取缺陷ID、批次号、缺陷类型、根因分析结果
2. 生成质量异常处理单
3. 推送给相关责任部门

处理流程：
- 必须从输入中提取缺陷ID（defect_id）、批次号（batch_no）、缺陷类型（defect_type）
- 调用创建质量异常单工具（create_quality_exception_order）
- 责任部门根据缺陷类型自动分配（外观缺陷→工艺部，尺寸问题→设备部）
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[CreateQualityExceptionOrderTool()])
    
    return Agent(
        name="单据生成Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )
