# 特性规格

| 属性 | 值 |
|------|-----|
| 特性编号 | Func-03-08-01-Feat-03 |
| 所属 Epic | 无 |
| SIG 归属 | ArkUI SIG |
| 特性名称 | HiSysEvent事件上报与异常诊断 |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| 复杂度 | 复杂 |
| 状态 | Baselined |

---

## 概述

本特性定义 ArkUI ace_engine 框架内部通过 HiSysEvent 进行异常事件上报与性能诊断数据采集的完整机制。

`EventReport` 是全部事件上报的统一入口（`frameworks/base/log/event_report.h:229-303`），所有方法均为 `static`，实现位于 `adapter/ohos/osal/event_report.cpp`。每个方法直接调用 `HiSysEventWrite`，domain 固定为 `"ACE"`（拖拽事件使用 `DRAG_UE`、表单超时使用 `FORM_MANAGER`、Web 白屏使用 `ARKWEB_UE`）。

框架定义了 11 个异常类别常量（`event_report.h:30-40`）和 15+ 个异常类型枚举（`event_report.h:43-213`），覆盖应用启动、页面路由、组件、API通道、渲染、JS、动画、事件、国际化、无障碍、表单、Vsync、滚动、富文本、通用交互等场景。

`ExceptionHandler`（`frameworks/base/log/exception_handler.h:29-33`）提供 JS 异常的统一处理入口 `HandleJsException`，ohos 实现（`adapter/ohos/osal/exception_handler.cpp:41-54`）通知 `ApplicationDataManager` 的错误观察者，若无观察者处理则调用 `KillApplicationSelf` 终止应用进程。

---

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 新增规格（为已有实现补录规格） | EventReport、ExceptionHandler 全部能力 |
| ADDED | 无新增 API | 框架内部能力，无公开 API 变更 |

---

## 输入文档

| 序号 | 文档 | 来源 | 关键内容 |
|------|------|------|----------|
| 1 | `event_report.h` | `frameworks/base/log/event_report.h` | EventReport 全部公开方法签名、异常类别常量、异常类型枚举、数据结构定义 |
| 2 | `event_report.cpp` | `adapter/ohos/osal/event_report.cpp` | 所有方法的 HiSysEventWrite 调用实现、domain/eventType 映射、参数组装 |
| 3 | `exception_handler.h` | `frameworks/base/log/exception_handler.h` | ExceptionHandler::HandleJsException 声明、JsErrorObject 结构体 |
| 4 | `exception_handler.cpp` | `adapter/ohos/osal/exception_handler.cpp` | JS 异常处理实现、应用终止逻辑 |

---

## 用户故事

### US-01：异常类别分发

**作为**框架开发者，**我希望**通过统一的异常类别常量和类型枚举分发不同领域的事件上报，**以便**所有异常被归类到正确的 HiSysEvent 事件名下。

### US-02：组件异常上报（Legacy + NG）

**作为**组件开发者，**我希望**分别通过 `SendComponentException` 和 `SendComponentExceptionNG` 上报旧组件和新组件（components_ng）的异常，**以便**在故障日志中区分组件代际并附带节点信息。

### US-03：ANR 检测与弹窗

**作为**系统可靠性工程师，**我希望**框架在 UI 线程阻塞时分阶段上报 WARNING（3s）、FREEZE（6s）并最终弹出 ANR 对话框，**以便**采集卡顿证据并通知用户。

### US-04：性能阈值违规上报

**作为**性能优化工程师，**我希望**当页面节点数、页面深度或生命周期函数执行时间超过阈值时自动上报 FAULT 事件，**以便**定位性能劣化根因。

### US-05：JS 异常处理

**作为**应用开发者，**我希望**JS 运行时异常通过 `ExceptionHandler::HandleJsException` 被捕获并通知注册的错误观察者，**以便**应用有机会自行处理错误而非直接崩溃。

### US-06：拖拽与滚动错误上报

**作为**交互体验工程师，**我希望**拖拽行为和滚动容器内部错误通过 BEHAVIOR/FAULT 事件被采集，**以便**分析拖拽跨窗成功率和滚动容器稳定性。

### US-07：表单更新超时监控

**作为**卡片系统开发者，**我希望**表单 modify 操作通过 XCollie 设置 10 秒超时定时器，超时后上报 FORM_ERROR 事件，**以便**监控卡片更新链路健康度。

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-01 | R-1 / R-4 | TASK-03 | 代码审查 | 代码审查 |
| AC-02 | R-3 | TASK-03 | 代码审查 | 代码审查 |
| AC-03 | R-3 / R-4 | TASK-03 | 代码审查 | 代码审查 |
| AC-04 | R-4 | TASK-03 | 代码审查 | 代码审查 |
| AC-05 | R-5 | TASK-03 | 代码审查 | 代码审查 |
| AC-06 | R-6 | TASK-03 | 代码审查 | 代码审查 |
| AC-07 | R-6 | TASK-03 | 代码审查 | 代码审查 |
| AC-08 | R-6 | TASK-03 | 代码审查 | 代码审查 |
| AC-09 | R-6 | TASK-03 | 代码审查 | 代码审查 |
| AC-10 | R-8 | TASK-03 | 代码审查 | 代码审查 |
| AC-11 | R-8 | TASK-03 | 代码审查 | 代码审查 |
| AC-12 | R-8 | TASK-03 | 代码审查 | 代码审查 |
| AC-13 | — | TASK-03 | 代码审查 | 代码审查 |
| AC-14 | — | TASK-03 | 代码审查 | 代码审查 |
| AC-15 | R-1 | TASK-03 | 代码审查 | 代码审查 |
| AC-16 | R-12 | TASK-03 | 代码审查 | 代码审查 |
| AC-17 | R-10 | TASK-03 | 代码审查 | 代码审查 |
| AC-18 | R-10 | TASK-03 | 代码审查 | 代码审查 |
| AC-19 | R-9 | TASK-03 | 代码审查 | 代码审查 |
| AC-20 | R-9 | TASK-03 | 代码审查 | 代码审查 |

---

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | EventReport 调用 HiSysEventWrite 上报事件 | Domain 固定为 "ACE"，除 ReportDragInfo(domain=DRAG_UE)、StartFormModifyTimeoutReportTimer超时回调(domain=FORM_MANAGER)、ReportWebBlanklessSnapshotTouchEvent(domain=ARKWEB_UE)、ReportDoubleClickTitle/ReportClickTitleMaximizeMenu(domain=SCENE_BOARD_UE) 外 | 4 个例外场景使用独立 domain | AC-01 / AC-15 |
| R-2 | 边界 | packageName 写入 HiSysEvent 字段 | Container::CurrentBundleName() 获取的 packageName 若长度超过 MAX_PACKAGE_NAME_LENGTH(128)，通过 StrTrim 截断至 128 字符 | MAX_PACKAGE_NAME_LENGTH = 128 | AC-01 |
| R-3 | 行为 | Send*Exception 方法选择异常类型枚举 | 每个异常类别常量与对应枚举配对使用，通过 static_cast<int32_t> 转为 errorType 字段 | 11 组配对关系（EXCEPTION_FRAMEWORK_APP_START↔AppStartExcepType 等） | AC-02 / AC-03 |
| R-4 | 行为 | SendEventInner 调用 HiSysEventWrite | 上报事件包含 ERROR_TYPE(int32) 和 PACKAGE_NAME(string) 两个字段，eventType 为 FAULT | 所有通过 SendEventInner 上报的异常遵循此格式 | AC-01 / AC-03 / AC-04 |
| R-5 | 行为 | SendComponentExceptionNG 调用 | 除基本字段外附加 NODE_TYPE(int32)、NODE_ID(int32)、ERROR_MESSAGE(string) | 仅 NG 组件异常使用此扩展格式 | AC-05 |
| R-6 | 行为 | ANR 上报流程触发 | 遵循 WARNING→UI_BLOCK_3S、FREEZE→UI_BLOCK_6S、RECOVER→UI_BLOCK_RECOVERED 三阶段；ANRShowDialog 独立使用 UI_BLOCK_DIALOG | 4 个独立事件名 | AC-06 / AC-07 / AC-08 / AC-09 |
| R-7 | 边界 | JsEventReport 调用 | 先调用 JsonUtil::ParseJsonString(jsonStr) 校验 JSON 合法性，校验失败记录 LOGE 并直接返回 | 校验失败不上报事件 | — |
| R-8 | 行为 | 性能阈值违规上报 | ReportPageNodeOverflow/ReportPageDepthOverflow/ReportFunctionTimeout 同时上报实际值和阈值 | 实际值和阈值成对出现 | AC-10 / AC-11 / AC-12 |
| R-9 | 行为 | formEventTimerMap_ 读写 | 在 formEventTimerMutex_ 保护下进行；StartFormModifyTimeoutReportTimer 设置新定时器前先停止同 formId 的旧定时器 | std::lock_guard<std::mutex> 保护 | AC-19 / AC-20 |
| R-10 | 行为 | 表单 modify 超时定时器设置 | 超时值为 WAIT_MODIFY_TIMEOUT(10秒)，XCollie flag 为 XCOLLIE_FLAG_NOOP；超时回调写入 domain=FORM_MANAGER、事件名=FORM_ERROR、ERROR_TYPE=WAIT_MODIFY_FAILED(1) | 超时值固定 10 秒 | AC-17 / AC-18 |
| R-11 | 行为 | JsErrReport 调用 | 写入事件名 JS_ERROR，domain 为 ACE，eventType 为 FAULT，包含 PACKAGE_NAME、REASON、SUMMARY 三个字段 | 固定三字段格式 | — |
| R-12 | 行为 | ReportScrollableErrorEvent 调用 | 携带 TARGET_API_VERSION（AceApplicationInfo::GetInstance().GetApiTargetVersion()）和 VERSION_CODE/VERSION_NAME | 用于按版本聚合错误 | AC-16 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R001 / AC-1.1 | 代码审查 | event_report.cpp 全文 HiSysEventWrite domain 参数为 ACE |
| VM-2 | R002 / AC-2.1 | 代码审查 | event_report.cpp:150-155 StrTrim 调用点及各 Report 方法 |
| VM-3 | R003 / AC-1.2..1.3 | 代码审查 | event_report.cpp:255-396 eventType 与枚举对应 |
| VM-4 | R004 / AC-1.4 | 代码审查 | event_report.cpp:473-480 SendEventInner 实现 |
| VM-5 | R005 / AC-2.2 | 代码审查 | event_report.cpp:286-295 SendComponentExceptionNG 参数 |
| VM-6 | R006 / AC-3.1..3.2 | 代码审查 | event_report.cpp:425-444 ANRRawReport switch 逻辑 |
| VM-7 | R007 / AC-4.1..4.2 | 代码审查 | event_report.cpp:410-416 JsEventReport JSON 校验 |
| VM-8 | R008 / AC-5.1..5.3 | 代码审查 | event_report.cpp:521-546 阈值上报方法参数 |
| VM-9 | R009..R010 / AC-3.3 | 代码审查 | event_report.cpp:638-668 mutex + XCollie 定时器 |
| VM-10 | R011 / AC-4.3 | 代码审查 | event_report.cpp:418-423 JsErrReport 实现 |
| VM-11 | R012 / AC-5.4 | 代码审查 | event_report.cpp:590-604 ReportScrollableErrorEvent 版本参数 |

---

## API 变更分析

### 新增 API

N/A，无新增 Public/System/InnerApi。

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 无 @since 标注（框架内部能力）

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| EventReport 全部方法为 static | 无实例状态（除 curFRCSceneFpsInfo_/calTime_/calFrameRate_/formEventTimerMap_ 四个 static 成员变量），调用方无需创建实例 | AC-01 |
| 头文件与实现路径分离 | event_report.h 位于 frameworks/base/log/，实现在 adapter/ohos/osal/event_report.cpp；preview 环境有独立 stub 实现 | AC-01 |
| EventReport 依赖外部能力 | HiSysEventWrite（HiSysEvent SDK）、XCollie（DFF 框架）、Container::CurrentBundleName()（容器管理）、AceApplicationInfo（应用信息） | AC-01 / AC-17 / AC-18 |
| ExceptionHandler ohos 实现依赖外部能力 | AppMgrClient（KillApplicationSelf）和 ApplicationDataManager（NotifyUnhandledException/NotifyExceptionObject），属 adapter/ohos/osal/ 层 | AC-13 / AC-14 |
| VsyncExcepType 编译宏控制 | VSYNC_TIMEOUT_CHECK 编译宏控制，仅在启用 Vsync 超时检查的构建配置中可用 | — |
| JankFrameReport 依赖 jank 数据采集 | JankFrameReport 类采集的 jank 数据（std::vector<uint16_t>），作为 STATISTIC 类型事件上报 | — |
| formEventTimerMap_ 受 mutex 保护 | std::unordered_map<int64_t, int32_t> 存储 formId → XCollie timerId 映射，受 formEventTimerMutex_ 保护 | AC-19 / AC-20 |

---

## 非功能性需求

| 需求ID | 类别 | 需求描述 | 指标/约束 |
|--------|------|----------|-----------|
| NFR-01 | 性能 | 单次 `HiSysEventWrite` 调用不应阻塞 UI 线程超过 5ms | HiSysEvent 内部异步写入 |
| NFR-02 | 可靠性 | `StrTrim` 截断逻辑需处理 `packageName.size() > 128` 的边界情况，避免 HiSysEvent 字段过长 | `MAX_PACKAGE_NAME_LENGTH = 128` |
| NFR-03 | 线程安全 | `formEventTimerMap_` 的并发访问必须通过 `formEventTimerMutex_` 保护 | `std::lock_guard<std::mutex>` |
| NFR-04 | 可维护性 | 新增异常类型需在对应枚举中追加，并通过 `static_cast<int32_t>` 隐式转换为 `errorType` 字段 | 枚举值从 0 开始自增 |
| NFR-05 | 可观测性 | ANR 上报需区分三个阶段（3s/6s/recovered）和独立弹窗事件，供 hiview 侧按阶段聚合分析 | 4 个独立事件名 |
| NFR-06 | 内存安全 | `KillApplicationByUid` 中 `AppMgrClient` 通过 `std::make_unique` 创建，使用 `CHECK_NULL_VOID` 空指针保护 | `exception_handler.cpp:27-28` |

---

## 多设备适配声明

无差异。

`EventReport` 和 `ExceptionHandler` 的接口定义在 `frameworks/base/log/` 层（平台无关），ohos 实现在 `adapter/ohos/osal/`，preview 实现在 `adapter/preview/osal/`。不同设备形态（手机、平板、折叠屏、穿戴）使用相同的 HiSysEvent domain 和事件名，无需差异化适配。

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 异常上报不干预无障碍路径 | — |
| 大字体 | 不适用 | 无影响 — 事件上报不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — 事件上报不涉及颜色主题 | — |
| 多窗口 | 不适用 | 无影响 — 事件上报与窗口数量无关 | — |
| 多用户 | 不适用 | 无影响 — 框架内部上报不区分用户 | — |
| 版本升级 | 适用 | 低影响 — ReportScrollableErrorEvent 携带 TARGET_API_VERSION 用于版本聚合（R-12） | 滚动错误版本携带 |
| 生态兼容 | 适用 | 无影响 — 框架内部 static 方法，不暴露公开 API | — |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "11 个异常类别常量定义 (event_report.h:30-40)"
  - repo: "openharmony/ace_engine"
    query: "异常类型枚举定义 AppStartExcepType 至 GeneralInteractionErrorType (event_report.h:43-170)"
  - repo: "openharmony/ace_engine"
    query: "数据结构定义 EventInfo/DragInfo/RichEditorInfo/GeneralInteractionErrorInfo/FRCSceneFpsInfo (event_report.h:172-227)"
  - repo: "openharmony/ace_engine"
    query: "EventReport 类全部 public/private 方法声明 (event_report.h:229-303)"
  - repo: "openharmony/ace_engine"
    query: "内部常量定义 EVENT_KEY_* / MAX_PACKAGE_NAME_LENGTH / StrTrim (event_report.cpp:36-157)"
  - repo: "openharmony/ace_engine"
    query: "SendEvent 实现 (event_report.cpp:159-168)"
  - repo: "openharmony/ace_engine"
    query: "各 Send*Exception 方法实现 (event_report.cpp:255-396)"
  - repo: "openharmony/ace_engine"
    query: "JsEventReport / JsErrReport / ANRRawReport / ANRShowDialog 实现 (event_report.cpp:410-456)"
  - repo: "openharmony/ace_engine"
    query: "JankFrameReport 实现 (event_report.cpp:458-471)"
  - repo: "openharmony/ace_engine"
    query: "SendEventInner 实现 (event_report.cpp:473-480)"
  - repo: "openharmony/ace_engine"
    query: "ReportDragInfo 实现 domain=DRAG_UE (event_report.cpp:482-489)"
  - repo: "openharmony/ace_engine"
    query: "ReportPageNodeOverflow / ReportPageDepthOverflow / ReportFunctionTimeout 实现 (event_report.cpp:521-546)"
  - repo: "openharmony/ace_engine"
    query: "ReportScrollableErrorEvent 实现 (event_report.cpp:590-604)"
  - repo: "openharmony/ace_engine"
    query: "StartFormModifyTimeoutReportTimer / StopFormModifyTimeoutReportTimer 实现 (event_report.cpp:638-668)"
  - repo: "openharmony/ace_engine"
    query: "JsErrorObject 结构体及 ExceptionHandler 类声明 (exception_handler.h:24-34)"
  - repo: "openharmony/ace_engine"
    query: "KillApplicationByUid 及 HandleJsException 实现 (exception_handler.cpp:25-54)"
```

**关键文档：**
- [design.md](03-engine-framework/08-dfx-foundation/01-logging/design.md)
