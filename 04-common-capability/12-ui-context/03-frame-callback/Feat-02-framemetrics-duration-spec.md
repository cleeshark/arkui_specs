# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FrameMetrics 帧耗时上报（单帧总耗时与实际开始时间戳） |
| 特性编号 | Func-04-12-03-Feat-02 |
| 所属 Epic | UI上下文 (04-12) |
| SIG 归属 | ArkUI SIG / ArkUI Framework / DFX Trace |
| 优先级 | P1 |
| 目标版本 | API Level 27（proposed） |
| 复杂度 | 复杂 |
| 状态 | Baselined |

本特性在既有 `FrameMetrics` InnerAPI 数据合同基础上，于结构尾部追加 `actualStartTime` 与 `totalDuration` 两个纳秒级字段，使应用或系统 DFX 开发者能从 FrameMetrics 回调直接取得统一口径的单帧总耗时与当帧 UI 管线实际开始时间，区分 VSync 信号时刻与 UI 管线实际执行时刻。回调完成后紧随输出带 `ACE_WINDOW_PIPELINE` tag 的 DEBUG 日志，作为不依赖窗口消费方的 ArkUI 独立验收面。

`FrameMetrics`（`interfaces/inner_api/ace/ui_content_config.h:50`）是 ArkUI InnerAPI 结构体，由 `UIContent::SetFrameMetricsCallBack`（`interfaces/inner_api/ace/ui_content.h:345`）按值返回。既有四字段为 `firstDrawFrame`、`vsyncTimestamp`、`inputHandlingDuration`、`layoutMeasureDuration`，本特性在其后固定追加 `actualStartTime`、`totalDuration` 两个 `uint64_t` 字段，默认 0。

`PipelineContext::FlushVsync`（`frameworks/core/pipeline_ng/pipeline_context.cpp:1184`）是帧处理入口：`actualStartTime` 在 RosenWindow 收到 VSync 时捕获（经 `vsyncStartTime` 参数传入），非 Rosen 路径（`vsyncStartTime = -1`）回退到 FlushVsync 入口的 `GetSysTimestamp()`；`totalDuration` 为 `window_->FlushVsync()` 返回后 `GetSysTimestamp()` 与 `actualStartTime` 的差值。两者均基于 `CLOCK_MONOTONIC`（`frameworks/base/utils/time_util.cpp:54`）。

DVSync 场景下 RS 分配的 `vsyncTimestamp`（回调 `nanoTimestamp`）可为未来时刻，因此本特性不建立 `actualStartTime >= vsyncTimestamp` 的不变量。

---

## 本次变更范围（Delta）

本规格基于已合入代码 PR `ace_engine!89074`（commit `41702899ede`）与 RK3568 当前 Animator Trace/hilog 归档，将实现固化为可追溯的验收规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `FrameMetrics::actualStartTime` | 帧实际开始时间字段；VSync 接收时刻捕获的 CLOCK_MONOTONIC 纳秒值；非 Rosen 路径回退到帧处理入口本地时钟值 |
| ADDED | `FrameMetrics::totalDuration` | 单帧总耗时字段；`actualStartTime` 到 `window_->FlushVsync()` 返回（`submitEndTime`）的纳秒差值 |
| ADDED | FrameMetrics DEBUG 日志 | 每次回调后输出 `ACE_WINDOW_PIPELINE` DEBUG 日志，包含 `actualStartTime`、`totalDuration`、`vsyncTimestamp` |
| MODIFIED | `OHOS::Ace::FrameMetrics` 数据布局 | 既有四字段后依次追加两个字段；仅承诺 API Level 27 匹配版本联调 |
| MODIFIED | VSync 回调链签名 | 新增参数传递 VSync 接收时刻；默认值保证非 Rosen 路径兼容 |
| UNCHANGED | 既有字段与回调频次 | `firstDrawFrame`、`vsyncTimestamp`、`inputHandlingDuration`、`layoutMeasureDuration` 语义和回调频次不变 |

---

## 输入文档

| 序号 | 文档 | 来源 | 关键内容 |
|------|------|------|----------|
| 1 | `ui_content_config.h` | `interfaces/inner_api/ace/ui_content_config.h:50` | `FrameMetrics` 六字段布局事实 |
| 2 | `ui_content.h` | `interfaces/inner_api/ace/ui_content.h:345` | `SetFrameMetricsCallBack` 现有回调签名 |
| 3 | `pipeline_context.cpp` | `frameworks/core/pipeline_ng/pipeline_context.cpp:1184` | `FlushVsync` 帧处理入口、`totalDuration` 计算边界 |
| 4 | `rosen_window.cpp` | `frameworks/core/components_ng/render/adapter/rosen_window.cpp:93` | RosenWindow VSync 回调捕获 `actualStartTime`（`ts = GetSysTimestamp()`） |
| 5 | `time_util.cpp` | `frameworks/base/utils/time_util.cpp:54` | `GetSysTimestamp()` 使用 `CLOCK_MONOTONIC`，纳秒单位 |
| 6 | 需求文档 | `proposal.md`（design-docs，v0.4） | 行为、异常、ABI、日志验收、RK3568 Trace 证据边界 |
| 7 | 验证规格 | `spec-for-validation.md`（design-docs，v0.4） | 验收标准、规则、2D 能力与 NFR 完整清单 |

---

## 用户故事

### US-1: 应用开发者需要取得统一口径的单帧总耗时

**作为** 应用或系统 DFX 开发者
**我想要** 从 FrameMetrics 回调直接取得 UI 管线单帧总耗时
**以便** 避免自行拼接分段耗时而遗漏阶段间隙，按统一口径分析帧性能

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 已注册 FrameMetrics 回调且一帧渲染提交完成后回调触发 THEN `totalDuration` 字段返回非负纳秒值，表示该帧从 VSync 接收到渲染提交完成的总耗时 | 正常 |
| AC-1.2 | WHEN 回调返回已完成提交的帧数据且检查 `totalDuration` 与分段耗时的关系 THEN `totalDuration` 覆盖 `actualStartTime` 到 `window_->FlushVsync()` 返回（`submitEndTime`）的全流程耗时，包含输入、布局以及 `FlushMessages`、`FlushAfterRenderTask`、`FlushLayoutSize`、`window_->FlushVsync()` 自身等阶段，故必然满足 `totalDuration >= inputHandlingDuration + layoutMeasureDuration` | 正常 |
| AC-1.3 | WHEN 当帧提交被冻结跳过或提交对象不可用但帧仍走完渲染流程 THEN 回调返回的 `totalDuration` 为正纳秒值（因帧仍完成渲染流程），冻结标志已复位 | 异常 |

### US-2: 应用开发者需要取得 UI 管线实际开始时间

**作为** 应用或系统 DFX 开发者
**我想要** 从 FrameMetrics 回调取得当帧实际处理起点
**以便** 区分 VSync 信号时刻与 UI 管线开始执行时刻，精确定位帧处理入口

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN OHOS Rosen NG 管线处理一帧并触发回调 THEN `actualStartTime` 字段为 VSync 接收时刻捕获的单调时钟纳秒值，与 `totalDuration` 使用同一时钟域 | 正常 |
| AC-2.2 | WHEN 当帧提交被冻结跳过且回调触发 THEN `actualStartTime` 仍保留有效的单调时钟纳秒值，`totalDuration` 为正纳秒值 | 异常 |
| AC-2.3 | WHEN DVSync 场景给出的 VSync 信号时间晚于实际处理起点且回调返回当帧数据 THEN 允许 `actualStartTime < vsyncTimestamp`，两字段分别遵循各自定义的时间语义 | 正常 |
| AC-2.4 | WHEN 非 Rosen 路径触发 VSync（如 FormRenderWindow、Classic Pipeline、`AceVsyncCallback` 调用方未传入 `vsyncStartTime` 参数致默认 -1）且回调返回数据 THEN `actualStartTime` 回退到 FlushVsync 入口的 `GetSysTimestamp()` 作为帧处理入口的本地时钟值，不崩溃或产生无效值，`totalDuration` 正常计算 | 边界 |

### US-3: 保持既有消费方行为并提供 ArkUI 独立验收面

**作为** FrameMetrics 现有消费方
**我想要** 升级到 API Level 27 匹配版本后继续读取既有字段，并能直接从 ArkUI 日志核对新增指标
**以便** 平滑扩展帧性能分析能力，并在窗口消费适配完成前独立验收

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API Level 27 匹配版本触发回调且检查既有字段 THEN `firstDrawFrame`、`vsyncTimestamp`、`inputHandlingDuration`、`layoutMeasureDuration` 的值域、计算口径和回调频次与变更前一致 | 正常 |
| AC-3.2 | WHEN API Level 27 的消费方按声明顺序读取 `FrameMetrics` THEN 先读取全部既有字段，再依次读取新增的 `actualStartTime`、`totalDuration` | 正常 |
| AC-3.3 | WHEN 已注册 FrameMetrics 回调且当帧回调完成 THEN 紧随回调产生 `ACE_WINDOW_PIPELINE` DEBUG 日志，日志包含 `actualStartTime`、`totalDuration`、`vsyncTimestamp` 且数值与该次回调数据一致 | 正常 |

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|--------|----------|----------|----------|------|
| AC-1.1 | R-1 / R-2 | TASK-01 | UT + 设备日志 | 见验证映射 VM-1 / VM-5 |
| AC-1.2 | R-2 | TASK-01 | UT + 设备日志 | 见验证映射 VM-1 / VM-5 |
| AC-1.3 | R-4 | TASK-01 | UT + 设备日志 | 见验证映射 VM-2 |
| AC-2.1 | R-1 / R-3 | TASK-01 | UT + 设备日志 | 见验证映射 VM-1 / VM-5 |
| AC-2.2 | R-4 | TASK-01 | UT + 设备日志 | 见验证映射 VM-2 |
| AC-2.3 | R-7 | TASK-01 | UT + 设备日志 | 见验证映射 VM-6 |
| AC-2.4 | R-3 | TASK-01 | UT + 设备日志 | 见验证映射 VM-1 / VM-2 |
| AC-3.1 | R-5 | TASK-01 | UT + ABI 检查 | 见验证映射 VM-3 / VM-7 |
| AC-3.2 | R-5 | TASK-01 | UT + ABI 检查 | 见验证映射 VM-3 |
| AC-3.3 | R-8 | TASK-01 | 设备日志 | 见验证映射 VM-4 |

---

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | OHOS Rosen NG 管线处理一帧并触发回调 | 回调返回 `actualStartTime`（VSync 接收时刻的单调时钟纳秒值）和 `totalDuration`（渲染提交完成后的总耗时） | 两者均为 `uint64_t` 纳秒值，使用同一单调时钟域 | AC-1.1、AC-2.1 |
| R-2 | 行为 | 一帧渲染提交完成后回调触发 | `totalDuration` 覆盖 `actualStartTime` 到 `window_->FlushVsync()` 返回（`submitEndTime`）的全流程耗时，包含输入、布局以及 `FlushMessages`、`FlushAfterRenderTask`、`FlushLayoutSize`、`window_->FlushVsync()` 自身等阶段，故必然满足 `totalDuration >= inputHandlingDuration + layoutMeasureDuration` | 不表示合成或上屏完成；非负纳秒值 | AC-1.1、AC-1.2 |
| R-3 | 行为 | 回调触发 | `actualStartTime` 表示 VSync 接收时刻捕获的单调时钟纳秒值；非 Rosen 路径（`vsyncStartTime = -1`）回退到 FlushVsync 入口 `GetSysTimestamp()` | 不复用 VSync 信号时间；未提交帧仍有效 | AC-2.1、AC-2.2、AC-2.4 |
| R-4 | 异常 | 当帧提交被冻结跳过或提交对象不可用 | 回调保留 `actualStartTime`；`totalDuration` 为正纳秒值（因帧仍走完渲染流程） | 冻结标志为一次性，下次正常帧恢复提交 | AC-1.3、AC-2.2 |
| R-5 | 边界 | API Level 27 匹配版本读取 FrameMetrics | 保持既有字段合同，在结构尾部依次追加 `actualStartTime`、`totalDuration` | 不承诺新旧独立编译产物混用；不修改回调注册签名和频次 | AC-3.1、AC-3.2 |
| R-6 | 边界 | 在 RK3568 当前刷新率运行 Animator demo 并采集 Trace/hilog | 逐帧关联 FrameMetrics、UI VSYNC 与提交边界，报告 `totalDuration` 分布 | 不区分 60/120 Hz，不要求 10,000 帧 A/B、p99 新增开销或运行时内存差值；摘要不代替可复算原始数据 | AC-1.1、AC-1.2、AC-2.1、AC-3.3 |
| R-7 | 边界 | DVSync 的 VSync 信号时间可能晚于实际处理起点 | 不建立 `actualStartTime >= vsyncTimestamp` 的不变量 | 两字段分别遵循实际处理起点和 VSync 信号语义 | AC-2.3 |
| R-8 | 行为 | FrameMetrics 回调完成 | 紧随回调输出 tag 为 `ACE_WINDOW_PIPELINE` 的 DEBUG 日志，按名称打印 `actualStartTime`、`totalDuration`、`vsyncTimestamp` | 三项使用 `%{public}` `PRIu64`；日志不改变回调频次或字段值 | AC-3.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1、R-2、R-3 / AC-1.1、AC-1.2、AC-2.1、AC-2.4 | UT + 设备日志 | `PipelineContextTestNg.FrameMetricsDurationCalculation`、`FrameMetricsFlushVsyncCallback`；RK3568 Animator + `hilog` 核对起止差值与回调频次 |
| VM-2 | R-4 / AC-1.3、AC-2.2 | UT + 设备日志（冻结场景） | `PipelineContextTestNg.FrameMetricsFreezeFrame`、`FrameMetricsMissingDirector`；设置 `IsFreezeFlushMessage(true)` 断言回调触发、开始时间有效、总耗时>0、冻结标志复位 |
| VM-3 | R-5 / AC-3.1、AC-3.2 | 类型/默认值/offsetof UT + 设备字段验证 | `PipelineContextTestNg.FrameMetricsApiContract`、`FrameMetricsExistingContract`；两字段 `uint64_t`、默认 0、尾追加、原回调合同保持 |
| VM-4 | R-8 / AC-3.3 | 日志与 Trace 对照 | RK3568 Animator 运行及 `hilog` 中 `ACE_WINDOW_PIPELINE` / `FrameMetrics`；三字段对应同帧回调 |
| VM-5 | R-6 / AC-1.1、AC-1.2、AC-2.1、AC-3.3 | 逐帧时序核验 | RK3568 当前 Animator Trace/hilog 采集；逐帧匹配 UI VSYNC 与提交边界，报告样本数/分布/输入 SHA |
| VM-6 | R-7 / AC-2.3 | 未来 VSync 输入 UT + 设备日志验证 | `PipelineContextTestNg.FrameMetricsDvSyncTimestamp`；保留输入 VSync，允许 `actualStartTime` 小于它；总耗时仍按单调时钟计算 |
| VM-7 | R-5 / AC-3.1 | UT 与兼容回归 + 设备全量验证 | `PipelineContextTestNg.FrameMetricsExistingContract`、`PipelineContextTestNg.*` 全量 target 基线对照；既有字段合同、原回调频次保持 |

---

## API 变更分析

### 新增 API

| API 名称 | 开放级别 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `OHOS::Ace::FrameMetrics::actualStartTime` | InnerAPI | N/A：数据字段 | `uint64_t` 纳秒时间戳 | N/A：数据字段不返回错误码 | 当帧 UI 管线实际开始处理时刻 | AC-2.1、AC-2.2、AC-2.3 |
| `OHOS::Ace::FrameMetrics::totalDuration` | InnerAPI | N/A：数据字段 | `uint64_t` 纳秒耗时 | N/A：数据字段不返回错误码 | `actualStartTime` 到 `window_->FlushVsync()` 返回的耗时 | AC-1.1、AC-1.2、AC-1.3 |

### 变更/废弃 API

| API 名称 | 当前开放级别 | 目标开放级别 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|--------------|--------------|----------|----------|----------|---------|
| `OHOS::Ace::FrameMetrics` | InnerAPI | InnerAPI | 结构尾追加字段 | 按值传递类型的大小和布局变化 | ArkUI 与窗口侧使用 API Level 27 匹配版本；不混用新旧独立编译产物 | AC-3.1、AC-3.2 |
| `UIContent::SetFrameMetricsCallBack` | InnerAPI | InnerAPI | 间接 ABI 影响，签名文本不变 | 回调参数类型布局随 FrameMetrics 扩展 | 同上；无需迁移到新回调接口 | AC-3.1 |

---

## 接口规格

### 接口定义

**`OHOS::Ace::FrameMetrics`**

| 属性 | 值 |
|------|-----|
| 接口形式 | `struct FrameMetrics`，由现有 UIContent 回调按值返回 |
| 返回值 | 既有四字段 + `actualStartTime` + `totalDuration` |
| 开放级别 | InnerAPI |
| 错误码 | N/A |

**当前完整数据合同**

```cpp
namespace OHOS::Ace {
struct FrameMetrics {
    bool firstDrawFrame = false;
    uint64_t vsyncTimestamp = 0;
    uint64_t inputHandlingDuration = 0;
    uint64_t layoutMeasureDuration = 0;
    uint64_t actualStartTime = 0;
    uint64_t totalDuration = 0;
};
}
```

| 字段 | 类型 / 默认值 | 含义与约束 |
|------|---------------|------------|
| firstDrawFrame | bool / false | 原有窗口首帧标志，判定口径不变 |
| vsyncTimestamp | uint64_t / 0 | 原有 VSync 输入时间戳，单位 ns；DVSync 可提供未来时刻 |
| inputHandlingDuration | uint64_t / 0 | 原有输入处理分段耗时，单位 ns，口径不变 |
| layoutMeasureDuration | uint64_t / 0 | 原有布局测量分段耗时，单位 ns，口径不变 |
| actualStartTime | uint64_t / 0 | RosenWindow 收到 VSync 时用 `GetSysTimestamp()` 捕获的 CLOCK_MONOTONIC 纳秒值（经 `vsyncStartTime` 参数传递到 FlushVsync）；非 Rosen 路径（`vsyncStartTime = -1`）回退到 FlushVsync 入口 `GetSysTimestamp()`；未提交帧仍有效 |
| totalDuration | uint64_t / 0 | `window_->FlushVsync()` 返回后 `GetSysTimestamp()` 减去 `actualStartTime` 的差值，单位 ns |

通过现有 `UIContent::SetFrameMetricsCallBack(std::function<void(FrameMetrics info)>&& callback)` 注册，主线程调用；回调按值接收以上六字段。没有注册消费者或管线已销毁时，不承诺新增回调。

---

## 兼容性声明

- **已有 API 行为变更：** 是。`FrameMetrics` 在结构尾部新增两个 InnerAPI 字段；既有字段语义和回调频次不变。
- **二进制兼容承诺：** 仅承诺 ArkUI 与窗口侧在 API Level 27 使用匹配版本；不承诺新旧独立编译产物混用。
- **配置文件格式变更：** 否。
- **数据存储格式变更：** 否，不持久化 FrameMetrics。
- **最低支持版本：** API Level 27。
- **API 版本号策略：** InnerAPI 随系统同迭代交付，不新增 Public/System `@since` 声明。
- **错误码兼容：** 无新增、修改或废弃错误码。
- **旧管线/跨平台：** Classic Pipeline、Preview、ArkUI-X 不在本特性范围内；仅约束 OHOS Rosen NG。

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 单调时钟一致性 | `actualStartTime` 与 `totalDuration` 使用同一单调时钟域（CLOCK_MONOTONIC），纳秒单位 | AC-1.1、AC-2.1、AC-2.2 |
| 提交语义边界 | 总耗时终点是渲染提交完成后，不代表合成或上屏完成 | AC-1.1、AC-1.3 |
| 时间差判定 | `totalDuration` 为非负纳秒值（`submitEndTime - actualStartTime`）；冻结路径 `totalDuration > 0`（帧仍走完渲染流程） | AC-1.1、AC-1.3 |
| 兼容字段布局 | 新字段仅尾追加，且顺序固定为 `actualStartTime`、`totalDuration` | AC-3.1、AC-3.2 |
| 回调行为不变 | 不新增 FrameMetrics 回调、不改变回调注册签名和触发频次 | AC-3.1、AC-3.3 |
| 日志紧随回调 | 回调后输出 `ACE_WINDOW_PIPELINE` DEBUG 日志，三个字段均以 `PRIu64` 格式输出 | AC-3.3 |
| 非 Rosen 回退 | `vsyncStartTime < 0` 时 `actualStartTime` 回退到 FlushVsync 入口 `GetSysTimestamp()`，不崩溃、不产生无效值 | AC-2.4 |

---

## 非功能性需求

| 需求ID | 类别 | 需求描述 | 指标/约束 |
|--------|------|----------|-----------|
| NFR-01 | 性能 | `FlushVsync` 逐帧热路径新增两次 `GetSysTimestamp()` 读取（`actualStartTime`、`submitEndTime`） | 无新增持久状态、堆分配、容器、缓存、锁或异步任务 |
| NFR-02 | 可观测性 | 回调后紧随输出 `ACE_WINDOW_PIPELINE` DEBUG 日志，三字段以 `%{public} PRIu64` 打印 | 日志值与回调数据一致，可逐帧关联 |
| NFR-03 | 可靠性 | 非 Rosen 路径 VSync 接收时刻不可用时回退本地时钟，无新增崩溃 | Mock 测试 + 全量基线对照 |
| NFR-04 | 兼容 | 既有四字段的值域、计算口径和回调频次与变更前一致 | 既有字段回归 UT + 全量基线对照 |
| NFR-05 | 可测试性 | 正常、Freeze、提交对象不可用、DVSync、既有字段回归和日志均有确定验证入口 | 定向 UT / ABI / `hilog` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 |
|----------|----------|-----------|----------|
| 手机（RK3568 基准） | 基准验证设备 | OHOS Rosen NG；使用设备当前刷新率 | pipeline UT + 当前 Animator Trace/hilog |
| Pad / PC / 穿戴 / 智慧屏 / 座舱 / 其他 | 合同无设计差异 | 使用相同纳秒、提交边界与异常哨兵合同 | 公共 pipeline UT；不要求额外设备抽样 |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无 UI、语义树或辅助事件变化 | N/A |
| 深色模式 | 否 | 不改变颜色、主题或资源 | N/A |
| 多窗口/分屏 | 是（合同一致） | 各 UIContent 沿用既有回调边界，字段语义一致 | AC-3.1、AC-3.3 |
| 版本升级 | 是 | API Level 27 匹配版本升级，不支持新旧独立产物混用 | AC-3.2 |
| 生态兼容 | 是 | 窗口侧后续必须使用匹配结构布局；该外部联调不作为本变更验收门禁 | AC-3.2 |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "FrameMetrics InnerAPI layout and callback chain"
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "PipelineContext FlushVsync to FlushMessages and RosenWindow SendMessages boundary"
```

**关键文档：**

- `interfaces/inner_api/ace/ui_content_config.h:50-60`：当前六字段布局事实。
- `interfaces/inner_api/ace/ui_content.h:345-351`：现有回调签名事实。
- `frameworks/core/pipeline_ng/pipeline_context.cpp:1184`：`FlushVsync` 帧处理入口与 `totalDuration` 计算边界。
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:93`：RosenWindow VSync 回调捕获 `actualStartTime`。
- `frameworks/base/utils/time_util.cpp:54`：`GetSysTimestamp()` 使用 `CLOCK_MONOTONIC`。
