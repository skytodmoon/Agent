import json
import os
from agentscope.tool import ToolResponse
from common.base_tool import BaseTool
from agentscope.message import TextBlock
from configs.settings import DATA_DIR

class BomQueryTool(BaseTool):
    name: str = "bom_query"
    description: str = "查询产品的物料清单（BOM），包括所有零部件及其用量"
    input_schema = {
        "type": "object",
        "properties": {
            "product_id": {"type": "string", "description": "产品ID"}
        },
        "required": ["product_id"],
        "description": "查询产品BOM表"
    }
    
    async def _call(self, product_id: str) -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "bom.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            bom_data = json.load(f)
        
        if product_id in bom_data:
            product_info = bom_data[product_id]
            result = {
                "product_id": product_id,
                "product_name": product_info.get("name", ""),
                "materials": product_info.get("materials", [])
            }
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的产品BOM")])

class InventoryQueryTool(BaseTool):
    name: str = "inventory_query"
    description: str = "查询物料的现有库存、在途数量、送检数量等信息"
    input_schema = {
        "type": "object",
        "properties": {
            "material_code": {"type": "string", "description": "物料编码"},
            "warehouse": {"type": "string", "description": "仓库"}
        },
        "required": ["material_code"],
        "description": "查询物料库存"
    }
    
    async def _call(self, material_code: str, warehouse: str = "") -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "inventory.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            inventory_data = json.load(f)
        
        results = []
        for item in inventory_data:
            if item.get("material_code") == material_code or item.get("material_id") == material_code:
                if warehouse and item["warehouse"] != warehouse:
                    continue
                results.append(item)
        
        if results:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的库存信息")])

class PurchaseOrderQueryTool(BaseTool):
    name: str = "purchase_order_query"
    description: str = "查询物料的在途采购订单，包括供应商、交期、数量等信息"
    input_schema = {
        "type": "object",
        "properties": {
            "material_code": {"type": "string", "description": "物料编码"},
            "supplier_id": {"type": "string", "description": "供应商ID"}
        },
        "required": ["material_code"],
        "description": "查询在途采购订单"
    }
    
    async def _call(self, material_code: str, supplier_id: str = "") -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "purchase_orders.json")
        if not os.path.exists(filepath):
            return ToolResponse(content=[TextBlock(type="text", text="未找到采购订单数据")])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            po_data = json.load(f)
        
        results = []
        for item in po_data:
            if item["material_code"] == material_code and item["status"] == "pending":
                if supplier_id and item["supplier_id"] != supplier_id:
                    continue
                results.append(item)
        
        if results:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的在途采购订单")])

class SupplierQueryTool(BaseTool):
    name: str = "supplier_query"
    description: str = "查询供应商的联系方式、供应物料、交货周期等信息"
    input_schema = {
        "type": "object",
        "properties": {
            "supplier_id": {"type": "string", "description": "供应商ID"},
            "material_code": {"type": "string", "description": "物料编码"}
        },
        "description": "查询供应商信息"
    }
    
    async def _call(self, supplier_id: str = "", material_code: str = "") -> ToolResponse:
        filepath = os.path.join(DATA_DIR, "suppliers.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            suppliers = json.load(f)
        
        results = []
        for item in suppliers:
            if supplier_id and item["id"] == supplier_id:
                results.append(item)
            elif material_code:
                if material_code in item["materials"]:
                    results.append(item)
        
        if results:
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="未找到匹配的供应商信息")])

class SendReminderTool(BaseTool):
    name: str = "send_reminder"
    description: str = "自动推送供应商催交通知，提醒及时交货"
    input_schema = {
        "type": "object",
        "properties": {
            "supplier_id": {"type": "string", "description": "供应商ID"},
            "supplier_name": {"type": "string", "description": "供应商名称"},
            "material_code": {"type": "string", "description": "物料编码"},
            "material_name": {"type": "string", "description": "物料名称"},
            "quantity": {"type": "number", "description": "催交数量"},
            "due_date": {"type": "string", "description": "预计交期"}
        },
        "required": ["supplier_id", "material_code", "quantity"],
        "description": "发送供应商催交通知"
    }
    
    async def _call(self, supplier_id: str, material_code: str, quantity: float,
                   supplier_name: str = "", material_name: str = "", 
                   due_date: str = "") -> ToolResponse:
        reminder = {
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "material_code": material_code,
            "material_name": material_name,
            "quantity": quantity,
            "due_date": due_date,
            "status": "sent"
        }
        
        reminders_file = os.path.join(DATA_DIR, "reminders.json")
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
            "message": f"已向供应商 {supplier_name} 发送催交通知，物料: {material_name}，数量: {quantity}"
        }, ensure_ascii=False))])

class GenerateMaterialReportTool(BaseTool):
    name: str = "generate_material_report"
    description: str = "输出物料齐套率报表，标注风险等级与影响工单。可以接收BOM数据、库存数据和采购订单数据来计算齐套率"
    input_schema = {
        "type": "object",
        "properties": {
            "product_id": {"type": "string", "description": "产品ID"},
            "production_qty": {"type": "number", "description": "生产数量"},
            "bom_data": {"type": "string", "description": "BOM数据（JSON格式）"},
            "inventory_data": {"type": "string", "description": "库存数据（JSON格式）"},
            "po_data": {"type": "string", "description": "采购订单数据（JSON格式）"},
            "risk_items": {"type": "string", "description": "风险项数据（JSON格式）"}
        },
        "required": ["product_id", "production_qty"],
        "description": "生成物料齐套率报表"
    }
    
    async def _call(self, product_id: str, production_qty: float, 
                   bom_data: str = "", inventory_data: str = "", po_data: str = "",
                   risk_items: str = "") -> ToolResponse:
        report = {
            "product_id": product_id,
            "production_qty": production_qty,
            "total_materials": 0,
            "kitting_materials": 0,
            "kitting_rate": 0.0,
            "risk_items": [],
            "material_details": [],
            "status": "generated"
        }
        
        try:
            if bom_data:
                bom = json.loads(bom_data)
            else:
                filepath = os.path.join(DATA_DIR, "bom.json")
                with open(filepath, 'r', encoding='utf-8') as f:
                    bom = json.load(f)
            
            if product_id in bom:
                materials = bom[product_id].get("materials", [])
                report["total_materials"] = len(materials)
                
                inventory_map = {}
                if inventory_data:
                    try:
                        inv_data = json.loads(inventory_data)
                        if isinstance(inv_data, list):
                            for item in inv_data:
                                mat_id = item.get("material_id") or item.get("material_code")
                                if mat_id:
                                    inventory_map[mat_id] = item
                        elif isinstance(inv_data, dict):
                            for item in inv_data.values():
                                if isinstance(item, list):
                                    for i in item:
                                        mat_id = i.get("material_id") or i.get("material_code")
                                        if mat_id:
                                            inventory_map[mat_id] = i
                    except:
                        pass
                
                if not inventory_map:
                    filepath = os.path.join(DATA_DIR, "inventory.json")
                    with open(filepath, 'r', encoding='utf-8') as f:
                        inv_data = json.load(f)
                        for item in inv_data:
                            mat_id = item.get("material_id") or item.get("material_code")
                            if mat_id:
                                inventory_map[mat_id] = item
                
                po_map = {}
                if po_data:
                    try:
                        po_list = json.loads(po_data)
                        if isinstance(po_list, list):
                            for item in po_list:
                                mat_id = item.get("material_id") or item.get("material_code")
                                if mat_id:
                                    if mat_id not in po_map:
                                        po_map[mat_id] = 0
                                    po_map[mat_id] += item.get("quantity", 0)
                    except:
                        pass
                
                kitting_count = 0
                for mat in materials:
                    mat_id = mat.get("material_id") or mat.get("material_code")
                    qty_per_unit = mat.get("quantity_per_unit", 1)
                    total_needed = qty_per_unit * production_qty
                    
                    inv = inventory_map.get(mat_id, {})
                    current_stock = inv.get("quantity", 0)
                    safety_stock = inv.get("safety_stock", 0)
                    on_order = po_map.get(mat_id, 0)
                    
                    available = current_stock - safety_stock + on_order
                    shortage = max(0, total_needed - available)
                    
                    is_kitting = shortage == 0
                    if is_kitting:
                        kitting_count += 1
                    
                    risk_level = "低"
                    if shortage > 0:
                        if shortage >= total_needed * 0.5:
                            risk_level = "高"
                        elif shortage >= total_needed * 0.2:
                            risk_level = "中"
                        else:
                            risk_level = "低"
                    
                    report["material_details"].append({
                        "material_id": mat_id,
                        "quantity_per_unit": qty_per_unit,
                        "total_needed": total_needed,
                        "current_stock": current_stock,
                        "safety_stock": safety_stock,
                        "on_order": on_order,
                        "available": available,
                        "shortage": shortage,
                        "risk_level": risk_level,
                        "is_kitting": is_kitting
                    })
                    
                    if shortage > 0:
                        report["risk_items"].append({
                            "material_id": mat_id,
                            "shortage": shortage,
                            "risk_level": risk_level
                        })
                
                report["kitting_materials"] = kitting_count
                if report["total_materials"] > 0:
                    report["kitting_rate"] = round(kitting_count / report["total_materials"] * 100, 2)
        except Exception as e:
            pass
        
        reports_file = os.path.join(DATA_DIR, "material_reports.json")
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
            "message": "物料齐套率报表已生成"
        }, ensure_ascii=False, indent=2))])
