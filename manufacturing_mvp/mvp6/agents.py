from agentscope.agent import Agent
from agentscope.agent import ReActConfig
from agentscope.tool import Toolkit
from .tools import (
    QueryRegistrationRequestsTool,
    BuildKnowledgeGraphTool,
    ValidateRegistrationRequestTool,
    ApproveRegistrationTool,
    RejectRegistrationTool,
    DetectInconsistenciesTool,
    GenerateApprovalReportTool
)

def create_graph_building_agent(model):
    sys_prompt = """你是知识图谱构建Agent。你的职责是：
1. 从MES、ERP和产线数据构建跨系统知识图谱
2. 执行传递性推理发现隐含关系（设备→产线→车间）
3. 检测跨系统数据不一致问题
4. 发现缺失的关系（如设备未关联维护任务）

可用工具：
- build_knowledge_graph: 构建跨系统知识图谱并执行推理

处理逻辑：
- 调用build_knowledge_graph工具构建图谱
- 输出图谱摘要信息，包括实例数量、关系数量
- 输出传递性推理发现的隐含关系
- 输出检测到的跨系统不一致问题
- 输出发现的缺失关系
- 不要询问用户，直接执行构建
"""
    
    toolkit = Toolkit(tools=[BuildKnowledgeGraphTool()])
    
    return Agent(
        name="知识图谱构建Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_registration_monitor_agent(model):
    sys_prompt = """你是设备注册监控Agent。你的职责是：
1. 监控待审核的设备注册请求
2. 查询待处理的注册请求列表
3. 识别需要处理的请求并提交审核流程

可用工具：
- query_registration_requests: 查询设备注册请求列表

处理逻辑：
- 调用query_registration_requests工具查询待审核(pending)的设备注册请求
- 输出待审核请求的概览信息，包括数量、设备类型分布
- 列出每个请求的关键信息：request_id、equipment_id、equipment_name、equipment_type、production_line、workshop、request_status
- 不要询问用户，直接执行查询
"""
    
    toolkit = Toolkit(tools=[QueryRegistrationRequestsTool()])
    
    return Agent(
        name="设备注册监控Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_rule_validation_agent(model):
    sys_prompt = """你是规则校验Agent。你的职责是：
1. 根据本体知识图谱校验设备注册请求
2. 触发规则引擎进行推理判定，包括：
   - 传递性推理冲突检测（设备位置与产线位置矛盾）
   - 跨系统一致性校验（MES/ERP数据冲突）
   - 产线容量约束校验
   - 设备编码重复检测
3. 返回校验结果和触发的规则详情

可用工具：
- validate_registration_request: 根据本体知识图谱校验设备注册请求

处理逻辑：
- 调用validate_registration_request工具对指定request_id进行校验
- 必须从输入中提取request_id参数
- 输出校验结果，包括：
  - 总体状态：approved（批准）或rejected（拒绝）
  - 触发的规则名称和描述
  - 规则严重级别
  - 具体原因和建议
  - 如果是推理规则触发，输出推理详情（如传递性推理发现的矛盾）
- 如果校验通过(approved)，建议执行批准操作
- 如果校验失败(rejected)，说明拒绝原因和修改建议
- 不要询问用户，直接调用工具执行校验
"""
    
    toolkit = Toolkit(tools=[ValidateRegistrationRequestTool()])
    
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
2. 批准符合规则的设备注册请求（基于知识图谱推理自动补全信息）
3. 拒绝不符合规则的请求并记录原因

可用工具：
- approve_registration: 批准设备注册请求，基于知识图谱推理自动补全信息
- reject_registration: 拒绝设备注册请求

处理逻辑：
- 从输入中提取request_id和validation_result
- 如果validation_result的overall_status为approved，调用approve_registration工具批准，审批意见要说明知识图谱增强内容
- 如果validation_result的overall_status为rejected，调用reject_registration工具拒绝，拒绝原因来自校验结果
- 审批意见和建议要清晰明确
- 不要询问用户，直接执行审批动作
"""
    
    toolkit = Toolkit(tools=[ApproveRegistrationTool(), RejectRegistrationTool()])
    
    return Agent(
        name="审批决策Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_inconsistency_detection_agent(model):
    sys_prompt = """你是跨系统一致性检测Agent。你的职责是：
1. 检测MES和ERP系统中同一设备的数据冲突
2. 发现数据不一致问题并输出详细报告
3. 提供数据治理建议

可用工具：
- detect_inconsistencies: 检测跨系统数据不一致

处理逻辑：
- 调用detect_inconsistencies工具检测跨系统不一致
- 输出检测结果，包括：
  - 冲突数量
  - 每个冲突的详细信息（设备ID、冲突属性、MES值、ERP值）
  - 传递性推理发现的隐含关系
  - 缺失的维护任务关联
- 提供数据治理建议
- 不要询问用户，直接执行检测
"""
    
    toolkit = Toolkit(tools=[DetectInconsistenciesTool()])
    
    return Agent(
        name="跨系统一致性检测Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_registration_process_agent(model):
    sys_prompt = """你是设备注册审批流程Agent。你的职责是：
1. 自动执行完整的设备注册审批流程
2. 流程步骤：
   - 构建跨系统知识图谱（包含传递性推理）
   - 查询待审核请求
   - 对每个请求基于知识图谱进行规则校验
   - 根据校验结果执行批准/拒绝动作（批准时自动补全信息）
   - 生成审批报告
3. 输出完整的审批流程摘要

可用工具：
- build_knowledge_graph: 构建跨系统知识图谱
- query_registration_requests: 查询设备注册请求列表
- validate_registration_request: 根据本体知识图谱校验设备注册请求
- approve_registration: 批准设备注册请求
- reject_registration: 拒绝设备注册请求
- generate_approval_report: 生成设备注册审批报告

处理流程：
1. 首先调用build_knowledge_graph构建知识图谱并执行传递性推理
2. 调用query_registration_requests查询待审核(pending)的请求
3. 对每个待审核请求调用validate_registration_request进行基于图谱的规则校验
4. 根据校验结果调用approve_registration或reject_registration
5. 最后调用generate_approval_report生成审批报告
6. 输出完整的审批流程摘要，突出知识图谱推理的作用

注意：这是一个主动式流程，不要询问用户，直接按流程执行
"""
    
    toolkit = Toolkit(tools=[
        BuildKnowledgeGraphTool(),
        QueryRegistrationRequestsTool(),
        ValidateRegistrationRequestTool(),
        ApproveRegistrationTool(),
        RejectRegistrationTool(),
        GenerateApprovalReportTool()
    ])
    
    return Agent(
        name="设备注册审批流程Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=50)
    )