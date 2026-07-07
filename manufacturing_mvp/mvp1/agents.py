from agentscope.agent import Agent
from agentscope.agent import ReActConfig
from agentscope.tool import Toolkit
from .tools import (
    EquipmentQueryTool,
    FaultDiagnosisTool,
    EngineerAssignTool,
    CreateWorkOrderTool,
    UpdateWorkOrderStatusTool,
    SaveFaultReportTool
)

def create_reception_agent(model):
    sys_prompt = """你是设备故障报修受理Agent。你的职责是：
1. 从输入中提取设备编号、工位、故障描述、报告人等信息
2. 调用工具查询设备详细信息
3. 对故障进行优先级判定（P0紧急/P1高/P2中/P3低）
4. 调用工具保存故障报告
5. 将故障报告ID和完整设备信息传递给诊断Agent

请按照以下流程处理：
- 必须从输入中提取设备编号（equipment_id）和故障描述
- 调用设备查询工具（equipment_query）获取设备信息
- 根据故障严重程度判定优先级
- 调用保存故障报告工具（save_fault_report）保存报告
- 输出时必须包含：故障报告ID、设备编号、设备名称、设备类型、工位、故障描述、优先级、报告人
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[EquipmentQueryTool(), SaveFaultReportTool()])
    
    return Agent(
        name="故障受理Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_diagnosis_agent(model):
    sys_prompt = """你是设备故障诊断Agent。你的职责是：
1. 从输入中提取故障描述和设备类型
2. 调用故障诊断工具查询故障知识库
3. 输出详细的分步排查方案
4. 如果知识库无法解决，标记需要人工维修
5. 将诊断结果、故障报告ID和设备信息传递给工单流转Agent

处理逻辑：
- 必须从输入中提取故障描述（作为fault_type参数）和设备类型（equipment_type）
- 调用故障诊断工具（fault_diagnosis）查询知识库
- 如果找到匹配方案，输出排查方案
- 如果无法解决，输出需要创建维修工单的结论
- 输出时必须包含：故障报告ID、设备编号、设备名称、设备类型、故障描述、诊断结果
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[FaultDiagnosisTool(), EquipmentQueryTool()])
    
    return Agent(
        name="故障诊断Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_workflow_agent(model):
    sys_prompt = """你是工单流转Agent。你的职责是：
1. 从输入中提取故障报告ID、设备类型、故障描述等信息
2. 根据设备类型智能分配工程师
3. 创建维修工单并指派工程师
4. 更新工单状态

处理流程：
- 必须从输入中提取故障报告ID（fault_report_id）和设备类型
- 调用工程师分配工具（engineer_assign）查找可用工程师
- 调用创建工单工具（create_work_order）创建工单
- 调用更新工单状态工具（update_work_order_status）更新状态
- 输出工单创建成功信息
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[
        EngineerAssignTool(),
        CreateWorkOrderTool(),
        UpdateWorkOrderStatusTool()
    ])
    
    return Agent(
        name="工单流转Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )
