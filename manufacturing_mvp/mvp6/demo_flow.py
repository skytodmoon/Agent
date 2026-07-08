import asyncio
import json
import os
from datetime import datetime
from .agents import (
    create_registration_monitor_agent,
    create_rule_validation_agent,
    create_approval_decision_agent,
    create_registration_process_agent
)
from .tools import (
    QueryRegistrationRequestsTool,
    ValidateRegistrationRequestTool,
    ApproveRegistrationTool,
    RejectRegistrationTool,
    ExecuteDeviceActionTool,
    GraphQueryTool,
    GenerateGraphVisualizationTool
)
from .graph_manager import get_graph, save_graph_to_json
from configs.model_config import get_model
from configs.settings import DATA_DIR

async def run_mvp6_demo():
    model = get_model("local")
    
    print("\n" + "=" * 100)
    print("🏭 MVP6 - 新设备MES上线准入自动审核（基于本体的业务+动作演示）")
    print("=" * 100)
    
    print("\n" + "▌" * 100)
    print("📚 本体思想核心概念演示")
    print("▌" * 100)
    print("""
本体(Ontology)是对领域知识的形式化表示，包含：
1. 类(Class)：设备、产线、车间、维护任务等
2. 属性(Property)：设备ID、名称、类型、状态等
3. 关系(Relation)：belongsTo(属于)、locatedIn(位于)、hasPart(包含)等
4. 规则(Rule)：容量约束、类型兼容性、传递性推理等

知识图谱基于本体构建，每个节点不仅有属性，还有可执行的动作(Action)
动作的可用性由设备类型和当前状态决定，体现了"语义+动作"的本体思想
""")
    
    graph = get_graph()
    print(f"\n📊 当前知识图谱状态:")
    print(f"   - 总实例数: {len(graph.node_properties)}")
    print(f"   - 总关系数: {sum(len(rels) for rels in graph.graph.values())}")
    
    equipment_nodes = graph.get_instances_by_class("Equipment")
    cnc_nodes = graph.get_instances_by_class("CNCMachine")
    robot_nodes = graph.get_instances_by_class("Robot")
    print(f"   - 设备实例: {len(equipment_nodes)} (CNC: {len(cnc_nodes)}, Robot: {len(robot_nodes)})")
    
    print("\n" + "▌" * 100)
    print("📋 阶段1: 查询待审核请求")
    print("▌" * 100)
    
    query_tool = QueryRegistrationRequestsTool()
    query_result = await query_tool._call(status="pending")
    query_data = json.loads(query_result.content[0].text)
    
    print(f"\n发现 {query_data['total_count']} 个待审核请求:")
    for req in query_data["requests"]:
        print(f"   📝 {req['request_id']} - {req['equipment_name']} ({req['equipment_type']})")
        print(f"      ├─ 设备ID: {req['equipment_id']}")
        print(f"      ├─ 位置: {req['location']}")
        print(f"      ├─ 产线: {req['production_line']}")
        print(f"      └─ 提交时间: {req['submit_time']}")
    
    print("\n" + "▌" * 100)
    print("🔍 阶段2: 基于本体的规则校验")
    print("▌" * 100)
    
    validation_agent = create_rule_validation_agent(model)
    
    for req in query_data["requests"][:2]:
        print(f"\n--- 校验请求: {req['request_id']} ---")
        
        validate_tool = ValidateRegistrationRequestTool()
        validate_result = await validate_tool._call(request_id=req["request_id"])
        validate_data = json.loads(validate_result.content[0].text)
        
        print(f"\n📋 规则校验结果:")
        print(f"   请求ID: {validate_data.get('request_id')}")
        print(f"   校验状态: {'✅ 通过' if validate_data.get('valid') else '❌ 不通过'}")
        
        if "validation_results" in validate_data:
            for rule_name, result in validate_data["validation_results"].items():
                status = "✅" if result.get("passed") else "❌"
                print(f"   {status} {rule_name}: {result.get('message')}")
        
        if "reasons" in validate_data:
            print(f"\n⚠️ 校验失败原因:")
            for reason in validate_data["reasons"]:
                print(f"   - {reason}")
        
        if "suggestions" in validate_data:
            print(f"\n💡 建议:")
            for suggestion in validate_data["suggestions"]:
                print(f"   - {suggestion}")
    
    print("\n" + "▌" * 100)
    print("🧠 阶段3: 语义推理演示")
    print("▌" * 100)
    
    print("""
本体推理能力展示：

1. 传递性推理(Transitive Reasoning)
   - 设备 A belongsTo 产线 L
   - 产线 L locatedIn 车间 W
   - → 推理得出: 设备 A locatedIn 车间 W

2. 容量约束推理(Capacity Constraint)
   - 产线 LINE-A 最大容量: 10台设备
   - 当前已有设备: 8台
   - 新注册设备: 1台
   - → 推理得出: 容量充足，可以批准

3. 类型兼容性推理(Type Compatibility)
   - 产线 LINE-A 需要: CNCMachine, Robot
   - 新设备类型: CNCMachine
   - → 推理得出: 类型兼容，可以批准
""")
    
    graph_query = GraphQueryTool()
    traverse_result = await graph_query._call(query_type="traverse", start_node="LINE-A")
    traverse_data = json.loads(traverse_result.content[0].text)
    
    print(f"\n🔗 产线 LINE-A 的关联节点 ({traverse_data['count']} 个):")
    for node in traverse_data["nodes"]:
        props = node.get("properties", {})
        print(f"   📌 {node['id']} ({props.get('equipment_name', props.get('__class__', 'Unknown'))})")
        for rel in node.get("relations", []):
            print(f"      └─ {rel[0]} → {rel[1]}")
    
    capacity_result = await graph_query._call(query_type="line_capacity", production_line="LINE-A")
    capacity_data = json.loads(capacity_result.content[0].text)
    print(f"\n📊 产线 LINE-A 容量信息:")
    print(f"   当前设备数: {capacity_data.get('current_count', 0)}")
    print(f"   最大容量: {capacity_data.get('max_capacity', 0)}")
    print(f"   剩余容量: {capacity_data.get('remaining_capacity', 0)}")
    print(f"   是否充足: {'✅ 充足' if capacity_data.get('capacity_ok') else '❌ 不足'}")
    
    print("\n" + "▌" * 100)
    print("✅ 阶段4: 审批决策与图谱更新")
    print("▌" * 100)
    
    approval_agent = create_approval_decision_agent(model)
    
    for req in query_data["requests"][:2]:
        print(f"\n--- 处理请求: {req['request_id']} ---")
        
        validate_tool = ValidateRegistrationRequestTool()
        validate_result = await validate_tool._call(request_id=req["request_id"])
        validate_data = json.loads(validate_result.content[0].text)
        
        if validate_data.get("valid"):
            print(f"\n✅ 校验通过，执行批准流程...")
            
            approve_result = await ApproveRegistrationTool()._call(request_id=req["request_id"])
            approve_data = json.loads(approve_result.content[0].text)
            
            print(f"   📝 审批结果: {approve_data.get('status')}")
            print(f"   📊 知识图谱更新: {approve_data.get('message')}")
            
            if "graph_update" in approve_data:
                update_info = approve_data["graph_update"]
                print(f"   ├─ 新增节点: {update_info.get('nodes_added', 0)}")
                print(f"   ├─ 新增关系: {update_info.get('relations_added', 0)}")
                print(f"   └─ 更新文件: {', '.join(update_info.get('files_updated', []))}")
            
        else:
            print(f"\n❌ 校验失败，执行拒绝流程...")
            
            reject_reason = "; ".join(validate_data.get("reasons", []))
            reject_result = await RejectRegistrationTool()._call(request_id=req["request_id"], reason=reject_reason)
            reject_data = json.loads(reject_result.content[0].text)
            
            print(f"   📝 审批结果: {reject_data.get('status')}")
            print(f"   📋 拒绝原因: {reject_data.get('message')}")
    
    save_graph_to_json()
    print(f"\n📊 知识图谱已更新并保存")
    
    print("\n" + "▌" * 100)
    print("⚡ 阶段5: 设备动作演示")
    print("▌" * 100)
    
    print("""
设备动作(Action)体现了本体思想的"语义+动作"能力：
- 每个设备节点根据其类型和状态，拥有不同的可执行动作
- 动作的可用性由状态机约束决定
- 执行动作会改变设备状态，进而影响知识图谱

动作列表：
  CNC Machine: start_production, stop_production, start_maintenance, reset_error, change_tool, calibrate
  Robot: start_task, stop_task, start_maintenance, reset_error, teach_mode, calibrate_joints
  Conveyor: start_convey, stop_convey, start_maintenance, reset_error, adjust_speed
""")
    
    execute_tool = ExecuteDeviceActionTool()
    
    actions_demo = [
        ("CNC-001", "start_production", "启动生产"),
        ("CNC-001", "start_maintenance", "开始维护"),
        ("ROB-001", "start_task", "启动任务"),
        ("CNC-001", "reset_error", "重置错误"),
    ]
    
    for equipment_id, action_name, action_label in actions_demo:
        print(f"\n--- 执行动作: {action_label} ({equipment_id}) ---")
        try:
            action_result = await execute_tool._call(equipment_id, action_name)
            action_data = json.loads(action_result.content[0].text)
            
            if action_data.get("status") == "success":
                print(f"   ✅ {action_data.get('message')}")
                print(f"      ├─ 设备: {action_data.get('equipment_name')}")
                print(f"      ├─ 类型: {action_data.get('equipment_type')}")
                print(f"      └─ 状态变化: {action_data.get('previous_status')} → {action_data.get('new_status')}")
            elif action_data.get("status") == "rejected":
                print(f"   ❌ {action_data.get('message')}")
                print(f"      ├─ 当前状态: {action_data.get('equipment_status')}")
                print(f"      └─ 需要状态: {', '.join(action_data.get('requires_status', []))}")
            else:
                print(f"   ⚠️ {action_data.get('message')}")
        except Exception as e:
            print(f"   ⚠️ 执行失败: {e}")
    
    save_graph_to_json()
    
    print("\n" + "▌" * 100)
    print("🎨 阶段6: 知识图谱可视化")
    print("▌" * 100)
    
    vis_tool = GenerateGraphVisualizationTool()
    vis_result = await vis_tool._call()
    vis_data = json.loads(vis_result.content[0].text)
    
    print(f"\n📊 可视化数据生成成功:")
    print(f"   - 实例数: {vis_data.get('total_instances')}")
    print(f"   - 关系数: {vis_data.get('total_relations')}")
    print(f"   - 文件: {vis_data.get('visualization_file')}")
    
    print("\n" + "=" * 100)
    print("🎉 MVP6 演示完成！")
    print("=" * 100)
    print("""
📋 演示总结：

1. 📚 本体知识图谱: 预构建的设备、产线、车间实例和关系
2. 🔍 规则校验: 基于本体规则引擎的语义校验
3. 🧠 语义推理: 传递性推理、容量约束、类型兼容性
4. ✅ 审批决策: 基于校验结果的自动审批
5. ⚡ 设备动作: 基于状态机的设备动作执行
6. 📊 图谱更新: 审批和动作执行后自动更新知识图谱

🌐 可视化页面: http://localhost:8080/mvp6/graph_visualization.html
""")

if __name__ == "__main__":
    asyncio.run(run_mvp6_demo())