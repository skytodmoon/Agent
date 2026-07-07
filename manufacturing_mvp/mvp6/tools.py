import json
import os
import uuid
from agentscope.tool import ToolResponse
from common.base_tool import BaseTool
from agentscope.message import TextBlock
from common.ontology_graph import OntologyGraph
from configs.settings import DATA_DIR

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
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])

class BuildKnowledgeGraphTool(BaseTool):
    name: str = "build_knowledge_graph"
    description: str = "从MES、ERP和产线数据构建跨系统知识图谱，并执行传递性推理发现隐含关系"
    input_schema = {
        "type": "object",
        "properties": {},
        "description": "构建知识图谱"
    }
    
    async def _call(self) -> ToolResponse:
        ontology_file = os.path.join(DATA_DIR, "ontology.json")
        mes_file = os.path.join(DATA_DIR, "mes_equipment.json")
        erp_file = os.path.join(DATA_DIR, "erp_equipment.json")
        production_units_file = os.path.join(DATA_DIR, "production_units.json")
        
        graph = OntologyGraph(ontology_file)
        
        with open(mes_file, 'r', encoding='utf-8') as f:
            mes_data = json.load(f)
        
        with open(erp_file, 'r', encoding='utf-8') as f:
            erp_data = json.load(f)
        
        with open(production_units_file, 'r', encoding='utf-8') as f:
            production_units = json.load(f)
        
        graph.build_from_data(mes_data, erp_data, production_units)
        
        inferred_relations = graph.infer_transitive_relations()
        
        cross_system_inconsistencies = graph.detect_cross_system_inconsistencies()
        
        missing_relations = graph.infer_missing_relations()
        
        result = {
            "status": "success",
            "graph_summary": {
                "total_instances": len(graph.node_properties),
                "total_relations": sum(len(rels) for rels in graph.graph.values()),
                "classes": graph.get_all_classes(),
                "relations": graph.get_all_relations()
            },
            "inferred_relations_count": len(inferred_relations),
            "inferred_relations": inferred_relations,
            "cross_system_inconsistencies_count": len(cross_system_inconsistencies),
            "cross_system_inconsistencies": cross_system_inconsistencies,
            "missing_relations_count": len(missing_relations),
            "missing_relations": missing_relations
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])

class ValidateRegistrationRequestTool(BaseTool):
    name: str = "validate_registration_request"
    description: str = "根据本体知识图谱校验设备注册请求，触发规则引擎进行推理判定，包括传递性推理冲突、跨系统一致性、容量约束等"
    input_schema = {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "注册请求ID"}
        },
        "required": ["request_id"],
        "description": "校验设备注册请求"
    }
    
    async def _call(self, request_id: str) -> ToolResponse:
        ontology_file = os.path.join(DATA_DIR, "ontology.json")
        requests_file = os.path.join(DATA_DIR, "device_registration_requests.json")
        mes_file = os.path.join(DATA_DIR, "mes_equipment.json")
        erp_file = os.path.join(DATA_DIR, "erp_equipment.json")
        production_units_file = os.path.join(DATA_DIR, "production_units.json")
        
        graph = OntologyGraph(ontology_file)
        
        with open(mes_file, 'r', encoding='utf-8') as f:
            mes_data = json.load(f)
        
        with open(erp_file, 'r', encoding='utf-8') as f:
            erp_data = json.load(f)
        
        with open(production_units_file, 'r', encoding='utf-8') as f:
            production_units = json.load(f)
        
        graph.build_from_data(mes_data, erp_data, production_units)
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request_data = next((r for r in requests if r["request_id"] == request_id), None)
        
        if not request_data:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "error": f"未找到请求ID: {request_id}"
            }, ensure_ascii=False))])
        
        validation_result = graph.validate_device_registration(request_data)
        
        result = {
            "request_id": request_id,
            "equipment_id": request_data.get("equipment_id"),
            "equipment_name": request_data.get("equipment_name"),
            "equipment_type": request_data.get("equipment_type"),
            **validation_result
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])

class ApproveRegistrationTool(BaseTool):
    name: str = "approve_registration"
    description: str = "批准设备注册请求，基于知识图谱推理自动补全信息，生成上线工单并同步至MES/ERP系统"
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
        production_units_file = os.path.join(DATA_DIR, "production_units.json")
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request_idx = next((i for i, r in enumerate(requests) if r["request_id"] == request_id), -1)
        
        if request_idx == -1:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "error": f"未找到请求ID: {request_id}"
            }, ensure_ascii=False))])
        
        request_data = requests[request_idx]
        
        ontology_file = os.path.join(DATA_DIR, "ontology.json")
        graph = OntologyGraph(ontology_file)
        
        with open(production_units_file, 'r', encoding='utf-8') as f:
            production_units = json.load(f)
        
        for item in production_units:
            if "line_id" in item and item["line_id"] == request_data.get("production_line"):
                if "workshop" in item and "workshop" not in request_data:
                    request_data["workshop"] = item["workshop"]
                    break
        
        work_order_id = f"WO-{uuid.uuid4().hex[:8].upper()}"
        
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
            "purchase_date": "2026-07-06",
            "installation_date": "2026-07-06",
            "asset_value": 0,
            "maintenance_cycle": 30,
            "assigned_line": request_data.get("production_line", "")
        }
        
        with open(erp_file, 'r', encoding='utf-8') as f:
            erp_equipment = json.load(f)
        erp_equipment.append(erp_data)
        with open(erp_file, 'w', encoding='utf-8') as f:
            json.dump(erp_equipment, f, ensure_ascii=False, indent=2)
        
        requests[request_idx]["request_status"] = "approved"
        requests[request_idx]["approved_at"] = "2026-07-06"
        requests[request_idx]["approval_comment"] = approval_comment
        requests[request_idx]["work_order_id"] = work_order_id
        
        with open(requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
        
        enhancements = []
        production_line = request_data.get("production_line")
        workshop = request_data.get("workshop")
        if production_line and workshop:
            enhancements.append({
                "type": "inferred_location",
                "property": "workshop",
                "value": workshop,
                "reason": f"通过传递性推理：产线 {production_line} 位于 {workshop}"
            })
        
        result = {
            "status": "success",
            "request_id": request_id,
            "equipment_id": request_data["equipment_id"],
            "work_order_id": work_order_id,
            "message": f"设备注册申请已批准，已生成上线工单 {work_order_id}，设备已同步至MES和ERP系统",
            "approval_comment": approval_comment,
            "synced_to_mes": True,
            "synced_to_erp": True,
            "knowledge_enhancements": enhancements
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])

class RejectRegistrationTool(BaseTool):
    name: str = "reject_registration"
    description: str = "拒绝设备注册请求，记录拒绝原因并通知申请人"
    input_schema = {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "注册请求ID"},
            "reject_reason": {"type": "string", "description": "拒绝原因"},
            "suggestion": {"type": "string", "description": "修改建议"}
        },
        "required": ["request_id", "reject_reason"],
        "description": "拒绝设备注册"
    }
    
    async def _call(self, request_id: str, reject_reason: str, suggestion: str = "") -> ToolResponse:
        requests_file = os.path.join(DATA_DIR, "device_registration_requests.json")
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request_idx = next((i for i, r in enumerate(requests) if r["request_id"] == request_id), -1)
        
        if request_idx == -1:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "error": f"未找到请求ID: {request_id}"
            }, ensure_ascii=False))])
        
        request_data = requests[request_idx]
        
        requests[request_idx]["request_status"] = "rejected"
        requests[request_idx]["rejected_at"] = "2026-07-06"
        requests[request_idx]["reject_reason"] = reject_reason
        requests[request_idx]["suggestion"] = suggestion
        
        with open(requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
        
        result = {
            "status": "success",
            "request_id": request_id,
            "equipment_id": request_data["equipment_id"],
            "equipment_name": request_data["equipment_name"],
            "reject_reason": reject_reason,
            "suggestion": suggestion,
            "message": f"设备注册申请已拒绝，拒绝原因：{reject_reason}。建议：{suggestion}",
            "notified_requestor": True
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])

class DetectInconsistenciesTool(BaseTool):
    name: str = "detect_inconsistencies"
    description: str = "检测跨系统数据不一致，发现MES和ERP中同一设备的信息冲突"
    input_schema = {
        "type": "object",
        "properties": {},
        "description": "检测跨系统不一致"
    }
    
    async def _call(self) -> ToolResponse:
        ontology_file = os.path.join(DATA_DIR, "ontology.json")
        mes_file = os.path.join(DATA_DIR, "mes_equipment.json")
        erp_file = os.path.join(DATA_DIR, "erp_equipment.json")
        production_units_file = os.path.join(DATA_DIR, "production_units.json")
        
        graph = OntologyGraph(ontology_file)
        
        with open(mes_file, 'r', encoding='utf-8') as f:
            mes_data = json.load(f)
        
        with open(erp_file, 'r', encoding='utf-8') as f:
            erp_data = json.load(f)
        
        with open(production_units_file, 'r', encoding='utf-8') as f:
            production_units = json.load(f)
        
        graph.build_from_data(mes_data, erp_data, production_units)
        
        cross_system_inconsistencies = graph.detect_cross_system_inconsistencies()
        
        inferred_relations = graph.infer_transitive_relations()
        
        missing_relations = graph.infer_missing_relations()
        
        result = {
            "status": "success",
            "cross_system_inconsistencies_count": len(cross_system_inconsistencies),
            "cross_system_inconsistencies": cross_system_inconsistencies,
            "inferred_relations_count": len(inferred_relations),
            "inferred_relations": inferred_relations,
            "missing_relations_count": len(missing_relations),
            "missing_relations": missing_relations
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])

class GenerateApprovalReportTool(BaseTool):
    name: str = "generate_approval_report"
    description: str = "生成设备注册审批报告，汇总审核结果和统计数据"
    input_schema = {
        "type": "object",
        "properties": {
            "period": {"type": "string", "description": "报告周期"}
        },
        "description": "生成审批报告"
    }
    
    async def _call(self, period: str = "daily") -> ToolResponse:
        requests_file = os.path.join(DATA_DIR, "device_registration_requests.json")
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        total = len(requests)
        approved = len([r for r in requests if r.get("request_status") == "approved"])
        rejected = len([r for r in requests if r.get("request_status") == "rejected"])
        pending = len([r for r in requests if r.get("request_status") not in ["approved", "rejected"]])
        
        rejected_reasons = {}
        for r in requests:
            if r.get("request_status") == "rejected":
                reason = r.get("reject_reason", "其他")
                rejected_reasons[reason] = rejected_reasons.get(reason, 0) + 1
        
        approved_by_type = {}
        for r in requests:
            if r.get("request_status") == "approved":
                eq_type = r.get("equipment_type", "未知")
                approved_by_type[eq_type] = approved_by_type.get(eq_type, 0) + 1
        
        report = {
            "report_period": period,
            "generated_at": "2026-07-06",
            "summary": {
                "total_requests": total,
                "approved_count": approved,
                "rejected_count": rejected,
                "pending_count": pending,
                "approval_rate": round(approved / total * 100, 2) if total > 0 else 0
            },
            "rejected_reasons": rejected_reasons,
            "approved_by_type": approved_by_type,
            "details": [
                {
                    "request_id": r["request_id"],
                    "equipment_id": r["equipment_id"],
                    "equipment_name": r["equipment_name"],
                    "equipment_type": r["equipment_type"],
                    "status": r.get("request_status", "pending"),
                    "work_order_id": r.get("work_order_id", "")
                }
                for r in requests
            ]
        }
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps(report, ensure_ascii=False, indent=2))])