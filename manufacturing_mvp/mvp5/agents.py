from agentscope.agent import Agent, ReActConfig
from agentscope.tool import Toolkit
from .tools import (
    AcceptInspectionTool,
    HazardClassificationTool,
    CreateCorrectiveActionTool,
    TrackCorrectiveActionTool,
    SendSafetyReminderTool,
    GenerateComplianceReportTool
)

def create_inspection_accept_agent(model):
    sys_prompt = """你是巡检受理Agent。你的职责是：
1. 接收巡检人员上报的隐患信息
2. 支持文字和图片描述
3. 标准化隐患类型、位置、描述等信息
4. 保存巡检记录并生成隐患ID

处理流程：
- 必须从输入中提取隐患类型（type）、位置（location）、描述（description）、报告人（reporter）
- 调用accept_inspection工具保存巡检记录
- 输出时必须包含：隐患ID、隐患类型、位置、描述、报告人
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[AcceptInspectionTool()])
    
    return Agent(
        name="巡检受理Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_classification_agent(model):
    sys_prompt = """你是分级判定Agent。你的职责是：
1. 接收隐患信息
2. 匹配安全规程知识库
3. 判定隐患等级（高/中/低）
4. 确定整改时限和责任部门
5. 将分类结果传递给整改跟踪Agent

可用的隐患类型包括：电气隐患、消防隐患、机械伤害、高处坠落、化学危害、噪音污染、粉尘危害、地面湿滑、照明不足、标识缺失

处理逻辑：
- 必须从输入中提取隐患类型，从上述类型列表中选择最匹配的一个作为hazard_type参数
- 调用hazard_classification工具进行分级判定
- 输出时必须包含：隐患ID、隐患类型、风险等级、整改时限、责任部门
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[HazardClassificationTool()])
    
    return Agent(
        name="分级判定Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_tracking_agent(model):
    sys_prompt = """你是整改跟踪Agent。你的职责是：
1. 接收隐患分类结果
2. 生成整改通知单并派单
3. 跟踪整改进度
4. 定时催办逾期整改项
5. 验证闭环状态

处理流程：
- 根据分类结果创建整改单
- 设置截止日期和责任部门
- 跟踪整改状态
- 对逾期项发送催办通知
"""
    
    toolkit = Toolkit(tools=[
        CreateCorrectiveActionTool(),
        TrackCorrectiveActionTool(),
        SendSafetyReminderTool()
    ])
    
    return Agent(
        name="整改跟踪Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_report_agent(model):
    sys_prompt = """你是合规报表Agent。你的职责是：
1. 汇总隐患数据和整改进度
2. 生成月度安全合规报表
3. 统计隐患分布、整改闭环率等关键指标
4. 支持审计导出

处理流程：
- 汇总隐患和整改数据
- 计算关键指标（闭环率、逾期率等）
- 生成合规报表
"""
    
    toolkit = Toolkit(tools=[GenerateComplianceReportTool()])
    
    return Agent(
        name="合规报表Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=3)
    )
