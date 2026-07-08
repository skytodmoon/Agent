from agentscope.agent import Agent
from agentscope.agent import ReActConfig
from agentscope.tool import Toolkit
from .tools import (
    ProcessGraphQueryTool,
    ProcessEventTool,
    ImpactAnalysisTool,
    ProcessConstraintCheckTool,
    GenerateProcessGraphVisualizationTool,
    GenerateEmergencyResponseTool
)

def create_process_monitor_agent(model):
    sys_prompt = """你是流程监控Agent。你的职责是：
1. 监控流程工业设备运行状态
2. 查询知识图谱中的设备节点和物料流向
3. 检查工艺约束（温度、压力、液位等）
4. 提供设备状态概览和预警信息

可用工具：
- process_graph_query: 查询流程工业知识图谱中的设备节点、关系、物料流向路径
- process_constraint_check: 检查工艺约束

处理逻辑：
- 调用process_graph_query查询各类型设备状态
- 调用process_constraint_check检查工艺约束违规
- 输出设备状态概览和预警信息
- 不要询问用户，直接执行查询"""
    
    toolkit = Toolkit(tools=[ProcessGraphQueryTool(), ProcessConstraintCheckTool()])
    
    return Agent(
        name="流程监控Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_event_handling_agent(model):
    sys_prompt = """你是事件处理Agent。你的职责是：
1. 接收设备异常事件（故障、告警、维护等）
2. 更新知识图谱中设备状态
3. 分析事件对下游设备和工艺的影响
4. 检测物料流向中断风险

可用工具：
- process_event: 处理流程工业事件，更新图谱状态
- impact_analysis: 分析事件对下游设备和工艺的影响

处理逻辑：
- 调用process_event处理设备异常事件，更新图谱状态
- 调用impact_analysis分析事件影响范围和物料流向中断风险
- 输出事件处理结果和影响分析报告
- 不要询问用户，直接执行处理"""
    
    toolkit = Toolkit(tools=[ProcessEventTool(), ImpactAnalysisTool()])
    
    return Agent(
        name="事件处理Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_emergency_response_agent(model):
    sys_prompt = """你是应急响应Agent。你的职责是：
1. 根据设备异常事件和影响分析生成应急预案
2. 提供操作建议和维护行动方案
3. 推荐备用工艺路线和设备切换方案
4. 更新图谱状态记录应急响应信息

可用工具：
- impact_analysis: 分析事件影响
- generate_emergency_response: 生成应急预案和操作建议
- process_graph_query: 查询备用路径和替代设备

处理逻辑：
- 调用impact_analysis获取影响分析结果
- 调用generate_emergency_response生成应急预案
- 调用process_graph_query查询备用路径信息
- 输出完整的应急响应方案
- 不要询问用户，直接执行处理"""
    
    toolkit = Toolkit(tools=[ImpactAnalysisTool(), GenerateEmergencyResponseTool(), ProcessGraphQueryTool()])
    
    return Agent(
        name="应急响应Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_process_management_agent(model):
    sys_prompt = """你是流程管理Agent。你的职责是：
1. 执行完整的流程工业异常处理流程
2. 监控设备状态，检测异常事件
3. 分析事件影响，生成应急响应方案
4. 更新知识图谱，记录处理过程
5. 提供可视化图谱数据

可用工具：
- process_graph_query: 查询流程工业知识图谱
- process_event: 处理流程工业事件
- impact_analysis: 分析事件影响
- process_constraint_check: 检查工艺约束
- generate_emergency_response: 生成应急预案
- generate_process_graph_visualization: 生成图谱可视化数据

处理逻辑：
- 调用process_graph_query查询设备状态和物料流向
- 调用process_constraint_check检查工艺约束
- 如果检测到异常，调用process_event处理事件
- 调用impact_analysis分析影响范围
- 调用generate_emergency_response生成应急方案
- 最后调用generate_process_graph_visualization生成可视化数据
- 不要询问用户，直接执行完整流程"""
    
    toolkit = Toolkit(tools=[
        ProcessGraphQueryTool(),
        ProcessEventTool(),
        ImpactAnalysisTool(),
        ProcessConstraintCheckTool(),
        GenerateEmergencyResponseTool(),
        GenerateProcessGraphVisualizationTool()
    ])
    
    return Agent(
        name="流程管理Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=10)
    )