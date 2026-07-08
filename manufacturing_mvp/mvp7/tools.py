import json
import os
from agentscope.tool import ToolResponse
from common.base_tool import BaseTool
from agentscope.message import TextBlock
from configs.settings import DATA_DIR
from .graph_manager import get_graph, simulate_event, analyze_event_impact, check_process_constraints, save_graph_to_json

class ProcessGraphQueryTool(BaseTool):
    name: str = "process_graph_query"
    description: str = "查询流程工业知识图谱中的设备节点、关系、物料流向路径等信息"
    input_schema = {
        "type": "object",
        "properties": {
            "query_type": {"type": "string", "description": "查询类型：nodes_by_class/traverse/downstream/flow_paths/equipment_status"},
            "class_name": {"type": "string", "description": "类名，用于按类查询节点"},
            "start_node": {"type": "string", "description": "起始节点ID，用于遍历和下游查询"},
            "equipment_id": {"type": "string", "description": "设备ID，用于查询状态"}
        },
        "description": "查询流程工业知识图谱"
    }
    
    async def _call(self, query_type: str = "nodes_by_class", class_name: str = None, 
                    start_node: str = None, equipment_id: str = None) -> ToolResponse:
        graph = get_graph()
        
        result = {}
        
        try:
            if query_type == "nodes_by_class":
                nodes = graph.get_instances_by_class(class_name) if class_name else []
                result = {
                    "query_type": "nodes_by_class",
                    "class_name": class_name,
                    "count": len(nodes),
                    "nodes": nodes
                }
            
            elif query_type == "traverse":
                nodes = graph.traverse(start_node, max_depth=3)
                result = {
                    "query_type": "traverse",
                    "start_node": start_node,
                    "count": len(nodes),
                    "nodes": nodes
                }
            
            elif query_type == "downstream":
                devices = graph.get_downstream_devices(start_node, "feedsInto", max_depth=5)
                result = {
                    "query_type": "downstream",
                    "start_node": start_node,
                    "downstream_count": len(devices),
                    "downstream_devices": devices
                }
            
            elif query_type == "flow_paths":
                paths = []
                tank_nodes = graph.get_instances_by_class("Tank")
                for tank in tank_nodes[:2]:
                    tank_id = tank.get("id")
                    downstream = graph.get_downstream_devices(tank_id, "feedsInto", max_depth=5)
                    if downstream:
                        paths.append({
                            "source": tank_id,
                            "source_name": tank.get("equipment_name", tank_id),
                            "path": [d["id"] for d in downstream],
                            "description": f"{tank.get('equipment_name', tank_id)} → {' → '.join(d.get('properties', {}).get('equipment_name', d['id']) for d in downstream)}"
                        })
                result = {
                    "query_type": "flow_paths",
                    "flow_paths": paths
                }
            
            elif query_type == "equipment_status":
                props = graph.get_instance_properties(equipment_id)
                downstream = graph.get_downstream_devices(equipment_id, "feedsInto", max_depth=3)
                result = {
                    "query_type": "equipment_status",
                    "equipment_id": equipment_id,
                    "properties": props,
                    "downstream_count": len(downstream),
                    "downstream_devices": downstream
                }
            
            else:
                result = {"error": f"未知查询类型: {query_type}"}
            
            result["status"] = "success"
        except Exception as e:
            result = {
                "status": "error",
                "message": str(e)
            }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class ProcessEventTool(BaseTool):
    name: str = "process_event"
    description: str = "处理流程工业事件，包括设备故障、告警、维护等，更新图谱状态并分析影响"
    input_schema = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "设备ID"},
            "event_type": {"type": "string", "description": "事件类型：fault/warning/maintenance/recovery/stopped"},
            "details": {"type": "object", "description": "事件详情"}
        },
        "required": ["equipment_id", "event_type"],
        "description": "处理流程工业事件"
    }
    
    async def _call(self, equipment_id: str, event_type: str, details: dict = None) -> ToolResponse:
        result = simulate_event(equipment_id, event_type, details)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class ImpactAnalysisTool(BaseTool):
    name: str = "impact_analysis"
    description: str = "分析设备异常事件对下游设备和工艺的影响，包括物料流向中断、工艺约束违规等"
    input_schema = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "设备ID"},
            "event_type": {"type": "string", "description": "事件类型"}
        },
        "required": ["equipment_id"],
        "description": "分析事件影响"
    }
    
    async def _call(self, equipment_id: str, event_type: str = "fault") -> ToolResponse:
        impact = analyze_event_impact(equipment_id, event_type)
        
        result = {
            "equipment_id": equipment_id,
            "event_type": event_type,
            **impact
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class ProcessConstraintCheckTool(BaseTool):
    name: str = "process_constraint_check"
    description: str = "检查工艺约束，包括温度、压力、液位等参数是否在安全范围内"
    input_schema = {
        "type": "object",
        "properties": {},
        "description": "检查工艺约束"
    }
    
    async def _call(self) -> ToolResponse:
        result = check_process_constraints()
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class GenerateProcessGraphVisualizationTool(BaseTool):
    name: str = "generate_process_graph_visualization"
    description: str = "生成流程工业知识图谱可视化数据"
    input_schema = {
        "type": "object",
        "properties": {},
        "description": "生成流程工业图谱可视化数据"
    }
    
    async def _call(self) -> ToolResponse:
        save_graph_to_json()
        
        graph = get_graph()
        summary = {
            "status": "success",
            "total_instances": len(graph.node_properties),
            "total_relations": sum(len(rels) for rels in graph.graph.values()),
            "visualization_file": "graph_process_visualization.json"
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(summary, ensure_ascii=False))])

class GenerateEmergencyResponseTool(BaseTool):
    name: str = "generate_emergency_response"
    description: str = "根据设备异常事件和影响分析生成应急预案和操作建议"
    input_schema = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "设备ID"},
            "event_type": {"type": "string", "description": "事件类型"},
            "impact_analysis": {"type": "object", "description": "影响分析结果"}
        },
        "required": ["equipment_id"],
        "description": "生成应急预案"
    }
    
    async def _call(self, equipment_id: str, event_type: str = "fault", impact_analysis: dict = None) -> ToolResponse:
        graph = get_graph()
        props = graph.get_instance_properties(equipment_id)
        equipment_name = props.get("equipment_name", equipment_id)
        equipment_type = props.get("__class__", "Equipment")
        
        if not impact_analysis:
            impact_analysis = analyze_event_impact(equipment_id, event_type)
        
        downstream_count = impact_analysis.get("downstream_count", 0)
        affected_units = impact_analysis.get("affected_units", [])
        potential_bottlenecks = impact_analysis.get("potential_bottlenecks", [])
        alternative_paths = impact_analysis.get("alternative_paths", [])
        
        response = {
            "equipment_id": equipment_id,
            "equipment_name": equipment_name,
            "equipment_type": equipment_type,
            "event_type": event_type,
            "impact_summary": {
                "downstream_devices_affected": downstream_count,
                "production_units_affected": len(affected_units),
                "potential_bottlenecks": potential_bottlenecks
            },
            "emergency_measures": [],
            "operational_adjustments": [],
            "maintenance_actions": [],
            "monitoring_suggestions": []
        }
        
        if event_type == "fault":
            response["emergency_measures"] = [
                f"立即启动设备 {equipment_name} 的备用设备",
                f"通知工艺工程师评估工艺参数调整方案",
                f"关闭相关阀门防止物料泄漏或回流",
                f"启动应急预案，通知相关岗位人员"
            ]
            
            if downstream_count > 0:
                response["operational_adjustments"] = [
                    f"降低下游设备负荷，避免连锁故障",
                    f"调整物料流向，启用备用路径"
                ]
            
            if alternative_paths:
                response["operational_adjustments"].append(
                    f"检测到 {len(alternative_paths)} 条备用路径，建议启用替代路线"
                )
        
        elif event_type == "warning":
            response["emergency_measures"] = [
                f"加强设备 {equipment_name} 的监控频率",
                f"准备备用设备待命"
            ]
            response["maintenance_actions"] = [
                f"安排预防性维护，检查设备状态"
            ]
        
        elif event_type == "maintenance":
            response["operational_adjustments"] = [
                f"切换至备用设备或工艺路线",
                f"调整生产计划，预留维护时间"
            ]
            response["monitoring_suggestions"] = [
                f"密切监控备用设备运行状态"
            ]
        
        response["maintenance_actions"].extend([
            f"生成维修工单，指派工程师处理",
            f"记录故障原因，更新设备维护档案"
        ])
        
        response["monitoring_suggestions"].extend([
            f"持续监控下游设备运行状态",
            f"跟踪工艺参数变化趋势",
            f"定期检查类似设备状态"
        ])
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(response, ensure_ascii=False))])