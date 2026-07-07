import json
import os
from agentscope.tool import ToolResponse
from common.base_tool import BaseTool
from agentscope.message import TextBlock
from common.utils import generate_id
from configs.settings import DATA_DIR

class ReportExceptionTool(BaseTool):
    name: str = "report_exception"
    description: str = "上报生产异常事件，记录异常类型、描述、影响范围"
    input_schema = {
        "type": "object",
        "properties": {
            "type": {"type": "string", "description": "异常类型"},
            "description": {"type": "string", "description": "异常描述"},
            "equipment_id": {"type": "string", "description": "设备编号"},
            "affected_orders": {"type": "string", "description": "受影响工单列表"},
            "severity": {"type": "string", "description": "严重程度"}
        },
        "required": ["type", "description"],
        "description": "上报生产异常"
    }
    
    async def _call(self, type: str, description: str, equipment_id: str = "", 
                   affected_orders: str = "", severity: str = "中") -> ToolResponse:
        exception_record = {
            "id": generate_id("EX-"),
            "type": type,
            "description": description,
            "equipment_id": equipment_id,
            "affected_orders": affected_orders,
            "severity": severity,
            "status": "pending"
        }
        
        exceptions_file = os.path.join(DATA_DIR, "exceptions.json")
        if os.path.exists(exceptions_file):
            with open(exceptions_file, 'r', encoding='utf-8') as f:
                exceptions = json.load(f)
        else:
            exceptions = []
        
        exceptions.append(exception_record)
        
        with open(exceptions_file, 'w', encoding='utf-8') as f:
            json.dump(exceptions, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "exception_id": exception_record["id"],
            "message": f"异常记录 {exception_record['id']} 已保存"
        }, ensure_ascii=False))])

class ProductionOrderQueryTool(BaseTool):
    name: str = "production_order_query"
    description: str = "查询生产工单信息，包括优先级、交期、已完成数量等"
    input_schema = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "工单ID"},
            "line_id": {"type": "string", "description": "产线编号"},
            "status": {"type": "string", "description": "状态"}
        },
        "description": "查询生产工单"
    }
    
    async def _call(self, order_id: str = "", line_id: str = "", status: str = "") -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "production_orders.json")
        if not os.path.exists(filepath):
            return ToolResponse(content=[TextBlock(type="text", text="未找到生产工单数据")])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            orders = json.load(f)
        
        results = []
        for item in orders:
            if order_id and item["id"] != order_id:
                continue
            if line_id and item["line_id"] != line_id:
                continue
            if status and item["status"] != status:
                continue
            results.append(item)
        
        if results:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的生产工单")])

class LineCapacityQueryTool(BaseTool):
    name: str = "line_capacity_query"
    description: str = "查询产线的产能信息，包括设备数量、节拍、可用产能等"
    input_schema = {
        "type": "object",
        "properties": {
            "line_id": {"type": "string", "description": "产线编号"}
        },
        "required": ["line_id"],
        "description": "查询产线产能"
    }
    
    async def _call(self, line_id: str) -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "line_capacity.json")
        if not os.path.exists(filepath):
            return ToolResponse(content=[TextBlock(type="text", text="未找到产线产能数据")])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            line_data = json.load(f)
        
        results = []
        for item in line_data:
            if item["line_id"] == line_id:
                results.append(item)
        
        if results:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的产线产能信息")])

class GenerateSchedulingPlanTool(BaseTool):
    name: str = "generate_scheduling_plan"
    description: str = "基于排程规则与产能约束，生成多套优先级调整方案"
    input_schema = {
        "type": "object",
        "properties": {
            "exception_id": {"type": "string", "description": "异常ID"},
            "line_id": {"type": "string", "description": "产线编号"},
            "affected_orders": {"type": "string", "description": "受影响工单"},
            "exception_type": {"type": "string", "description": "异常类型"}
        },
        "required": ["exception_id", "line_id"],
        "description": "生成排程调整方案"
    }
    
    async def _call(self, exception_id: str, line_id: str, affected_orders: str = "", 
                   exception_type: str = "") -> ToolResponse:
        plans = []
        
        plan_a = {
            "plan_id": generate_id("SP-"),
            "exception_id": exception_id,
            "line_id": line_id,
            "strategy": "优先保障紧急订单",
            "description": "将受影响工单中的紧急订单优先安排到备用设备或加班处理",
            "impact": "部分非紧急订单交期可能延迟"
        }
        plans.append(plan_a)
        
        plan_b = {
            "plan_id": generate_id("SP-"),
            "exception_id": exception_id,
            "line_id": line_id,
            "strategy": "均衡分配产能",
            "description": "将产能平均分配给所有受影响工单，保证整体进度",
            "impact": "所有工单进度略有延迟"
        }
        plans.append(plan_b)
        
        plans_file = os.path.join(DATA_DIR, "scheduling_plans.json")
        if os.path.exists(plans_file):
            with open(plans_file, 'r', encoding='utf-8') as f:
                existing_plans = json.load(f)
        else:
            existing_plans = []
        
        existing_plans.extend(plans)
        
        with open(plans_file, 'w', encoding='utf-8') as f:
            json.dump(existing_plans, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "plans": plans,
            "message": f"已生成 {len(plans)} 套排程调整方案"
        }, ensure_ascii=False))])

class ApprovalTool(BaseTool):
    name: str = "approval"
    description: str = "审批排程调整方案，支持人在回路干预"
    input_schema = {
        "type": "object",
        "properties": {
            "plan_id": {"type": "string", "description": "方案ID"},
            "approved": {"type": "boolean", "description": "是否批准"},
            "comment": {"type": "string", "description": "审批意见"}
        },
        "required": ["plan_id", "approved"],
        "description": "审批排程方案"
    }
    
    async def _call(self, plan_id: str, approved: bool, comment: str = "") -> ToolResponse:
        plans_file = os.path.join(DATA_DIR, "scheduling_plans.json")
        if not os.path.exists(plans_file):
            return ToolResponse(content=[TextBlock(type="text", text="方案不存在")])
        
        with open(plans_file, 'r', encoding='utf-8') as f:
            plans = json.load(f)
        
        found = False
        for plan in plans:
            if plan["plan_id"] == plan_id:
                plan["approved"] = approved
                plan["comment"] = comment
                plan["status"] = "approved" if approved else "rejected"
                found = True
                break
        
        if found:
            with open(plans_file, 'w', encoding='utf-8') as f:
                json.dump(plans, f, ensure_ascii=False, indent=2)
            
            status_text = "已批准" if approved else "已拒绝"
            return ToolResponse(content=[TextBlock(type="text", text=f"方案 {plan_id} {status_text}")])
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"未找到方案 {plan_id}")])

class SyncToMesTool(BaseTool):
    name: str = "sync_to_mes"
    description: str = "同步排程调整结果至MES系统，通知相关部门"
    input_schema = {
        "type": "object",
        "properties": {
            "plan_id": {"type": "string", "description": "方案ID"},
            "line_id": {"type": "string", "description": "产线编号"},
            "order_changes": {"type": "string", "description": "工单变更信息"}
        },
        "required": ["plan_id", "line_id"],
        "description": "同步排程调整到MES"
    }
    
    async def _call(self, plan_id: str, line_id: str, order_changes: str = "") -> ToolResponse:
        sync_record = {
            "plan_id": plan_id,
            "line_id": line_id,
            "order_changes": order_changes,
            "status": "synced",
            "timestamp": "2026-07-06"
        }
        
        sync_file = os.path.join(DATA_DIR, "mes_sync.json")
        if os.path.exists(sync_file):
            with open(sync_file, 'r', encoding='utf-8') as f:
                sync_records = json.load(f)
        else:
            sync_records = []
        
        sync_records.append(sync_record)
        
        with open(sync_file, 'w', encoding='utf-8') as f:
            json.dump(sync_records, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "message": f"排程方案 {plan_id} 已同步至 {line_id} 产线MES系统"
        }, ensure_ascii=False))])
