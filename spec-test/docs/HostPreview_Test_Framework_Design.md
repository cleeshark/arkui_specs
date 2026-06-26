# SpecTest HostPreview 测试框架设计（实现对齐版）

> 文档版本: v1.3  
> 更新时间: 2026-06-26  
> 适用工程: `arkui-specs/spec-test`

---

## 1. 目标与范围

本文档描述 `arkui-specs/spec-test` 当前已落地的 HostPreview 自动化测试框架实现，目标是：

1. 让用例目录与 `specs/` 路径保持可追溯映射。
2. 通过 Previewer + Inspector 做可重复的布局断言。
3. 支持全量执行与按 `suite/case` 精确执行。
4. 通过 `previewer/previewer-20260625.tar.gz` 提供 Previewer 完整包归档，支持在独立 `spec-test` 仓库中开箱即用地运行 HostPreview。

当前验证重点是 layout 类属性，已覆盖 size、position、flex 等属性用例。

---

## 2. 当前实现总览

### 2.1 执行模式

`run_feature.sh` 不接受 `--url` 入参，统一通过“用例管理清单”驱动执行：

1. 编译 HAP。
2. 解析 `spec_cases/**/suite.manifest.json` + `expected/expected.json`。
3. 校验 case URL 是否在 `main_pages.json` 注册。
4. 逐 case 启动 Previewer 并按 URL 直达页面。
5. 按 `operationSequence` 顺序执行操作（点击注入、滑动、等待等）。
6. 采集 Inspector。
7. 断言并输出报告。

说明：

- 自动化执行不依赖 `pages/Index` 的业务逻辑。
- 页面加载入口是 case URL（通过 Previewer `-url` 指定）。

### 2.2 当前可用执行粒度

- 全量：执行所有可解析 case。
- `--suite-id <suite-id>`：执行指定 suite。
- `--case-id <case-id>`：执行指定 case。
- `--archive-screenshot`：开启截图归档（默认不归档）。
- `--openharmony-root <path>`：指定 OpenHarmony 源码根目录，用于 build 工具链和默认 Previewer 候选路径。

### 2.3 运行时体验

- 阶段进度以黄色加粗输出，例如 `[3/6] [1/28] Collect inspector ...`。
- `collect_inspector.sh` 每个 case 会打印实际使用的 `Previewer bin: ...`。
- 汇总结果中 `total_cases` 使用青色，`failed_cases=0` 使用绿色，`failed_cases>0` 使用红色。
- 脚本退出时会清理本轮新增的 `Xvfb` 残留进程；如有清理动作，会打印 `Cleaning Xvfb processes: <pid...>`。
- 当 `OPENHARMONY_ROOT` 推导到 `/` 时，脚本立即提示使用 `--openharmony-root <OpenHarmonyRoot>`。

---

## 3. 框架组件与职责

### 3.1 组件清单

| 组件 | 文件 | 职责 |
|---|---|---|
| 执行编排 | `tools/host_preview/run_feature.sh` | build、生成执行计划、逐 case 调用采集与断言、汇总退出码 |
| 计划解析 | `tools/host_preview/resolve_case_plan.py` | 扫描 suite/expected，应用过滤条件，校验路由，生成 `case_plan.json` |
| 路径解析 | `tools/host_preview/common.sh` | 运行时解析 Previewer 路径，提供 `Xvfb` 快照与清理辅助函数，避免脚本硬编码绝对路径 |
| 操作执行器 | `tools/host_preview/execute_operations.py` | 读取 `operationSequence` 并按顺序执行 `wait/click/swipe/action` |
| Inspector 采集 | `tools/host_preview/collect_inspector.sh` | 拉起 Previewer，执行操作序列，采集 Inspector，保存原始响应 |
| 断言器 | `tools/host_preview/assert_cases.py` | 解析 inspector 响应，按 `targetNodeId` 对比 `expectedRect`，输出 `report.json/md` |
| 汇总器 | `tools/host_preview/merge_report.py` | 汇总单 case 报告，产出 `summary_report.json/md` |
| 调试脚本 | `tools/host_preview/run_inspector_only.sh` | 仅采集 inspector（不做断言） |

### 3.2 数据流

1. `run_feature.sh` 生成本次 `RUN_ID` 与输出目录。
2. `resolve_case_plan.py` 输出 `case_plan.json`（已完成 route 校验）。
3. `run_feature.sh` 将 case_plan 展平成 `case_lines.txt`。
4. 对每条 case：
   - `collect_inspector.sh` 拉起 Previewer，并调用 `execute_operations.py` 执行操作序列。
   - `collect_inspector.sh` 产出 `operations_runtime_response.txt`、`inspector_runtime_response.txt`、`screenshot.png`、`previewer.log`。
   - `assert_cases.py` 产出 `report.json`、`report.md`。
5. `merge_report.py` 聚合单 case 报告，产出总报告。
6. `run_feature.sh` 输出 `total_cases`、`failed_cases`，失败时返回非 0。

---

## 4. 用例目录与 spec 路径映射

### 4.1 映射规则

- 规格路径：`specs/<L1>/<L2>/<L3>/Feat-xx-<name>-spec.md`
- 用例路径：`entry/src/main/ets/spec_cases/<L1>/<L2>/<L3>/Feat-xx-<name>/`

示例：

- `specs/04-common-capability/03-common-attributes/01-layout-attributes/Feat-01-size-properties-spec.md`
- `entry/src/main/ets/spec_cases/04-common-capability/03-common-attributes/01-layout-attributes/Feat-01-size-properties/`

### 4.2 当前落地目录结构

```text
arkui-specs/
├── previewer/
│   └── previewer-20260625.tar.gz  # Previewer 完整包归档，约 209 MB
└── spec-test/
    ├── tools/host_preview/
    │   ├── run_feature.sh
    │   ├── resolve_case_plan.py
    │   ├── common.sh
    │   ├── execute_operations.py
    │   ├── collect_inspector.sh
    │   ├── assert_cases.py
    │   ├── merge_report.py
    │   └── run_inspector_only.sh
    ├── .report/
    │   └── <YYYYMMDD_HHMMSS>/run_feature/...
    └── entry/src/main/
        ├── ets/spec_cases/
        │   └── 04-common-capability/03-common-attributes/01-layout-attributes/
        │       └── Feat-01-size-properties/
        │           ├── feature.manifest.json
        │           └── suites/
        │               └── suite-01-width-height-basic/
        │                   ├── suite.manifest.json
        │                   ├── cases/
        │                   │   ├── case_001_width_height_basic.ets
        │                   │   ├── case_002_width_height_basic.ets
        │                   │   └── case_003_width_height_zero.ets
        │                   └── expected/expected.json
        └── resources/base/profile/main_pages.json
```

---

## 5. 配置契约（当前实现）

### 5.1 `feature.manifest.json`

当前主要作为 feature 元数据记录，包含：

- `featureId`
- `featureName`
- `specPath`
- `targetApi`
- `suites`

说明：当前执行计划生成不直接依赖 `feature.manifest.json`，后续可扩展为 feature 级筛选入口。

### 5.2 `suite.manifest.json`

当前实现中用于提供 suite 元数据及 case URL 映射。`cases[]` 至少包含：

- `caseId`
- `nodeId`
- `url`

### 5.3 `expected/expected.json`

断言输入源。`cases[]` 至少包含：

- `caseId`
- `targetNodeId`
- `expectedRect.width`
- `expectedRect.height`
- `tolerancePx`

### 5.4 `main_pages.json`

路由注册表。每个 case 的 `url` 必须在 `src[]` 中存在；否则 `resolve_case_plan.py` 直接报错并终止。

### 5.5 `operationSequence`（定义在 `suite.manifest.json` 的 case 项）

- 可选字段；未配置时视为空序列 `[]`。
- 由 `resolve_case_plan.py` 透传到 `case_plan.json`，再由执行链路按顺序执行。
- 每个操作对象必须包含 `op` 字段，当前支持：
  1. `wait`
     - `durationMs`（`>=0`）
  2. `click`
     - `inject`: `touch|mouse`（默认 `touch`）
     - `x`, `y`
     - `holdMs`（默认 `40`）
  3. `swipe`
     - `inject`: `touch|mouse`（默认 `touch`）
     - 坐标：`from/to` 或 `startX/startY/endX/endY`
     - `durationMs`（默认 `300`）
     - `steps`（默认 `6`）
  4. `action`
     - `command`（PreviewerCLI action 命令名）
     - `args`（键值参数对象）

---

## 6. 命名规范（当前约定）

1. suite: `suite-<2位序号>-<topic>`
2. caseId: `case-<3位序号>-<topic>`
3. case 文件: `case_<3位序号>_<topic>.ets`
4. 节点 id: `N_F<feat>_C<case>_<ROLE>`
   - 示例：`N_F01_C003_TARGET`

---

## 7. 执行入口与命令

### 7.1 Previewer 完整包归档

仓库根目录下提供：

```text
previewer/previewer-20260625.tar.gz  # 约 209 MB
```

该归档是 Previewer 的完整包，解压后包含：

```text
previewer/common/bin/Previewer
previewer/common/bin/PreviewerCLI
```

推荐的开箱即用流程：

```bash
cd /path/to/arkui-specs
mkdir -p previewer/runtime
tar -xzf previewer/previewer-20260625.tar.gz -C previewer/runtime

cd spec-test
PREVIEWER_BIN="$(pwd)/../previewer/runtime/previewer/common/bin" \
./tools/host_preview/run_feature.sh --openharmony-root /path/to/openharmony
```

说明：

- `PREVIEWER_BIN` 优先级最高，只影响 HostPreview 运行时 Previewer 选择。
- HAP 编译仍依赖 OpenHarmony SDK 与 Node，可通过 `local.properties` 的 `sdk.dir/nodejs.dir` 或环境变量配置。
- HostPreview 通过 `xvfb-run` 启动无头显示环境，系统需安装 `Xvfb`。
- 如果未设置 `PREVIEWER_BIN`，脚本会继续从 `OHOS_BASE_SDK_HOME`、`DEVECO_SDK_HOME`、`OPENHARMONY_ROOT` 下的默认 SDK/Previewer 路径查找。

### 7.2 执行命令

在 `spec-test` 目录执行：

```bash
# 全量
./tools/host_preview/run_feature.sh
./tools/host_preview/run_feature.sh --openharmony-root /path/to/openharmony

# 指定 suite
./tools/host_preview/run_feature.sh --suite-id suite-01-width-height-basic

# 指定 case
./tools/host_preview/run_feature.sh --case-id case-003-width-height-zero

# 开启截图归档（默认不归档）
./tools/host_preview/run_feature.sh --archive-screenshot
```

调试（仅采集 inspector，不做断言）：

```bash
./tools/host_preview/run_inspector_only.sh
./tools/host_preview/run_inspector_only.sh spec_cases/.../cases/case_001_width_height_basic
./tools/host_preview/run_inspector_only.sh \
  spec_cases/.../cases/case_001_width_height_basic \
  --openharmony-root /path/to/openharmony
```

Previewer 查找优先级：

1. `PREVIEWER_BIN`
2. `${OHOS_BASE_SDK_HOME}/previewer/common/bin`
3. `${DEVECO_SDK_HOME}/previewer/common/bin`
4. `${OPENHARMONY_ROOT}/out/sdk/ohos-sdk/linux/previewer/common/bin`
5. `${OPENHARMONY_ROOT}/prebuilts/ohos-sdk/linux/previewer/common/bin`

---

## 8. 报告与产物

单次执行输出目录：

```text
.report/<RUN_ID>/run_feature/
├── case_plan.json
├── case_lines.txt
├── summary_report.json
├── summary_report.md
└── <suite-id>/<case-id>/
    ├── previewer.log
    ├── operations.json
    ├── operations_runtime_response.txt
    ├── inspector_runtime_response.txt
    ├── screenshot_runtime_response.txt  # optional
    ├── screenshot.png                   # optional
    ├── report.json
    └── report.md
```

终端汇总字段：

- `run_root`
- `plan_json`
- `summary_json`
- `summary_md`
- `total_cases`
- `failed_cases`

终端输出约定：

- 阶段进度高亮显示。
- `Previewer bin` 高亮显示，便于确认本次实际使用的 Previewer 包。
- `total_cases`、`failed_cases` 使用不同颜色；失败数非 0 时颜色变为红色。

约束：

- `failed_cases > 0` 时脚本返回非 0。
- 断言按 case 独立执行，失败不阻断后续 case。
- `report.json` 中包含截图归档路径字段（`artifacts.screenshotFile`、`results[].screenshotFile`）。
- `run_feature.sh`、`collect_inspector.sh`、`run_inspector_only.sh` 会清理本轮执行新增的 `Xvfb` 残留进程。

---

## 9. 新增用例流程（实现对齐）

1. 在目标 suite 的 `cases/` 下新增 `*.ets` 页面，给目标节点设置稳定 `.id(...)`。
2. 在 `suite.manifest.json` 增加 case 条目（`caseId/nodeId/url`）。
3. 在 `expected/expected.json` 增加同 `caseId` 的期望断言。
4. 在 `main_pages.json` 注册该 case URL。
5. 先跑单 case：`run_feature.sh --case-id ...`，再跑全量回归。

---

## 10. 已知边界与后续建议

### 10.1 已知边界

1. route 注册需要手工维护（`main_pages.json`）。
2. 当前没有独立的 feature 级 CLI 过滤参数（通过 suite/case 过滤实现）。
3. 当前报告包含 case 级结果，未做 AC 维度聚合统计。
4. `previewer/previewer-20260625.tar.gz` 只归档 Previewer 运行包；编译 HAP 仍需可用的 SDK、Node 与 OpenHarmony 根目录。
5. HostPreview 执行依赖系统提供 `xvfb-run`；未安装 `Xvfb` 时会出现 `xvfb-run: command not found` 或显示打开失败。

### 10.2 后续建议

1. 增加 feature 级过滤参数（如 `--feature-id`）。
2. 增加 AC 维度汇总与总报告聚合器。
3. 提供 case 脚手架工具，自动更新 suite/expected/main_pages。
