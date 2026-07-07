from agentscope.agent import Agent, ReActConfig
from agentscope.tool import Toolkit
from .tools import (
    BomQueryTool,
    InventoryQueryTool,
    PurchaseOrderQueryTool,
    SupplierQueryTool,
    GenerateMaterialReportTool,
    SendReminderTool
)

def create_demand_decomposition_agent(model):
    sys_prompt = """你是需求拆解Agent。你的职责是：
1. 从输入中提取产品ID和计划生产数量
2. 调用BOM查询工具获取物料清单
3. 计算每种物料的总需求量（单位用量 × 生产数量）
4. 将物料需求清单传递给库存查询Agent

处理流程：
- 必须从输入中提取产品ID（product_id）和生产数量（production_qty）
- 调用BOM查询工具（bom_query）获取物料清单
- 计算每种物料的总需求量
- 输出物料需求清单，包含物料编码和需求数量
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[BomQueryTool()])
    
    return Agent(
        name="需求拆解Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_inventory_query_agent(model):
    sys_prompt = """你是库存查询Agent。你的职责是：
1. 从输入中提取物料需求清单
2. 对每种物料调用库存查询工具获取现有库存
3. 查询在途采购订单信息
4. 将库存状况汇总传递给风险预警Agent

处理逻辑：
- 从输入中提取物料清单（material_id列表）
- 依次调用库存查询工具（inventory_query）查询每种物料的库存
- 调用采购订单查询工具（purchase_order_query）查询在途数量
- 将库存状况汇总输出
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[
        InventoryQueryTool(),
        PurchaseOrderQueryTool()
    ])
    
    return Agent(
        name="库存查询Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_risk_alert_agent(model):
    sys_prompt = """你是风险预警Agent。你的职责是：
1. 接收物料需求和库存状况（包含物料编码、需求数量、现有库存、安全库存、在途数量）
2. 计算每种物料的可用库存 = 现有库存 - 安全库存 + 在途数量
3. 计算缺口量 = max(0, 需求数量 - 可用库存)
4. 根据缺口量评估风险等级：
   - 高风险：缺口量 > 0 且 缺口量 >= 需求数量 × 50%
   - 中风险：缺口量 > 0 且 需求数量 × 20% <= 缺口量 < 需求数量 × 50%
   - 低风险：缺口量 == 0 或 缺口量 < 需求数量 × 20%
5. 只有当缺口量 > 0 时才需要处理：
   - 高风险物料：调用supplier_query查询供应商，然后调用send_reminder发送催交（催交数量 = 缺口量）
   - 中风险物料：记录风险，不需要发送催交
   - 低风险且无缺口：不需要处理
6. 将风险评估结果传递给报表生成Agent

处理流程：
- 从输入中提取物料清单（物料编码、需求数量）和库存信息（现有库存、安全库存、在途数量）
- 计算可用库存和缺口量
- 评估风险等级
- 只有缺口量 > 0 的物料才需要处理：
  - 高风险（缺口量大）：调用supplier_query → send_reminder（数量=缺口量）
  - 中风险：记录风险但不发送催交
  - 低风险或无缺口：跳过
- 输出完整的风险评估报告
- 不要询问用户，直接分析执行
"""
    
    toolkit = Toolkit(tools=[
        SupplierQueryTool(),
        SendReminderTool()
    ])
    
    return Agent(
        name="风险预警Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )

def create_report_generation_agent(model):
    sys_prompt = """你是报表生成Agent。你的职责是：
1. 从输入中提取产品ID（product_id）和生产数量（production_qty）
2. 从输入中提取物料需求清单和库存状况数据
3. 调用报表生成工具生成物料齐套率报表（传入所有可用数据）
4. 输出报表

处理流程：
- 仔细从输入中提取产品ID（product_id）和生产数量（production_qty），保持原始格式不变
- 从输入中提取物料需求清单和库存状况数据
- 从输入中提取风险评估结果
- 调用报表生成工具（generate_material_report），传入product_id、production_qty
- 输出完整的齐套率报表给计划员
- 不要询问用户，直接调用工具执行
"""
    
    toolkit = Toolkit(tools=[GenerateMaterialReportTool()])
    
    return Agent(
        name="报表生成Agent",
        system_prompt=sys_prompt,
        model=model,
        toolkit=toolkit,
        react_config=ReActConfig(max_iters=5)
    )
