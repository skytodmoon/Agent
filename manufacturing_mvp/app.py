import sys
import os
import json
import logging
import threading
from datetime import datetime
from io import StringIO
from http.server import HTTPServer, SimpleHTTPRequestHandler

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

mvp_options = {
    "mvp1": "MVP1: 核心设备故障诊断与工单闭环助手",
    "mvp2": "MVP2: 质检缺陷根因追溯Agent",
    "mvp3": "MVP3: 物料齐套核算与交期预警Agent",
    "mvp4": "MVP4: 产线异常应急排程调度Agent",
    "mvp5": "MVP5: 车间安全巡检与隐患整改闭环Agent",
    "mvp6": "MVP6: 新设备MES上线准入自动审核",
    "mvp7": "MVP7: 流程工业知识图谱与物料流向推理",
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
        {"key": "demo_mode", "label": "演示模式", "default": "full", "help": "full（完整演示）/ simple（简洁演示）"},
        {"key": "request_id", "label": "注册请求ID", "default": "REQ-020", "help": "例如：REQ-020"},
    ],
    "mvp7": [
        {"key": "process_unit", "label": "生产单元", "default": "PU-001", "help": "例如：PU-001"},
        {"key": "analysis_mode", "label": "分析模式", "default": "full", "help": "full/flow/constraint（完整分析/物料流向/工艺约束）"},
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
            {"name": "本体知识图谱", "icon": "�", "color": "#3B82F6"},
            {"name": "规则校验推理", "icon": "🧠", "color": "#10B981"},
            {"name": "审批决策执行", "icon": "✅", "color": "#EF4444"},
            {"name": "设备动作控制", "icon": "⚡", "color": "#F59E0B"},
        ],
        "description": "基于本体思想的设备注册审批演示，展示知识图谱的语义+动作能力。包含：📚 本体知识图谱（类、属性、关系、规则）、🔍 规则校验（编码规范、必填属性、跨系统一致性）、🧠 语义推理（传递性推理、容量约束、类型兼容性）、✅ 审批决策（自动批准/拒绝）、⚡ 设备动作（启动生产、停止生产、开始维护、重置错误，基于状态机约束）。",
    },
    "mvp7": {
        "agents": [
            {"name": "流程监控Agent", "icon": "👀", "color": "#3B82F6"},
            {"name": "事件处理Agent", "icon": "⚡", "color": "#EF4444"},
            {"name": "应急响应Agent", "icon": "🚨", "color": "#F59E0B"},
            {"name": "流程管理Agent", "icon": "🧠", "color": "#8B5CF6"},
        ],
        "description": "解决流程工业中物料流向不透明、工艺约束难监控、异常响应慢的痛点。基于预构建的本体知识图谱，通过事件驱动架构实现：设备异常检测→影响分析→约束推理→应急响应→图谱更新的完整闭环流程。",
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
    from mvp6.tools import GenerateGraphVisualizationTool, ExecuteDeviceActionTool, GraphQueryTool, QueryRegistrationRequestsTool, ValidateRegistrationRequestTool, ApproveRegistrationTool, RejectRegistrationTool
    from mvp6.graph_manager import get_graph, save_graph_to_json
    
    model = get_model(model_type)
    demo_mode = st.session_state.get("demo_mode", "full")
    
    results = []
    
    with st.status("📚 本体知识图谱初始化...", expanded=True) as status_container:
        graph = get_graph()
        st.success(f"✅ 知识图谱加载完成")
        st.markdown(f"""
        **本体知识图谱概览**:
        - 总实例数: `{len(graph.node_properties)}`
        - 总关系数: `{sum(len(rels) for rels in graph.graph.values())}`
        - 设备实例: CNC({len(graph.get_instances_by_class('CNCMachine'))}), Robot({len(graph.get_instances_by_class('Robot'))}), Milling({len(graph.get_instances_by_class('MillingMachine'))})
        
        **本体核心概念**:
        - 📦 **类(Class)**: Equipment, CNCMachine, Robot, ProductionLine, Workshop
        - 🔗 **关系(Relation)**: belongsTo(属于), locatedIn(位于), hasPart(包含)
        - 📝 **属性(Property)**: equipment_id, equipment_name, status, location
        - ⚡ **动作(Action)**: start_production, stop_production, start_maintenance, reset_error
        - 🧠 **规则(Rule)**: 容量约束、类型兼容性、传递性推理
        
        **演示模式**: {'完整演示' if demo_mode == 'full' else '简洁演示'}
        """)
        status_container.update(label="✅ 本体知识图谱初始化完成", state="complete")
    
    with st.status("� 阶段1: 查询待审核请求...", expanded=True) as status_container:
        query_tool = QueryRegistrationRequestsTool()
        query_result = await query_tool._call(status="pending")
        query_data = query_result.content[0].text
        
        try:
            data = json.loads(query_data)
            count = data.get("total_count", 0)
            st.success(f"✅ 发现 {count} 个待审核请求")
            
            if data.get("requests"):
                for req in data["requests"]:
                    st.markdown(f"""
                    **📝 {req['request_id']}** - {req['equipment_name']} ({req['equipment_type']})
                    - 设备ID: {req['equipment_id']}
                    - 位置: {req['location']}
                    - 产线: {req['production_line']}
                    """)
        except:
            st.code(query_data)
        
        results.append(("查询待审核请求", query_data))
        status_container.update(label="✅ 阶段1完成 - 查询待审核请求", state="complete")
    
    with st.status("� 阶段2: 基于本体的规则校验与语义推理...", expanded=True) as status_container:
        query_tool = QueryRegistrationRequestsTool()
        query_result = await query_tool._call(status="pending")
        query_data = json.loads(query_result.content[0].text)
        
        for req in query_data["requests"][:2]:
            st.markdown(f"---\n**校验请求: {req['request_id']}**")
            
            validate_tool = ValidateRegistrationRequestTool()
            validate_result = await validate_tool._call(request_id=req["request_id"])
            validate_data = json.loads(validate_result.content[0].text)
            
            st.markdown(f"**校验结果**: {'✅ 通过' if validate_data.get('valid') else '❌ 不通过'}")
            
            if "validation_results" in validate_data:
                for rule_name, result in validate_data["validation_results"].items():
                    status = "✅" if result.get("passed") else "❌"
                    st.markdown(f"- {status} **{rule_name}**: {result.get('message')}")
            
            if "reasons" in validate_data:
                st.markdown("**⚠️ 校验失败原因**:")
                for reason in validate_data["reasons"]:
                    st.markdown(f"- {reason}")
        
        st.markdown("---\n**🧠 语义推理演示**:")
        
        graph_query = GraphQueryTool()
        
        traverse_result = await graph_query._call(query_type="traverse", start_node="LINE-A")
        traverse_data = json.loads(traverse_result.content[0].text)
        st.markdown(f"**🔗 产线 LINE-A 关联节点**: {traverse_data['count']} 个")
        
        capacity_result = await graph_query._call(query_type="line_capacity", production_line="LINE-A")
        capacity_data = json.loads(capacity_result.content[0].text)
        st.markdown(f"""
        **📊 产线 LINE-A 容量约束**:
        - 当前设备数: {capacity_data.get('current_count', 0)}
        - 最大容量: {capacity_data.get('max_capacity', 0)}
        - 剩余容量: {capacity_data.get('remaining_capacity', 0)}
        - 容量充足: {'✅' if capacity_data.get('capacity_ok') else '❌'}
        """)
        
        compatibility_result = await graph_query._call(query_type="type_compatibility", equipment_type="CNCMachine", production_line="LINE-A")
        compatibility_data = json.loads(compatibility_result.content[0].text)
        st.markdown(f"""
        **🔧 类型兼容性**:
        - 兼容: {'✅' if compatibility_data.get('compatible') else '❌'}
        - 支持的类型: {', '.join(compatibility_data.get('supported_types', []))}
        """)
        
        results.append(("规则校验与语义推理", "完成"))
        status_container.update(label="✅ 阶段2完成 - 规则校验与语义推理", state="complete")
    
    with st.status("✅ 阶段3: 审批决策与图谱更新...", expanded=True) as status_container:
        query_tool = QueryRegistrationRequestsTool()
        query_result = await query_tool._call(status="pending")
        query_data = json.loads(query_result.content[0].text)
        
        for req in query_data["requests"][:2]:
            st.markdown(f"---\n**处理请求: {req['request_id']}**")
            
            validate_tool = ValidateRegistrationRequestTool()
            validate_result = await validate_tool._call(request_id=req["request_id"])
            validate_data = json.loads(validate_result.content[0].text)
            
            if validate_data.get("valid"):
                approve_result = await ApproveRegistrationTool()._call(request_id=req["request_id"])
                approve_data = json.loads(approve_result.content[0].text)
                
                st.success(f"✅ {approve_data.get('message')}")
                
                if "graph_update" in approve_data:
                    update_info = approve_data["graph_update"]
                    st.markdown(f"""
                    **📊 知识图谱更新**:
                    - 新增节点: {update_info.get('nodes_added', 0)}
                    - 新增关系: {update_info.get('relations_added', 0)}
                    """)
            else:
                reject_reason = "; ".join(validate_data.get("reasons", []))
                reject_result = await RejectRegistrationTool()._call(request_id=req["request_id"], reject_reason=reject_reason)
                reject_data = json.loads(reject_result.content[0].text)
                
                st.error(f"❌ {reject_data.get('message')}")
        
        save_graph_to_json()
        st.success("✅ 知识图谱已更新并保存")
        
        results.append(("审批决策与图谱更新", "完成"))
        status_container.update(label="✅ 阶段3完成 - 审批决策与图谱更新", state="complete")
    
    with st.status("⚡ 阶段4: 设备动作演示...", expanded=True) as status_container:
        st.markdown("""
        **设备动作(Action)体现本体思想的"语义+动作"能力**:
        - 每个设备根据类型和状态拥有不同的可执行动作
        - 动作可用性由状态机约束决定
        - 执行动作会改变设备状态，进而更新知识图谱
        """)
        
        execute_tool = ExecuteDeviceActionTool()
        
        actions_demo = [
            ("CNC-001", "start_production", "启动生产"),
            ("CNC-001", "start_maintenance", "开始维护"),
            ("ROB-001", "start_task", "启动任务"),
            ("CNC-001", "reset_error", "重置错误"),
        ]
        
        for equipment_id, action_name, action_label in actions_demo:
            st.markdown(f"---\n**执行动作: {action_label} ({equipment_id})**")
            try:
                action_result = await execute_tool._call(equipment_id, action_name)
                action_data = json.loads(action_result.content[0].text)
                
                if action_data.get("status") == "success":
                    st.success(f"✅ {action_data.get('message')}")
                    st.markdown(f"""
                    - 设备: {action_data.get('equipment_name')}
                    - 类型: {action_data.get('equipment_type')}
                    - 状态变化: {action_data.get('previous_status')} → {action_data.get('new_status')}
                    """)
                elif action_data.get("status") == "rejected":
                    st.warning(f"⚠️ {action_data.get('message')}")
                    st.markdown(f"""
                    - 当前状态: {action_data.get('equipment_status')}
                    - 需要状态: {', '.join(action_data.get('requires_status', []))}
                    """)
                else:
                    st.error(f"❌ {action_data.get('message')}")
            except Exception as e:
                st.error(f"⚠️ 执行失败: {e}")
        
        save_graph_to_json()
        st.success("✅ 设备动作执行完成，知识图谱已更新")
        
        results.append(("设备动作演示", "完成"))
        status_container.update(label="✅ 阶段4完成 - 设备动作演示", state="complete")
    
    with st.status("🎨 阶段5: 生成知识图谱可视化...", expanded=True) as status_container:
        visualization_tool = GenerateGraphVisualizationTool()
        vis_result = await visualization_tool._call()
        vis_data = json.loads(vis_result.content[0].text)
        
        st.success(f"✅ 可视化数据生成成功")
        st.markdown(f"""
        - 实例数: {vis_data.get('total_instances')}
        - 关系数: {vis_data.get('total_relations')}
        """)
        
        results.append(("生成知识图谱可视化", "完成"))
        status_container.update(label="✅ 阶段5完成 - 生成知识图谱可视化", state="complete")
    
    return results

async def run_mvp7():
    from mvp7.agents import (
        create_process_monitor_agent,
        create_event_handling_agent,
        create_emergency_response_agent,
        create_process_management_agent
    )
    from mvp7.tools import GenerateProcessGraphVisualizationTool
    
    model = get_model(model_type)
    monitor_agent = create_process_monitor_agent(model)
    event_agent = create_event_handling_agent(model)
    response_agent = create_emergency_response_agent(model)
    management_agent = create_process_management_agent(model)
    
    process_unit = st.session_state.process_unit
    analysis_mode = st.session_state.analysis_mode
    
    results = []
    
    monitor_input = "查询所有设备状态，检查工艺约束，提供监控概览"
    with st.status(f"🔄 {agent_flow_configs['mvp7']['agents'][0]['icon']} 流程监控Agent 正在处理...", expanded=True) as status_container:
        st.markdown(f"**输入**: {monitor_input}")
        msg = Msg(name="user", content=[TextBlock(type="text", text=str(monitor_input))], role="user")
        result = await run_agent_stream(monitor_agent, msg, status_container, "流程监控Agent", agent_flow_configs["mvp7"]["agents"][0])
        results.append(("流程监控Agent", result))
        status_container.update(label=f"✅ {agent_flow_configs['mvp7']['agents'][0]['icon']} 流程监控Agent 处理完成", state="complete")
    
    event_input = "处理设备故障事件：PMP-001进料泵故障，分析对下游设备的影响"
    with st.status(f"🔄 {agent_flow_configs['mvp7']['agents'][1]['icon']} 事件处理Agent 正在处理...", expanded=True) as status_container:
        st.markdown(f"**输入**: {event_input}")
        msg = Msg(name="user", content=[TextBlock(type="text", text=str(event_input))], role="user")
        result = await run_agent_stream(event_agent, msg, status_container, "事件处理Agent", agent_flow_configs["mvp7"]["agents"][1])
        results.append(("事件处理Agent", result))
        status_container.update(label=f"✅ {agent_flow_configs['mvp7']['agents'][1]['icon']} 事件处理Agent 处理完成", state="complete")
    
    response_input = "针对PMP-001进料泵故障，生成应急预案和操作建议"
    with st.status(f"🔄 {agent_flow_configs['mvp7']['agents'][2]['icon']} 应急响应Agent 正在处理...", expanded=True) as status_container:
        st.markdown(f"**输入**: {response_input}")
        msg = Msg(name="user", content=[TextBlock(type="text", text=str(response_input))], role="user")
        result = await run_agent_stream(response_agent, msg, status_container, "应急响应Agent", agent_flow_configs["mvp7"]["agents"][2])
        results.append(("应急响应Agent", result))
        status_container.update(label=f"✅ {agent_flow_configs['mvp7']['agents'][2]['icon']} 应急响应Agent 处理完成", state="complete")
    
    management_input = "执行完整流程：监控→检测→分析→响应→更新图谱"
    with st.status(f"🔄 {agent_flow_configs['mvp7']['agents'][3]['icon']} 流程管理Agent 正在处理...", expanded=True) as status_container:
        st.markdown(f"**输入**: {management_input}")
        msg = Msg(name="user", content=[TextBlock(type="text", text=str(management_input))], role="user")
        result = await run_agent_stream(management_agent, msg, status_container, "流程管理Agent", agent_flow_configs["mvp7"]["agents"][3])
        results.append(("流程管理Agent", result))
        status_container.update(label=f"✅ {agent_flow_configs['mvp7']['agents'][3]['icon']} 流程管理Agent 处理完成", state="complete")
    
    with st.status("🔄 生成可视化数据...", expanded=True) as status_container:
        visualization_tool = GenerateProcessGraphVisualizationTool()
        await visualization_tool._call()
        st.success("✅ 知识图谱可视化数据生成完成")
        st.info("🌐 可视化页面：http://localhost:8080/mvp7/graph_visualization.html")
        status_container.update(label="✅ 可视化数据生成完成", state="complete")
    
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
    
    if selected_mvp == "mvp6":
        try:
            requests_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "device_registration_requests.json")
            with open(requests_file, 'r', encoding='utf-8') as f:
                requests = json.load(f)
            
            pending_requests = [r for r in requests if r.get("request_status") == "pending"]
            
            if pending_requests:
                st.markdown("---")
                st.markdown("### 📋 待审核请求列表")
                for req in pending_requests:
                    status_color = "#10B981"
                    radio_key = f"select_req_{req['request_id']}"
                    if st.radio(
                        f"**{req['request_id']}** - {req['equipment_name']} ({req['equipment_type']})",
                        ["选择此请求"],
                        key=radio_key,
                        label_visibility="collapsed"
                    ):
                        st.session_state.request_id = req["request_id"]
                        st.session_state.auto_process = "no"
                    
                    st.markdown(f"""
                    <div style="padding: 8px 12px; background-color: #F3F4F6; border-radius: 8px; margin-bottom: 8px;">
                        <div style="font-size: 14px; color: #374151;">
                            <strong>设备ID:</strong> {req['equipment_id']}
                        </div>
                        <div style="font-size: 14px; color: #374151;">
                            <strong>位置:</strong> {req.get('location', '-')}
                        </div>
                        <div style="font-size: 14px; color: #374151;">
                            <strong>提交时间:</strong> {req.get('submit_time', '-')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("---")
                st.info("✅ 当前没有待审核的设备注册请求")
                st.markdown("所有请求已处理完毕，可在右侧查看场景说明")
        except Exception as e:
            st.warning(f"加载待审核请求列表失败: {e}")
    
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
                elif selected_mvp == "mvp7":
                    final_results = asyncio.run(run_mvp7())
                
                st.divider()
                st.subheader("📋 执行结果汇总")
                
                icon_map = {
                    "查询待审核请求": "📋",
                    "规则校验与语义推理": "🔍",
                    "审批决策与图谱更新": "✅",
                    "设备动作演示": "⚡",
                    "生成知识图谱可视化": "🎨",
                    "注册监控Agent": "👀",
                    "规则校验Agent": "✅",
                    "审批决策Agent": "🔍",
                    "设备注册审批流程Agent": "🚀",
                }
                
                for i, (agent_name, result) in enumerate(final_results):
                    icon = icon_map.get(agent_name, "📌")
                    with st.expander(f"{icon} {agent_name}", expanded=True):
                        st.markdown(result)
                
                st.success("🎉 流程执行完成！")
                
                if selected_mvp == "mvp6":
                    st.markdown("""
                    ---
                    📊 **知识图谱可视化**
                    
                    点击下方链接查看本体知识图谱可视化页面：
                    
                    [🌐 MVP6 - 设备注册知识图谱](http://localhost:8080/mvp6/graph_visualization.html)
                    """)
                elif selected_mvp == "mvp7":
                    st.markdown("""
                    ---
                    📊 **流程工业知识图谱可视化**
                    
                    点击下方链接查看流程工业知识图谱可视化页面：
                    
                    [🌐 MVP7 - 流程工业知识图谱](http://localhost:8080/mvp7/graph_visualization.html)
                    """)
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

def start_visualization_server(port=8080):
    class CustomHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
        
        def log_message(self, format, *args):
            pass
    
    server = HTTPServer(("localhost", port), CustomHandler)
    logging.info(f"🌐 知识图谱可视化服务已启动: http://localhost:{port}")
    server.serve_forever()

if "visualization_server_started" not in st.session_state:
    try:
        server_thread = threading.Thread(target=start_visualization_server, args=(8080,), daemon=True)
        server_thread.start()
        st.session_state.visualization_server_started = True
        logging.info("✅ 可视化服务器线程已启动")
    except Exception as e:
        logging.warning(f"⚠️ 可视化服务器启动失败（可能端口已占用）: {e}")
