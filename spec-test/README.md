# SpecTest HostPreview 用例框架说明

## 1. 目标

`spec-test` 用于基于规格文档执行 ArkUI 组件行为验证，当前采用 HostPreview + Inspector 的方式：

- 通过 URL 直接加载用例页面（不走 `pages/Index` 作为测试入口）。
- 采集 Inspector 树。
- 对比 `expected.json` 中的期望值，输出 `PASS/FAIL` 报告。

参考设计文档：`docs/HostPreview_Test_Framework_Design.md`

## 2. 执行链路

`run_feature.sh` 的流程固定为：

1. 编译 HAP（`./build.sh build`）
2. 扫描 `spec_cases/**/suite.manifest.json` + `expected/expected.json`
3. 校验每个用例 URL 是否已注册到 `main_pages.json`
4. 按 case 逐条启动 Previewer，并加载该 case 的 URL
5. 按 `operationSequence` 执行操作序列（如点击注入、滑动、等待）
6. 通过 `PreviewerCLI inspector` 采集树
7. 用 `assert_cases.py` 按 `targetNodeId` + `expectedRect` 断言
8. 输出分 case 报告和汇总结果

## 3. 目录结构

```text
arkui-specs/
├── previewer/
│   └── previewer-20260625.tar.gz # Previewer 完整包归档，约 209 MB
└── spec-test/
    ├── build.sh
    ├── tools/host_preview/
    │   ├── run_feature.sh          # 全量/筛选执行入口
    │   ├── resolve_case_plan.py    # 解析清单并生成 case_plan.json
    │   ├── common.sh               # 运行时路径解析（Previewer 等）
    │   ├── execute_operations.py   # 操作序列执行器（wait/click/swipe/action）
    │   ├── collect_inspector.sh    # 启动 Previewer + 采集 inspector
    │   ├── assert_cases.py         # 断言逻辑并生成报告
    │   ├── merge_report.py         # 总体报告汇总
    │   └── run_inspector_only.sh   # 仅采集 inspector（调试）
    ├── entry/src/main/ets/spec_cases/
    │   └── 04-common-capability/.../Feat-xx-.../
    │       ├── feature.manifest.json
    │       └── suites/
    │           └── suite-xx-.../
    │               ├── suite.manifest.json
    │               ├── cases/
    │               │   ├── case_xxx.ets
    │               │   └── ...
    │               └── expected/
    │                   └── expected.json
    └── entry/src/main/resources/base/profile/main_pages.json
```

## 4. 清单字段约定

### 4.1 `feature.manifest.json`

- 用于描述 feature 基本信息和 suite 列表。
- 关键字段：`featureId`、`specPath`、`suites`。

### 4.2 `suite.manifest.json`

- 用于描述 suite 内 case 元数据。
- `cases[]` 每项建议包含：
  - `caseId`：全局唯一。
  - `nodeId`：目标节点 id（与用例页面内 `.id(...)` 对应）。
  - `url`：页面 URL（无 `.ets` 后缀）。
  - `description`：可读描述。

### 4.3 `expected/expected.json`

- 用于描述断言目标。
- `cases[]` 每项至少包含：
  - `caseId`
  - `targetNodeId`
  - `expectedRect.width`
  - `expectedRect.height`
  - `tolerancePx`

### 4.4 `main_pages.json`

- 路由注册表，`src[]` 必须包含每个 case 的 `url`。
- `run_feature.sh` 在生成执行计划时会做硬校验，不存在即报错并中断。

### 4.5 `operationSequence`（定义在 `suite.manifest.json` 的 case 项）

- 用于定义该 case 在采集 inspector 前的操作序列。
- 执行顺序：严格按数组顺序执行。
- 字段位置：
  - `suite.manifest.json -> cases[i].operationSequence`
- 可选；不配置时等价于空序列 `[]`。

支持的操作：

1. `wait`：延时等待
   - `op`: `"wait"`
   - `durationMs`: 等待毫秒数（`>=0`）
2. `click`：点击注入
   - `op`: `"click"`
   - `inject`: `"touch"` 或 `"mouse"`（默认 `"touch"`）
   - `x`, `y`: 点击坐标
   - `holdMs`: 按下保持时长（默认 `40`）
3. `swipe`：滑动注入
   - `op`: `"swipe"`
   - `inject`: `"touch"` 或 `"mouse"`（默认 `"touch"`）
   - 支持两种坐标写法（二选一）：
     - `from: { x, y }` + `to: { x, y }`
     - `startX/startY/endX/endY`
   - `durationMs`: 滑动总时长（默认 `300`）
   - `steps`: 插值步数（默认 `6`）

示例：

```json
{
  "caseId": "case-xxx",
  "url": "spec_cases/.../case_xxx",
  "operationSequence": [
    { "op": "wait", "durationMs": 300 },
    { "op": "click", "inject": "touch", "x": 216, "y": 466, "holdMs": 60 },
    {
      "op": "swipe",
      "inject": "touch",
      "from": { "x": 216, "y": 760 },
      "to": { "x": 216, "y": 320 },
      "durationMs": 400,
      "steps": 8
    },
    { "op": "wait", "durationMs": 200 }
  ]
}
```

## 5. 新增用例方法（同一个 suite 下）

以下步骤必须全部完成，否则不会被执行或会断言失败。

1. 新增页面文件  
在 `cases/` 下新增 `case_xxx.ets`，使用 `@Entry` 导出页面，并给待断言节点设置稳定 id。

2. 更新 `suite.manifest.json`  
在 `cases[]` 中添加条目，至少填 `caseId`、`nodeId`、`url`。

3. 更新 `expected/expected.json`  
添加同 `caseId` 的断言配置，补齐 `targetNodeId` 与期望尺寸。

4. 更新 `main_pages.json`  
把该 case 的 `url` 加入 `src[]`。

5. 运行定向验证  
`./tools/host_preview/run_feature.sh --case-id <case-id>`

注意：

- 不需要改 `pages/Index`。
- URL 必须和路由表中的字符串完全一致。

## 6. 新增 suite / feature 方法

1. 新建 `Feat-xx-...` 目录并添加 `feature.manifest.json`。
2. 在 `suites/` 下新建 `suite-xx-.../`，补齐：
  - `suite.manifest.json`
  - `cases/*.ets`
  - `expected/expected.json`
3. 将所有新 case 的 `url` 注册到 `main_pages.json`。
4. 执行：
  - 指定 suite：`./tools/host_preview/run_feature.sh --suite-id <suite-id>`
  - 或全量：`./tools/host_preview/run_feature.sh`

## 7. 执行方法

### 7.1 环境前提

- OpenHarmony SDK 与 Node 可用，用于编译 HAP。
- `build.sh` 支持两种配置方式：
  - 环境变量：`OHOS_BASE_SDK_HOME`、`NODE_HOME`
  - `local.properties`：`sdk.dir`、`nodejs.dir`
- OpenHarmony 根目录默认按脚本相对路径推导，也可通过 `OPENHARMONY_ROOT` 环境变量或 `--openharmony-root <path>` 指定。
  - 如果推导结果为 `/`，脚本会提示增加 `--openharmony-root <OpenHarmonyRoot>`。
- Previewer 路径在运行时自动解析，优先级如下：
  - `PREVIEWER_BIN`（显式指定）
  - `${OHOS_BASE_SDK_HOME}/previewer/common/bin`
  - `${DEVECO_SDK_HOME}/previewer/common/bin`
  - `${OPENHARMONY_ROOT}/out/sdk/ohos-sdk/linux/previewer/common/bin`
  - `${OPENHARMONY_ROOT}/prebuilts/ohos-sdk/linux/previewer/common/bin`
- 仓库提供 `previewer/previewer-20260625.tar.gz`（约 209 MB），这是 Previewer 的完整包归档；解压后可直接通过 `PREVIEWER_BIN` 指向其中的 `previewer/common/bin`，不依赖 OpenHarmony SDK 目录中的 Previewer。
- HostPreview 通过 `xvfb-run` 拉起无头显示环境，系统需要已安装 `Xvfb`。

### 7.2 Previewer 开箱即用

从仓库根目录执行：

```bash
mkdir -p previewer/runtime
tar -xzf previewer/previewer-20260625.tar.gz -C previewer/runtime
```

归档解压后的关键目录为：

```text
previewer/runtime/previewer/common/bin/
├── Previewer
├── PreviewerCLI
└── ...
```

执行测试时显式指定该 Previewer：

```bash
cd spec-test
PREVIEWER_BIN="$(pwd)/../previewer/runtime/previewer/common/bin" \
./tools/host_preview/run_feature.sh --openharmony-root /path/to/openharmony
```

如果已经通过 `local.properties` 配置了 `sdk.dir` 和 `nodejs.dir`，仍然可以继续使用；`PREVIEWER_BIN` 只覆盖运行 HostPreview 时使用的 Previewer 目录。

### 7.3 编译

```bash
cd spec-test
./build.sh clean
./build.sh build
./build.sh all
./build.sh build --openharmony-root /path/to/openharmony
```

产物：

```text
entry/build/default/outputs/default/entry-default-unsigned.hap
```

### 7.4 运行 HostPreview 测试

```bash
cd spec-test

# 全量（所有已注册且有 expected 的 case）
./tools/host_preview/run_feature.sh
./tools/host_preview/run_feature.sh --openharmony-root /path/to/openharmony

# 按 suite 跑
./tools/host_preview/run_feature.sh --suite-id suite-01-width-height-basic

# 按单 case 跑
./tools/host_preview/run_feature.sh --case-id case-001-width-height-basic

# 开启截图归档（默认不归档）
./tools/host_preview/run_feature.sh --archive-screenshot
```

执行过程中会高亮打印：

- 当前阶段进度，如 `[1/6] Build SpecTest HAP`。
- 每个 case 实际使用的 `Previewer bin: ...`。
- 汇总结果：`total_cases` 为青色，`failed_cases=0` 为绿色，`failed_cases>0` 为红色。
- 如发现本轮执行新增的 `Xvfb` 残留，会打印 `Cleaning Xvfb processes: ...` 并清理。

### 7.5 仅采集 Inspector（调试）

```bash
cd spec-test

# 使用默认 URL（脚本内默认 case）
./tools/host_preview/run_inspector_only.sh

# 指定 URL
./tools/host_preview/run_inspector_only.sh \
  spec_cases/.../cases/case_001_width_height_basic
./tools/host_preview/run_inspector_only.sh \
  spec_cases/.../cases/case_001_width_height_basic \
  --openharmony-root /path/to/openharmony
```

## 8. 报告输出

`run_feature.sh` 每次执行会生成时间戳目录：

```text
.report/<YYYYMMDD_HHMMSS>/run_feature/
├── case_plan.json
├── case_lines.txt
├── summary_report.json
├── summary_report.md
└── <suite-id>/<case-id>/
    ├── previewer.log
    ├── operations.json
    ├── operations_runtime_response.txt
    ├── inspector_runtime_response.txt
    ├── screenshot_runtime_response.txt  # 可选（archive-screenshot=true）
    ├── screenshot.png                   # 可选（archive-screenshot=true）
    ├── report.json
    └── report.md
```

终端会输出：

- `run_root=...`
- `total_cases=...`
- `failed_cases=...`
- `summary_json=...`
- `summary_md=...`

`failed_cases > 0` 时脚本返回非 0 退出码。

终端中的进度、Previewer 路径、`total_cases` 和 `failed_cases` 会用 ANSI 颜色高亮显示，便于在长日志中快速定位关键结果。

`report.json` 的 `artifacts.screenshotFile` 与 `results[].screenshotFile` 会记录截图归档路径。
默认不归档截图；只有传 `--archive-screenshot` 时才会生成 `screenshot.png` 与 `screenshot_runtime_response.txt`。

`summary_report.json/md` 为本次运行的总体汇总报告，包含 suite 级统计、case 明细、失败原因与单 case 报告链接。

## 9. 常见问题与排查

1. `Route 'xxx' ... is not registered in main_pages.json`  
原因：case URL 未注册。  
处理：把 URL 加入 `entry/src/main/resources/base/profile/main_pages.json`。

2. `Missing url for case 'xxx'`  
原因：`suite.manifest.json` 和 `expected.json` 中 case 对不上，或缺少 url。  
处理：校对 `caseId` 与 `url` 字段。

3. `Target node not found` / `Node has no $rect`  
原因：`targetNodeId` 与页面 `.id(...)` 不一致，或节点未进入树。  
处理：核对 `suite.manifest.json`、`expected.json` 与用例页面 id。

4. `Failed to get inspector response` / commandPipe 连接问题  
原因：Previewer 进程异常或旧进程占用。  
处理：重跑 `run_feature.sh`。脚本会清理同名 Previewer 旧进程，并在退出时清理本轮新增的 `Xvfb` 残留；如果系统中还有更早残留，可再手动检查。

5. 页面加载失败（如 `Cannot find module ...`）  
处理：确认：
  - 用例 URL 与文件路径一致（不带 `.ets`）。
  - `main_pages.json` 已注册该 URL。
  - 重新 `./build.sh build` 后再执行。

6. `OPENHARMONY_ROOT resolved to filesystem root (/)`  
原因：当前 `spec-test` 目录不在脚本默认假设的 OpenHarmony 源码树相对位置下。  
处理：增加 `--openharmony-root <OpenHarmonyRoot>`，或导出 `OPENHARMONY_ROOT`。

7. 找不到 Previewer  
处理：优先使用仓库归档包：
  - 解压 `previewer/previewer-20260625.tar.gz`
  - 设置 `PREVIEWER_BIN=<解压目录>/previewer/common/bin`
  - 确认该目录下存在可执行的 `Previewer` 和 `PreviewerCLI`

8. `xvfb-run: command not found` / `Failed to open display`  
原因：系统未安装 `Xvfb`，或 `xvfb-run` 不在 `PATH` 中。  
处理：
  - Ubuntu/Debian：`sudo apt-get install xvfb`
  - openEuler/CentOS/RHEL：`sudo yum install xorg-x11-server-Xvfb` 或 `sudo dnf install xorg-x11-server-Xvfb`
  - 安装后确认：`command -v xvfb-run`

## 10. 当前项目关键配置

- `build-profile.json5`
  - `runtimeOS: OpenHarmony`
  - `compileSdkVersion/targetSdkVersion/compatibleSdkVersion: 26`
  - `useNormalizedOHMUrl: false`
- `entry/src/main/module.json5`
  - `pages: "$profile:main_pages"`
