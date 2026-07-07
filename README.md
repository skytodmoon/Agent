# 🏭 制造业Agent Demo平台

基于AgentScope 2.0构建的制造业智能Agent演示平台，包含6个面向制造业核心业务场景的MVP演示。

## 🎯 项目简介

本项目旨在展示如何利用大语言模型和Agent技术解决制造业中的实际业务问题。通过多Agent协作，实现自动化的业务流程闭环，包括故障诊断、质量追溯、物料齐套、排程调度、安全巡检和设备准入审核等场景。

## 🛠️ 技术栈

- **框架**: AgentScope 2.0
- **Web界面**: Streamlit
- **语言**: Python 3.11+
- **数据存储**: JSON文件（演示用）
- **知识图谱**: 基于本体的知识图谱推理

## 🚀 快速开始

### 环境要求

```bash
Python >= 3.11
pip >= 23.0
```

### 安装依赖

```bash
cd Agent/manufacturing_mvp
pip install -r requirements.txt
```

### 配置环境变量

```bash
# 使用OpenAI模型（可选）
export OPENAI_API_KEY=your_openai_api_key

# 使用阿里云通义千问（可选）
export DASHSCOPE_API_KEY=your_dashscope_api_key

# 使用本地模型（默认）
export MODEL_TYPE=local
```

### 启动服务

```bash
# 启动Streamlit Web界面
cd manufacturing_mvp
streamlit run app.py

# 或运行单个MVP演示
python -m mvp1.main
python -m mvp2.main
python -m mvp3.main
python -m mvp4.main
python -m mvp5.main
python -m mvp6.main
```

## 📋 MVP场景介绍

### MVP1: 核心设备故障诊断与工单闭环助手

**解决痛点**: 设备故障排查靠经验、报修流程繁琐

**流程**: 故障受理 → 智能诊断 → 工单生成 → 派单流转

**Agent组成**:
- 📝 故障受理Agent - 接收故障报告
- 🔍 故障诊断Agent - 匹配知识库输出排查方案
- 📋 工单流转Agent - 生成维修工单并智能派单

---

### MVP2: 质检缺陷根因追溯Agent

**解决痛点**: 质检缺陷根因定位耗时

**流程**: 缺陷录入 → 数据检索 → 根因分析 → 整改建议

**Agent组成**:
- 📝 缺陷受理Agent - 接收缺陷信息
- 🔍 数据检索Agent - 拉取工艺、设备、物料数据
- 🧠 根因分析Agent - 交叉分析定位根因
- 📄 单据生成Agent - 生成整改建议和报告

---

### MVP3: 物料齐套核算与交期预警Agent

**解决痛点**: 物料齐套核算效率低、缺料预警不及时

**流程**: 需求拆解 → 库存查询 → 风险预警 → 报表生成

**Agent组成**:
- 📊 需求拆解Agent - 拆解BOM物料需求
- 🔍 库存查询Agent - 查询库存和在途数量
- ⚠️ 风险预警Agent - 识别缺料风险并推送预警
- 📈 报表生成Agent - 生成齐套分析报表

---

### MVP4: 产线异常应急排程调度Agent

**解决痛点**: 产线异常应急排程慢

**流程**: 异常感知 → 排程计算 → 人工审批 → 执行同步

**Agent组成**:
- 🛡️ 异常感知Agent - 接收异常事件评估影响
- 🔢 排程计算Agent - 生成多套排程调整方案
- ✅ 人工审批Agent - 支持人工审批流程
- 🚀 执行同步Agent - 同步执行排程调整

---

### MVP5: 车间安全巡检与隐患整改闭环Agent

**解决痛点**: 安全巡检记录分散、隐患整改跟踪难

**流程**: 巡检受理 → 分级判定 → 整改跟踪 → 合规报表

**Agent组成**:
- 📝 巡检受理Agent - 接收巡检记录
- 🏷️ 分级判定Agent - 自动判定隐患等级
- 🔄 整改跟踪Agent - 生成整改通知单并跟踪闭环
- 📋 合规报表Agent - 生成安全合规报表

---

### MVP6: 新设备MES上线准入自动审核

**解决痛点**: 新设备上线流程繁琐、数据标准不统一

**流程**: 注册监控 → 规则校验 → 审批决策 → 执行同步

**Agent组成**:
- 👀 注册监控Agent - 监控待审核注册请求
- ✅ 规则校验Agent - 基于本体规则引擎校验
- 🔍 审批决策Agent - 自动审批决策
- 🚀 执行同步Agent - 同步至MES和ERP系统

**核心能力**:
- 跨系统知识图谱构建（MES+ERP+产线数据）
- 传递性推理（设备→产线→车间隐含关系发现）
- 跨系统一致性校验（检测数据冲突）
- 产线容量约束校验
- 本体规则引擎驱动的智能审核

## 📁 项目结构

```
Agent/
├── manufacturing_mvp/           # 主应用目录
│   ├── common/                  # 公共模块
│   │   ├── base_tool.py         # 工具基类
│   │   ├── ontology_graph.py    # 本体知识图谱
│   │   ├── data_models.py       # 数据模型
│   │   └── utils.py             # 工具函数
│   ├── configs/                 # 配置文件
│   │   ├── model_config.py      # 模型配置
│   │   └── settings.py          # 全局设置
│   ├── data/                    # 数据文件
│   │   ├── equipment.json       # 设备数据
│   │   ├── mes_equipment.json   # MES设备数据
│   │   ├── erp_equipment.json   # ERP设备数据
│   │   ├── ontology.json        # 本体定义
│   │   └── ...                  # 其他数据文件
│   ├── mvp1~mvp6/               # MVP场景模块
│   │   ├── agents.py            # Agent定义
│   │   ├── tools.py             # 工具定义
│   │   └── main.py              # 入口文件
│   ├── app.py                   # Streamlit Web应用
│   └── run_all.py               # 批量运行脚本
└── README.md                    # 项目说明
```

## 🔧 使用说明

### Web界面操作

1. 启动Streamlit服务: `streamlit run app.py`
2. 在左侧边栏选择要演示的MVP场景
3. 选择模型类型（local/openai/dashscope）
4. 填写输入参数
5. 点击「开始执行」按钮启动流程
6. 实时查看Agent执行过程和日志

### 命令行操作

```bash
# 运行单个MVP演示
cd manufacturing_mvp
python -m mvp1.main

# 查看详细日志
python -m mvp6.main 2>&1 | grep -E "\[本体\]|规则引擎|批准|拒绝"
```

## 📊 数据说明

项目使用JSON文件作为演示数据存储，包含以下主要数据：

| 数据文件 | 说明 |
|---------|------|
| `equipment.json` | 设备主数据 |
| `mes_equipment.json` | MES系统设备数据 |
| `erp_equipment.json` | ERP系统设备数据 |
| `production_units.json` | 产线和车间数据 |
| `ontology.json` | 本体定义（类、关系、约束） |
| `bom.json` | 物料清单数据 |
| `inventory.json` | 库存数据 |
| `fault_knowledge_base.json` | 故障知识库 |
| `quality_knowledge_base.json` | 质量知识库 |

## 🎨 Agent架构设计

每个MVP场景采用多Agent协作架构，遵循以下设计原则：

1. **职责分离**: 每个Agent专注于单一职责
2. **消息驱动**: Agent之间通过消息传递协作
3. **工具增强**: Agent可以调用工具获取外部数据
4. **可观测性**: 支持实时日志和执行跟踪

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！