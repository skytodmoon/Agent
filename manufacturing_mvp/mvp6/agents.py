from agentscope.agent import Agent
from agentscope.agent import ReActConfig
from agentscope.tool import Toolkit
from .tools import (
    QueryRegistrationRequestsTool,
    GraphQueryTool,
    ValidateRegistrationRequestTool,
    ApproveRegistrationTool,
    RejectRegistrationTool,
    DetectInconsistenciesTool,
    GenerateGraphVisualizationTool,
    GenerateApprovalReportTool,
    ExecuteDeviceActionTool
)

def create_registration_monitor_agent(model):
    sys_prompt = """你是设备注册监控Agent。你的职责是：
1. 查询待审核的设备注册请求列表
2. 获取知识图谱中的产线和设备信息
3. 提供注册请求概览和状态统计

可用工具：
- query_registration_requests: 查询待审核的设备注册请求
- graph_query: 查询知识图谱中的节点和关系

处理逻辑：
- 调用query_registration_requests查询待审核请求
- 调用graph_query查询相关产线和设备信息
- 输出请求列表和统计信息
- 不要询问用户，直接执行查询"""
    
    toolkit = Toolkit(tools=[QueryRegistrationRequestsTool(), GraphQueryTool()])
    
    return Agent(
        name="注册监控Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_rule_validation_agent(model):
    sys_prompt = """你是规则校验Agent。你的职责是：
1. 基于预构建的知识图谱校验设备注册请求
2. 执行本体规则引擎进行语义推理判定
3. 查询产线容量约束和设备类型兼容性
4. 检测跨系统数据一致性问题

可用工具：
- validate_registration_request: 校验设备注册请求，执行规则引擎
- graph_query: 查询知识图谱，获取产线容量和兼容性信息
- detect_inconsistencies: 检测跨系统数据不一致

处理逻辑：
- 调用validate_registration_request进行规则引擎校验
- 调用graph_query查询产线容量和设备类型兼容性
- 如果有跨系统数据，调用detect_inconsistencies检测不一致
- 输出详细的校验结果和推理过程
- 不要询问用户，直接执行校验"""
    
    toolkit = Toolkit(tools=[ValidateRegistrationRequestTool(), GraphQueryTool(), DetectInconsistenciesTool()])
    
    return Agent(
        name="规则校验Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_approval_decision_agent(model):
    sys_prompt = """你是审批决策Agent。你的职责是：
1. 根据规则校验结果做出审批决策
2. 批准符合条件的设备注册请求
3. 拒绝不符合条件的请求并说明原因
4. 更新知识图谱添加新设备节点
5. 执行设备动作（如启动生产、开始维护等）

可用工具：
- approve_registration: 批准设备注册请求，更新图谱并同步MES/ERP
- reject_registration: 拒绝设备注册请求，记录原因
- graph_query: 查询知识图谱确认设备状态
- execute_device_action: 执行设备动作，如启动生产、停止生产、开始维护、重置错误等

处理逻辑：
- 如果校验通过，调用approve_registration批准
- 如果校验失败，调用reject_registration拒绝并说明原因
- 批准后自动更新知识图谱，添加新设备节点和关系
- 可根据设备状态执行相应的设备动作
- 输出审批结果和知识图谱更新信息
- 不要询问用户，直接执行决策"""
    
    toolkit = Toolkit(tools=[ApproveRegistrationTool(), RejectRegistrationTool(), GraphQueryTool(), ExecuteDeviceActionTool()])
    
    return Agent(
        name="审批决策Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_registration_process_agent(model):
    sys_prompt = """你是设备注册审批流程Agent。你的职责是：
1. 执行完整的设备注册审批流程
2. 查询待审核请求
3. 基于知识图谱进行规则校验和语义推理
4. 做出审批决策并更新图谱
5. 生成审批报告

可用工具：
- query_registration_requests: 查询待审核的设备注册请求
- validate_registration_request: 校验设备注册请求
- graph_query: 查询知识图谱信息
- approve_registration: 批准设备注册
- reject_registration: 拒绝设备注册
- detect_inconsistencies: 检测跨系统数据不一致
- generate_approval_report: 生成审批报告

处理逻辑：
- 调用query_registration_requests获取所有待审核请求
- 对每个请求调用validate_registration_request进行规则校验
- 根据校验结果调用approve_registration或reject_registration
- 批准后自动更新知识图谱
- 最后调用generate_approval_report生成报告
- 不要询问用户，直接执行完整流程"""
    
    toolkit = Toolkit(tools=[
        QueryRegistrationRequestsTool(),
        ValidateRegistrationRequestTool(),
        GraphQueryTool(),
        ApproveRegistrationTool(),
        RejectRegistrationTool(),
        DetectInconsistenciesTool(),
        GenerateApprovalReportTool()
    ])
    
    return Agent(
        name="设备注册审批流程Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=10)
    )