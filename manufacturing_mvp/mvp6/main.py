import asyncio
import json
import os
from agentscope.message import Msg, TextBlock
from .agents import (
    create_graph_building_agent,
    create_registration_monitor_agent,
    create_rule_validation_agent,
    create_approval_decision_agent,
    create_inconsistency_detection_agent,
    create_registration_process_agent
)
from configs.model_config import get_model
from configs.settings import DATA_DIR

def reset_registration_data():
    default_data = [
        {
            "request_id": "REQ-001",
            "equipment_id": "CNC-401",
            "equipment_name": "新五轴数控加工中心",
            "equipment_type": "CNCMachine",
            "manufacturer": "沈阳机床",
            "model": "VMC-850",
            "location": "A车间-1区",
            "workshop": "A车间",
            "production_line": "LINE-A",
            "status": "normal",
            "spindle_speed": 8000,
            "tool_count": 24,
            "axis_count": 5,
            "max_diameter": 300,
            "max_length": 800,
            "spindle_taper": "BT40",
            "table_size": "800x500",
            "submit_time": "2026-07-06 10:00:00",
            "request_status": "pending"
        },
        {
            "request_id": "REQ-002",
            "equipment_id": "ROB-007",
            "equipment_name": "新焊接机器人",
            "equipment_type": "Robot",
            "manufacturer": "ABB",
            "model": "IRB-6700",
            "location": "B车间-2区",
            "workshop": "B车间",
            "production_line": "LINE-B",
            "status": "normal",
            "payload": 200,
            "reach": 3.0,
            "axis_count": 6,
            "submit_time": "2026-07-06 11:00:00",
            "request_status": "pending"
        },
        {
            "request_id": "REQ-003",
            "equipment_id": "CNC-999",
            "equipment_name": "测试设备",
            "equipment_type": "CNCMachine",
            "location": "C车间",
            "workshop": "C车间",
            "production_line": "LINE-C",
            "status": "unknown",
            "spindle_speed": -100,
            "submit_time": "2026-07-06 12:00:00",
            "request_status": "pending"
        },
        {
            "request_id": "REQ-004",
            "equipment_id": "INVALID-123",
            "equipment_name": "无效编码设备",
            "equipment_type": "Lathe",
            "manufacturer": "大连机床",
            "model": "CA6140",
            "location": "A车间-3区",
            "workshop": "A车间",
            "production_line": "LINE-A",
            "status": "normal",
            "max_diameter": 400,
            "max_length": 1000,
            "submit_time": "2026-07-06 13:00:00",
            "request_status": "pending"
        },
        {
            "request_id": "REQ-005",
            "equipment_id": "MLG-401",
            "equipment_name": "新立式铣床",
            "equipment_type": "MillingMachine",
            "manufacturer": "北京第一机床",
            "model": "XA5032",
            "location": "D车间-1区",
            "workshop": "D车间",
            "production_line": "LINE-D",
            "status": "normal",
            "spindle_speed": 3000,
            "table_size": "320x1250",
            "axis_count": 3,
            "spindle_taper": "BT30",
            "submit_time": "2026-07-06 14:00:00",
            "request_status": "pending"
        },
        {
            "request_id": "REQ-006",
            "equipment_id": "CNC-501",
            "equipment_name": "新FANUC加工中心",
            "equipment_type": "CNCMachine",
            "manufacturer": "FANUC",
            "model": "M-20iA",
            "location": "A车间-1号工位",
            "workshop": "A车间",
            "production_line": "LINE-A",
            "status": "normal",
            "spindle_speed": 8000,
            "tool_count": 24,
            "axis_count": 5,
            "submit_time": "2026-07-06 15:00:00",
            "request_status": "pending"
        },
        {
            "request_id": "REQ-007",
            "equipment_id": "CNC-301",
            "equipment_name": "位置矛盾设备",
            "equipment_type": "CNCMachine",
            "manufacturer": "Haas",
            "model": "VF-2",
            "location": "B车间",
            "workshop": "B车间",
            "production_line": "LINE-A",
            "status": "normal",
            "spindle_speed": 7500,
            "tool_count": 20,
            "axis_count": 3,
            "submit_time": "2026-07-06 16:00:00",
            "request_status": "pending"
        }
    ]
    
    requests_file = os.path.join(DATA_DIR, "device_registration_requests.json")
    with open(requests_file, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, ensure_ascii=False, indent=2)

async def run_device_onboarding_demo():
    model = get_model()
    
    graph_agent = create_graph_building_agent(model)
    monitor_agent = create_registration_monitor_agent(model)
    validation_agent = create_rule_validation_agent(model)
    decision_agent = create_approval_decision_agent(model)
    inconsistency_agent = create_inconsistency_detection_agent(model)
    process_agent = create_registration_process_agent(model)
    
    print("=" * 80)
    print("MVP6: 跨系统设备数据一致性治理与智能审核")
    print("=" * 80)
    print("业务场景: 基于本体知识图谱的数据治理与智能审核")
    print("流程: 构建图谱 → 推理发现不一致 → 智能审核 → 自动增强")
    print("=" * 80)
    
    print("\n[步骤1] 重置测试数据...")
    reset_registration_data()
    print("测试数据已重置，包含7个设备注册请求：")
    print("  - REQ-001: 正常设备（CNC-201，新编码）")
    print("  - REQ-002: 正常设备（ROB-006，新编码）")
    print("  - REQ-003: 异常设备（无效状态+负数转速+缺少必需属性）")
    print("  - REQ-004: 异常设备（无效编码格式）")
    print("  - REQ-005: 正常设备（MLG-301，新编码）")
    print("  - REQ-006: 异常设备（重复编码，CNC-001已在MES/ERP中存在）")
    print("  - REQ-007: 异常设备（位置矛盾：声称在B车间，但产线LINE-A在A车间）")
    print("-" * 80)
    
    print("\n[步骤2] 知识图谱构建Agent - 构建跨系统知识图谱并执行推理...")
    print("这将从MES、ERP和产线数据构建知识图谱，并执行传递性推理")
    graph_msg = Msg(name="user", content=[TextBlock(type="text", text="构建跨系统知识图谱并执行传递性推理")], role="user")
    graph_result = await graph_agent.reply(graph_msg)
    print(f"[图谱构建结果]: {graph_result.content}")
    print("-" * 80)
    
    print("\n[步骤3] 跨系统一致性检测Agent - 检测MES/ERP数据不一致...")
    inconsistency_msg = Msg(name="user", content=[TextBlock(type="text", text="检测跨系统数据不一致")], role="user")
    inconsistency_result = await inconsistency_agent.reply(inconsistency_msg)
    print(f"[一致性检测结果]: {inconsistency_result.content}")
    print("-" * 80)
    
    print("\n[步骤4] 设备注册监控Agent - 查询待审核请求...")
    monitor_msg = Msg(name="user", content=[TextBlock(type="text", text="查询所有待审核的设备注册请求")], role="user")
    monitor_result = await monitor_agent.reply(monitor_msg)
    print(f"[监控结果]: {monitor_result.content}")
    print("-" * 80)
    
    print("\n[步骤5] 规则校验Agent - 校验REQ-001（正常案例）...")
    print("验证基于知识图谱的规则校验：传递性推理、跨系统一致性、容量约束")
    validation_msg1 = Msg(name="user", content=[TextBlock(type="text", text="校验设备注册请求 REQ-001")], role="user")
    validation_result1 = await validation_agent.reply(validation_msg1)
    print(f"[校验结果]: {validation_result1.content}")
    print("-" * 80)
    
    print("\n[步骤6] 规则校验Agent - 校验REQ-007（位置矛盾案例）...")
    print("验证传递性推理冲突检测：设备声称在B车间，但产线LINE-A位于A车间")
    validation_msg2 = Msg(name="user", content=[TextBlock(type="text", text="校验设备注册请求 REQ-007")], role="user")
    validation_result2 = await validation_agent.reply(validation_msg2)
    print(f"[校验结果]: {validation_result2.content}")
    print("-" * 80)
    
    print("\n[步骤7] 规则校验Agent - 校验REQ-006（重复编码案例）...")
    print("验证跨系统一致性校验：CNC-001已在MES/ERP系统中存在")
    validation_msg3 = Msg(name="user", content=[TextBlock(type="text", text="校验设备注册请求 REQ-006")], role="user")
    validation_result3 = await validation_agent.reply(validation_msg3)
    print(f"[校验结果]: {validation_result3.content}")
    print("-" * 80)
    
    print("\n[步骤8] 审批决策Agent - 处理校验结果...")
    print("处理REQ-001（校验通过）...")
    decision_msg1 = Msg(name="user", content=[TextBlock(type="text", text=f"request_id=REQ-001, validation_result={validation_result1.content}")], role="user")
    decision_result1 = await decision_agent.reply(decision_msg1)
    print(f"[审批结果]: {decision_result1.content}")
    print("-" * 80)
    
    print("\n[步骤9] 审批决策Agent - 处理位置矛盾请求...")
    print("处理REQ-007（传递性推理发现位置矛盾）...")
    decision_msg2 = Msg(name="user", content=[TextBlock(type="text", text=f"request_id=REQ-007, validation_result={validation_result2.content}")], role="user")
    decision_result2 = await decision_agent.reply(decision_msg2)
    print(f"[审批结果]: {decision_result2.content}")
    print("-" * 80)
    
    print("\n[步骤10] 设备注册审批流程Agent - 执行完整自动化流程...")
    print("这将自动构建图谱→推理→审核→增强→报告")
    process_msg = Msg(name="user", content=[TextBlock(type="text", text="执行完整的设备注册审批流程")], role="user")
    process_result = await process_agent.reply(process_msg)
    print(f"[流程结果]: {process_result.content}")
    
    print("\n" + "=" * 80)
    print("业务闭环完成！")
    print("流程总结:")
    print("  1. 构建跨系统知识图谱（MES+ERP+产线数据）")
    print("  2. 执行传递性推理（设备→产线→车间，发现隐含关系）")
    print("  3. 检测跨系统不一致（MES和ERP同一设备数据冲突）")
    print("  4. 新设备注册校验（基于图谱的规则推理）")
    print("     - 传递性推理冲突检测（位置矛盾）")
    print("     - 跨系统一致性校验（重复编码）")
    print("     - 产线容量约束校验")
    print("  5. 审批决策（批准/拒绝）")
    print("  6. 知识图谱增强（自动补全车间信息）")
    print("  7. 同步MES/ERP系统")
    print("  8. 生成审批报告")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_device_onboarding_demo())