import asyncio
import sys

async def run_mvp1():
    from mvp1.main import run_fault_diagnosis_demo
    await run_fault_diagnosis_demo()

async def run_mvp2():
    from mvp2.main import run_quality_analysis_demo
    await run_quality_analysis_demo()

async def run_mvp3():
    from mvp3.main import run_material_kit_demo
    await run_material_kit_demo()

async def run_mvp4():
    from mvp4.main import run_reschedule_demo
    await run_reschedule_demo()

async def run_mvp5():
    from mvp5.main import run_safety_inspection_demo
    await run_safety_inspection_demo()

async def run_mvp6():
    from mvp6.main import run_ontology_governance_demo
    await run_ontology_governance_demo()

async def main():
    print("=" * 80)
    print("制造业6个梯度MVP Demo - 基于AgentScope 2.0")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        mvp_num = sys.argv[1]
        if mvp_num == "1":
            await run_mvp1()
        elif mvp_num == "2":
            await run_mvp2()
        elif mvp_num == "3":
            await run_mvp3()
        elif mvp_num == "4":
            await run_mvp4()
        elif mvp_num == "5":
            await run_mvp5()
        elif mvp_num == "6":
            await run_mvp6()
        else:
            print(f"无效的MVP编号: {mvp_num}，请输入1-6")
    else:
        print("请选择要运行的MVP：")
        print("1 - 核心设备故障诊断与工单闭环助手")
        print("2 - 质检缺陷根因追溯Agent")
        print("3 - 物料齐套核算与交期预警Agent")
        print("4 - 产线异常应急排程调度Agent")
        print("5 - 车间安全巡检与隐患整改闭环Agent")
        print("6 - 设备元数据治理与本体图谱推理Agent")
        print("\n使用方式: python run_all.py <编号>")

if __name__ == "__main__":
    asyncio.run(main())
