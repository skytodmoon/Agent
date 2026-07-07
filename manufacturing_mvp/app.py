import sys
import os
import json
import logging
from datetime import datetime
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import asyncio
from agentscope.message import Msg, TextBlock
from agentscope.event import (
    AgentEvent,
    ThinkingBlockStartEvent,
    ThinkingBlockDeltaEvent,
    ThinkingBlockEndEvent,
    ToolCallStartEvent,
    ToolCallEndEvent,
    ToolResultStartEvent,
    ToolResultTextDeltaEvent,
    ToolResultEndEvent,
    TextBlockStartEvent,
    TextBlockDeltaEvent,
    TextBlockEndEvent,
)

from configs.model_config import get_model

class StreamlitLogHandler(logging.Handler):
    def __init__(self, buffer):
        super().__init__()
        self.buffer = buffer
    
    def emit(self, record):
        msg = self.format(record)
        self.buffer.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": record.levelname,
            "message": msg
        })

log_buffer = []
streamlit_handler = StreamlitLogHandler(log_buffer)
streamlit_handler.setLevel(logging.INFO)
streamlit_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))

root_logger = logging.getLogger()
root_logger.addHandler(streamlit_handler)
root_logger.setLevel(logging.INFO)

st.set_page_config(
    page_title="制造业Agent Demo平台",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("🏭 制造业Agent Demo平台")
st.sidebar.markdown("基于AgentScope 2.0构建")

mvp_options = {
    "mvp1": "MVP1: 核心设备故障诊断与工单闭环助手",
    "mvp2": "MVP2: 质检缺陷根因追溯Agent",
    "mvp3": "MVP3: 物料齐套核算与交期预警Agent",
    "mvp4": "MVP4: 产线异常应急排程调度Agent",
    "mvp5": "MVP5: 车间安全巡检与隐患整改闭环Agent",
    "mvp6": "MVP6: 新设备MES上线准入自动审核",
}

selected_mvp = st.sidebar.selectbox("选择MVP场景", list(mvp_options.keys()), format_func=lambda x: mvp_options[x])

model_type = st.sidebar.selectbox("选择模型", ["local", "openai", "dashscope"], index=0)

st.sidebar.divider()
st.sidebar.markdown("### 使用说明")
st.sidebar.markdown("1. 选择要演示的MVP场景")
st.sidebar.markdown("2. 在输入框中填写相关信息")
st.sidebar.markdown("3. 点击开始按钮启动流程")
st.sidebar.markdown("4. 实时查看Agent执行过程")

st.title(mvp_options[selected_mvp])

input_configs = {
    "mvp1": [
        {"key": "equipment_id", "label": "设备编号", "default": "CNC-001", "help": "例如：CNC-001"},
        {"key": "fault_description", "label": "故障描述", "default": "主轴异响", "help": "例如：主轴异响"},
        {"key": "location", "label": "工位", "default": "A车间-1号工位", "help": "例如：A车间-1号工位"},
        {"key": "reporter", "label": "报告人", "default": "张三", "help": "报告人姓名"},
    ],
    "mvp2": [
        {"key": "defect_type", "label": "缺陷类型", "default": "外观划痕", "help": "例如：外观划痕、尺寸超差"},
        {"key": "batch_no", "label": "批次号", "default": "B2026070601", "help": "例如：B2026070601"},
        {"key": "location", "label": "工位", "default": "B车间-1号工位", "help": "例如：B车间-1号工位"},
        {"key": "severity", "label": "严重程度", "default": "高", "help": "高/中/低"},
    ],
    "mvp3": [
        {"key": "product_id", "label": "产品ID", "default": "PRD-001", "help": "例如：PRD-001"},
        {"key": "production_qty", "label": "计划生产数量", "default": "100", "help": "例如：100"},
    ],
    "mvp4": [
        {"key": "line_id", "label": "产线编号", "default": "LINE-A", "help": "例如：LINE-A"},
        {"key": "equipment_id", "label": "设备编号", "default": "CNC-001", "help": "例如：CNC-001"},
        {"key": "fault_description", "label": "异常描述", "default": "主轴异响", "help": "例如：主轴异响"},
        {"key": "affected_order", "label": "受影响工单", "default": "PO-001", "help": "例如：PO-001"},
        {"key": "severity", "label": "严重程度", "default": "高", "help": "高/中/低"},
    ],
    "mvp5": [
        {"key": "hazard_type", "label": "隐患类型", "default": "电气隐患", "help": "例如：电气隐患、消防安全"},
        {"key": "location", "label": "位置", "default": "A车间", "help": "例如：A车间"},
        {"key": "description", "label": "隐患描述", "default": "配电箱未上锁，存在安全风险", "help": "详细描述隐患情况"},
        {"key": "reporter", "label": "报告人", "default": "王安全", "help": "报告人姓名"},
    ],
    "mvp6": [
        {"key": "request_id", "label": "注册请求ID", "default": "REQ-001", "help": "例如：REQ-001"},
        {"key": "auto_process", "label": "自动处理所有请求", "default": "yes", "help": "yes/no（选择yes将自动处理所有待审核请求）"},
    ],
}

agent_flow_configs = {
    "mvp1": {
        "agents": [
            {"name": "故障受理Agent", "icon": "📝", "color": "#3B82F6"},
            {"name": "故障诊断Agent", "icon": "🔍", "color": "#10B981"},
            {"name": "工单流转Agent", "icon": "📋", "color": "#F59E0B"},
        ],
        "description": "解决设备故障排查靠经验、报修流程繁琐的痛点。一线员工上报故障后，Agent自动匹配知识库输出排查方案，无法解决则生成维修工单并智能派单。",
    },
    "mvp2": {
        "agents": [
            {"name": "缺陷受理Agent", "icon": "📝", "color": "#3B82F6"},
            {"name": "数据检索Agent", "icon": "🔍", "color": "#10B981"},
            {"name": "根因分析Agent", "icon": "🧠", "color": "#8B5CF6"},
            {"name": "单据生成Agent", "icon": "📄", "color": "#F59E0B"},
        ],
        "description": "解决质检缺陷根因定位耗时的痛点。录入缺陷信息后，自动拉取工艺、设备、物料数据进行交叉分析，快速定位根因并生成整改建议。",
    },
    "mvp3": {
        "agents": [
            {"name": "需求拆解Agent", "icon": "📊", "color": "#3B82F6"},
            {"name": "库存查询Agent", "icon": "🔍", "color": "#10B981"},
            {"name": "风险预警Agent", "icon": "⚠️", "color": "#EF4444"},
            {"name": "报表生成Agent", "icon": "📈", "color": "#F59E0B"},
        ],
        "description": "解决物料齐套核算效率低、缺料预警不及时的痛点。输入生产计划后自动拆解BOM，查询库存和在途数量，识别缺料风险并推送预警。",
    },
    "mvp4": {
        "agents": [
            {"name": "异常感知Agent", "icon": "🛡️", "color": "#EF4444"},
            {"name": "排程计算Agent", "icon": "🔢", "color": "#3B82F6"},
            {"name": "人工审批Agent", "icon": "✅", "color": "#10B981"},
            {"name": "执行同步Agent", "icon": "🚀", "color": "#F59E0B"},
        ],
        "description": "解决产线异常应急排程慢的痛点。接收异常事件后快速评估影响范围，生成多套排程调整方案，支持人工审批后同步执行。",
    },
    "mvp5": {
        "agents": [
            {"name": "巡检受理Agent", "icon": "📝", "color": "#3B82F6"},
            {"name": "分级判定Agent", "icon": "🏷️", "color": "#EF4444"},
            {"name": "整改跟踪Agent", "icon": "🔄", "color": "#10B981"},
            {"name": "合规报表Agent", "icon": "📋", "color": "#F59E0B"},
        ],
        "description": "解决安全巡检记录分散、隐患整改跟踪难的痛点。接收巡检记录后自动判定隐患等级，生成整改通知单并跟踪闭环状态。",
    },
    "mvp6": {
        "agents": [
            {"name": "注册监控Agent", "icon": "👀", "color": "#3B82F6"},
            {"name": "规则校验Agent", "icon": "✅", "color": "#10B981"},
            {"name": "审批决策Agent", "icon": "🔍", "color": "#EF4444"},
            {"name": "执行同步Agent", "icon": "🚀", "color": "#F59E0B"},
        ],
        "description": "解决新设备上线流程繁琐、数据标准不统一的痛点。基于本体规则引擎自动校验设备注册信息，触发规则判定后自动审批，批准的设备同步至MES和ERP系统。",
    },
}

async def run_agent_stream(agent, input_msg, status_container, agent_name, agent_info):
    thinking_text = ""
    tool_call_info = {}
    tool_result_text = ""
    final_response = ""
    step_count = 0
    
    async for event in agent.reply_stream(input_msg):
        step_count += 1
        
        if isinstance(event, ThinkingBlockStartEvent):
            with status_container:
                st.info(f"🧠 {agent_info['icon']} 思考中...")
        elif isinstance(event, ThinkingBlockDeltaEvent):
            thinking_text += event.delta
        elif isinstance(event, ThinkingBlockEndEvent):
            with status_container:
                st.code(thinking_text, language="text")
                st.session_state.execution_history.append({
                    "step": step_count,
                    "agent": agent_name,
                    "action": "思考",
                    "details": thinking_text[:100] + "..." if len(thinking_text) > 100 else thinking_text,
                    "status": "success"
                })
                thinking_text = ""
        elif isinstance(event, ToolCallStartEvent):
            tool_call_info = {
                "name": event.tool_call_name,
                "tool_call_id": event.tool_call_id
            }
            with status_container:
                st.warning(f"🛠️ 调用工具: {event.tool_call_name}")
                st.info(f"工具调用ID: {event.tool_call_id}")
        elif isinstance(event, ToolCallEndEvent):
            with status_container:
                st.session_state.execution_history.append({
                    "step": step_count,
                    "agent": agent_name,
                    "action": "工具调用",
                    "details": tool_call_info.get("name", ""),
                    "status": "success"
                })
        elif isinstance(event, ToolResultStartEvent):
            with status_container:
                st.success(f"📊 工具返回: {event.tool_call_name}")
        elif isinstance(event, ToolResultTextDeltaEvent):
            tool_result_text += event.delta
        elif isinstance(event, ToolResultEndEvent):
            with status_container:
                if tool_result_text:
                    st.code(tool_result_text, language="json")
                st.session_state.execution_history.append({
                    "step": step_count,
                    "agent": agent_name,
                    "action": "工具结果",
                    "details": tool_result_text[:100] + "..." if len(tool_result_text) > 100 else tool_result_text,
                    "status": "success"
                })
                tool_result_text = ""
        elif isinstance(event, TextBlockStartEvent):
            pass
        elif isinstance(event, TextBlockDeltaEvent):
            final_response += event.delta
        elif isinstance(event, TextBlockEndEvent):
            pass
    
    return final_response

async def run_mvp1():
    from mvp1.agents import create_reception_agent, create_diagnosis_agent, create_workflow_agent
    
    model = get_model(model_type)
    reception_agent = create_reception_agent(model)
    diagnosis_agent = create_diagnosis_agent(model)
    workflow_agent = create_workflow_agent(model)
    
    user_input = f"{st.session_state.equipment_id}设备{st.session_state.fault_description}，{st.session_state.location}，报告人：{st.session_state.reporter}"
    
    agents = [
        ("故障受理Agent", reception_agent, agent_flow_configs["mvp1"]["agents"][0]),
        ("故障诊断Agent", diagnosis_agent, agent_flow_configs["mvp1"]["agents"][1]),
        ("工单流转Agent", workflow_agent, agent_flow_configs["mvp1"]["agents"][2]),
    ]
    
    results = []
    prev_result = user_input
    
    for agent_name, agent, agent_info in agents:
        with st.status(f"🔄 {agent_info['icon']} {agent_name} 正在处理...", expanded=True) as status_container:
            st.markdown(f"**输入**: {prev_result}")
            msg = Msg(name="user", content=[TextBlock(type="text", text=str(prev_result))], role="user")
            result = await run_agent_stream(agent, msg, status_container, agent_name, agent_info)
            results.append((agent_name, result))
            prev_result = result
            status_container.update(label=f"✅ {agent_info['icon']} {agent_name} 处理完成", state="complete")
    
    return results

async def run_mvp2():
    from mvp2.agents import create_defect_accept_agent, create_data_retrieval_agent, create_root_cause_agent, create_doc_generation_agent
    
    model = get_model(model_type)
    accept_agent = create_defect_accept_agent(model)
    retrieval_agent = create_data_retrieval_agent(model)
    analysis_agent = create_root_cause_agent(model)
    doc_agent = create_doc_generation_agent(model)
    
    user_input = f"{st.session_state.defect_type}，批次号{st.session_state.batch_no}，{st.session_state.location}，严重程度{st.session_state.severity}"
    
    agents = [
        ("缺陷受理Agent", accept_agent, agent_flow_configs["mvp2"]["agents"][0]),
        ("数据检索Agent", retrieval_agent, agent_flow_configs["mvp2"]["agents"][1]),
        ("根因分析Agent", analysis_agent, agent_flow_configs["mvp2"]["agents"][2]),
        ("单据生成Agent", doc_agent, agent_flow_configs["mvp2"]["agents"][3]),
    ]
    
    results = []
    prev_result = user_input
    
    for agent_name, agent, agent_info in agents:
        with st.status(f"🔄 {agent_info['icon']} {agent_name} 正在处理...", expanded=True) as status_container:
            st.markdown(f"**输入**: {prev_result}")
            msg = Msg(name="user", content=[TextBlock(type="text", text=str(prev_result))], role="user")
            result = await run_agent_stream(agent, msg, status_container, agent_name, agent_info)
            results.append((agent_name, result))
            prev_result = result
            status_container.update(label=f"✅ {agent_info['icon']} {agent_name} 处理完成", state="complete")
    
    return results

async def run_mvp3():
    from mvp3.agents import create_demand_decomposition_agent, create_inventory_query_agent, create_risk_alert_agent, create_report_generation_agent
    
    model = get_model(model_type)
    decomposition_agent = create_demand_decomposition_agent(model)
    inventory_agent = create_inventory_query_agent(model)
    risk_agent = create_risk_alert_agent(model)
    report_agent = create_report_generation_agent(model)
    
    user_input = f"产品{st.session_state.product_id}计划生产{st.session_state.production_qty}件"
    
    agents = [
        ("需求拆解Agent", decomposition_agent, agent_flow_configs["mvp3"]["agents"][0]),
        ("库存查询Agent", inventory_agent, agent_flow_configs["mvp3"]["agents"][1]),
        ("风险预警Agent", risk_agent, agent_flow_configs["mvp3"]["agents"][2]),
        ("报表生成Agent", report_agent, agent_flow_configs["mvp3"]["agents"][3]),
    ]
    
    results = []
    prev_result = user_input
    
    for agent_name, agent, agent_info in agents:
        with st.status(f"🔄 {agent_info['icon']} {agent_name} 正在处理...", expanded=True) as status_container:
            st.markdown(f"**输入**: {prev_result}")
            msg = Msg(name="user", content=[TextBlock(type="text", text=str(prev_result))], role="user")
            result = await run_agent_stream(agent, msg, status_container, agent_name, agent_info)
            results.append((agent_name, result))
            prev_result = result
            status_container.update(label=f"✅ {agent_info['icon']} {agent_name} 处理完成", state="complete")
    
    return results

async def run_mvp4():
    from mvp4.agents import create_exception_detection_agent, create_scheduling_agent, create_approval_agent, create_execution_agent
    
    model = get_model(model_type)
    detection_agent = create_exception_detection_agent(model)
    scheduling_agent = create_scheduling_agent(model)
    approval_agent = create_approval_agent(model)
    execution_agent = create_execution_agent(model)
    
    user_input = f"{st.session_state.line_id}产线{st.session_state.equipment_id}设备故障，{st.session_state.fault_description}，受影响工单{st.session_state.affected_order}，严重程度{st.session_state.severity}"
    
    agents = [
        ("异常感知Agent", detection_agent, agent_flow_configs["mvp4"]["agents"][0]),
        ("排程计算Agent", scheduling_agent, agent_flow_configs["mvp4"]["agents"][1]),
        ("人工审批Agent", approval_agent, agent_flow_configs["mvp4"]["agents"][2]),
        ("执行同步Agent", execution_agent, agent_flow_configs["mvp4"]["agents"][3]),
    ]
    
    results = []
    prev_result = user_input
    
    for agent_name, agent, agent_info in agents:
        with st.status(f"🔄 {agent_info['icon']} {agent_name} 正在处理...", expanded=True) as status_container:
            st.markdown(f"**输入**: {prev_result}")
            msg = Msg(name="user", content=[TextBlock(type="text", text=str(prev_result))], role="user")
            result = await run_agent_stream(agent, msg, status_container, agent_name, agent_info)
            results.append((agent_name, result))
            prev_result = result
            status_container.update(label=f"✅ {agent_info['icon']} {agent_name} 处理完成", state="complete")
    
    return results

async def run_mvp5():
    from mvp5.agents import create_inspection_accept_agent, create_classification_agent, create_tracking_agent, create_report_agent
    
    model = get_model(model_type)
    accept_agent = create_inspection_accept_agent(model)
    classification_agent = create_classification_agent(model)
    tracking_agent = create_tracking_agent(model)
    report_agent = create_report_agent(model)
    
    user_input = f"{st.session_state.hazard_type}，{st.session_state.location}{st.session_state.description}，报告人：{st.session_state.reporter}"
    
    agents = [
        ("巡检受理Agent", accept_agent, agent_flow_configs["mvp5"]["agents"][0]),
        ("分级判定Agent", classification_agent, agent_flow_configs["mvp5"]["agents"][1]),
        ("整改跟踪Agent", tracking_agent, agent_flow_configs["mvp5"]["agents"][2]),
        ("合规报表Agent", report_agent, agent_flow_configs["mvp5"]["agents"][3]),
    ]
    
    results = []
    prev_result = user_input
    
    for agent_name, agent, agent_info in agents:
        with st.status(f"🔄 {agent_info['icon']} {agent_name} 正在处理...", expanded=True) as status_container:
            st.markdown(f"**输入**: {prev_result}")
            msg = Msg(name="user", content=[TextBlock(type="text", text=str(prev_result))], role="user")
            result = await run_agent_stream(agent, msg, status_container, agent_name, agent_info)
            results.append((agent_name, result))
            prev_result = result
            status_container.update(label=f"✅ {agent_info['icon']} {agent_name} 处理完成", state="complete")
    
    return results

async def run_mvp6():
    from mvp6.agents import create_registration_monitor_agent, create_rule_validation_agent, create_approval_decision_agent, create_registration_process_agent
    
    model = get_model(model_type)
    monitor_agent = create_registration_monitor_agent(model)
    validation_agent = create_rule_validation_agent(model)
    decision_agent = create_approval_decision_agent(model)
    process_agent = create_registration_process_agent(model)
    
    auto_process = st.session_state.auto_process == "yes"
    
    if auto_process:
        user_input = "执行完整的设备注册审批流程"
        
        with st.status(f"🔄 🚀 设备注册审批流程Agent 正在处理...", expanded=True) as status_container:
            st.markdown(f"**输入**: {user_input}")
            msg = Msg(name="user", content=[TextBlock(type="text", text=str(user_input))], role="user")
            result = await run_agent_stream(process_agent, msg, status_container, "设备注册审批流程Agent", {"icon": "🚀", "color": "#F59E0B"})
            status_container.update(label=f"✅ 🚀 设备注册审批流程Agent 处理完成", state="complete")
        
        return [("设备注册审批流程Agent", result)]
    else:
        request_id = st.session_state.request_id
        
        agents = [
            ("注册监控Agent", monitor_agent, agent_flow_configs["mvp6"]["agents"][0]),
            ("规则校验Agent", validation_agent, agent_flow_configs["mvp6"]["agents"][1]),
            ("审批决策Agent", decision_agent, agent_flow_configs["mvp6"]["agents"][2]),
        ]
        
        results = []
        
        monitor_input = "查询所有待审核的设备注册请求"
        with st.status(f"🔄 {agent_flow_configs['mvp6']['agents'][0]['icon']} 注册监控Agent 正在处理...", expanded=True) as status_container:
            st.markdown(f"**输入**: {monitor_input}")
            msg = Msg(name="user", content=[TextBlock(type="text", text=str(monitor_input))], role="user")
            result = await run_agent_stream(monitor_agent, msg, status_container, "注册监控Agent", agent_flow_configs["mvp6"]["agents"][0])
            results.append(("注册监控Agent", result))
            status_container.update(label=f"✅ {agent_flow_configs['mvp6']['agents'][0]['icon']} 注册监控Agent 处理完成", state="complete")
        
        validation_input = f"校验设备注册请求 {request_id}"
        with st.status(f"🔄 {agent_flow_configs['mvp6']['agents'][1]['icon']} 规则校验Agent 正在处理...", expanded=True) as status_container:
            st.markdown(f"**输入**: {validation_input}")
            msg = Msg(name="user", content=[TextBlock(type="text", text=str(validation_input))], role="user")
            result = await run_agent_stream(validation_agent, msg, status_container, "规则校验Agent", agent_flow_configs["mvp6"]["agents"][1])
            results.append(("规则校验Agent", result))
            status_container.update(label=f"✅ {agent_flow_configs['mvp6']['agents'][1]['icon']} 规则校验Agent 处理完成", state="complete")
        
        decision_input = f"request_id={request_id}, validation_result={results[-1][1]}"
        with st.status(f"🔄 {agent_flow_configs['mvp6']['agents'][2]['icon']} 审批决策Agent 正在处理...", expanded=True) as status_container:
            st.markdown(f"**输入**: {decision_input}")
            msg = Msg(name="user", content=[TextBlock(type="text", text=str(decision_input))], role="user")
            result = await run_agent_stream(decision_agent, msg, status_container, "审批决策Agent", agent_flow_configs["mvp6"]["agents"][2])
            results.append(("审批决策Agent", result))
            status_container.update(label=f"✅ {agent_flow_configs['mvp6']['agents'][2]['icon']} 审批决策Agent 处理完成", state="complete")
        
        return results

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("输入参数")
    for config in input_configs[selected_mvp]:
        if config["key"] not in st.session_state:
            st.session_state[config["key"]] = config["default"]
        st.text_input(
            config["label"],
            key=config["key"],
            help=config["help"],
        )
    
    start_button = st.button("🚀 开始执行", type="primary", use_container_width=True)

with col2:
    st.subheader("执行过程")
    
    if "execution_history" not in st.session_state:
        st.session_state.execution_history = []
    
    if start_button:
        st.session_state.execution_history = []
        log_buffer.clear()
        
        with st.spinner("正在初始化..."):
            try:
                if selected_mvp == "mvp1":
                    final_results = asyncio.run(run_mvp1())
                elif selected_mvp == "mvp2":
                    final_results = asyncio.run(run_mvp2())
                elif selected_mvp == "mvp3":
                    final_results = asyncio.run(run_mvp3())
                elif selected_mvp == "mvp4":
                    final_results = asyncio.run(run_mvp4())
                elif selected_mvp == "mvp5":
                    final_results = asyncio.run(run_mvp5())
                elif selected_mvp == "mvp6":
                    final_results = asyncio.run(run_mvp6())
                
                st.divider()
                st.subheader("📋 执行结果汇总")
                
                for i, (agent_name, result) in enumerate(final_results):
                    with st.expander(f"{agent_flow_configs[selected_mvp]['agents'][i]['icon']} {agent_name}", expanded=True):
                        st.markdown(result)
                
                st.success("🎉 流程执行完成！")
            except ValueError as e:
                st.error(f"❌ 错误: {e}")
                st.info("请在环境变量中设置 OPENAI_API_KEY 或 DASHSCOPE_API_KEY")
            except Exception as e:
                st.error(f"❌ 执行出错: {str(e)}")
                import traceback
                st.code(traceback.format_exc(), language="text")
    else:
        st.info("请填写输入参数并点击「开始执行」按钮启动流程")
        st.markdown("---")
        st.markdown("### 📖 场景说明")
        st.markdown(agent_flow_configs[selected_mvp]["description"])
        
        st.markdown("### 🔄 Agent流程")
        agents = agent_flow_configs[selected_mvp]["agents"]
        flow_html = ""
        for i, agent in enumerate(agents):
            flow_html += f"""
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="
                    padding: 8px 16px; 
                    background-color: {agent['color']}; 
                    color: white; 
                    border-radius: 12px; 
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">
                    <span>{agent['icon']}</span>
                    <span>{agent['name']}</span>
                </div>
                {'<span style="margin: 0 12px; color: #9CA3AF;">→</span>' if i < len(agents) - 1 else ''}
            </div>
            """
        st.markdown(flow_html, unsafe_allow_html=True)

with col3:
    st.subheader("📊 实时日志")
    
    log_placeholder = st.empty()
    
    if log_buffer:
        log_placeholder.markdown("### 最近日志")
        for log in log_buffer[-10:]:
            level_color = {
                "INFO": "#10B981",
                "WARNING": "#F59E0B",
                "ERROR": "#EF4444",
                "DEBUG": "#6B7280",
            }.get(log["level"], "#6B7280")
            st.markdown(f"""
            <div style="padding: 6px 12px; margin-bottom: 4px; background-color: #F3F4F6; border-radius: 6px;">
                <span style="color: {level_color}; font-weight: 600;">[{log['timestamp']}] {log['level']}</span>
                <div style="margin-top: 4px; font-size: 13px; color: #374151;">{log['message']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        log_placeholder.info("暂无日志，执行流程后将显示详细日志")

    if "execution_history" in st.session_state and st.session_state.execution_history:
        st.markdown("---")
        st.markdown("### 📈 执行统计")
        
        total_steps = len(st.session_state.execution_history)
        successful_steps = sum(1 for step in st.session_state.execution_history if step.get("status") == "success")
        
        st.metric("总步骤数", total_steps)
        st.metric("成功步骤", successful_steps)
        
        if total_steps > 0:
            progress = successful_steps / total_steps
            st.progress(progress)
