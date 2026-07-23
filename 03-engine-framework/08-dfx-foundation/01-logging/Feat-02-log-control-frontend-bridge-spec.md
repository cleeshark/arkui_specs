# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 日志控制开关与前端日志桥接 |
| 特性编号 | Func-03-08-01-Feat-02 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 ArkUI ace_engine 日志系统的编译期控制开关（USE_HILOG / IS_RELEASE_VERSION / STRIP_RELEASE_LOG / ACE_INSTANCE_LOG / ACE_DEBUG / ACE_UNITTEST）、运行时级别门控（JudgeLevel / SetLogLevel / GetDebugEnabled）、JS console.\* 桥接（JSI + NAPI 双路径）、标签化 JS 日志（JsLogPrint）、Web console.log 事件桥接、以及 4 个独立专用 HiLog 封装器。不涉及 LogWrapper 核心框架与 HiLog 域映射（Feat-01）、HiSysEvent 事件上报（Feat-03）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 编译期日志控制开关系列规格 | ace_config.gni:213-240 定义 USE_HILOG / IS_RELEASE_VERSION / ACE_INSTANCE_LOG / ACE_DEBUG 四个开关；STRIP_RELEASE_LOG / ACE_UNITTEST 为外部注入编译宏 |
| ADDED | STRIP_RELEASE_LOG 宏裁剪规格 | log_wrapper.h:75-116 定义 LOGD/LOGI/LOGW / TAG_LOGD/I/W / APP_LOGD/I/W 在 STRIP_RELEASE_LOG 下展开为 ((void)0) |
| ADDED | IS_RELEASE_VERSION 文件名行号剥离规格 | log_wrapper.h:40-55 定义 PRINT_LOG 在 IS_RELEASE_VERSION 下省略 ACE_FMT_PREFIX 中的 filename:line |
| ADDED | 运行时 DEBUG 门控规格 | log_wrapper.cpp:25-31 定义 JudgeLevel 对 DEBUG 级别额外检查 GetDebugEnabled()，log_wrapper.cpp:33-41 定义 SetLogLevel/GetLogLevel |
| ADDED | JS console.\* JSI 桥接规格 | jsi_declarative_engine.cpp:291-300 定义 PreloadConsole，将 console.log/debug/info/warn/error 绑定到 AppInfoLogPrint 等函数 |
| ADDED | JS console.\* NAPI 桥接规格 | jsi_declarative_engine.cpp:1052-1069 将相同函数注册为 napi 函数 |
| ADDED | 标签化 JsLogPrint 规格 | jsi_base_utils.cpp:694-800 定义 GetLogTag 解析数字 tag（0/1/default）并调用 TAG_LOG\* |
| ADDED | Web console.log 事件桥接规格 | js_web.cpp:676-745 定义 JSWebConsoleLog 包装 WebConsoleLog，:3719-3747 定义 OnConsoleLog 注册回调 |
| ADDED | 4 个专用 HiLog 封装器独立性规格 | ui_service_hilog.h(0xD003935) / ui_session_log.h(0xD003936) / form_renderer_hilog.h(0xD0039FF) / xcomponent_controller_log.h(0xD003931) 各自独立 domain，绕过 LogWrapper |
| ADDED | JsTrace JS 侧 HiTrace 控制规格 | jsi_base_utils.cpp:850-866 定义 JsTraceBegin/End，由 GetDebugEnabled() 门控 |

## 输入文档

- 关联设计：`specs/03-engine-framework/08-dfx-foundation/01-logging/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `ace_config.gni:211-240`（编译开关定义：USE_HILOG / IS_RELEASE_VERSION / ACE_INSTANCE_LOG / ACE_DEBUG）
  - `frameworks/base/log/log_wrapper.h:28-118`（ACE_INSTANCE_LOG 前缀、PRINT_LOG 宏分支、STRIP_RELEASE_LOG 裁剪宏）
  - `frameworks/base/log/log_wrapper.cpp:25-41`（JudgeLevel / SetLogLevel / GetLogLevel 实现）
  - `frameworks/base/log/ace_trace.h:54-58`（ACE_DEBUG_SCOPED_TRACE 宏）
  - `frameworks/bridge/declarative_frontend/engine/jsi/jsi_declarative_engine.cpp:291-300,1052-1069`（JSI/NAPI console.\* 注册）
  - `frameworks/bridge/js_frontend/engine/jsi/jsi_base_utils.cpp:694-866`（JsLogPrint / GetLogTag / AppLogPrint / JsTraceBegin/End）
  - `frameworks/bridge/declarative_frontend/jsview/js_web.cpp:676-745,3719-3747`（Web console.log 桥接）
  - `adapter/ohos/services/uiservice/include/ui_service_hilog.h`（UIService 专用 HiLog）
  - `adapter/ohos/entrance/ui_session/include/ui_session_log.h`（UISession 专用 HiLog + ACE_UNITTEST mock）
  - `interfaces/inner_api/form_render/include/form_renderer_hilog.h`（FormRenderer 专用 HiLog）
  - `interfaces/inner_api/xcomponent_controller/xcomponent_controller_log.h`（XComponentController 专用 HiLog）

## 用户故事

### US-1: STRIP_RELEASE_LOG 编译期裁剪

- As a 发布构建工程师
- I want STRIP_RELEASE_LOG 编译宏在定义后将 DEBUG/INFO/WARN 级别日志宏裁剪为空操作
- So that Release 包体减小且不输出非关键日志，同时保留 ERROR/FATAL 用于线上诊断

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 定义了 STRIP_RELEASE_LOG THEN LOGD(fmt,...) 展开为 `((void)0)`（`log_wrapper.h:76`），LOGI(fmt,...) 展开为 `((void)0)`（`log_wrapper.h:77`），LOGW(fmt,...) 展开为 `((void)0)`（`log_wrapper.h:78`）。来源：`log_wrapper.h:76-78` | 正常 |
| AC-1.2 | WHEN 定义了 STRIP_RELEASE_LOG THEN TAG_LOGD(tag,fmt,...) 展开为 `((void)0)`（`log_wrapper.h:88`），TAG_LOGI 展开为 `((void)0)`（`log_wrapper.h:89`），TAG_LOGW 展开为 `((void)0)`（`log_wrapper.h:90`）。来源：`log_wrapper.h:88-90` | 正常 |
| AC-1.3 | WHEN 定义了 STRIP_RELEASE_LOG THEN APP_LOGD(fmt,...) 展开为 `((void)0)`（`log_wrapper.h:109`），APP_LOGI 展开为 `((void)0)`（`log_wrapper.h:110`），APP_LOGW 展开为 `((void)0)`（`log_wrapper.h:111`）。来源：`log_wrapper.h:109-111` | 正常 |
| AC-1.4 | WHEN 定义了 STRIP_RELEASE_LOG THEN LOGE/LOGF（`log_wrapper.h:84-85`）、TAG_LOGE/TAG_LOGF（`log_wrapper.h:96-97`）、APP_LOGE/APP_LOGF（`log_wrapper.h:117-118`）不受裁剪，仍展开为 PRINT_LOG / PRINT_APP_LOG 输出 ERROR/FATAL 级别日志。来源：`log_wrapper.h:84-85,96-97,117-118` | 边界 |

### US-2: USE_HILOG 编译开关切换后端

- As a 跨平台构建工程师
- I want USE_HILOG 编译开关在 OHOS 构建中默认启用、Preview 构建中关闭
- So that OHOS 平台直接调用 HiLog 宏输出日志，Preview/非 OHOS 平台走 LogWrapper 跨平台 fallback

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 定义了 USE_HILOG THEN PRINT_LOG(level, tag, fmt,...) 展开为 HILOG_IMPL(LOG_CORE, LOG_##level, (tag + ACE_DOMAIN), g_DOMAIN_CONTENTS_MAP.at(tag), ACE_FMT_PREFIX fmt, ...)（`log_wrapper.h:51-54`），并 `#include "hilog/log.h"`（`log_wrapper.h:37`），ACE_DOMAIN=0xD003900（`log_wrapper.h:38`）。来源：`log_wrapper.h:36-55` | 正常 |
| AC-2.2 | WHEN 未定义 USE_HILOG THEN PRINT_LOG(level, tag, fmt,...) 展开为 do-while 块，先调用 LogWrapper::JudgeLevel(level)，通过后调用 LogWrapper::PrintLog(FRAMEWORK, level, tag, ...)（`log_wrapper.h:61-68`）。PRINT_APP_LOG 展开为 LogWrapper::PrintLog(JS_APP, level, ACE_DEFAULT_DOMAIN, ...)（`log_wrapper.h:70-73`）。来源：`log_wrapper.h:61-73` | 正常 |
| AC-2.3 | WHEN ace_config.gni 计算 use_hilog THEN 条件为 `is_mingw || is_mac || is_linux || is_ohos || is_ohos_standard_system`（`ace_config.gni:119`），为 true 时 ace_common_defines 追加 "USE_HILOG"（`ace_config.gni:213-214`）。来源：`ace_config.gni:119,213-214` | 正常 |

### US-3: IS_RELEASE_VERSION 文件名行号剥离

- As a 发布构建工程师
- I want IS_RELEASE_VERSION 编译宏在 Release(user) 构建中定义后剥离日志中的文件名和行号前缀
- So that Release 日志不含源码路径信息，减少信息泄露和包体

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 定义了 IS_RELEASE_VERSION（USE_HILOG 模式下） THEN PRINT_LOG 展开为 `HILOG_IMPL(LOG_CORE, LOG_##level, (tag + ACE_DOMAIN), g_DOMAIN_CONTENTS_MAP.at(tag), "[(%{public}s)] " fmt, LogWrapper::GetIdWithReason().c_str(), ...)`，不包含 GetBriefFileName(__FILE__) 和 __LINE__。来源：`log_wrapper.h:40-46` | 正常 |
| AC-3.2 | WHEN 未定义 IS_RELEASE_VERSION（USE_HILOG 模式下） THEN PRINT_LOG 展开为 `HILOG_IMPL(..., ACE_FMT_PREFIX fmt, GetBriefFileName(__FILE__), __LINE__ ACE_LOG_ID_WITH_REASON, ...)`，包含文件名和行号前缀。来源：`log_wrapper.h:51-54` | 正常 |
| AC-3.3 | WHEN ace_config.gni 中 build_variant == "user" THEN ace_common_defines 追加 "IS_RELEASE_VERSION"（`ace_config.gni:238-239`）。来源：`ace_config.gni:238-239` | 正常 |

### US-4: JudgeLevel DEBUG 门控与运行时级别控制

- As a 框架维护者
- I want JudgeLevel 对 DEBUG 级别实施独立运行时门控（GetDebugEnabled），其余级别仅比较 level_ 阈值
- So that DEBUG 日志受独立开关控制，INFO 以上日志受全局 level_ 控制

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN JudgeLevel(LogLevel::DEBUG) 被调用 THEN 返回 SystemProperties::GetDebugEnabled() 的值，不检查 level_（`log_wrapper.cpp:27-28`）。来源：`log_wrapper.cpp:25-31` | 正常 |
| AC-4.2 | WHEN JudgeLevel(LogLevel::INFO) 被调用 THEN 返回 `level_ <= level`，即 `level_ <= INFO(1)`。level_ 默认为 DEBUG(0)，0 <= 1 为 true。来源：`log_wrapper.cpp:30` | 正常 |
| AC-4.3 | WHEN 调用 SetLogLevel(LogLevel::ERROR) 设置 level_=3 后，再调用 JudgeLevel(LogLevel::WARN) THEN 因 level_(3) <= WARN(2) 为 false，返回 false。来源：`log_wrapper.cpp:30,33-36` | 正常 |
| AC-4.4 | WHEN 调用 GetLogLevel() THEN 返回当前 level_ 的值（`log_wrapper.cpp:38-41`）。level_ 初始值为 LogLevel::DEBUG(0)。来源：`log_wrapper.cpp:38-41` | 边界 |

### US-5: JSI/NAPI console.\* 桥接到 APP_LOG\*

- As a JS 应用开发者
- I want JS 的 console.log/debug/info/warn/error 在 JSI 和 NAPI 两种引擎模式下都能输出到 HiLog APP 域
- So that 应用日志通过 APP_DOMAIN(0xC0D0) + LOG_APP 类型统一输出，与框架日志分离

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN JSI 模式下 PreloadConsole 注册 console 对象 THEN console.log 绑定到 AppInfoLogPrint（`jsi_declarative_engine.cpp:294`），console.debug 绑定到 AppDebugLogPrint（`:295`），console.info 绑定到 AppInfoLogPrint（`:296`），console.warn 绑定到 AppWarnLogPrint（`:297`），console.error 绑定到 AppErrorLogPrint（`:298`）。来源：`jsi_declarative_engine.cpp:291-299` | 正常 |
| AC-5.2 | WHEN NAPI 模式下注册 console 对象 THEN 通过 napi_create_function 创建 log/debug/info/warn/error 函数，分别绑定到 AppInfoLogPrint/AppDebugLogPrint/AppInfoLogPrint/AppWarnLogPrint/AppErrorLogPrint（`jsi_declarative_engine.cpp:1052-1061`），并通过 napi_set_named_property 注册到 consoleObj（`:1064-1068`）。来源：`jsi_declarative_engine.cpp:1052-1069` | 正常 |
| AC-5.3 | WHEN AppLogPrint 被 AppDebugLogPrint/AppInfoLogPrint/AppWarnLogPrint/AppErrorLogPrint 调用 THEN 根据 JsLogLevel 分别调用 APP_LOGD/APP_LOGI/APP_LOGW/APP_LOGE 输出日志（`jsi_base_utils.cpp:723-736`），APP_LOG\* 最终展开为 HILOG_IMPL(LOG_APP, LOG_##level, APP_DOMAIN=0xC0D0, "JSAPP", ...)。来源：`jsi_base_utils.cpp:715-737`, `log_wrapper.h:56` | 正常 |
| AC-5.4 | WHEN JS 代码调用 console.log("msg") 或 console.info("msg") THEN 两者均映射到 JsLogLevel::INFO，最终调用 APP_LOGI 输出 INFO 级别日志。来源：`jsi_declarative_engine.cpp:294,296`, `jsi_base_utils.cpp:728` | 正常 |

### US-6: JsLogPrint 标签化日志映射

- As a 状态管理/组件框架开发者
- I want JsLogPrint 接受数字 tag 参数，将 JS 侧日志路由到对应的 AceLogTag 子域
- So that 状态管理和 Ark 组件日志可通过 HiLog 子域独立过滤

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN JsLogPrint 的第一个参数为数字 0 THEN GetLogTag 解析 tagNum=0，映射为 AceLogTag::ACE_STATE_MGMT（`jsi_base_utils.cpp:702-703`），随后调用 TAG_LOGD/TAG_LOGI/TAG_LOGW/TAG_LOGE 输出使用该 tag。来源：`jsi_base_utils.cpp:701-703,783-795` | 正常 |
| AC-6.2 | WHEN JsLogPrint 的第一个参数为数字 1 THEN GetLogTag 解析 tagNum=1，映射为 AceLogTag::ACE_ARK_COMPONENT（`jsi_base_utils.cpp:705-706`）。来源：`jsi_base_utils.cpp:705-706` | 正常 |
| AC-6.3 | WHEN JsLogPrint 的第一个参数为 0 或 1 以外的值 THEN GetLogTag default 分支映射为 AceLogTag::ACE_DEFAULT_DOMAIN（`jsi_base_utils.cpp:708-709`）。来源：`jsi_base_utils.cpp:708-710` | 边界 |
| AC-6.4 | WHEN JsDebugLogPrint/JsInfoLogPrint/JsWarnLogPrint/JsErrorLogPrint 被调用 THEN 分别委托 JsLogPrint 并传入 JsLogLevel::DEBUG/INFO/WARNING/ERROR（`jsi_base_utils.cpp:824-846`），JsLogPrint 根据 level 调用 TAG_LOGD/TAG_LOGI/TAG_LOGW/TAG_LOGE（`jsi_base_utils.cpp:783-795`），使用 ACE_DOMAIN(0xD003900) 而非 APP_DOMAIN。来源：`jsi_base_utils.cpp:769-800,824-846` | 正常 |

### US-7: Web console.log 事件桥接

- As a Web 组件开发者
- I want Web 组件的 onConsole 事件将 Web 控制台日志传递给 JS 回调
- So that 应用可监听和处理 Web 页面的控制台输出

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN JSWebConsoleLog 类被声明 THEN 继承 WebTransferBase<RefPtr<WebConsoleLog>>（`js_web.cpp:676`），通过 JSClass::Declare("ConsoleMessage") 注册（`:680`），暴露 getLineNumber/getMessage/getMessageLevel/getSourceId/getSource 方法（`:681-685`）。来源：`js_web.cpp:676-686` | 正常 |
| AC-7.2 | WHEN JSWeb::OnConsoleLog 被调用 THEN 创建 JsEventFunction<LoadWebConsoleLogEvent,1> 包装 JS 回调（`js_web.cpp:3724-3725`），最终调用 WebModel::GetInstance()->SetOnConsoleLog(jsCallback) 注册回调（`:3747`）。来源：`js_web.cpp:3719-3747` | 正常 |
| AC-7.3 | WHEN Web console.log 事件触发 THEN LoadWebConsoleLogEventToJSValue 创建 JSWebConsoleLog 实例（`js_web.cpp:2700-2701`），调用 SetMessage 填充 WebConsoleLog 数据（`:2706`），传递给 JS 回调函数。来源：`js_web.cpp:2696-2707` | 正常 |

### US-8: 专用 HiLog 封装器独立性与 ACE_UNITTEST mock

- As a 独立模块维护者
- I want UIService / UISession / FormRenderer / XComponentController 各自维护独立 domain 的 HiLog 封装器，绕过 LogWrapper
- So that 这些模块的日志不依赖 LogWrapper 宏链，拥有独立的 domain 和 tag

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN ui_service_hilog.h 被使用 THEN domain=0xD003935（UISERVICE_LOG_DOMAIN，`:21`），tag="AceUIService"（`:22`），PRINT_LOG 直接调用 HILOG_IMPL（`:28-33`），不经过 LogWrapper；IS_RELEASE_VERSION 下省略 filename:line（`:27-29`），非 IS_RELEASE_VERSION 下附加 ACE_FMT_PREFIX（`:31-33`）。来源：`ui_service_hilog.h:21-34` | 正常 |
| AC-8.2 | WHEN ui_session_log.h 被使用 THEN domain=0xD003936（UISERVICE_LOG_DOMAIN，`:20`），tag="AceUISession"（`:21`）；定义 ACE_UNITTEST 时 PRINT_LOG 展开为空 `#define PRINT_LOG(level, fmt, ...)`（`:27-28`），未定义时走 HILOG_IMPL。来源：`ui_session_log.h:20-39` | 边界 |
| AC-8.3 | WHEN form_renderer_hilog.h 被使用 THEN domain=0xD0039FF（FR_LOG_DOMAIN，`:44`），tag="FormRenderer"（`:48`），IS_RELEASE_VERSION 下 PRINT_HILOG 省略 filename:line（`:58-60`），非 IS_RELEASE_VERSION 下附加 "[%{public}s:%{public}d]" 前缀（`:62-64`）。来源：`form_renderer_hilog.h:43-65` | 正常 |
| AC-8.4 | WHEN xcomponent_controller_log.h 被使用 THEN domain=0xD003931（FR_LOG_DOMAIN，`:44`），tag="XComponentController"（`:48`），与 form_renderer_hilog.h 结构相同，PRINT_HILOG 直接调用 HILOG_IMPL。来源：`xcomponent_controller_log.h:43-59` | 正常 |
| AC-8.5 | WHEN 4 个专用封装器的 domain 值比较 THEN 0xD003935(UIService) / 0xD003936(UISession) / 0xD0039FF(FormRenderer) / 0xD003931(XComponentController) 各不相同，且均不属于 AceLogTag 枚举中的 tag + ACE_DOMAIN 映射体系。来源：4 个 hilog 头文件 | 正常 |

### US-9: ACE_INSTANCE_LOG / ACE_DEBUG / JsTrace 辅助开关

- As a 框架调试开发者
- I want ACE_INSTANCE_LOG 在日志中附加容器实例 ID，ACE_DEBUG 启用 ACE_DEBUG_SCOPED_TRACE，JS 侧 JsTraceBegin/End 由 GetDebugEnabled 门控
- So that 多实例调试时可区分实例来源，调试 trace 可按需开启

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 定义了 ACE_INSTANCE_LOG THEN ACE_FMT_PREFIX 为 `"[%{public}s(%{public}d)-(%{public}s)] "`（`log_wrapper.h:29`），ACE_LOG_ID_WITH_REASON 展开为 `, LogWrapper::GetIdWithReason().c_str()`（`:30`）；未定义时 ACE_FMT_PREFIX 为 `"[%{private}s(%{private}d)] "`（`:32`），ACE_LOG_ID_WITH_REASON 为空。来源：`log_wrapper.h:28-34` | 正常 |
| AC-9.2 | WHEN ace_config.gni 中 enable_ace_instance_log 为 true THEN ace_common_defines 追加 "ACE_INSTANCE_LOG"（`ace_config.gni:230-231`），enable_ace_instance_log 默认值为 true（`ace_config.gni:25`）。来源：`ace_config.gni:25,230-231` | 正常 |
| AC-9.3 | WHEN 定义了 ACE_DEBUG THEN ACE_DEBUG_SCOPED_TRACE(fmt,...) 展开为 `AceScopedTrace aceScopedTrace(fmt, ...)`（`ace_trace.h:55`）；未定义时展开为空（`ace_trace.h:57`）。ace_config.gni 中 enable_ace_debug 默认为 false（`:22`），为 true 时追加 "ACE_DEBUG"（`:226-227`）。来源：`ace_trace.h:54-58`, `ace_config.gni:22,226-227` | 边界 |
| AC-9.4 | WHEN JsTraceBegin 被调用且 SystemProperties::GetDebugEnabled() 返回 true THEN 创建 AceScopedTrace 并压入 aceScopedTrace_ 栈（`jsi_base_utils.cpp:853-855`）；GetDebugEnabled() 为 false 时不创建 trace。JsTraceEnd 在栈非空且 GetDebugEnabled() 为 true 时弹出栈顶（`jsi_base_utils.cpp:863-864`）。来源：`jsi_base_utils.cpp:850-866` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-02 | 宏展开验证 | 代码审查 |
| AC-1.2 | R-1 | TASK-02 | 宏展开验证 | 代码审查 |
| AC-1.3 | R-1 | TASK-02 | 宏展开验证 | 代码审查 |
| AC-1.4 | R-2 | TASK-02 | 宏展开验证 | 代码审查 |
| AC-2.1 | R-3 | TASK-02 | 代码评审 + HiLog 输出验证 | 代码审查 |
| AC-2.2 | R-4 | TASK-02 | 代码评审 | 代码审查 |
| AC-2.3 | R-3 | TASK-02 | 构建配置验证 | 代码审查 |
| AC-3.1 | R-5 | TASK-02 | 宏展开验证 | 代码审查 |
| AC-3.2 | R-5 | TASK-02 | 宏展开验证 | 代码审查 |
| AC-3.3 | R-5 | TASK-02 | 构建变体验证 | 代码审查 |
| AC-4.1 | R-6 | TASK-02 | 单元测试 | 代码审查 |
| AC-4.2 | R-7 | TASK-02 | 单元测试 | 代码审查 |
| AC-4.3 | R-7 | TASK-02 | 单元测试 | 代码审查 |
| AC-4.4 | R-8 | TASK-02 | 代码评审 | 代码审查 |
| AC-5.1 | R-9 | TASK-02 | 代码评审 | 代码审查 |
| AC-5.2 | R-9 | TASK-02 | 代码评审 | 代码审查 |
| AC-5.3 | R-10 | TASK-02 | 代码评审 + HiLog 输出验证 | 代码审查 |
| AC-5.4 | R-9 | TASK-02 | 运行时验证 | 代码审查 |
| AC-6.1 | R-11 | TASK-02 | 代码评审 | 代码审查 |
| AC-6.2 | R-11 | TASK-02 | 代码评审 | 代码审查 |
| AC-6.3 | R-11 | TASK-02 | 代码评审 | 代码审查 |
| AC-6.4 | R-12 | TASK-02 | 代码评审 | 代码审查 |
| AC-7.1 | R-13 | TASK-02 | 代码评审 | 代码审查 |
| AC-7.2 | R-14 | TASK-02 | 代码评审 | 代码审查 |
| AC-7.3 | R-14 | TASK-02 | 运行时验证 | 代码审查 |
| AC-8.1 | R-15 | TASK-02 | 代码评审 | 代码审查 |
| AC-8.2 | R-16 | TASK-02 | 代码评审 + 编译变体验证 | 代码审查 |
| AC-8.3 | R-15 | TASK-02 | 代码评审 | 代码审查 |
| AC-8.4 | R-15 | TASK-02 | 代码评审 | 代码审查 |
| AC-8.5 | R-15 | TASK-02 | 代码评审 | 代码审查 |
| AC-9.1 | R-17 | TASK-02 | 宏展开验证 | 代码审查 |
| AC-9.2 | R-17 | TASK-02 | 构建配置验证 | 代码审查 |
| AC-9.3 | R-18 | TASK-02 | 宏展开验证 + 构建变体验证 | 代码审查 |
| AC-9.4 | R-6 | TASK-02 | 代码评审 + 运行时验证 | 代码审查 |

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 边界 | STRIP_RELEASE_LOG 已定义 | LOGD/LOGI/LOGW、TAG_LOGD/TAG_LOGI/TAG_LOGW、APP_LOGD/APP_LOGI/APP_LOGW 共 9 个宏展开为 `((void)0)` 空操作。 | STRIP_RELEASE_LOG 为外部注入编译宏，不在 ace_config.gni 中定义。 | AC-1.1 / AC-1.2 / AC-1.3 |
| R-2 | 行为 | STRIP_RELEASE_LOG 已定义时 LOGE/LOGF / TAG_LOGE/TAG_LOGF / APP_LOGE/APP_LOGF | ERROR 和 FATAL 级别不受 STRIP_RELEASE_LOG 裁剪，始终展开为 PRINT_LOG / PRINT_APP_LOG。 | 无例外，LOGE/LOGF 宏定义在 STRIP_RELEASE_LOG 条件块之外。 | AC-1.4 |
| R-3 | 行为 | USE_HILOG 编译开关状态 | 定义时 PRINT_LOG 展开为 HILOG_IMPL 直接调用；未定义时展开为 JudgeLevel + LogWrapper::PrintLog 跨平台 fallback。 | use_hilog 默认在 OHOS/macOS/Linux/MinGW 平台为 true。 | AC-2.1 / AC-2.2 / AC-2.3 |
| R-4 | 行为 | 非 USE_HILOG 模式下 PRINT_LOG 展开后端 | 先调用 JudgeLevel(level) 进行运行时级别判断，通过后调用 LogWrapper::PrintLog(FRAMEWORK, level, tag, ACE_FMT_PREFIX fmt, ...)。 | fallback 路径需要平台实现 PrintLog(va_list) 变体。 | AC-2.2 |
| R-5 | 行为 | IS_RELEASE_VERSION 编译开关状态 | 定义时 PRINT_LOG 省略 ACE_FMT_PREFIX 中的 GetBriefFileName(__FILE__) 和 __LINE__，使用固定 "[(%{public}s)] " 前缀 + GetIdWithReason()；未定义时附加文件名:行号前缀。 | build_variant == "user" 时定义 IS_RELEASE_VERSION。 | AC-3.1 / AC-3.2 / AC-3.3 |
| R-6 | 行为 | JudgeLevel(LogLevel::DEBUG) 或 JsTraceBegin 调用 | DEBUG 级别日志和 JS trace 均由 SystemProperties::GetDebugEnabled() 运行时门控，不受 level_ 控制。 | GetDebugEnabled() 为全局运行时开关，默认 false。 | AC-4.1 / AC-9.4 |
| R-7 | 行为 | JudgeLevel(INFO/WARN/ERROR/FATAL) | 返回 `level_ <= level`，即当前全局阈值小于等于请求级别时输出。 | level_ 默认为 DEBUG(0)，所有非 DEBUG 级别均通过。 | AC-4.2 / AC-4.3 |
| R-8 | 边界 | LogWrapper::level_ 初始化与 GetLogLevel | level_ 初始值为 LogLevel::DEBUG(0)；GetLogLevel 返回 level_ 当前值；SetLogLevel 可修改 level_。 | level_ 定义在 adapter/ohos/osal/log_wrapper.cpp:147。 | AC-4.4 |
| R-9 | 行为 | JS console.\* JSI/NAPI 注册 | JSI 模式通过 PreloadConsole 在全局 console 对象上设置 log/debug/info/warn/error 属性；NAPI 模式通过 napi_create_function + napi_set_named_property 注册。两者绑定相同 C++ 函数。 | console.log 和 console.info 均映射到 AppInfoLogPrint（INFO 级别）。 | AC-5.1 / AC-5.2 / AC-5.4 |
| R-10 | 行为 | AppLogPrint 日志输出 | 根据 JsLogLevel 分别调用 APP_LOGD/APP_LOGI/APP_LOGW/APP_LOGE，最终展开为 HILOG_IMPL(LOG_APP, ..., APP_DOMAIN=0xC0D0, "JSAPP", ...)。 | APP_LOG\* 受 STRIP_RELEASE_LOG 裁剪（DEBUG/INFO/WARN）。 | AC-5.3 |
| R-11 | 行为 | GetLogTag 数字 tag 解析 | tagNum=0 映射 ACE_STATE_MGMT，tagNum=1 映射 ACE_ARK_COMPONENT，其他值映射 ACE_DEFAULT_DOMAIN。 | GetLogTag 在 argc < 1 时返回 false。 | AC-6.1 / AC-6.2 / AC-6.3 |
| R-12 | 行为 | JsLogPrint 使用 TAG_LOG\* | JsLogPrint 根据 level 调用 TAG_LOGD/TAG_LOGI/TAG_LOGW/TAG_LOGE，使用 ACE_DOMAIN(0xD003900) + tag 子域，而非 APP_DOMAIN。 | 与 AppLogPrint 的 APP_LOG\* 形成域分离。 | AC-6.4 |
| R-13 | 行为 | JSWebConsoleLog 包装 WebConsoleLog | JSWebConsoleLog 继承 WebTransferBase<RefPtr<WebConsoleLog>>，声明为 "ConsoleMessage"，暴露 getLineNumber/getMessage/getMessageLevel/getSourceId/getSource 方法。 | 仅为 JS 包装层，不含日志输出逻辑。 | AC-7.1 |
| R-14 | 行为 | JSWeb::OnConsoleLog 回调注册 | 创建 JsEventFunction<LoadWebConsoleLogEvent,1> 包装 JS 回调，调用 WebModel::GetInstance()->SetOnConsoleLog 注册。事件触发时通过 LoadWebConsoleLogEventToJSValue 构建 JSWebConsoleLog 实例传给回调。 | 回调在 UI 线程执行。 | AC-7.2 / AC-7.3 |
| R-15 | 行为 | 专用 HiLog 封装器独立 domain | UIService(0xD003935) / UISession(0xD003936) / FormRenderer(0xD0039FF) / XComponentController(0xD003931) 各自维护独立 domain 和 tag，直接调用 HILOG_IMPL，绕过 LogWrapper 宏链。 | 4 个 domain 各不相同，均不属于 AceLogTag 枚举映射体系。 | AC-8.1 / AC-8.3 / AC-8.4 / AC-8.5 |
| R-16 | 边界 | ACE_UNITTEST 下 ui_session_log.h PRINT_LOG mock | 定义 ACE_UNITTEST 时 PRINT_LOG 展开为空，抑制 UISession 模块所有日志输出；仅 ui_session_log.h 和 ace_trace.h 受此开关影响。 | ACE_UNITTEST 在 test/unittest/BUILD.gn:127,185 等处定义。 | AC-8.2 |
| R-17 | 行为 | ACE_INSTANCE_LOG 实例 ID 附加 | 定义时 ACE_FMT_PREFIX 包含实例 ID 和 reason（`"[%{public}s(%{public}d)-(%{public}s)] "`），通过 GetIdWithReason() 获取；未定义时使用 `%{private}s` 标记的简洁前缀。 | enable_ace_instance_log 默认 true。 | AC-9.1 / AC-9.2 |
| R-18 | 边界 | ACE_DEBUG 下 ACE_DEBUG_SCOPED_TRACE | 定义 ACE_DEBUG 时展开为 AceScopedTrace 局部对象；未定义时展开为空。enable_ace_debug 默认 false。 | ACE_DEBUG_SCOPED_TRACE 用于细粒度调试 trace。 | AC-9.3 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.4 / R-1 / R-2 | 宏展开验证 + 编译变体验证 | 预处理器输出对照：STRIP_RELEASE_LOG defined/undefined |
| VM-2 | AC-2.1..2.3 / R-3 / R-4 | 代码评审 + 构建配置验证 | ace_config.gni:119,213-214；log_wrapper.h:36-73 宏分支对照 |
| VM-3 | AC-3.1..3.3 / R-5 | 宏展开验证 + 编译变体验证 | IS_RELEASE_VERSION 分支 PRINT_LOG 预处理器输出 |
| VM-4 | AC-4.1..4.4 / R-6..R-8 | 单元测试 | test/unittest/core/base/log_wrapper_test.cpp（JudgeLevel / SetLogLevel / GetLogLevel） |
| VM-5 | AC-5.1..5.4 / R-9 / R-10 | 代码评审 + HiLog 输出验证 | jsi_declarative_engine.cpp JSI/NAPI console 注册 + APP_LOG\* 域验证 |
| VM-6 | AC-6.1..6.4 / R-11 / R-12 | 代码评审 | jsi_base_utils.cpp GetLogTag/JsLogPrint/TAG_LOG\* 对照 |
| VM-7 | AC-7.1..7.3 / R-13 / R-14 | 代码评审 + 运行时验证 | js_web.cpp JSWebConsoleLog + OnConsoleLog + WebModel 回调 |
| VM-8 | AC-8.1..8.5 / R-15 / R-16 | 代码评审 + 编译变体验证 | 4 个专用 hilog 头文件 domain/tag 对照 + ACE_UNITTEST mock 验证 |
| VM-9 | AC-9.1..9.4 / R-6 / R-17 / R-18 | 宏展开验证 + 构建配置验证 + 运行时验证 | ACE_INSTANCE_LOG/ACE_DEBUG 宏分支 + GetDebugEnabled trace 门控 |

## API 变更分析

### 新增 API

N/A，无新增 Public/System/InnerApi。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

无新增接口规格。

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 无 @since 标注（框架内部能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 编译期开关统一管理 | USE_HILOG / IS_RELEASE_VERSION / STRIP_RELEASE_LOG 在 ace_config.gni 中统一管理，不允许在业务 BUILD.gn 中重复定义 | AC-1.1 |
| JS console 桥接双引擎 | JS console.\* 桥接必须同时支持 JSI 和 NAPI 两种引擎模式，两条路径绑定的 C++ 函数必须保持一致 | AC-2.1 |
| 日志域分离 | JsLogPrint 使用 TAG_LOG*（ACE_DOMAIN），AppLogPrint 使用 APP_LOG*（APP_DOMAIN），两者域分离不可混用 | AC-3.1 |
| 专用 HiLog 封装器独立域 | 4 个封装器直接调用 HILOG_IMPL，绕过 LogWrapper 宏链，拥有独立 domain，不参与 AceLogTag 枚举体系 | AC-4.1 |
| ACE_UNITTEST 仅测试构建 | 仅在单元测试构建中定义（test/unittest/BUILD.gn），生产构建中不得定义 | AC-5.1 |
| ACE_DEBUG_SCOPED_TRACE 默认关闭 | 仅在 ACE_DEBUG 定义时生效，不得在生产代码中依赖其输出 | AC-6.1 |

## 非功能性需求

- 性能：STRIP_RELEASE_LOG 裁剪的 9 个宏在编译期展开为 `((void)0)`，零运行时开销；JudgeLevel 为简单整数比较，未通过时零额外开销。
- 可观测：IS_RELEASE_VERSION 构建中日志不含文件名/行号前缀，减少信息泄露；ACE_INSTANCE_LOG 模式下每条日志附加容器实例 ID。
- 鲁棒性：ACE_UNITTEST 下 ui_session_log.h PRINT_LOG 展开为空，测试中不产生实际日志输出；JsTraceBegin/End 在 GetDebugEnabled() 为 false 时静默跳过。
- 安全：IS_RELEASE_VERSION 构建中 ACE_FMT_PREFIX 使用 `%{public}s` 暴露 GetIdWithReason()，非 Release 版本中文件名和行号使用 `%{public}s`/`%{public}d`。

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 本 Feat 为框架内部日志控制与桥接 | — |
| 大字体 | 不适用 | 无影响 — 日志控制不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — 日志控制不涉及颜色主题 | — |
| 多窗口 | 不适用 | 无影响 — 日志开关与窗口数量无关 | — |
| 多用户 | 不适用 | 无影响 — 框架日志不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | JS console.* 桥接影响所有 JS 应用日志输出 | JSI/NAPI 桥接路径 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "enable_ace_debug 默认值 false (ace_config.gni:22)"
  - repo: "openharmony/ace_engine"
    query: "enable_ace_instance_log 默认值 true (ace_config.gni:25)"
  - repo: "openharmony/ace_engine"
    query: "use_hilog 条件：is_mingw || is_mac || is_linux || is_ohos || is_ohos_standard_system (ace_config.gni:119)"
  - repo: "openharmony/ace_engine"
    query: "USE_HILOG 编译开关定义 (ace_config.gni:213-214)"
  - repo: "openharmony/ace_engine"
    query: "ACE_DEBUG 编译开关定义 (ace_config.gni:226-227)"
  - repo: "openharmony/ace_engine"
    query: "ACE_INSTANCE_LOG 编译开关定义 (ace_config.gni:230-231)"
  - repo: "openharmony/ace_engine"
    query: "IS_RELEASE_VERSION 编译开关定义 (ace_config.gni:238-239)"
  - repo: "openharmony/ace_engine"
    query: "ACE_INSTANCE_LOG 条件编译前缀 ACE_FMT_PREFIX / ACE_LOG_ID_WITH_REASON (log_wrapper.h:28-34)"
  - repo: "openharmony/ace_engine"
    query: "USE_HILOG include 与 ACE_DOMAIN=0xD003900 / APP_DOMAIN=0xC0D0 (log_wrapper.h:36-39)"
  - repo: "openharmony/ace_engine"
    query: "IS_RELEASE_VERSION 分支下的 PRINT_LOG 宏定义 (log_wrapper.h:40-55)"
  - repo: "openharmony/ace_engine"
    query: "PRINT_APP_LOG 宏定义，USE_HILOG 模式 (log_wrapper.h:56)"
  - repo: "openharmony/ace_engine"
    query: "非 USE_HILOG 分支下的 PRINT_LOG / PRINT_APP_LOG 宏定义 (log_wrapper.h:57-74)"
  - repo: "openharmony/ace_engine"
    query: "STRIP_RELEASE_LOG 条件下的 LOGD/LOGI/LOGW 宏定义 (log_wrapper.h:75-83)"
  - repo: "openharmony/ace_engine"
    query: "LOGE/LOGF 宏定义，不受 STRIP_RELEASE_LOG 裁剪 (log_wrapper.h:84-85)"
  - repo: "openharmony/ace_engine"
    query: "STRIP_RELEASE_LOG 条件下的 TAG_LOGD/TAG_LOGI/TAG_LOGW 宏定义 (log_wrapper.h:87-95)"
  - repo: "openharmony/ace_engine"
    query: "TAG_LOGE/TAG_LOGF 宏定义，不受 STRIP_RELEASE_LOG 裁剪 (log_wrapper.h:96-97)"
  - repo: "openharmony/ace_engine"
    query: "STRIP_RELEASE_LOG 条件下的 APP_LOGD/APP_LOGI/APP_LOGW 宏定义 (log_wrapper.h:108-116)"
  - repo: "openharmony/ace_engine"
    query: "APP_LOGE/APP_LOGF 宏定义，不受 STRIP_RELEASE_LOG 裁剪 (log_wrapper.h:117-118)"
  - repo: "openharmony/ace_engine"
    query: "JudgeLevel 实现：DEBUG 门控 GetDebugEnabled + level_ 比较 (log_wrapper.cpp:25-31)"
  - repo: "openharmony/ace_engine"
    query: "SetLogLevel 实现 (log_wrapper.cpp:33-36)"
  - repo: "openharmony/ace_engine"
    query: "GetLogLevel 实现 (log_wrapper.cpp:38-41)"
  - repo: "openharmony/ace_engine"
    query: "ACE_DEBUG 条件下的 ACE_DEBUG_SCOPED_TRACE 宏定义 (ace_trace.h:54-58)"
  - repo: "openharmony/ace_engine"
    query: "ACE_UNITTEST 条件下的 mock trace 函数 (ace_trace.h:218-222)"
  - repo: "openharmony/ace_engine"
    query: "PreloadConsole：JSI 模式 console.* 注册 (jsi_declarative_engine.cpp:291-300)"
  - repo: "openharmony/ace_engine"
    query: "NAPI 模式 console.* 注册 (jsi_declarative_engine.cpp:1052-1069)"
  - repo: "openharmony/ace_engine"
    query: "GetLogTag：数字 tag 解析 0/1/default (jsi_base_utils.cpp:694-713)"
  - repo: "openharmony/ace_engine"
    query: "AppLogPrint：JsLogLevel → APP_LOG* 映射 (jsi_base_utils.cpp:715-737)"
  - repo: "openharmony/ace_engine"
    query: "AppDebugLogPrint/AppInfoLogPrint/AppWarnLogPrint/AppErrorLogPrint 包装函数 (jsi_base_utils.cpp:742-767)"
  - repo: "openharmony/ace_engine"
    query: "JsLogPrint：GetLogTag + TAG_LOG* 输出 (jsi_base_utils.cpp:769-800)"
  - repo: "openharmony/ace_engine"
    query: "JsDebugLogPrint/JsInfoLogPrint/JsWarnLogPrint/JsErrorLogPrint 包装函数 (jsi_base_utils.cpp:824-846)"
  - repo: "openharmony/ace_engine"
    query: "JsTraceBegin/JsTraceEnd：GetDebugEnabled 门控 + AceScopedTrace 栈 (jsi_base_utils.cpp:848-866)"
  - repo: "openharmony/ace_engine"
    query: "JSWebConsoleLog 类声明与方法注册 (js_web.cpp:676-686)"
  - repo: "openharmony/ace_engine"
    query: "JSWebConsoleLog 实现：SetMessage/Constructor/Destructor (js_web.cpp:689-745)"
  - repo: "openharmony/ace_engine"
    query: "JSWeb::StaticMethod 'onConsole' → OnConsoleLog (js_web.cpp:2469)"
  - repo: "openharmony/ace_engine"
    query: "LoadWebConsoleLogEventToJSValue：事件 → JSWebConsoleLog 实例 (js_web.cpp:2696-2707)"
  - repo: "openharmony/ace_engine"
    query: "JSWeb::OnConsoleLog：回调注册 WebModel::SetOnConsoleLog (js_web.cpp:3719-3747)"
  - repo: "openharmony/ace_engine"
    query: "UIService 专用 HiLog：domain=0xD003935, tag=AceUIService (ui_service_hilog.h:21-34)"
  - repo: "openharmony/ace_engine"
    query: "UISession 专用 HiLog：domain=0xD003936, tag=AceUISession, ACE_UNITTEST mock (ui_session_log.h:20-39)"
  - repo: "openharmony/ace_engine"
    query: "FormRenderer 专用 HiLog：domain=0xD0039FF, tag=FormRenderer (form_renderer_hilog.h:43-65)"
  - repo: "openharmony/ace_engine"
    query: "XComponentController 专用 HiLog：domain=0xD003931, tag=XComponentController (xcomponent_controller_log.h:43-59)"
  - repo: "openharmony/ace_engine"
    query: "ACE_UNITTEST 编译宏定义位置 (test/unittest/BUILD.gn:127,185)"
  - repo: "openharmony/ace_engine"
    query: "ACE_UNITTEST 在 ui_session 测试中的定义 (test/unittest/adapter/ohos/entrance/ui_session/BUILD.gn:28)"
```

**关键文档：**
- [design.md](03-engine-framework/08-dfx-foundation/01-logging/design.md)
