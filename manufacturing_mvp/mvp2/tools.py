import json
import os
from agentscope.tool import ToolResponse
from common.base_tool import BaseTool
from agentscope.message import TextBlock
from common.utils import generate_id
from configs.settings import DATA_DIR

class DefectAcceptTool(BaseTool):
    name: str = "defect_accept"
    description: str = "接收并标准化缺陷信息，锁定对应生产批次、时间范围、关联工位"
    input_schema = {
        "type": "object",
        "properties": {
            "defect_type": {"type": "string", "description": "缺陷类型"},
            "batch_no": {"type": "string", "description": "批次号"},
            "location": {"type": "string", "description": "工位"},
            "severity": {"type": "string", "description": "严重程度"},
            "operator": {"type": "string", "description": "操作人员"}
        },
        "required": ["defect_type", "batch_no"],
        "description": "标准化缺陷信息"
    }
    
    async def _call(self, defect_type: str, batch_no: str, location: str = "", 
                   severity: str = "中", operator: str = "") -> ToolResponse:
        defect_record = {
            "id": generate_id("DF-"),
            "defect_type": defect_type,
            "batch_no": batch_no,
            "location": location,
            "severity": severity,
            "operator": operator,
            "status": "pending"
        }
        
        defects_file = os.path.join(DATA_DIR, "defects.json")
        if os.path.exists(defects_file):
            with open(defects_file, 'r', encoding='utf-8') as f:
                defects = json.load(f)
        else:
            defects = []
        
        defects.append(defect_record)
        
        with open(defects_file, 'w', encoding='utf-8') as f:
            json.dump(defects, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "defect_id": defect_record["id"],
            "message": f"缺陷记录 {defect_record['id']} 已保存"
        }, ensure_ascii=False))])

class ProcessDataQueryTool(BaseTool):
    name: str = "process_data_query"
    description: str = "查询生产批次的工艺参数，包括温度、压力、速度等关键参数"
    input_schema = {
        "type": "object",
        "properties": {
            "batch_no": {"type": "string", "description": "批次号"},
            "workstation": {"type": "string", "description": "工位"}
        },
        "required": ["batch_no"],
        "description": "查询批次的工艺参数"
    }
    
    async def _call(self, batch_no: str, workstation: str = "") -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "process_data.json")
        if not os.path.exists(filepath):
            return ToolResponse(content=[TextBlock(type="text", text="未找到工艺数据")])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            process_data = json.load(f)
        
        results = []
        for item in process_data:
            if item["batch_no"] == batch_no:
                if workstation and item["workstation"] != workstation:
                    continue
                results.append(item)
        
        if results:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的工艺数据")])

class EquipmentDataQueryTool(BaseTool):
    name: str = "equipment_data_query"
    description: str = "查询设备运行数据，包括温度、振动、电流等参数"
    input_schema = {
        "type": "object",
        "properties": {
            "equipment_id": {"type": "string", "description": "设备编号"},
            "start_time": {"type": "string", "description": "开始时间"},
            "end_time": {"type": "string", "description": "结束时间"}
        },
        "required": ["equipment_id"],
        "description": "查询设备运行数据"
    }
    
    async def _call(self, equipment_id: str, start_time: str = "", end_time: str = "") -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "equipment_data.json")
        if not os.path.exists(filepath):
            return ToolResponse(content=[TextBlock(type="text", text="未找到设备运行数据")])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            equipment_data = json.load(f)
        
        results = []
        for item in equipment_data:
            if item["equipment_id"] == equipment_id:
                results.append(item)
        
        if results:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(results[:10], ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的设备运行数据")])

class MaterialBatchQueryTool(BaseTool):
    name: str = "material_batch_query"
    description: str = "查询生产批次使用的物料批次、供应商、质检状态等信息"
    input_schema = {
        "type": "object",
        "properties": {
            "batch_no": {"type": "string", "description": "批次号"},
            "material_code": {"type": "string", "description": "物料编码"}
        },
        "required": ["batch_no"],
        "description": "查询批次使用的物料信息"
    }
    
    async def _call(self, batch_no: str, material_code: str = "") -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "material_batch.json")
        if not os.path.exists(filepath):
            return ToolResponse(content=[TextBlock(type="text", text="未找到物料批次数据")])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            material_data = json.load(f)
        
        results = []
        for item in material_data:
            if item["product_batch"] == batch_no:
                if material_code and item["material_code"] != material_code:
                    continue
                results.append(item)
        
        if results:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的物料批次数据")])

class RootCauseAnalysisTool(BaseTool):
    name: str = "root_cause_analysis"
    description: str = "匹配质量知识库与历史异常案例，输出根因与整改建议"
    input_schema = {
        "type": "object",
        "properties": {
            "defect_type": {"type": "string", "description": "缺陷类型"},
            "process_data": {"type": "string", "description": "工艺参数数据"},
            "equipment_data": {"type": "string", "description": "设备运行数据"},
            "material_data": {"type": "string", "description": "物料批次数据"}
        },
        "required": ["defect_type"],
        "description": "根因分析"
    }
    
    async def _call(self, defect_type: str, process_data: str = "", 
                   equipment_data: str = "", material_data: str = "") -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "quality_knowledge_base.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        
        results = []
        for item in knowledge_base:
            if defect_type in item["defect_type"]:
                results.append(item)
        
        if results:
            analysis_result = {
                "defect_type": defect_type,
                "possible_causes": [],
                "recommendations": []
            }
            
            for item in results:
                if "cause" in item:
                    analysis_result["possible_causes"].append(item["cause"])
                    analysis_result["recommendations"].append(item["recommendation"])
                else:
                    analysis_result["possible_causes"].extend(item.get("possible_causes", []))
                    analysis_result["recommendations"].extend(item.get("solutions", []))
            
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(analysis_result, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的根因分析方案，请联系质量工程师")])

class CreateQualityExceptionOrderTool(BaseTool):
    name: str = "create_quality_exception_order"
    description: str = "生成质量异常处理单，推送至责任部门"
    input_schema = {
        "type": "object",
        "properties": {
            "defect_id": {"type": "string", "description": "缺陷记录ID"},
            "batch_no": {"type": "string", "description": "批次号"},
            "defect_type": {"type": "string", "description": "缺陷类型"},
            "root_cause": {"type": "string", "description": "根因分析结果"},
            "recommendations": {"type": "string", "description": "整改建议"},
            "responsible_department": {"type": "string", "description": "责任部门"}
        },
        "required": ["defect_id", "batch_no", "defect_type"],
        "description": "创建质量异常处理单"
    }
    
    async def _call(self, defect_id: str, batch_no: str, defect_type: str,
                   root_cause: str = "", recommendations: str = "", 
                   responsible_department: str = "") -> ToolResponse:
        exception_order = {
            "id": generate_id("QE-"),
            "defect_id": defect_id,
            "batch_no": batch_no,
            "defect_type": defect_type,
            "root_cause": root_cause,
            "recommendations": recommendations,
            "responsible_department": responsible_department,
            "status": "pending"
        }
        
        orders_file = os.path.join(DATA_DIR, "quality_exception_orders.json")
        if os.path.exists(orders_file):
            with open(orders_file, 'r', encoding='utf-8') as f:
                orders = json.load(f)
        else:
            orders = []
        
        orders.append(exception_order)
        
        with open(orders_file, 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
        
        return ToolResponse(content=[TextBlock(type="text", text=json.dumps({
            "status": "success",
            "exception_order_id": exception_order["id"],
            "message": f"质量异常处理单 {exception_order['id']} 已创建"
        }, ensure_ascii=False))])
