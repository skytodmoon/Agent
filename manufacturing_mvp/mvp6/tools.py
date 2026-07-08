import json
import os
import uuid
from agentscope.tool import ToolResponse
from common.base_tool import BaseTool
from agentscope.message import TextBlock
from configs.settings import DATA_DIR
from .graph_manager import get_graph, save_graph_to_json

class QueryRegistrationRequestsTool(BaseTool):
    name: str = "query_registration_requests"
    description: str = "查询待审核的设备注册请求列表"
    input_schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "请求状态筛选：pending/approved/rejected"},
            "limit": {"type": "integer", "description": "返回数量限制"}
        },
        "description": "查询设备注册请求"
    }
    
    async def _call(self, status: str = "pending", limit: int = 10) -> ToolResponse:
        requests_file = os.path.join(DATA_DIR, "device_registration_requests.json")
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        if status != "all":
            requests = [r for r in requests if r.get("request_status", "pending") == status]
        
        requests = requests[:limit]
        
        result = {
            "total_count": len(requests),
            "requests": requests
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class GraphQueryTool(BaseTool):
    name: str = "graph_query"
    description: str = "查询知识图谱中的节点和关系，支持按类名、属性筛选、关系遍历等查询操作"
    input_schema = {
        "type": "object",
        "properties": {
            "query_type": {"type": "string", "description": "查询类型：nodes_by_class/nodes_by_property/traverse/line_capacity/type_compatibility"},
            "class_name": {"type": "string", "description": "类名，用于按类查询节点"},
            "property_filter": {"type": "object", "description": "属性筛选条件"},
            "start_node": {"type": "string", "description": "起始节点ID，用于遍历查询"},
            "relation_type": {"type": "string", "description": "关系类型过滤"},
            "production_line": {"type": "string", "description": "产线ID，用于容量查询"},
            "equipment_type": {"type": "string", "description": "设备类型，用于兼容性查询"}
        },
        "description": "查询知识图谱"
    }
    
    async def _call(self, query_type: str = "nodes_by_class", class_name: str = None, 
                    property_filter: dict = None, start_node: str = None, 
                    relation_type: str = None, production_line: str = None,
                    equipment_type: str = None) -> ToolResponse:
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
            
            elif query_type == "nodes_by_property":
                nodes = graph.query_nodes(property_filter=property_filter or {})
                result = {
                    "query_type": "nodes_by_property",
                    "property_filter": property_filter,
                    "count": len(nodes),
                    "nodes": nodes
                }
            
            elif query_type == "traverse":
                nodes = graph.traverse(start_node, relation_type, max_depth=3)
                result = {
                    "query_type": "traverse",
                    "start_node": start_node,
                    "relation_type": relation_type,
                    "count": len(nodes),
                    "nodes": nodes
                }
            
            elif query_type == "line_capacity":
                capacity_info = graph.get_production_line_capacity(production_line)
                result = {
                    "query_type": "line_capacity",
                    **capacity_info
                }
            
            elif query_type == "type_compatibility":
                compatibility = graph.check_type_compatibility(equipment_type, production_line)
                result = {
                    "query_type": "type_compatibility",
                    **compatibility
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

class ValidateRegistrationRequestTool(BaseTool):
    name: str = "validate_registration_request"
    description: str = "基于预构建的知识图谱校验设备注册请求，执行本体规则引擎进行语义推理判定"
    input_schema = {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "注册请求ID"}
        },
        "required": ["request_id"],
        "description": "校验设备注册请求"
    }
    
    async def _call(self, request_id: str) -> ToolResponse:
        requests_file = os.path.join(DATA_DIR, "device_registration_requests.json")
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request_data = next((r for r in requests if r["request_id"] == request_id), None)
        
        if not request_data:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "error": f"未找到请求ID: {request_id}"
            }, ensure_ascii=False))])
        
        graph = get_graph()
        validation_result = graph.validate_device_registration(request_data)
        
        production_line = request_data.get("production_line")
        if production_line:
            capacity_info = graph.get_production_line_capacity(production_line)
            validation_result["capacity_info"] = capacity_info
        
        equipment_type = request_data.get("equipment_type")
        if equipment_type and production_line:
            compatibility = graph.check_type_compatibility(equipment_type, production_line)
            validation_result["compatibility_check"] = compatibility
        
        result = {
            "request_id": request_id,
            "equipment_id": request_data.get("equipment_id"),
            "equipment_name": request_data.get("equipment_name"),
            "equipment_type": request_data.get("equipment_type"),
            **validation_result
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class ApproveRegistrationTool(BaseTool):
    name: str = "approve_registration"
    description: str = "批准设备注册请求，更新知识图谱添加新设备节点和关系，同步至MES/ERP系统"
    input_schema = {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "注册请求ID"},
            "approval_comment": {"type": "string", "description": "审批意见"}
        },
        "required": ["request_id"],
        "description": "批准设备注册"
    }
    
    async def _call(self, request_id: str, approval_comment: str = "") -> ToolResponse:
        requests_file = os.path.join(DATA_DIR, "device_registration_requests.json")
        mes_file = os.path.join(DATA_DIR, "mes_equipment.json")
        erp_file = os.path.join(DATA_DIR, "erp_equipment.json")
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request_idx = next((i for i, r in enumerate(requests) if r["request_id"] == request_id), -1)
        
        if request_idx == -1:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "error": f"未找到请求ID: {request_id}"
            }, ensure_ascii=False))])
        
        request_data = requests[request_idx]
        equipment_id = request_data["equipment_id"]
        
        requests[request_idx]["request_status"] = "approved"
        requests[request_idx]["approved_at"] = "2026-07-08"
        requests[request_idx]["approval_comment"] = approval_comment
        
        with open(requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
        
        mes_data = {
            "equipment_id": request_data["equipment_id"],
            "equipment_name": request_data["equipment_name"],
            "equipment_type": request_data["equipment_type"],
            "location": request_data["location"],
            "status": "normal",
            "manufacturer": request_data.get("manufacturer", ""),
            "model": request_data.get("model", ""),
            "production_line": request_data.get("production_line", ""),
            "workshop": request_data.get("workshop", "")
        }
        
        for key in ["spindle_speed", "tool_count", "axis_count", "max_diameter", "max_length", 
                    "spindle_taper", "table_size", "payload", "reach", "length", "speed", "capacity"]:
            if key in request_data:
                mes_data[key] = request_data[key]
        
        with open(mes_file, 'r', encoding='utf-8') as f:
            mes_equipment = json.load(f)
        mes_equipment.append(mes_data)
        with open(mes_file, 'w', encoding='utf-8') as f:
            json.dump(mes_equipment, f, ensure_ascii=False, indent=2)
        
        type_mapping = {"CNCMachine": "数控机床", "Lathe": "车床", "MillingMachine": "铣床", 
                        "Robot": "工业机器人", "Conveyor": "传送带", "Equipment": "设备"}
        
        erp_data = {
            "equipment_code": request_data["equipment_id"],
            "equipment_name": request_data["equipment_name"],
            "equipment_type": type_mapping.get(request_data["equipment_type"], request_data["equipment_type"]),
            "department": request_data.get("workshop", ""),
            "status": "运行中",
            "brand": request_data.get("manufacturer", ""),
            "model_no": request_data.get("model", ""),
            "purchase_date": "2026-07-08",
            "installation_date": "2026-07-08",
            "asset_value": 0,
            "maintenance_cycle": 30,
            "assigned_line": request_data.get("production_line", "")
        }
        
        with open(erp_file, 'r', encoding='utf-8') as f:
            erp_equipment = json.load(f)
        erp_equipment.append(erp_data)
        with open(erp_file, 'w', encoding='utf-8') as f:
            json.dump(erp_equipment, f, ensure_ascii=False, indent=2)
        
        graph = get_graph()
        graph_result = graph.add_new_device(request_data)
        
        save_graph_to_json()
        
        work_order_id = f"WO-{uuid.uuid4().hex[:8].upper()}"
        
        result = {
            "status": "approved",
            "request_id": request_id,
            "equipment_id": equipment_id,
            "work_order_id": work_order_id,
            "message": f"设备注册申请已批准，工单 {work_order_id} 已生成",
            "graph_update": graph_result,
            "synced_to_mes": True,
            "synced_to_erp": True,
            "approval_comment": approval_comment
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class RejectRegistrationTool(BaseTool):
    name: str = "reject_registration"
    description: str = "拒绝设备注册请求，记录拒绝原因"
    input_schema = {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "注册请求ID"},
            "reject_reason": {"type": "string", "description": "拒绝原因"}
        },
        "required": ["request_id"],
        "description": "拒绝设备注册"
    }
    
    async def _call(self, request_id: str, reject_reason: str = "") -> ToolResponse:
        requests_file = os.path.join(DATA_DIR, "device_registration_requests.json")
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request_idx = next((i for i, r in enumerate(requests) if r["request_id"] == request_id), -1)
        
        if request_idx == -1:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "error": f"未找到请求ID: {request_id}"
            }, ensure_ascii=False))])
        
        requests[request_idx]["request_status"] = "rejected"
        requests[request_idx]["rejected_at"] = "2026-07-08"
        requests[request_idx]["reject_reason"] = reject_reason
        
        with open(requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
        
        result = {
            "status": "rejected",
            "request_id": request_id,
            "message": "设备注册申请已拒绝",
            "reject_reason": reject_reason
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class DetectInconsistenciesTool(BaseTool):
    name: str = "detect_inconsistencies"
    description: str = "基于知识图谱检测MES/ERP跨系统数据不一致问题"
    input_schema = {
        "type": "object",
        "properties": {},
        "description": "检测跨系统数据不一致"
    }
    
    async def _call(self) -> ToolResponse:
        graph = get_graph()
        inconsistencies = graph.detect_cross_system_inconsistencies()
        
        result = {
            "status": "success",
            "total_inconsistencies": len(inconsistencies),
            "inconsistencies": inconsistencies
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class GenerateGraphVisualizationTool(BaseTool):
    name: str = "generate_graph_visualization"
    description: str = "生成知识图谱可视化数据，包含节点、关系、推理路径和不一致信息"
    input_schema = {
        "type": "object",
        "properties": {},
        "description": "生成图谱可视化数据"
    }
    
    def _get_actions_for_device(self, equipment_type: str, status: str) -> list:
        action_templates = {
            "CNCMachine": [
                {"name": "start_production", "label": "启动生产", "description": "启动数控加工程序", "requires_status": ["normal"]},
                {"name": "stop_production", "label": "停止生产", "description": "停止数控加工程序", "requires_status": ["normal", "warning"]},
                {"name": "start_maintenance", "label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"]},
                {"name": "reset_error", "label": "重置错误", "description": "清除故障状态", "requires_status": ["error"]},
                {"name": "change_tool", "label": "更换刀具", "description": "更换加工刀具", "requires_status": ["normal", "maintenance"]},
                {"name": "calibrate", "label": "校准", "description": "执行设备校准", "requires_status": ["normal", "maintenance"]}
            ],
            "Lathe": [
                {"name": "start_production", "label": "启动生产", "description": "启动车削程序", "requires_status": ["normal"]},
                {"name": "stop_production", "label": "停止生产", "description": "停止车削程序", "requires_status": ["normal", "warning"]},
                {"name": "start_maintenance", "label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"]},
                {"name": "reset_error", "label": "重置错误", "description": "清除故障状态", "requires_status": ["error"]},
                {"name": "change_chuck", "label": "更换卡盘", "description": "更换工件卡盘", "requires_status": ["maintenance"]}
            ],
            "MillingMachine": [
                {"name": "start_production", "label": "启动生产", "description": "启动铣削程序", "requires_status": ["normal"]},
                {"name": "stop_production", "label": "停止生产", "description": "停止铣削程序", "requires_status": ["normal", "warning"]},
                {"name": "start_maintenance", "label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"]},
                {"name": "reset_error", "label": "重置错误", "description": "清除故障状态", "requires_status": ["error"]},
                {"name": "change_spindle", "label": "更换主轴", "description": "更换铣削主轴", "requires_status": ["maintenance"]}
            ],
            "Robot": [
                {"name": "start_task", "label": "启动任务", "description": "启动机器人作业任务", "requires_status": ["normal"]},
                {"name": "stop_task", "label": "停止任务", "description": "停止机器人作业任务", "requires_status": ["normal", "warning"]},
                {"name": "start_maintenance", "label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"]},
                {"name": "reset_error", "label": "重置错误", "description": "清除故障状态", "requires_status": ["error"]},
                {"name": "teach_mode", "label": "示教模式", "description": "进入示教编程模式", "requires_status": ["normal", "maintenance"]},
                {"name": "calibrate_joints", "label": "关节校准", "description": "执行关节精度校准", "requires_status": ["maintenance"]}
            ],
            "Conveyor": [
                {"name": "start_convey", "label": "启动输送", "description": "启动传送带", "requires_status": ["normal"]},
                {"name": "stop_convey", "label": "停止输送", "description": "停止传送带", "requires_status": ["normal", "warning"]},
                {"name": "start_maintenance", "label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"]},
                {"name": "reset_error", "label": "重置错误", "description": "清除故障状态", "requires_status": ["error"]},
                {"name": "adjust_speed", "label": "调整速度", "description": "调整传送带速度", "requires_status": ["normal"]}
            ],
            "Equipment": [
                {"name": "start_maintenance", "label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"]},
                {"name": "reset_error", "label": "重置错误", "description": "清除故障状态", "requires_status": ["error"]},
                {"name": "check_status", "label": "状态检查", "description": "检查设备当前状态", "requires_status": ["normal", "warning", "error", "maintenance"]}
            ]
        }
        
        templates = action_templates.get(equipment_type, action_templates["Equipment"])
        
        available_actions = []
        for action in templates:
            if status in action["requires_status"]:
                available_actions.append({
                    "name": action["name"],
                    "label": action["label"],
                    "description": action["description"],
                    "available": True
                })
            else:
                available_actions.append({
                    "name": action["name"],
                    "label": action["label"],
                    "description": action["description"],
                    "available": False,
                    "reason": f"当前状态 '{status}' 不允许此操作，需要状态: {', '.join(action['requires_status'])}"
                })
        
        return available_actions
    
    async def _call(self) -> ToolResponse:
        graph = get_graph()
        
        color_map = {
            "CNCMachine": "#3498DB",
            "Lathe": "#E74C3C",
            "MillingMachine": "#2ECC71",
            "Robot": "#9B59B6",
            "Conveyor": "#F39C12",
            "Equipment": "#95A5A6",
            "ProductionLine": "#1ABC9C",
            "Workshop": "#34495E",
            "MaintenanceTask": "#E91E63"
        }
        
        type_labels = {
            "CNCMachine": "数控机床",
            "Lathe": "车床",
            "MillingMachine": "铣床",
            "Robot": "工业机器人",
            "Conveyor": "传送带",
            "Equipment": "设备",
            "ProductionLine": "产线",
            "Workshop": "车间",
            "MaintenanceTask": "维护任务"
        }
        
        nodes = []
        for instance_id, props in graph.node_properties.items():
            class_name = props.get("__class__", "Equipment")
            is_erp = instance_id.startswith("ERP_")
            status = props.get("status", "unknown")
            
            node_label = props.get("equipment_name", instance_id)
            if is_erp:
                node_label = f"ERP:{props.get('equipment_name', instance_id.replace('ERP_', ''))}"
            
            color = color_map.get(class_name, "#95A5A6")
            size = 20 if class_name in ["ProductionLine", "Workshop"] else 15
            
            node_data = {
                "id": instance_id,
                "label": node_label,
                "type": class_name,
                "color": color,
                "size": size,
                "is_erp": is_erp,
                "properties": {k: v for k, v in props.items() if k != "__class__"}
            }
            
            if class_name in ["CNCMachine", "Lathe", "MillingMachine", "Robot", "Conveyor", "Equipment"]:
                actions = self._get_actions_for_device(class_name, status)
                node_data["properties"]["actions"] = actions
            
            nodes.append(node_data)
        
        links = []
        for subject, relations in graph.graph.items():
            for predicate, obj in relations:
                links.append({
                    "source": subject,
                    "target": obj,
                    "relation": predicate,
                    "is_inferred": False
                })
        
        cross_system_inconsistencies = graph.detect_cross_system_inconsistencies()
        
        result = {
            "status": "success",
            "nodes": nodes,
            "links": links,
            "inferred_relations": [],
            "inference_paths": [],
            "cross_system_inconsistencies": cross_system_inconsistencies,
            "color_map": color_map,
            "type_labels": type_labels,
            "graph_summary": {
                "total_instances": len(graph.node_properties),
                "total_relations": sum(len(rels) for rels in graph.graph.values()),
                "inferred_count": 0,
                "conflict_count": len(cross_system_inconsistencies)
            }
        }
        
        visualization_file = os.path.join(DATA_DIR, "graph_visualization.json")
        with open(visualization_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        summary = {
            "status": "success",
            "total_instances": len(graph.node_properties),
            "total_relations": sum(len(rels) for rels in graph.graph.values()),
            "visualization_file": "graph_visualization.json"
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(summary, ensure_ascii=False))])

class ExecuteDeviceActionTool(BaseTool):
    name: str = "execute_device_action"
    description: str = "执行设备动作，如启动生产、停止生产、开始维护、重置错误等，根据设备当前状态判断动作是否可执行"
    input_schema = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "设备ID"},
            "action_name": {"type": "string", "description": "动作名称：start_production/stop_production/start_maintenance/reset_error/change_tool/calibrate等"}
        },
        "required": ["equipment_id", "action_name"],
        "description": "执行设备动作"
    }
    
    async def _call(self, equipment_id: str, action_name: str) -> ToolResponse:
        graph = get_graph()
        
        if equipment_id not in graph.node_properties:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "status": "error",
                "message": f"设备 {equipment_id} 不存在于知识图谱中"
            }, ensure_ascii=False))])
        
        props = graph.get_instance_properties(equipment_id)
        equipment_type = props.get("__class__")
        current_status = props.get("status", "unknown")
        
        action_templates = {
            "CNCMachine": {
                "start_production": {"label": "启动生产", "description": "启动数控加工程序", "requires_status": ["normal"], "new_status": "normal"},
                "stop_production": {"label": "停止生产", "description": "停止数控加工程序", "requires_status": ["normal", "warning"], "new_status": "normal"},
                "start_maintenance": {"label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"], "new_status": "maintenance"},
                "reset_error": {"label": "重置错误", "description": "清除故障状态", "requires_status": ["error"], "new_status": "normal"},
                "change_tool": {"label": "更换刀具", "description": "更换加工刀具", "requires_status": ["normal", "maintenance"], "new_status": "normal"},
                "calibrate": {"label": "校准", "description": "执行设备校准", "requires_status": ["normal", "maintenance"], "new_status": "normal"}
            },
            "Lathe": {
                "start_production": {"label": "启动生产", "description": "启动车削程序", "requires_status": ["normal"], "new_status": "normal"},
                "stop_production": {"label": "停止生产", "description": "停止车削程序", "requires_status": ["normal", "warning"], "new_status": "normal"},
                "start_maintenance": {"label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"], "new_status": "maintenance"},
                "reset_error": {"label": "重置错误", "description": "清除故障状态", "requires_status": ["error"], "new_status": "normal"},
                "change_chuck": {"label": "更换卡盘", "description": "更换工件卡盘", "requires_status": ["maintenance"], "new_status": "normal"}
            },
            "MillingMachine": {
                "start_production": {"label": "启动生产", "description": "启动铣削程序", "requires_status": ["normal"], "new_status": "normal"},
                "stop_production": {"label": "停止生产", "description": "停止铣削程序", "requires_status": ["normal", "warning"], "new_status": "normal"},
                "start_maintenance": {"label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"], "new_status": "maintenance"},
                "reset_error": {"label": "重置错误", "description": "清除故障状态", "requires_status": ["error"], "new_status": "normal"},
                "change_spindle": {"label": "更换主轴", "description": "更换铣削主轴", "requires_status": ["maintenance"], "new_status": "normal"}
            },
            "Robot": {
                "start_task": {"label": "启动任务", "description": "启动机器人作业任务", "requires_status": ["normal"], "new_status": "normal"},
                "stop_task": {"label": "停止任务", "description": "停止机器人作业任务", "requires_status": ["normal", "warning"], "new_status": "normal"},
                "start_maintenance": {"label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"], "new_status": "maintenance"},
                "reset_error": {"label": "重置错误", "description": "清除故障状态", "requires_status": ["error"], "new_status": "normal"},
                "teach_mode": {"label": "示教模式", "description": "进入示教编程模式", "requires_status": ["normal", "maintenance"], "new_status": "maintenance"},
                "calibrate_joints": {"label": "关节校准", "description": "执行关节精度校准", "requires_status": ["maintenance"], "new_status": "normal"}
            },
            "Conveyor": {
                "start_convey": {"label": "启动输送", "description": "启动传送带", "requires_status": ["normal"], "new_status": "normal"},
                "stop_convey": {"label": "停止输送", "description": "停止传送带", "requires_status": ["normal", "warning"], "new_status": "normal"},
                "start_maintenance": {"label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"], "new_status": "maintenance"},
                "reset_error": {"label": "重置错误", "description": "清除故障状态", "requires_status": ["error"], "new_status": "normal"},
                "adjust_speed": {"label": "调整速度", "description": "调整传送带速度", "requires_status": ["normal"], "new_status": "normal"}
            },
            "Equipment": {
                "start_maintenance": {"label": "开始维护", "description": "进入维护模式", "requires_status": ["normal", "warning", "error"], "new_status": "maintenance"},
                "reset_error": {"label": "重置错误", "description": "清除故障状态", "requires_status": ["error"], "new_status": "normal"},
                "check_status": {"label": "状态检查", "description": "检查设备当前状态", "requires_status": ["normal", "warning", "error", "maintenance"], "new_status": current_status}
            }
        }
        
        templates = action_templates.get(equipment_type, action_templates["Equipment"])
        
        if action_name not in templates:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "status": "error",
                "message": f"动作 '{action_name}' 不支持设备类型 {equipment_type}",
                "supported_actions": list(templates.keys())
            }, ensure_ascii=False))])
        
        action_info = templates[action_name]
        
        if current_status not in action_info["requires_status"]:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "status": "rejected",
                "message": f"动作 '{action_info['label']}' 当前不可执行",
                "reason": f"设备当前状态 '{current_status}' 不允许此操作",
                "requires_status": action_info["requires_status"],
                "equipment_status": current_status
            }, ensure_ascii=False))])
        
        graph.update_device_status(equipment_id, action_info["new_status"])
        save_graph_to_json()
        
        result = {
            "status": "success",
            "equipment_id": equipment_id,
            "equipment_name": props.get("equipment_name", equipment_id),
            "equipment_type": equipment_type,
            "action_name": action_name,
            "action_label": action_info["label"],
            "action_description": action_info["description"],
            "previous_status": current_status,
            "new_status": action_info["new_status"],
            "message": f"设备 {equipment_id} 已执行动作 '{action_info['label']}'，状态从 '{current_status}' 变为 '{action_info['new_status']}'"
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False))])

class GenerateApprovalReportTool(BaseTool):
    name: str = "generate_approval_report"
    description: str = "生成设备注册审批报告，包含审批流程、校验结果和知识图谱推理详情"
    input_schema = {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "注册请求ID"}
        },
        "description": "生成审批报告"
    }
    
    async def _call(self, request_id: str = None) -> ToolResponse:
        requests_file = os.path.join(DATA_DIR, "device_registration_requests.json")
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        if request_id:
            filtered_requests = [r for r in requests if r["request_id"] == request_id]
        else:
            filtered_requests = requests
        
        graph = get_graph()
        
        report = {
            "report_id": f"RPT-{uuid.uuid4().hex[:8].upper()}",
            "generated_at": "2026-07-08",
            "total_requests": len(filtered_requests),
            "approved_count": len([r for r in filtered_requests if r.get("request_status") == "approved"]),
            "rejected_count": len([r for r in filtered_requests if r.get("request_status") == "rejected"]),
            "pending_count": len([r for r in filtered_requests if r.get("request_status") == "pending"]),
            "graph_summary": {
                "total_instances": len(graph.node_properties),
                "total_relations": sum(len(rels) for rels in graph.graph.values())
            },
            "requests": filtered_requests
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(report, ensure_ascii=False))])