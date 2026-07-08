import asyncio
import json
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from agentscope.message import Msg, TextBlock
from .agents import (
    create_process_monitor_agent,
    create_event_handling_agent,
    create_emergency_response_agent,
    create_process_management_agent
)
from .tools import GenerateProcessGraphVisualizationTool
from configs.model_config import get_model
from configs.settings import DATA_DIR

def start_visualization_server(port=8080):
    class CustomHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
        
        def log_message(self, format, *args):
            pass
    
    server = HTTPServer(("localhost", port), CustomHandler)
    print(f"\n🌐 流程工业知识图谱可视化服务已启动: http://localhost:{port}/graph_visualization.html")
    server.serve_forever()

async def run_process_industry_demo():
    print("\n" + "=" * 80)
    print("🏭 MVP7 - 流程工业知识图谱演示 - PP聚合装置")
    print("=" * 80)
    print("\n📋 场景说明:")
    print("   本场景展示化工生产流程中的知识图谱应用，包含:")
    print("   1. 预构建知识图谱: 设备本体、生产单元、物料流向关系")
    print("   2. 事件驱动架构: 设备故障、告警、维护等事件触发")
    print("   3. 语义推理: 物料流向传递性推理、工艺约束校验")
    print("   4. 影响分析: 设备异常对下游设备和工艺的影响")
    print("   5. 应急响应: 自动生成应急预案和操作建议")
    print("=" * 80)
    
    print("\n[步骤1] 流程监控Agent - 查询设备状态和物料流向...")
    monitor_agent = create_process_monitor_agent(get_model())
    monitor_msg = Msg(name="user", content=[TextBlock(type="text", text="查询所有设备状态，检查工艺约束，提供监控概览")], role="user")
    monitor_result = await monitor_agent.reply(monitor_msg)
    print(f"[监控结果]: {monitor_result.content}")
    print("-" * 80)
    
    print("\n[步骤2] 事件处理Agent - 模拟设备故障事件...")
    event_agent = create_event_handling_agent(get_model())
    event_msg = Msg(name="user", content=[TextBlock(type="text", text="处理设备故障事件：PMP-001进料泵故障，分析对下游设备的影响")], role="user")
    event_result = await event_agent.reply(event_msg)
    print(f"[事件处理结果]: {event_result.content}")
    print("-" * 80)
    
    print("\n[步骤3] 应急响应Agent - 生成应急预案和操作建议...")
    response_agent = create_emergency_response_agent(get_model())
    response_msg = Msg(name="user", content=[TextBlock(type="text", text="针对PMP-001进料泵故障，生成应急预案和操作建议")], role="user")
    response_result = await response_agent.reply(response_msg)
    print(f"[应急响应结果]: {response_result.content}")
    print("-" * 80)
    
    print("\n[步骤4] 流程管理Agent - 执行完整异常处理流程...")
    management_agent = create_process_management_agent(get_model())
    management_msg = Msg(name="user", content=[TextBlock(type="text", text="执行完整流程：监控→检测→分析→响应→更新图谱")], role="user")
    management_result = await management_agent.reply(management_msg)
    print(f"[流程管理结果]: {management_result.content}")
    print("-" * 80)
    
    print("\n[步骤5] 知识图谱可视化 - 生成可视化数据...")
    print("这将生成节点、关系、物料流向等可视化数据，并启动可视化服务")
    visualization_tool = GenerateProcessGraphVisualizationTool()
    visualization_result = await visualization_tool._call()
    print(f"[可视化数据生成成功]")
    
    server_thread = threading.Thread(target=start_visualization_server, args=(8080,), daemon=True)
    server_thread.start()
    time.sleep(1)
    
    print("=" * 80)
    print("\n📊 MVP7 - 流程工业知识图谱可视化已准备就绪！")
    print("   请在浏览器中打开: http://localhost:8080/graph_visualization.html")
    print("   可视化功能包含:")
    print("   - PP聚合装置完整设备图谱")
    print("   - 物料流向动画演示")
    print("   - 设备状态监控面板")
    print("   - 事件影响分析路径")

if __name__ == "__main__":
    asyncio.run(run_process_industry_demo())