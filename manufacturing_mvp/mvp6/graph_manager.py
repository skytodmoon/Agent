import json
import os
import logging
from common.ontology_graph import OntologyGraph
from configs.settings import DATA_DIR

logger = logging.getLogger(__name__)

_graph_instance = None

def get_graph():
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = _build_graph()
    return _graph_instance

def _build_graph():
    ontology_file = os.path.join(DATA_DIR, "ontology.json")
    mes_file = os.path.join(DATA_DIR, "mes_equipment.json")
    erp_file = os.path.join(DATA_DIR, "erp_equipment.json")
    production_units_file = os.path.join(DATA_DIR, "production_units.json")
    
    logger.info("[MVP6 图谱管理器] 初始化预构建知识图谱...")
    
    graph = OntologyGraph(ontology_file)
    
    with open(mes_file, 'r', encoding='utf-8') as f:
        mes_data = json.load(f)
    
    with open(erp_file, 'r', encoding='utf-8') as f:
        erp_data = json.load(f)
    
    with open(production_units_file, 'r', encoding='utf-8') as f:
        production_units = json.load(f)
    
    graph.build_from_data(mes_data, erp_data, production_units)
    graph.infer_transitive_relations()
    
    logger.info(f"[MVP6 图谱管理器] 知识图谱预构建完成: {len(graph.node_properties)} 个实例, {sum(len(rels) for rels in graph.graph.values())} 条关系")
    
    return graph

def rebuild_graph():
    global _graph_instance
    _graph_instance = _build_graph()
    return _graph_instance

def _get_actions_for_device(equipment_type: str, status: str) -> list:
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

def save_graph_to_json():
    graph = get_graph()
    
    nodes = []
    for instance_id, props in graph.node_properties.items():
        class_name = props.get("__class__")
        status = props.get("status", "unknown")
        
        node_data = {
            "id": instance_id,
            "class": class_name,
            "properties": {k: v for k, v in props.items() if k != "__class__"}
        }
        
        if class_name in ["CNCMachine", "Lathe", "MillingMachine", "Robot", "Conveyor", "Equipment"]:
            actions = _get_actions_for_device(class_name, status)
            node_data["properties"]["actions"] = actions
        
        nodes.append(node_data)
    
    links = []
    for subject, relations in graph.graph.items():
        for predicate, obj in relations:
            links.append({
                "source": subject,
                "target": obj,
                "relation": predicate
            })
    
    result = {
        "nodes": nodes,
        "links": links,
        "total_instances": len(nodes),
        "total_relations": len(links)
    }
    
    output_file = os.path.join(DATA_DIR, "graph_mvp6.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"[MVP6 图谱管理器] 图谱数据已保存到: {output_file}")
    return output_file