import json
import os
from datetime import datetime, timedelta
from agentscope.tool import ToolResponse
from common.base_tool import BaseTool
from agentscope.message import TextBlock
from common.utils import generate_id
from configs.settings import DATA_DIR

class AcceptInspectionTool(BaseTool):
    name: str = "accept_inspection"
    description: str = "接收文字/图片巡检记录，标准化隐患信息"
    input_schema = {
        "type": "object",
        "properties": {
            "type": {"type": "string", "description": "隐患类型"},
            "location": {"type": "string", "description": "位置"},
            "description": {"type": "string", "description": "隐患描述"},
            "reporter": {"type": "string", "description": "报告人"},
            "severity": {"type": "string", "description": "严重程度"}
        },
        "required": ["type", "location", "description"],
        "description": "接收巡检记录"
    }
    
    async def _call(self, type: str, location: str, description: str, 
                   reporter: str = "", severity: str = "中") -> ToolResponse:
        inspection_record = {
            "id": generate_id("IN-"),
            "type": type,
            "location": location,
            "description": description,
            "reporter": reporter,
            "severity": severity,
            "status": "pending"
        }
        
        inspections_file = os.path.join(DATA_DIR, "inspections.json")
        if os.path.exists(inspections_file):
            with open(inspections_file, 'r', encoding='utf-8') as f:
                inspections = json.load(f)
        else:
            inspections = []
        
        inspections.append(inspection_record)
        
        with open(inspections_file, 'w', encoding='utf-8') as f:
            json.dump(inspections, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "inspection_id": inspection_record["id"],
            "message": f"巡检记录 {inspection_record['id']} 已保存"
        }, ensure_ascii=False))])

class HazardClassificationTool(BaseTool):
    name: str = "hazard_classification"
    description: str = "匹配安全规程知识库，判定隐患等级、整改时限、责任部门"
    input_schema = {
        "type": "object",
        "properties": {
            "hazard_type": {"type": "string", "description": "隐患类型"},
            "description": {"type": "string", "description": "隐患描述"},
            "location": {"type": "string", "description": "位置"}
        },
        "required": ["hazard_type"],
        "description": "隐患分级判定"
    }
    
    async def _call(self, hazard_type: str, description: str = "", location: str = "") -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "safety_hazard_knowledge.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        
        results = []
        for item in knowledge_base:
            if hazard_type in item["hazard_type"]:
                results.append(item)
        
        if results:
            classification_result = {
                "hazard_type": hazard_type,
                "level": results[0]["level"],
                "priority": results[0]["priority"],
                "deadline": results[0]["deadline"],
                "responsible_department": results[0]["responsible_department"],
                "description": results[0]["description"]
            }
            
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(classification_result, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的隐患分级标准，请联系安全工程师")])

class CreateCorrectiveActionTool(BaseTool):
    name: str = "create_corrective_action"
    description: str = "生成整改通知单，派单给责任部门"
    input_schema = {
        "type": "object",
        "properties": {
            "inspection_id": {"type": "string", "description": "巡检记录ID"},
            "hazard_type": {"type": "string", "description": "隐患类型"},
            "location": {"type": "string", "description": "位置"},
            "description": {"type": "string", "description": "整改内容"},
            "level": {"type": "string", "description": "隐患等级"},
            "deadline": {"type": "string", "description": "整改时限"},
            "responsible_department": {"type": "string", "description": "责任部门"},
            "assignee": {"type": "string", "description": "责任人"}
        },
        "required": ["inspection_id", "hazard_type", "description"],
        "description": "创建整改通知单"
    }
    
    async def _call(self, inspection_id: str, hazard_type: str, description: str,
                   location: str = "", level: str = "一般", deadline: str = "",
                   responsible_department: str = "", assignee: str = "") -> ToolResponse:
        corrective_action = {
            "id": generate_id("CA-"),
            "inspection_id": inspection_id,
            "hazard_type": hazard_type,
            "location": location,
            "description": description,
            "level": level,
            "deadline": deadline,
            "responsible_department": responsible_department,
            "assignee": assignee,
            "status": "pending"
        }
        
        actions_file = os.path.join(DATA_DIR, "corrective_actions.json")
        if os.path.exists(actions_file):
            with open(actions_file, 'r', encoding='utf-8') as f:
                actions = json.load(f)
        else:
            actions = []
        
        actions.append(corrective_action)
        
        with open(actions_file, 'w', encoding='utf-8') as f:
            json.dump(actions, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "action_id": corrective_action["id"],
            "message": f"整改通知单 {corrective_action['id']} 已创建"
        }, ensure_ascii=False))])

class TrackCorrectiveActionTool(BaseTool):
    name: str = "track_corrective_action"
    description: str = "跟踪整改进度，更新状态"
    input_schema = {
        "type": "object",
        "properties": {
            "action_id": {"type": "string", "description": "整改通知单ID"},
            "status": {"type": "string", "description": "新状态"},
            "remark": {"type": "string", "description": "备注"}
        },
        "required": ["action_id"],
        "description": "跟踪整改进度"
    }
    
    async def _call(self, action_id: str, status: str = "", remark: str = "") -> ToolResponse:
        actions_file = os.path.join(DATA_DIR, "corrective_actions.json")
        if not os.path.exists(actions_file):
            return ToolResponse(content=[TextBlock(type="text", text="整改通知单不存在")])
        
        with open(actions_file, 'r', encoding='utf-8') as f:
            actions = json.load(f)
        
        found = False
        result = {}
        for action in actions:
            if action["id"] == action_id:
                if status:
                    action["status"] = status
                    action["remark"] = remark
                result = action
                found = True
                break
        
        if found:
            with open(actions_file, 'w', encoding='utf-8') as f:
                json.dump(actions, f, ensure_ascii=False, indent=2)
            
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"未找到整改通知单 {action_id}")])

class SendSafetyReminderTool(BaseTool):
    name: str = "send_safety_reminder"
    description: str = "定时催办逾期整改项，无需人工跟进"
    input_schema = {
        "type": "object",
        "properties": {
            "action_id": {"type": "string", "description": "整改通知单ID"},
            "assignee": {"type": "string", "description": "责任人"},
            "deadline": {"type": "string", "description": "整改时限"},
            "message": {"type": "string", "description": "催办消息"}
        },
        "required": ["action_id"],
        "description": "发送催办通知"
    }
    
    async def _call(self, action_id: str, assignee: str = "", 
                   deadline: str = "", message: str = "") -> ToolResponse:
        reminder = {
            "action_id": action_id,
            "assignee": assignee,
            "deadline": deadline,
            "message": message,
            "status": "sent"
        }
        
        reminders_file = os.path.join(DATA_DIR, "safety_reminders.json")
        if os.path.exists(reminders_file):
            with open(reminders_file, 'r', encoding='utf-8') as f:
                reminders = json.load(f)
        else:
            reminders = []
        
        reminders.append(reminder)
        
        with open(reminders_file, 'w', encoding='utf-8') as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "message": f"已向 {assignee} 发送整改催办通知"
        }, ensure_ascii=False))])

class GenerateComplianceReportTool(BaseTool):
    name: str = "generate_compliance_report"
    description: str = "自动汇总隐患数据，生成月度安全合规报表"
    input_schema = {
        "type": "object",
        "properties": {
            "period": {"type": "string", "description": "报表周期"},
            "location": {"type": "string", "description": "位置"}
        },
        "description": "生成安全合规报表"
    }
    
    async def _call(self, period: str = "monthly", location: str = "") -> ToolResponse:
        actions_file = os.path.join(DATA_DIR, "corrective_actions.json")
        if os.path.exists(actions_file):
            with open(actions_file, 'r', encoding='utf-8') as f:
                actions = json.load(f)
        else:
            actions = []
        
        total = len(actions)
        completed = len([a for a in actions if a["status"] == "completed"])
        pending = len([a for a in actions if a["status"] == "pending"])
        overdue = len([a for a in actions if a["status"] == "overdue"])
        
        report = {
            "period": period,
            "location": location,
            "total_hazards": total,
            "completed_hazards": completed,
            "pending_hazards": pending,
            "overdue_hazards": overdue,
            "completion_rate": round(completed / total * 100, 2) if total > 0 else 0,
            "status": "generated"
        }
        
        reports_file = os.path.join(DATA_DIR, "compliance_reports.json")
        if os.path.exists(reports_file):
            with open(reports_file, 'r', encoding='utf-8') as f:
                reports = json.load(f)
        else:
            reports = []
        
        reports.append(report)
        
        with open(reports_file, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "report": report,
            "message": "安全合规报表已生成"
        }, ensure_ascii=False))])
