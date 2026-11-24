# 砂漏工坊 · 转化漏斗与分群留存分析平台

面向事件明细接入、漏斗步骤定义、转化率计算、分群切分、留存矩阵与口径对比的用户行为分析平台。

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 目录结构

```text
.
├── frontend/                 Vue 3 + Vite + TypeScript 前端
│   ├── src/views/WorkbenchView.vue|tsx  全部模块共享工作台
│   ├── src/data/modules.ts              18个业务模块配置
│   ├── src/api/              统一请求封装
│   └── vite.config.ts        dev server 配置（open: false）
├── backend/                  FastAPI（Python） 后端
│   ├── app/routers/resource.py  通用查询/导出/登记/动作接口
│   ├── app/services/<key>.py    每个模块独立领域逻辑
│   ├── app/services/base.py     共享服务骨架
│   └── app/store.py          内存数据仓库与示例数据
├── .gitignore
└── docker-compose.yml
```

## 启动

### 后端

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh
```

健康检查：`curl http://127.0.0.1:8013/api/health`

### 前端

```bash
cd frontend
npm ci
npm run dev
```

前端默认监听 `http://127.0.0.1:5186/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8013`。

## 业务模块

| 模块 | 目录 | 业务对象 | 主要字段 |
| --- | --- | --- | --- |
| 事件接入 | `event_intake` | 接入批次 | 批次编号、事件来源、窗口起点 |
| 漏斗定义 | `funnel_def` | 漏斗条目 | 漏斗编号、漏斗名称、步骤数 |
| 步骤配置 | `step_config` | 配置条目 | 配置编号、漏斗编号、步骤序号 |
| 转化计算 | `conv_calc` | 计算批次 | 计算编号、漏斗编号、统计日期 |
| 步骤明细 | `step_detail` | 明细条目 | 明细编号、计算编号、步骤序号 |
| 分群切分 | `cohort_split` | 分群条目 | 分群编号、切分维度、切分取值 |
| 分群追踪 | `cohort_track` | 追踪明细 | 追踪编号、分群编号、观察周期 |
| 留存矩阵 | `retain_matrix` | 矩阵条目 | 矩阵编号、分群编号、矩阵维度 |
| 口径对比 | `caliber_compare` | 对比记录 | 对比编号、漏斗编号、旧口径转化率 |
| 流失分析 | `drop_analysis` | 分析条目 | 分析编号、计算编号、流失步骤 |
| 分群规则 | `segment_rule` | 规则条目 | 规则编号、规则名称、圈选条件 |
| 指标看板 | `metric_board` | 看板快照 | 快照编号、统计日期、漏斗数量 |
| 事件去重 | `event_dedup` | 去重记录 | 去重编号、批次编号、重复条数 |
| 窗口调整 | `window_adjust` | 调整记录 | 调整编号、漏斗编号、原窗口期 |
| 路径下钻 | `path_drill` | 下钻条目 | 下钻编号、计算编号、下钻路径 |
| 流失预警 | `churn_alert` | 预警条目 | 预警编号、分群编号、流失阈值 |
| 重放校验 | `replay_verify` | 校验记录 | 校验编号、计算编号、原转化人数 |
| 延迟登记 | `data_delay` | 延迟记录 | 延迟编号、批次编号、预计到达 |
| 漏斗版本 | `funnel_version` | 版本条目 | 版本号、漏斗编号、变更摘要 |
| 导出任务 | `export_task` | 任务单 | 任务编号、导出范围、导出格式 |
| 访问审计 | `access_audit` | 审计明细 | 审计编号、访问者、访问数据集 |
| 洞察笔记 | `insight_note` | 笔记条目 | 笔记编号、分析编号、洞察摘要 |

## 约定

- 全部模块共享`frontend/src/views/WorkbenchView.vue|tsx`和一套资源路由。
- 每个模块仍保留独立`backend/app/services/<模块>.py`；纯前端保留
  `frontend/src/domain/<模块>.ts`，用于承载真实业务差异并维持36题位容量。
- 列表接口统一返回 `{ items, total, page, size }`，动作接口统一返回 `{ ok, message }`。
- 状态流转只允许在 `app/services` 里改，路由层不做业务判断。

领域：数据工程
子方向：数据分析与数据应用
