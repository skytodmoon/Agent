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
    ontology_file = os.path.join(DATA_DIR, "ontology_process.json")
    equipment_file = os.path.join(DATA_DIR, "process_equipment.json")
    units_file = os.path.join(DATA_DIR, "process_units.json")
    
    logger.info("[MVP7 图谱管理器] 初始化预构建流程工业知识图谱...")
    
    graph = OntologyGraph(ontology_file)
    
    with open(equipment_file, 'r', encoding='utf-8') as f:
        equipment_data = json.load(f)
    
    with open(units_file, 'r', encoding='utf-8') as f:
        units_data = json.load(f)
    
    graph.build_from_data(equipment_data, [], units_data)
    
    _add_material_flow_relations(graph)
    graph.infer_transitive_relations()
    
    logger.info(f"[MVP7 图谱管理器] 知识图谱预构建完成: {len(graph.node_properties)} 个实例, {sum(len(rels) for rels in graph.graph.values())} 条关系")
    
    return graph

def _add_material_flow_relations(graph):
    flow_relations = [
        ("TNK-001", "feedsInto", "FLT-001"),
        ("TNK-002", "feedsInto", "FLT-001"),
        ("FLT-001", "feedsInto", "PMP-001"),
        ("FLT-001", "feedsInto", "PMP-002"),
        ("PMP-001", "feedsInto", "HEX-001"),
        ("PMP-002", "feedsInto", "HEX-001"),
        ("HEX-001", "feedsInto", "RCT-001"),
        ("HEX-001", "feedsInto", "RCT-002"),
        ("TNK-004", "feedsInto", "RCT-001"),
        ("TNK-004", "feedsInto", "RCT-002"),
        ("CMP-001", "feedsInto", "RCT-001"),
        ("CMP-001", "feedsInto", "RCT-002"),
        ("RCT-001", "feedsInto", "HEX-002"),
        ("RCT-002", "feedsInto", "HEX-002"),
        ("HEX-002", "feedsInto", "DST-001"),
        ("DST-001", "feedsInto", "FLT-002"),
        ("FLT-002", "feedsInto", "PMP-004"),
        ("PMP-004", "feedsInto", "TNK-003"),
    ]
    
    for subject, predicate, obj in flow_relations:
        try:
            graph.add_relation(subject, predicate, obj)
        except:
            pass

def rebuild_graph():
    global _graph_instance
    _graph_instance = _build_graph()
    return _graph_instance

def simulate_event(equipment_id: str, event_type: str, details: dict = None) -> Dict:
    graph = get_graph()
    
    if equipment_id not in graph.node_properties:
        return {"status": "error", "message": f"设备 {equipment_id} 不存在"}
    
    old_status = graph.get_instance_properties(equipment_id).get("status", "unknown")
    
    status_mapping = {
        "fault": "error",
        "warning": "warning",
        "maintenance": "maintenance",
        "recovery": "normal",
        "stopped": "stopped"
    }
    
    new_status = status_mapping.get(event_type, event_type)
    
    result = graph.update_device_status(equipment_id, new_status)
    
    result.update({
        "event_type": event_type,
        "details": details,
        "impact_analysis": analyze_event_impact(equipment_id, event_type)
    })
    
    save_graph_to_json()
    
    return result

def analyze_event_impact(equipment_id: str, event_type: str) -> Dict:
    graph = get_graph()
    
    downstream_devices = graph.get_downstream_devices(equipment_id, "feedsInto", max_depth=5)
    
    affected_units = []
    for device in downstream_devices:
        props = device.get("properties", {})
        unit_id = props.get("production_unit")
        if unit_id and unit_id not in affected_units:
            affected_units.append(unit_id)
    
    potential_bottlenecks = []
    for device in downstream_devices:
        props = device.get("properties", {})
        if props.get("status") == "warning" or props.get("status") == "error":
            potential_bottlenecks.append(device.get("id"))
    
    alternative_paths = []
    if event_type in ["fault", "warning"]:
        downstream_targets = [d["id"] for d in downstream_devices]
        if downstream_targets:
            for target in downstream_targets[:3]:
                paths = graph.find_paths("TNK-001", target, "feedsInto", max_depth=6)
                if len(paths) > 1:
                    alternative_paths.append({
                        "target": target,
                        "path_count": len(paths),
                        "paths": paths
                    })
    
    return {
        "downstream_devices": downstream_devices,
        "downstream_count": len(downstream_devices),
        "affected_units": affected_units,
        "affected_unit_count": len(affected_units),
        "potential_bottlenecks": potential_bottlenecks,
        "alternative_paths": alternative_paths
    }

def check_process_constraints() -> Dict:
    graph = get_graph()
    
    violations = []
    warnings = []
    
    for instance_id, props in graph.node_properties.items():
        class_name = props.get("__class__")
        
        if class_name == "Tank":
            level = props.get("level", 0)
            if level < 10:
                violations.append({
                    "equipment_id": instance_id,
                    "equipment_name": props.get("equipment_name", instance_id),
                    "constraint": "储罐液位过低",
                    "value": f"{level}%",
                    "threshold": ">10%",
                    "severity": "high"
                })
            elif level > 90:
                violations.append({
                    "equipment_id": instance_id,
                    "equipment_name": props.get("equipment_name", instance_id),
                    "constraint": "储罐液位过高",
                    "value": f"{level}%",
                    "threshold": "<90%",
                    "severity": "high"
                })
            elif level > 85:
                warnings.append({
                    "equipment_id": instance_id,
                    "equipment_name": props.get("equipment_name", instance_id),
                    "constraint": "储罐液位偏高",
                    "value": f"{level}%",
                    "threshold": "<90%",
                    "severity": "medium"
                })
        
        if class_name == "Reactor":
            temp = props.get("operating_temperature", 0)
            pressure = props.get("operating_pressure", 0)
            if temp > 200:
                violations.append({
                    "equipment_id": instance_id,
                    "equipment_name": props.get("equipment_name", instance_id),
                    "constraint": "反应温度过高",
                    "value": f"{temp}°C",
                    "threshold": "<200°C",
                    "severity": "high"
                })
            if pressure > 3.0:
                violations.append({
                    "equipment_id": instance_id,
                    "equipment_name": props.get("equipment_name", instance_id),
                    "constraint": "反应压力过高",
                    "value": f"{pressure}MPa",
                    "threshold": "<3.0MPa",
                    "severity": "high"
                })
        
        if class_name == "Pump":
            discharge = props.get("discharge_pressure", 0)
            suction = props.get("suction_pressure", 0)
            if discharge <= suction and suction > 0:
                violations.append({
                    "equipment_id": instance_id,
                    "equipment_name": props.get("equipment_name", instance_id),
                    "constraint": "泵出口压力异常（小于等于入口压力）",
                    "value": f"出口{discharge}MPa / 入口{suction}MPa",
                    "severity": "high"
                })
    
    return {
        "status": "success",
        "total_violations": len(violations),
        "total_warnings": len(warnings),
        "violations": violations,
        "warnings": warnings
    }

def save_graph_to_json():
    graph = get_graph()
    
    color_map = {
        "Reactor": "#FF6B6B",
        "Tank": "#4ECDC4",
        "Pump": "#FFEAA7",
        "Valve": "#96CEB4",
        "HeatExchanger": "#45B7D1",
        "DistillationColumn": "#DDA0DD",
        "Compressor": "#BB8FCE",
        "Filter": "#FF9FF3",
        "ProductionUnit": "#54A0FF",
        "Workshop": "#5F27CD"
    }
    
    nodes = []
    for instance_id, props in graph.node_properties.items():
        class_name = props.get("__class__", "Equipment")
        node_label = props.get("equipment_name", instance_id)
        
        color = color_map.get(class_name, "#95A5A6")
        
        nodes.append({
            "id": instance_id,
            "label": node_label,
            "type": class_name,
            "color": color,
            "size": 18 if class_name in ["ProductionUnit", "Workshop"] else 15,
            "properties": {k: v for k, v in props.items() if k != "__class__"}
        })
    
    links = []
    for subject, relations in graph.graph.items():
        for predicate, obj in relations:
            links.append({
                "source": subject,
                "target": obj,
                "relation": predicate,
                "relation_label": {"feedsInto": "进料至", "locatedIn": "位于", "belongsTo": "属于", "hasPart": "包含"}.get(predicate, predicate),
                "is_inferred": False
            })
    
    flow_steps = [
        {"path": ["TNK-001", "FLT-001", "PMP-001", "HEX-001", "RCT-001"], "description": "原料储罐→过滤器→进料泵→预热器→反应釜A"},
        {"path": ["TNK-002", "FLT-001", "PMP-002", "HEX-001", "RCT-002"], "description": "原料储罐→过滤器→进料泵→预热器→反应釜B"},
        {"path": ["RCT-001", "HEX-002", "DST-001", "FLT-002", "PMP-004", "TNK-003"], "description": "反应釜→冷凝器→精馏塔→过滤器→输送泵→成品储罐"}
    ]
    
    result = {
        "nodes": nodes,
        "links": links,
        "inference_paths": flow_steps,
        "cross_system_inconsistencies": [],
        "color_map": color_map,
        "type_labels": {
            "Reactor": "反应器",
            "Tank": "储罐",
            "Pump": "泵",
            "Valve": "阀门",
            "HeatExchanger": "换热器",
            "DistillationColumn": "蒸馏塔",
            "Compressor": "压缩机",
            "Filter": "过滤器",
            "ProductionUnit": "生产单元",
            "Workshop": "车间"
        },
        "graph_summary": {
            "total_instances": len(nodes),
            "total_relations": len(links),
            "inferred_count": 0,
            "conflict_count": 0
        }
    }
    
    output_file = os.path.join(DATA_DIR, "graph_process_visualization.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"[MVP7 图谱管理器] 图谱数据已保存到: {output_file}")
    return output_file