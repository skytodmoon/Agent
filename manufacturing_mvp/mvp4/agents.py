from agentscope.agent import Agent, ReActConfig
from agentscope.tool import Toolkit
from .tools import (
    ReportExceptionTool,
    ProductionOrderQueryTool,
    LineCapacityQueryTool,
    GenerateSchedulingPlanTool,
    ApprovalTool,
    SyncToMesTool
)

def create_exception_detection_agent(model):
    sys_prompt = """你是异常感知Agent。你的职责是：
1. 接收异常上报事件
2. 评估异常影响的工单、设备、人员范围
3. 查询相关生产工单和资源分配情况
4. 将影响评估结果传递给排程计算Agent

处理流程：
- 接收异常类型和描述
- 查询受影响产线的生产工单
- 查询设备状态和资源分配
- 评估异常严重程度和影响范围
"""
    
    toolkit = Toolkit(tools=[
        ReportExceptionTool(),
        ProductionOrderQueryTool(),
        LineCapacityQueryTool()
    ])
    
    return Agent(
        name="异常感知Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_scheduling_agent(model):
    sys_prompt = """你是排程计算Agent。你的职责是：
1. 接收异常影响评估结果
2. 基于排程规则与产能约束，生成多套优先级调整方案
3. 评估每套方案的影响（交期延误、成本增加等）
4. 将方案列表传递给人工审批Agent

处理逻辑：
- 根据异常类型生成排程调整方案
- 考虑交期优先级、产能约束、资源可用性
- 生成至少2套方案供选择
"""
    
    toolkit = Toolkit(tools=[
        LineCapacityQueryTool(),
        GenerateSchedulingPlanTool()
    ])
    
    return Agent(
        name="排程计算Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_approval_agent(model):
    sys_prompt = """你是人工审批Agent。你的职责是：
1. 接收排程调整方案列表
2. 重大排程调整触发计划主管确认
3. 支持人在回路干预，选择最优方案
4. 将审批结果传递给执行同步Agent

处理流程：
- 展示多套方案及其影响评估
- 等待人工选择或自动选择推荐方案
- 记录审批意见
"""
    
    toolkit = Toolkit(tools=[ApprovalTool()])
    
    return Agent(
        name="人工审批Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=3)
    )

def create_execution_agent(model):
    sys_prompt = """你是执行同步Agent。你的职责是：
1. 接收审批通过的排程调整方案
2. 同步调整结果至MES系统
3. 通知生产、物料、质量部门
4. 更新工单状态和资源分配

处理流程：
- 将方案变更同步至MES系统
- 通知相关部门
- 更新异常状态为已处理
"""
    
    toolkit = Toolkit(tools=[SyncToMesTool()])
    
    return Agent(
        name="执行同步Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=3)
    )
