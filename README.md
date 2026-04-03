# 围棋战争(Weqi Battle)

**KataGo 多模型 AI 围棋对战平台 + OpenSkill 实时评级系统**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org)
[![uv](https://img.shields.io/badge/uv-Project%20Manager-4A3E4F)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

让不同版本的 **KataGo** 模型自动互相对战，并使用现代 **OpenSkill**（Plackett-Luce 模型）进行动态技能评级，比传统 Elo 更准确、更稳定。

---

## ✨ 特性

- 支持任意数量 KataGo 模型（.bin.gz）互相对战
- 使用 **OpenSkill** 实时计算 mu、sigma 和 ordinal 分数
- 自动切换先后手，公平对战
- 每局自动生成标准 SGF 棋谱（可直接用 Sabaki / KaTrain 打开复盘）
- 使用 `uv` 管理依赖，安装极简
- 代码简洁，易于二次开发（加模型、加网页天梯、加批量对战等）

---

## 📋 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/korman/weiqi-battle.git
cd weiqi-battle
```

### 2. 使用 uv 安装环境（推荐）

```bash
# 安装 uv（如果还没装）
# Windows: winget install --id=astral-sh.uv
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

uv sync          # 自动创建虚拟环境并安装依赖
uv run python -m pip list   # 查看已安装依赖
```

### 3. 准备文件

把以下文件放到项目根目录：

- katago.exe（推荐 OpenCL 版）
- my.cfg（运行 katago.exe genconfig 生成）
- 两个或多个 KataGo 模型（.bin.gz），例如：
  - kata1-zhizi-b28c512nbt-muonfd2.bin.gz（最强版）
  - 其他任意模型

### 4. 开始对战

```bash
uv run python katago_battle_openskill.py
```

程序会自动进行多局对战，并在终端实时显示 **OpenSkill 排行榜**，对战结束后生成 battle_xxx.sgf 棋谱文件。

------

## 📁 项目结构

```text
weiqi-battle/
├── katago_battle_openskill.py     # 主对战脚本（已集成 OpenSkill）
├── my.cfg                         # KataGo 配置文件
├── katago.exe                     # KataGo 执行文件
├── *.bin.gz                       # 你的 KataGo 模型文件
├── model_ratings.json             # 对战后自动保存的 rating 数据（下次可继续）
├── pyproject.toml                 # uv 项目配置文件
├── README.md
└── battle_*.sgf                   # 自动生成的棋谱（对战后出现）
```

------

## ⚙️ 配置说明

- 在 katago_battle_openskill.py 中修改以下变量即可自定义：

  ```python
  MODEL1 = "你的模型1.bin.gz"
  MODEL2 = "你的模型2.bin.gz"
  NUM_GAMES = 50          # 对战局数
  ```

- 建议在 my.cfg 中把 maxVisits 调到 **200~400**，这样对战速度更快（评级不需要太高思考量）。

------

## 📈 OpenSkill 评级

本项目使用 openskill 库的 **PlackettLuce** 模型：

- mu：技能值（越高越强）
- sigma：不确定性（局数越多越小）
- ordinal：综合实力分数（常用排序依据）

对战结束后会自动保存到 model_ratings.json，下次运行可继续累积评级。

------

## 🚀 后续计划（欢迎 PR）

-  Web 天梯排行榜（FastAPI + HTMX）
-  支持 3 个以上模型循环赛
-  自动生成 rating 变化曲线图
-  Docker 一键部署
-  Analysis Engine 模式（JSON 协议，更快）

------

## 🙏 致谢

- [KataGo](https://github.com/lightvector/KataGo) —— 目前最强开源围棋 AI
- [OpenSkill](https://github.com/OpenSkill-org/openskill.py) —— 现代技能评级算法
- 所有贡献模型的 KataGo 训练者

------

**有任何问题或想加功能，欢迎 Issue / PR！** 一起把这个项目打造成最强的 KataGo 模型天梯吧！🏆
