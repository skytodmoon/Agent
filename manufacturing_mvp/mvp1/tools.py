import json
import os
from typing import List, Dict
from agentscope.tool import ToolResponse
from common.base_tool import BaseTool
from agentscope.message import TextBlock
from common.utils import generate_id
from configs.settings import DATA_DIR

class EquipmentQueryTool(BaseTool):
    name: str = "equipment_query"
    description: str = "查询设备详细信息，包括设备类型、位置、当前状态等"
    input_schema = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "设备编号"},
            "equipment_name": {"type": "string", "description": "设备名称"}
        },
        "description": "查询设备信息"
    }
    
    async def _call(self, equipment_id: str = None, equipment_name: str = None) -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "equipment.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            equipments = json.load(f)
        
        results = []
        for eq in equipments:
            if equipment_id and eq["id"] == equipment_id:
                results.append(eq)
            elif equipment_name and equipment_name in eq["name"]:
                results.append(eq)
        
        if results:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的设备信息")])

class FaultDiagnosisTool(BaseTool):
    name: str = "fault_diagnosis"
    description: str = "查询故障知识库，获取故障分类、严重程度和分步排查方案"
    input_schema = {
        "type": "object",
        "properties": {
            "fault_type": {"type": "string", "description": "故障类型"},
            "equipment_type": {"type": "string", "description": "设备类型"}
        },
        "required": ["fault_type"],
        "description": "根据故障类型和设备类型查询故障解决方案"
    }
    
    async def _call(self, fault_type: str, equipment_type: str = None) -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "fault_knowledge_base.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        
        results = []
        for item in knowledge_base:
            if fault_type in item["fault_type"] or fault_type in item["description"]:
                if equipment_type and item["equipment_type"] != equipment_type:
                    continue
                results.append(item)
        
        if results:
            solutions = []
            for item in results:
                solutions.append({
                    "故障类型": item["fault_type"],
                    "设备类型": item["equipment_type"],
                    "严重程度": item["severity"],
                    "解决方案": item["solution"]
                })
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(solutions, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的故障解决方案，请联系维修工程师")])

class EngineerAssignTool(BaseTool):
    name: str = "engineer_assign"
    description: str = "查询可用工程师，根据设备类型和技能要求智能分配"
    input_schema = {
        "type": "object",
        "properties": {
            "equipment_type": {"type": "string", "description": "设备类型"},
            "skill_requirement": {"type": "string", "description": "技能要求"}
        },
        "required": ["equipment_type"],
        "description": "根据设备类型和技能要求分配工程师"
    }
    
    async def _call(self, equipment_type: str, skill_requirement: str = None) -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "engineers.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            engineers = json.load(f)
        
        candidates = []
        for eng in engineers:
            if eng["availability"] == "available" and eng["specialty"] == equipment_type:
                if skill_requirement:
                    has_skill = any(skill_requirement in s for s in eng["skills"])
                    if has_skill:
                        candidates.append(eng)
                else:
                    candidates.append(eng)
        
        if candidates:
            best_match = candidates[0]
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
                "engineer_id": best_match["id"],
                "engineer_name": best_match["name"],
                "specialty": best_match["specialty"],
                "skills": best_match["skills"]
            }, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="当前没有可用的工程师，请稍后重试或联系主管")])

class CreateWorkOrderTool(BaseTool):
    name: str = "create_work_order"
    description: str = "创建维修工单，记录故障详情和指派信息"
    input_schema = {
        "type": "object",
        "properties": {
            "fault_report_id": {"type": "string", "description": "故障报告ID"},
            "title": {"type": "string", "description": "工单标题"},
            "description": {"type": "string", "description": "工单描述"},
            "equipment_id": {"type": "string", "description": "设备编号"},
            "priority": {"type": "string", "description": "优先级"},
            "assignee_id": {"type": "string", "description": "指派工程师ID"},
            "assignee_name": {"type": "string", "description": "指派工程师姓名"}
        },
        "required": ["fault_report_id", "title", "description", "equipment_id"],
        "description": "创建维修工单"
    }
    
    async def _call(self, fault_report_id: str, title: str, description: str, 
                   equipment_id: str, priority: str = "P2", 
                   assignee_id: str = None, assignee_name: str = None) -> ToolResponse:
        work_order = {
            "id": generate_id("WO-"),
            "fault_report_id": fault_report_id,
            "title": title,
            "description": description,
            "equipment_id": equipment_id,
            "priority": priority,
            "status": "pending",
            "assignee_id": assignee_id,
            "assignee_name": assignee_name
        }
        
        work_orders_file = os.path.join(DATA_DIR, "work_orders.json")
        if os.path.exists(work_orders_file):
            with open(work_orders_file, 'r', encoding='utf-8') as f:
                work_orders = json.load(f)
        else:
            work_orders = []
        
        work_orders.append(work_order)
        
        with open(work_orders_file, 'w', encoding='utf-8') as f:
            json.dump(work_orders, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "work_order_id": work_order["id"],
            "message": f"工单 {work_order['id']} 已创建成功"
        }, ensure_ascii=False))])

class UpdateWorkOrderStatusTool(BaseTool):
    name: str = "update_work_order_status"
    description: str = "更新工单状态，如待处理、处理中、已解决、已关闭"
    input_schema = {
        "type": "object",
        "properties": {
            "work_order_id": {"type": "string", "description": "工单ID"},
            "status": {"type": "string", "description": "新状态"},
            "remark": {"type": "string", "description": "备注"}
        },
        "required": ["work_order_id", "status"],
        "description": "更新工单状态"
    }
    
    async def _call(self, work_order_id: str, status: str, remark: str = "") -> ToolResponse:
        work_orders_file = os.path.join(DATA_DIR, "work_orders.json")
        if not os.path.exists(work_orders_file):
            return ToolResponse(content=[TextBlock(type="text", text="工单不存在")])
        
        with open(work_orders_file, 'r', encoding='utf-8') as f:
            work_orders = json.load(f)
        
        found = False
        for wo in work_orders:
            if wo["id"] == work_order_id:
                wo["status"] = status
                wo["remark"] = remark
                found = True
                break
        
        if found:
            with open(work_orders_file, 'w', encoding='utf-8') as f:
                json.dump(work_orders, f, ensure_ascii=False, indent=2)
            return ToolResponse(content=[TextBlock(type="text", text=f"工单 {work_order_id} 状态已更新为: {status}")])
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"未找到工单 {work_order_id}")])

class SaveFaultReportTool(BaseTool):
    name: str = "save_fault_report"
    description: str = "保存故障报告到系统，生成唯一报告ID"
    input_schema = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "设备编号"},
            "equipment_name": {"type": "string", "description": "设备名称"},
            "location": {"type": "string", "description": "工位"},
            "description": {"type": "string", "description": "故障描述"},
            "priority": {"type": "string", "description": "优先级"},
            "reported_by": {"type": "string", "description": "报告人"}
        },
        "required": ["equipment_id", "description"],
        "description": "保存故障报告"
    }
    
    description = "保存故障报告到系统，生成唯一报告ID"
    
    async def _call(self, equipment_id: str, description: str, 
                   equipment_name: str = "", location: str = "",
                   priority: str = "P2", reported_by: str = "unknown") -> ToolResponse:
        fault_report = {
            "id": generate_id("FR-"),
            "equipment_id": equipment_id,
            "equipment_name": equipment_name,
            "location": location,
            "description": description,
            "priority": priority,
            "reported_by": reported_by,
            "status": "pending"
        }
        
        reports_file = os.path.join(DATA_DIR, "fault_reports.json")
        if os.path.exists(reports_file):
            with open(reports_file, 'r', encoding='utf-8') as f:
                reports = json.load(f)
        else:
            reports = []
        
        reports.append(fault_report)
        
        with open(reports_file, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "fault_report_id": fault_report["id"],
            "message": f"故障报告 {fault_report['id']} 已保存"
        }, ensure_ascii=False))])
