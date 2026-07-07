from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class Equipment(BaseModel):
    id: str = Field(..., description="设备编号")
    name: str = Field(..., description="设备名称")
    type: str = Field(..., description="设备类型")
    location: str = Field(..., description="所在工位")
    status: str = Field(default="running", description="设备状态")

class FaultReport(BaseModel):
    id: str = Field(..., description="故障报告ID")
    equipment_id: str = Field(..., description="设备编号")
    equipment_name: str = Field(..., description="设备名称")
    location: str = Field(..., description="工位")
    description: str = Field(..., description="故障描述")
    priority: str = Field(default="P2", description="优先级")
    reported_by: str = Field(..., description="报告人")
    reported_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="pending", description="状态")

class WorkOrder(BaseModel):
    id: str = Field(..., description="工单ID")
    fault_report_id: str = Field(..., description="关联故障报告ID")
    title: str = Field(..., description="工单标题")
    description: str = Field(..., description="工单描述")
    assignee: str = Field(..., description="指派工程师")
    priority: str = Field(default="P2", description="优先级")
    status: str = Field(default="pending", description="状态")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

class QualityDefect(BaseModel):
    id: str = Field(..., description="缺陷ID")
    type: str = Field(..., description="缺陷类型")
    batch_no: str = Field(..., description="批次号")
    location: str = Field(..., description="工位")
    severity: str = Field(default="medium", description="严重程度")
    description: str = Field(..., description="缺陷描述")
    reported_at: datetime = Field(default_factory=datetime.now)

class RootCauseAnalysis(BaseModel):
    defect_id: str = Field(..., description="缺陷ID")
    root_causes: List[str] = Field(default_factory=list, description="根因列表")
    recommendations: List[str] = Field(default_factory=list, description="整改建议")
    analysis_time: datetime = Field(default_factory=datetime.now)

class Material(BaseModel):
    id: str = Field(..., description="物料编码")
    name: str = Field(..., description="物料名称")
    unit: str = Field(..., description="单位")
    category: str = Field(..., description="物料类别")

class Inventory(BaseModel):
    material_id: str = Field(..., description="物料编码")
    warehouse: str = Field(..., description="仓库")
    quantity: float = Field(..., description="库存数量")
    safety_stock: float = Field(default=0, description="安全库存")

class PurchaseOrder(BaseModel):
    id: str = Field(..., description="采购订单ID")
    material_id: str = Field(..., description="物料编码")
    supplier_id: str = Field(..., description="供应商ID")
    quantity: float = Field(..., description="数量")
    expected_delivery_date: datetime = Field(..., description="预计交货日期")
    status: str = Field(default="pending", description="状态")

class ProductionOrder(BaseModel):
    id: str = Field(..., description="生产工单ID")
    product_id: str = Field(..., description="产品ID")
    quantity: int = Field(..., description="计划数量")
    status: str = Field(default="pending", description="状态")
    scheduled_start: datetime = Field(..., description="计划开始时间")
    scheduled_end: datetime = Field(..., description="计划结束时间")

class ProductionException(BaseModel):
    id: str = Field(..., description="异常ID")
    type: str = Field(..., description="异常类型")
    description: str = Field(..., description="异常描述")
    affected_orders: List[str] = Field(default_factory=list, description="受影响工单")
    severity: str = Field(default="medium", description="严重程度")
    reported_at: datetime = Field(default_factory=datetime.now)

class SafetyHazard(BaseModel):
    id: str = Field(..., description="隐患ID")
    type: str = Field(..., description="隐患类型")
    location: str = Field(..., description="位置")
    level: str = Field(default="medium", description="隐患等级")
    description: str = Field(..., description="隐患描述")
    reported_by: str = Field(..., description="报告人")
    reported_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="pending", description="状态")

class CorrectiveAction(BaseModel):
    id: str = Field(..., description="整改单ID")
    hazard_id: str = Field(..., description="关联隐患ID")
    responsible_dept: str = Field(..., description="责任部门")
    deadline: datetime = Field(..., description="整改截止日期")
    status: str = Field(default="pending", description="状态")
    completed_at: Optional[datetime] = None
