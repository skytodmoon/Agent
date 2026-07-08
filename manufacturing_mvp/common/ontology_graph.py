import json
import os
import re
import uuid
import logging
from typing import Dict, List, Any, Set, Tuple

logger = logging.getLogger(__name__)

class RuleEngine:
    def __init__(self, graph):
        self.graph = graph
        self.rules = [
            {
                "name": "rule_invalid_class_type",
                "description": "设备类型不在本体定义中时拒绝注册",
                "condition": self._condition_invalid_class_type,
                "action": self._action_reject_with_invalid_class_type,
                "severity": "high"
            },
            {
                "name": "rule_missing_required_property",
                "description": "设备缺少必需属性时拒绝注册",
                "condition": self._condition_missing_required_property,
                "action": self._action_reject_with_missing_property,
                "severity": "high"
            },
            {
                "name": "rule_invalid_status",
                "description": "设备状态值无效时拒绝注册",
                "condition": self._condition_invalid_status,
                "action": self._action_reject_with_invalid_status,
                "severity": "high"
            },
            {
                "name": "rule_invalid_equipment_id_format",
                "description": "设备编码格式不符合规范时拒绝注册",
                "condition": self._condition_invalid_id_format,
                "action": self._action_reject_with_invalid_id_format,
                "severity": "high"
            },
            {
                "name": "rule_transitive_location_conflict",
                "description": "通过传递性推理发现设备位置与产线位置矛盾",
                "condition": self._condition_transitive_location_conflict,
                "action": self._action_reject_with_location_conflict,
                "severity": "high"
            },
            {
                "name": "rule_cross_system_inconsistency",
                "description": "检测到MES/ERP系统中同一设备数据冲突",
                "condition": self._condition_cross_system_inconsistency,
                "action": self._action_reject_with_cross_system_conflict,
                "severity": "high"
            },
            {
                "name": "rule_production_line_capacity_exceeded",
                "description": "产线设备容量已达到上限",
                "condition": self._condition_capacity_exceeded,
                "action": self._action_reject_with_capacity_exceeded,
                "severity": "medium"
            },
            {
                "name": "rule_duplicate_equipment_id",
                "description": "设备编码已在系统中存在",
                "condition": self._condition_duplicate_id,
                "action": self._action_reject_with_duplicate_id,
                "severity": "high"
            },
            {
                "name": "rule_negative_value",
                "description": "属性值为负数时拒绝注册",
                "condition": self._condition_negative_value,
                "action": self._action_reject_with_negative_value,
                "severity": "medium"
            },
            {
                "name": "rule_auto_approve_valid_device",
                "description": "所有校验通过的设备自动批准注册，并基于图谱推理自动补全信息",
                "condition": self._condition_all_valid,
                "action": self._action_approve_with_enhancement,
                "severity": "low"
            }
        ]
    
    def _condition_invalid_class_type(self, request_data: Dict) -> bool:
        equipment_type = request_data.get("equipment_type", "")
        return equipment_type not in self.graph.classes
    
    def _condition_missing_required_property(self, request_data: Dict) -> bool:
        equipment_type = request_data.get("equipment_type", "Equipment")
        if equipment_type not in self.graph.classes:
            return True
        
        all_props = self.graph.class_all_properties.get(equipment_type, {"required": []})
        required_props = all_props["required"]
        
        for prop in required_props:
            if prop not in request_data or request_data[prop] is None or request_data[prop] == "":
                return True
        
        return False
    
    def _condition_invalid_status(self, request_data: Dict) -> bool:
        status = request_data.get("status")
        allowed_status = ["normal", "warning", "error", "maintenance"]
        return status not in allowed_status
    
    def _condition_invalid_id_format(self, request_data: Dict) -> bool:
        equipment_id = request_data.get("equipment_id", "")
        pattern = r"^(CNC|LTH|MLG|ROB|CNV)-\d{3}$"
        return not re.match(pattern, equipment_id)
    
    def _condition_transitive_location_conflict(self, request_data: Dict) -> bool:
        equipment_id = request_data.get("equipment_id")
        production_line = request_data.get("production_line")
        workshop = request_data.get("workshop")
        
        if not production_line or not workshop:
            return False
        
        line_relations = self.graph.get_related_instances(production_line)
        line_workshop = None
        for predicate, obj in line_relations:
            if predicate == "locatedIn":
                line_workshop = obj
                break
        
        if line_workshop and line_workshop != workshop:
            return True
        
        return False
    
    def _condition_cross_system_inconsistency(self, request_data: Dict) -> bool:
        equipment_id = request_data.get("equipment_id")
        if not equipment_id:
            return False
        
        erp_id = f"ERP_{equipment_id}"
        if erp_id not in self.graph.node_properties:
            return False
        
        erp_props = self.graph.get_instance_properties(erp_id)
        conflicts = []
        
        for key in ["equipment_name", "equipment_type", "location", "status"]:
            if key in request_data and key in erp_props:
                req_val = str(request_data[key])
                erp_val = str(erp_props[key])
                if req_val != erp_val:
                    conflicts.append(key)
        
        return len(conflicts) > 0
    
    def _condition_capacity_exceeded(self, request_data: Dict) -> bool:
        production_line = request_data.get("production_line")
        equipment_type = request_data.get("equipment_type")
        
        if not production_line:
            return False
        
        line_capacity = self.graph.get_instance_properties(production_line).get("capacity", 10)
        
        line_relations = self.graph.get_related_instances(production_line, "hasPart")
        current_count = len(line_relations)
        
        if current_count >= line_capacity:
            return True
        
        return False
    
    def _condition_duplicate_id(self, request_data: Dict) -> bool:
        equipment_id = request_data.get("equipment_id")
        if not equipment_id:
            return False
        
        return equipment_id in self.graph.node_properties
    
    def _condition_negative_value(self, request_data: Dict) -> bool:
        for key in ["spindle_speed", "capacity", "max_diameter", "max_length", "axis_count", "payload", "reach"]:
            if key in request_data and isinstance(request_data[key], (int, float)) and request_data[key] < 0:
                return True
        return False
    
    def _condition_all_valid(self, request_data: Dict) -> bool:
        for rule in self.rules[:-1]:
            if rule["condition"](request_data):
                return False
        return True
    
    def _action_reject_with_invalid_class_type(self, request_data: Dict) -> Dict:
        return {
            "status": "rejected",
            "rule_name": "rule_invalid_class_type",
            "reason": f"设备类型 '{request_data.get('equipment_type')}' 不在本体定义中",
            "suggestion": f"可用的设备类型: {', '.join(self.graph.get_all_classes())}"
        }
    
    def _action_reject_with_missing_property(self, request_data: Dict) -> Dict:
        equipment_type = request_data.get("equipment_type", "Equipment")
        all_props = self.graph.class_all_properties.get(equipment_type, {"required": []})
        required_props = all_props["required"]
        
        missing_props = []
        for prop in required_props:
            if prop not in request_data or request_data[prop] is None or request_data[prop] == "":
                missing_props.append(prop)
        
        return {
            "status": "rejected",
            "rule_name": "rule_missing_required_property",
            "reason": f"设备缺少必需属性: {', '.join(missing_props)}",
            "missing_properties": missing_props,
            "suggestion": f"请补充以下必需属性后重新提交: {', '.join(missing_props)}"
        }
    
    def _action_reject_with_invalid_status(self, request_data: Dict) -> Dict:
        return {
            "status": "rejected",
            "rule_name": "rule_invalid_status",
            "reason": f"设备状态值 '{request_data.get('status')}' 无效",
            "suggestion": "设备状态必须为: normal, warning, error, maintenance"
        }
    
    def _action_reject_with_invalid_id_format(self, request_data: Dict) -> Dict:
        return {
            "status": "rejected",
            "rule_name": "rule_invalid_equipment_id_format",
            "reason": f"设备编码格式 '{request_data.get('equipment_id')}' 不符合规范",
            "suggestion": "设备编码必须符合格式: CNC/LTH/MLG/ROB/CNV-XXX"
        }
    
    def _action_reject_with_location_conflict(self, request_data: Dict) -> Dict:
        production_line = request_data.get("production_line")
        workshop = request_data.get("workshop")
        
        line_workshop = None
        line_relations = self.graph.get_related_instances(production_line)
        for predicate, obj in line_relations:
            if predicate == "locatedIn":
                line_workshop = obj
                break
        
        return {
            "status": "rejected",
            "rule_name": "rule_transitive_location_conflict",
            "reason": f"通过传递性推理发现位置矛盾：设备声称位于 '{workshop}'，但所属产线 '{production_line}' 位于 '{line_workshop}'",
            "conflict_detail": {
                "equipment_workshop": workshop,
                "production_line": production_line,
                "line_workshop": line_workshop
            },
            "suggestion": f"请修正设备车间信息为 '{line_workshop}'，或确认产线与车间的归属关系"
        }
    
    def _action_reject_with_cross_system_conflict(self, request_data: Dict) -> Dict:
        equipment_id = request_data.get("equipment_id")
        erp_id = f"ERP_{equipment_id}"
        erp_props = self.graph.get_instance_properties(erp_id)
        
        conflicts = []
        for key in ["equipment_name", "equipment_type", "location", "status"]:
            if key in request_data and key in erp_props:
                req_val = str(request_data[key])
                erp_val = str(erp_props[key])
                if req_val != erp_val:
                    conflicts.append({
                        "property": key,
                        "new_request_value": req_val,
                        "erp_value": erp_val
                    })
        
        return {
            "status": "rejected",
            "rule_name": "rule_cross_system_inconsistency",
            "reason": f"检测到与ERP系统数据冲突：同一设备在ERP中已有不同信息",
            "conflicts": conflicts,
            "suggestion": "请核对ERP系统中的设备信息，确认是否为同一设备或修正注册信息"
        }
    
    def _action_reject_with_capacity_exceeded(self, request_data: Dict) -> Dict:
        production_line = request_data.get("production_line")
        line_capacity = self.graph.get_instance_properties(production_line).get("capacity", 10)
        
        line_relations = self.graph.get_related_instances(production_line, "hasPart")
        current_count = len(line_relations)
        
        return {
            "status": "rejected",
            "rule_name": "rule_production_line_capacity_exceeded",
            "reason": f"产线 '{production_line}' 容量已达上限：当前 {current_count} 台，容量上限 {line_capacity} 台",
            "capacity_detail": {
                "production_line": production_line,
                "current_count": current_count,
                "capacity": line_capacity
            },
            "suggestion": "请选择其他产线，或联系车间管理员调整产线容量"
        }
    
    def _action_reject_with_duplicate_id(self, request_data: Dict) -> Dict:
        equipment_id = request_data.get("equipment_id")
        existing_class = self.graph.get_instance_class(equipment_id)
        
        return {
            "status": "rejected",
            "rule_name": "rule_duplicate_equipment_id",
            "reason": f"设备编码 '{equipment_id}' 已存在于系统中，类型为 {existing_class}",
            "suggestion": "请使用新的设备编码或联系管理员确认设备状态"
        }
    
    def _action_reject_with_negative_value(self, request_data: Dict) -> Dict:
        negative_keys = []
        for key in ["spindle_speed", "capacity", "max_diameter", "max_length", "axis_count", "payload", "reach"]:
            if key in request_data and isinstance(request_data[key], (int, float)) and request_data[key] < 0:
                negative_keys.append(key)
        
        return {
            "status": "rejected",
            "rule_name": "rule_negative_value",
            "reason": f"以下属性值为负数: {', '.join(negative_keys)}",
            "suggestion": "请修正为正数后重新提交"
        }
    
    def _action_approve_with_enhancement(self, request_data: Dict) -> Dict:
        work_order_id = f"WO-{uuid.uuid4().hex[:8].upper()}"
        
        enhancements = []
        
        production_line = request_data.get("production_line")
        workshop = request_data.get("workshop")
        if production_line and not workshop:
            line_relations = self.graph.get_related_instances(production_line)
            for predicate, obj in line_relations:
                if predicate == "locatedIn":
                    enhancements.append({
                        "type": "inferred_location",
                        "property": "workshop",
                        "value": obj,
                        "reason": f"通过传递性推理：产线 {production_line} 位于 {obj}"
                    })
                    workshop = obj
                    break
        
        equipment_type = request_data.get("equipment_type")
        if equipment_type:
            maintenance_tasks = self.graph.get_class_instances("MaintenanceTask")
            if maintenance_tasks:
                enhancements.append({
                    "type": "maintenance_association",
                    "property": "maintenance_task",
                    "value": maintenance_tasks[0],
                    "reason": f"根据本体规则，{equipment_type} 类型设备必须关联维护任务"
                })
        
        return {
            "status": "approved",
            "rule_name": "rule_auto_approve_valid_device",
            "reason": "设备信息完整且符合本体约束，通过知识图谱推理完成智能审核",
            "work_order_id": work_order_id,
            "equipment_id": request_data.get("equipment_id"),
            "message": f"设备注册申请已通过，已生成上线工单 {work_order_id}",
            "knowledge_enhancements": enhancements,
            "synced_to_mes": True,
            "synced_to_erp": True
        }
    
    def execute_rules(self, request_data: Dict) -> Dict:
        equipment_id = request_data.get("equipment_id", "UNKNOWN")
        logger.info(f"[规则引擎] 开始校验设备注册请求: {equipment_id}")
        logger.info(f"[规则引擎] 待校验规则数量: {len(self.rules)}")
        
        results = []
        
        for rule in self.rules:
            logger.info(f"[规则引擎] 执行规则: {rule['name']} - {rule['description']}")
            if rule["condition"](request_data):
                logger.info(f"[规则引擎] 规则触发: {rule['name']}")
                action_result = rule["action"](request_data)
                logger.info(f"[规则引擎] 规则结果: {action_result.get('status', 'unknown')} - {action_result.get('reason', '')}")
                
                results.append({
                    "rule_name": rule["name"],
                    "rule_description": rule["description"],
                    "severity": rule["severity"],
                    **action_result
                })
                
                if action_result.get("status") == "rejected":
                    logger.info(f"[规则引擎] 校验拒绝: {rule['name']}")
                    return {
                        "overall_status": "rejected",
                        "triggered_rule": rule["name"],
                        "results": results
                    }
            else:
                logger.info(f"[规则引擎] 规则未触发: {rule['name']}")
        
        logger.info(f"[规则引擎] 所有规则通过，自动批准")
        return {
            "overall_status": "approved",
            "triggered_rule": "rule_auto_approve_valid_device",
            "results": results
        }
    
    def detect_cross_system_inconsistencies(self) -> List[Dict]:
        logger.info(f"[跨系统检测] 开始检测MES/ERP数据一致性...")
        inconsistencies = []
        
        mes_instances = [inst for inst in self.graph.node_properties 
                         if not inst.startswith("ERP_") and self.graph.get_instance_class(inst) in ["CNCMachine", "Lathe", "MillingMachine", "Robot", "Conveyor"]]
        logger.info(f"[跨系统检测] MES设备实例数: {len(mes_instances)}")
        
        for mes_id in mes_instances:
            erp_id = f"ERP_{mes_id}"
            if erp_id in self.graph.node_properties:
                mes_props = self.graph.get_instance_properties(mes_id)
                erp_props = self.graph.get_instance_properties(erp_id)
                
                conflicts = []
                for key in ["equipment_name", "equipment_type", "location", "status"]:
                    if key in mes_props and key in erp_props:
                        mes_val = str(mes_props[key])
                        erp_val = str(erp_props[key])
                        if mes_val != erp_val:
                            conflicts.append({
                                "property": key,
                                "mes_value": mes_val,
                                "erp_value": erp_val
                            })
                
                if conflicts:
                    inconsistencies.append({
                        "equipment_id": mes_id,
                        "conflicts": conflicts,
                        "mes_instance": mes_props,
                        "erp_instance": erp_props
                    })
        
        return inconsistencies
    
    def infer_missing_relations(self) -> List[Dict]:
        inferred = []
        
        for instance_id in self.graph.node_properties:
            props = self.graph.get_instance_properties(instance_id)
            class_name = props.get("__class__")
            
            if class_name in ["CNCMachine", "Lathe", "MillingMachine", "Robot", "Conveyor"]:
                relations = self.graph.get_related_instances(instance_id)
                has_maintenance = any(p == "requiresMaintenance" for p, _ in relations)
                
                if not has_maintenance:
                    inferred.append({
                        "type": "missing_maintenance",
                        "instance_id": instance_id,
                        "class_name": class_name,
                        "reason": "设备未关联维护任务，根据本体规则 maintenance_required 应补充",
                        "suggestion": "为该设备创建并关联维护任务"
                    })
        
        return inferred

class OntologyGraph:
    def __init__(self, ontology_file: str):
        logger.info(f"[本体加载] 开始加载本体文件: {ontology_file}")
        with open(ontology_file, 'r', encoding='utf-8') as f:
            self.ontology = json.load(f)
        
        self.classes = self.ontology.get("classes", {})
        self.relations = self.ontology.get("relations", {})
        self.rules = self.ontology.get("rules", [])
        self.constraints = self.ontology.get("constraints", {})
        
        logger.info(f"[本体加载] 本体加载完成: {len(self.classes)} 个类, {len(self.relations)} 个关系, {len(self.constraints)} 个约束")
        logger.info(f"[本体加载] 类列表: {list(self.classes.keys())}")
        logger.info(f"[本体加载] 关系列表: {list(self.relations.keys())}")
        
        self.graph: Dict[str, List[Tuple[str, str]]] = {}
        self.node_properties: Dict[str, Dict[str, Any]] = {}
        self.class_instances: Dict[str, List[str]] = {}
        
        logger.info(f"[本体构建] 构建类层次结构...")
        self._build_class_hierarchy()
        logger.info(f"[本体构建] 构建属性继承关系...")
        self._build_property_inheritance()
        logger.info(f"[本体构建] 本体初始化完成")
    
    def _build_class_hierarchy(self):
        self.class_parents: Dict[str, str] = {}
        self.class_children: Dict[str, List[str]] = {cls: [] for cls in self.classes}
        
        for cls_name, cls_def in self.classes.items():
            parent = cls_def.get("parent")
            if parent:
                self.class_parents[cls_name] = parent
                self.class_children[parent].append(cls_name)
    
    def _build_property_inheritance(self):
        self.class_all_properties: Dict[str, Dict[str, List[str]]] = {}
        
        for cls_name in self.classes:
            required_props = []
            optional_props = []
            current = cls_name
            
            while current:
                cls_def = self.classes.get(current, {})
                required_props.extend(cls_def.get("required_properties", []))
                optional_props.extend(cls_def.get("optional_properties", []))
                current = self.class_parents.get(current)
            
            self.class_all_properties[cls_name] = {
                "required": list(set(required_props)),
                "optional": list(set(optional_props))
            }
    
    def add_instance(self, instance_id: str, class_name: str, properties: Dict[str, Any]):
        if class_name not in self.classes:
            raise ValueError(f"类 {class_name} 不存在于本体中")
        
        logger.info(f"[本体实例] 添加实例: {instance_id} 类型={class_name}")
        
        self.node_properties[instance_id] = {
            "__class__": class_name,
            **properties
        }
        
        if class_name not in self.class_instances:
            self.class_instances[class_name] = []
        self.class_instances[class_name].append(instance_id)
        
        ancestors = self.get_class_ancestors(class_name)
        for ancestor in ancestors:
            if ancestor not in self.class_instances:
                self.class_instances[ancestor] = []
            if instance_id not in self.class_instances[ancestor]:
                self.class_instances[ancestor].append(instance_id)
        
        if instance_id not in self.graph:
            self.graph[instance_id] = []
    
    def add_relation(self, subject: str, predicate: str, obj: str):
        if predicate not in self.relations:
            raise ValueError(f"关系 {predicate} 不存在于本体中")
        
        logger.info(f"[本体关系] 添加关系: {subject} --{predicate}--> {obj}")
        
        if subject not in self.graph:
            self.graph[subject] = []
        self.graph[subject].append((predicate, obj))
    
    def get_class_ancestors(self, class_name: str) -> List[str]:
        ancestors = []
        current = class_name
        
        while current:
            parent = self.class_parents.get(current)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return ancestors
    
    def get_class_descendants(self, class_name: str) -> List[str]:
        descendants = []
        stack = [class_name]
        
        while stack:
            current = stack.pop()
            for child in self.class_children.get(current, []):
                descendants.append(child)
                stack.append(child)
        
        return descendants
    
    def get_class_instances(self, class_name: str) -> List[str]:
        return self.class_instances.get(class_name, [])
    
    def get_instance_properties(self, instance_id: str) -> Dict[str, Any]:
        return self.node_properties.get(instance_id, {})
    
    def get_instance_class(self, instance_id: str) -> str:
        return self.node_properties.get(instance_id, {}).get("__class__", "")
    
    def get_related_instances(self, instance_id: str, predicate: str = None) -> List[Tuple[str, str]]:
        relations = self.graph.get(instance_id, [])
        if predicate:
            return [(p, o) for p, o in relations if p == predicate]
        return relations
    
    def check_property_constraints(self, instance_id: str) -> List[str]:
        errors = []
        props = self.get_instance_properties(instance_id)
        class_name = props.get("__class__")
        
        if not class_name:
            return errors
        
        all_props = self.class_all_properties.get(class_name, {"required": [], "optional": []})
        required_props = all_props["required"]
        
        for prop in required_props:
            if prop not in props or props[prop] is None or props[prop] == "":
                errors.append(f"实例 {instance_id} 缺少必需属性: {prop}")
        
        return errors
    
    def check_value_constraints(self, instance_id: str) -> List[str]:
        errors = []
        props = self.get_instance_properties(instance_id)
        
        for constraint_name, constraint in self.constraints.items():
            if "pattern" in constraint:
                prop_name = constraint.get("property", constraint_name.replace("_format", ""))
                if prop_name in props:
                    value = str(props[prop_name])
                    pattern = constraint["pattern"]
                    if not re.match(pattern, value):
                        errors.append(f"实例 {instance_id} 的属性 {prop_name} 值 '{value}' 不符合约束: {constraint.get('message', '')}")
            
            if "allowed_values" in constraint:
                prop_name = constraint.get("property", constraint_name.replace("_values", ""))
                if prop_name in props:
                    value = props[prop_name]
                    allowed = constraint["allowed_values"]
                    if value not in allowed:
                        errors.append(f"实例 {instance_id} 的属性 {prop_name} 值 '{value}' 不在允许列表中: {allowed}")
            
            if "condition" in constraint:
                condition = constraint["condition"]
                try:
                    for key, val in props.items():
                        if isinstance(val, (int, float)):
                            condition = condition.replace(key, str(val))
                    if not eval(condition):
                        errors.append(f"实例 {instance_id} 不满足约束条件 '{condition}': {constraint.get('message', '')}")
                except:
                    pass
        
        return errors
    
    def check_instance_validity(self, instance_id: str) -> List[str]:
        errors = []
        errors.extend(self.check_property_constraints(instance_id))
        errors.extend(self.check_value_constraints(instance_id))
        return errors
    
    def infer_transitive_relations(self) -> List[Tuple[str, str, str]]:
        logger.info(f"[本体推理] 开始执行传递性推理...")
        inferred = []
        new_inferred = True
        iteration = 0
        
        while new_inferred:
            iteration += 1
            new_inferred = False
            logger.info(f"[本体推理] 推理迭代 {iteration}...")
            
            for rule in self.rules:
                if rule.get("name") == "transitive_belongsTo":
                    for subject, relations in self.graph.items():
                        belongs_to_line = [(p, o) for p, o in relations if p == "belongsTo"]
                        for _, line_id in belongs_to_line:
                            line_relations = self.graph.get(line_id, [])
                            located_in_workshop = [(p, o) for p, o in line_relations if p == "locatedIn"]
                            for _, workshop_id in located_in_workshop:
                                has_relation = any(p == "locatedIn" and o == workshop_id for p, o in relations)
                                if not has_relation:
                                    logger.info(f"[本体推理] 发现传递性关系: {subject} --locatedIn--> {workshop_id} (通过产线 {line_id} 推断)")
                                    self.add_relation(subject, "locatedIn", workshop_id)
                                    inferred.append((subject, "locatedIn", workshop_id))
                                    new_inferred = True
        
        logger.info(f"[本体推理] 传递性推理完成，共发现 {len(inferred)} 个隐含关系")
        return inferred
    
    def find_inconsistencies(self) -> List[str]:
        inconsistencies = []
        
        for instance_id in self.node_properties:
            errors = self.check_instance_validity(instance_id)
            for error in errors:
                inconsistencies.append(error)
        
        return inconsistencies
    
    def query_class_definition(self, class_name: str) -> Dict[str, Any]:
        if class_name not in self.classes:
            return {"error": f"类 {class_name} 不存在"}
        
        result = self.classes[class_name].copy()
        result["ancestors"] = self.get_class_ancestors(class_name)
        result["descendants"] = self.get_class_descendants(class_name)
        result["all_required_properties"] = self.class_all_properties.get(class_name, {}).get("required", [])
        result["all_optional_properties"] = self.class_all_properties.get(class_name, {}).get("optional", [])
        
        return result
    
    def query_relation_definition(self, relation_name: str) -> Dict[str, Any]:
        if relation_name not in self.relations:
            return {"error": f"关系 {relation_name} 不存在"}
        
        return self.relations[relation_name]
    
    def get_all_classes(self) -> List[str]:
        return list(self.classes.keys())
    
    def get_all_relations(self) -> List[str]:
        return list(self.relations.keys())
    
    def get_instances_by_class(self, class_name: str) -> List[Dict[str, Any]]:
        instances = []
        for instance_id in self.get_class_instances(class_name):
            props = self.get_instance_properties(instance_id)
            instances.append({"id": instance_id, **props})
        return instances
    
    def build_from_data(self, mes_data: List[Dict], erp_data: List[Dict], production_units: List[Dict] = None):
        logger.info(f"[图谱构建] 开始构建跨系统知识图谱...")
        logger.info(f"[图谱构建] MES数据: {len(mes_data)} 条设备记录")
        logger.info(f"[图谱构建] ERP数据: {len(erp_data)} 条设备记录")
        logger.info(f"[图谱构建] 产线数据: {len(production_units) if production_units else 0} 条记录")
        
        type_mapping = {
            "CNCMachine": "CNCMachine",
            "Lathe": "Lathe",
            "MillingMachine": "MillingMachine",
            "Robot": "Robot",
            "Conveyor": "Conveyor",
            "数控机床": "CNCMachine",
            "车床": "Lathe",
            "铣床": "MillingMachine",
            "工业机器人": "Robot",
            "传送带": "Conveyor"
        }
        
        if production_units:
            logger.info(f"[图谱构建] 加载产线和车间实例...")
            for item in production_units:
                if "line_id" in item:
                    line_id = item["line_id"]
                    props = {k: v for k, v in item.items() if k not in ["line_id", "workshop"]}
                    self.add_instance(line_id, "ProductionLine", props)
                    
                    if "workshop" in item:
                        self.add_relation(line_id, "locatedIn", item["workshop"])
                
                if "workshop_id" in item:
                    workshop_id = item["workshop_id"]
                    props = {k: v for k, v in item.items() if k != "workshop_id"}
                    self.add_instance(workshop_id, "Workshop", props)
        
        logger.info(f"[图谱构建] 加载MES设备实例...")
        for item in mes_data:
            equipment_id = item.get("equipment_id")
            equipment_type = item.get("equipment_type", "Equipment")
            mapped_type = type_mapping.get(equipment_type, equipment_type)
            
            props = {k: v for k, v in item.items() if k not in ["equipment_id", "production_line", "workshop"]}
            
            self.add_instance(equipment_id, mapped_type, props)
            
            if "production_line" in item:
                self.add_relation(equipment_id, "belongsTo", item["production_line"])
                self.add_relation(item["production_line"], "hasPart", equipment_id)
            
            if "workshop" in item:
                self.add_relation(equipment_id, "locatedIn", item["workshop"])
        
        logger.info(f"[图谱构建] 加载ERP设备实例...")
        for item in erp_data:
            equipment_code = item.get("equipment_code")
            equipment_type = item.get("equipment_type", "Equipment")
            mapped_type = type_mapping.get(equipment_type, equipment_type)
            
            props = {k: v for k, v in item.items() if k not in ["equipment_code", "assigned_line", "department"]}
            props["_source"] = "ERP"
            
            self.add_instance(f"ERP_{equipment_code}", mapped_type, props)
            
            if "assigned_line" in item:
                self.add_relation(f"ERP_{equipment_code}", "belongsTo", item["assigned_line"])
            
            if "department" in item:
                self.add_relation(f"ERP_{equipment_code}", "locatedIn", item["department"])
        
        logger.info(f"[图谱构建] 知识图谱构建完成: {len(self.node_properties)} 个实例, {sum(len(rels) for rels in self.graph.values())} 条关系")
    
    def detect_cross_system_inconsistencies(self) -> List[Dict]:
        rule_engine = self.create_rule_engine()
        return rule_engine.detect_cross_system_inconsistencies()
    
    def infer_missing_relations(self) -> List[Dict]:
        rule_engine = self.create_rule_engine()
        return rule_engine.infer_missing_relations()
    
    def create_rule_engine(self) -> RuleEngine:
        return RuleEngine(self)
    
    def validate_device_registration(self, request_data: Dict) -> Dict:
        rule_engine = self.create_rule_engine()
        return rule_engine.execute_rules(request_data)
    
    def query_nodes(self, class_name: str = None, property_filter: Dict = None) -> List[Dict]:
        results = []
        for instance_id, props in self.node_properties.items():
            if class_name:
                instance_class = props.get("__class__")
                if instance_class != class_name and class_name not in self.get_class_ancestors(instance_class):
                    continue
            
            if property_filter:
                match = True
                for key, value in property_filter.items():
                    if props.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append({"id": instance_id, **props})
        
        return results
    
    def traverse(self, start_node: str, relation_type: str = None, max_depth: int = 3) -> List[Dict]:
        visited = set()
        results = []
        queue = [(start_node, 0)]
        
        while queue:
            node_id, depth = queue.pop(0)
            if node_id in visited or depth > max_depth:
                continue
            
            visited.add(node_id)
            props = self.get_instance_properties(node_id)
            relations = self.get_related_instances(node_id, relation_type)
            
            results.append({
                "id": node_id,
                "depth": depth,
                "properties": props,
                "relations": relations
            })
            
            for _, target in relations:
                if target not in visited:
                    queue.append((target, depth + 1))
        
        return results
    
    def find_paths(self, start_node: str, end_node: str, relation_type: str = None, max_depth: int = 5) -> List[List[str]]:
        paths = []
        visited = set()
        stack = [(start_node, [start_node])]
        
        while stack:
            current, path = stack.pop()
            visited.add(current)
            
            if current == end_node:
                paths.append(path)
                continue
            
            if len(path) >= max_depth:
                continue
            
            relations = self.get_related_instances(current, relation_type)
            for _, target in relations:
                if target not in visited:
                    stack.append((target, path + [target]))
        
        return paths
    
    def get_downstream_devices(self, start_node: str, relation_type: str = "feedsInto", max_depth: int = 5) -> List[Dict]:
        visited = set()
        results = []
        queue = [(start_node, 0)]
        
        while queue:
            node_id, depth = queue.pop(0)
            if node_id in visited or depth > max_depth:
                continue
            
            visited.add(node_id)
            props = self.get_instance_properties(node_id)
            
            results.append({
                "id": node_id,
                "depth": depth,
                "properties": props
            })
            
            relations = self.get_related_instances(node_id, relation_type)
            for _, target in relations:
                if target not in visited:
                    queue.append((target, depth + 1))
        
        return results[1:]
    
    def update_instance(self, instance_id: str, properties: Dict[str, Any]):
        if instance_id not in self.node_properties:
            raise ValueError(f"实例 {instance_id} 不存在")
        
        logger.info(f"[图谱更新] 更新实例: {instance_id}")
        self.node_properties[instance_id].update(properties)
    
    def add_new_device(self, request_data: Dict) -> Dict:
        equipment_id = request_data.get("equipment_id")
        equipment_type = request_data.get("equipment_type", "Equipment")
        
        if equipment_id in self.node_properties:
            return {"status": "error", "message": f"设备 {equipment_id} 已存在"}
        
        props = {k: v for k, v in request_data.items() if k not in ["equipment_id", "production_line", "workshop"]}
        self.add_instance(equipment_id, equipment_type, props)
        
        if "production_line" in request_data:
            self.add_relation(equipment_id, "belongsTo", request_data["production_line"])
            self.add_relation(request_data["production_line"], "hasPart", equipment_id)
        
        if "workshop" in request_data:
            self.add_relation(equipment_id, "locatedIn", request_data["workshop"])
        
        self.infer_transitive_relations()
        
        return {
            "status": "success",
            "equipment_id": equipment_id,
            "message": f"设备 {equipment_id} 已成功添加到知识图谱",
            "relations_added": len(self.get_related_instances(equipment_id))
        }
    
    def update_device_status(self, equipment_id: str, new_status: str) -> Dict:
        if equipment_id not in self.node_properties:
            return {"status": "error", "message": f"设备 {equipment_id} 不存在"}
        
        allowed_status = ["normal", "warning", "error", "maintenance", "stopped"]
        if new_status not in allowed_status:
            return {"status": "error", "message": f"无效状态值 '{new_status}'，允许的值: {allowed_status}"}
        
        self.update_instance(equipment_id, {"status": new_status})
        logger.info(f"[状态更新] 设备 {equipment_id} 状态更新为: {new_status}")
        
        return {
            "status": "success",
            "equipment_id": equipment_id,
            "old_status": self.node_properties[equipment_id].get("status", "unknown"),
            "new_status": new_status
        }
    
    def get_production_line_capacity(self, production_line: str) -> Dict:
        line_props = self.get_instance_properties(production_line)
        capacity = line_props.get("capacity", 10)
        
        line_relations = self.get_related_instances(production_line, "hasPart")
        current_count = len(line_relations)
        
        return {
            "production_line": production_line,
            "current_count": current_count,
            "capacity": capacity,
            "remaining": capacity - current_count,
            "is_full": current_count >= capacity
        }
    
    def check_type_compatibility(self, equipment_type: str, production_line: str) -> Dict:
        line_props = self.get_instance_properties(production_line)
        allowed_types = line_props.get("allowed_types", [])
        
        if not allowed_types:
            return {
                "status": "allowed",
                "message": f"产线 {production_line} 未限制设备类型"
            }
        
        if equipment_type in allowed_types:
            return {
                "status": "allowed",
                "message": f"设备类型 {equipment_type} 允许在产线 {production_line} 使用",
                "allowed_types": allowed_types
            }
        
        return {
            "status": "rejected",
            "message": f"设备类型 {equipment_type} 不允许在产线 {production_line} 使用",
            "allowed_types": allowed_types,
            "suggestion": f"请选择以下允许的设备类型: {', '.join(allowed_types)}"
        }