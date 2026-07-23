# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | LogWrapper核心框架与HiLog适配 |
| 特性编号 | Func-03-08-01-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 ArkUI ace_engine 日志框架的核心基础设施：AceLogTag 子域枚举体系、LogWrapper 跨平台接口、HiLog 适配后端、编译期宏展开链、CallbackLogger crash 上下文注册。不涉及日志控制开关与前端桥接（Feat-02）、HiSysEvent 事件上报（Feat-03）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | AceLogTag 子域枚举与 HiLog domain 映射规格 | log_wrapper.h:149-256 定义 105 个枚举值（0-103 + 255），每个 tag 映射为 tag + ACE_DOMAIN 的 HiLog 子域 |
| ADDED | LogWrapper 跨平台接口规格 | log_wrapper.h:273-298, log_wrapper.cpp:25-62 定义 JudgeLevel / SetLogLevel / GetBriefFileName / PrintLog 等接口 |
| ADDED | OHOS HiLog 适配后端规格 | adapter/ohos/osal/log_wrapper.cpp 定义 g_DOMAIN_CONTENTS_MAP(102 条)、CallbackLogger 实现、LogBacktrace |
| ADDED | 编译期宏展开链规格 | log_wrapper.h:36-118 定义 LOGD-LOGF / TAG_LOGD-TAG_LOGF / APP_LOGD-APP_LOGF / PRINT_LOG / PRINT_APP_LOG 宏链 |
| ADDED | CallbackLogger crash 上下文生命周期规格 | log_wrapper.h:300-311, adapter/ohos/osal/log_wrapper.cpp:189-228 RAII 式 crash 对象注册/清除 |

## 输入文档

- 关联设计：`specs/03-engine-framework/08-dfx-foundation/01-logging/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/base/log/log_wrapper.h`（314 行）—— 中央头文件，枚举/宏/类声明
  - `frameworks/base/log/log_wrapper.cpp`（74 行）—— 跨平台实现
  - `adapter/ohos/osal/log_wrapper.cpp`（229 行）—— OHOS HiLog 后端适配

## 用户故事

### US-1: AceLogTag 子域映射 HiLog

- As a 框架日志消费者
- I want 每个组件日志使用独立的 AceLogTag 子域号，映射为 `tag + ACE_DOMAIN` 的 HiLog 域 ID
- So that 运维和开发人员可通过 `hilog -D <tag_string>` 精确过滤单个组件的日志

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN AceLogTag 枚举定义完成 THEN 包含 105 个枚举值：ACE_DEFAULT_DOMAIN=0 至 ACE_LAZY_WATER_FLOW=103（连续 104 个），以及 FORM_RENDER=255（末位保留）。来源：`log_wrapper.h:149-256` | 正常 |
| AC-1.2 | WHEN 计算 HiLog 域 ID THEN 公式为 `tag + ACE_DOMAIN`，其中 ACE_DOMAIN=0xD003900（`log_wrapper.h:38`）。示例：ACE_DEFAULT_DOMAIN=0 产生 0xD003900（注释 C03900），ACE_TEXT=19 产生 0xD003913（注释 C03913），ACE_NATIVE_NODE=61 产生 0xD00393D（注释 C0393D），FORM_RENDER=255 产生 0xD0039FF（注释 C039FF）。来源：`log_wrapper.h:38,149-256` | 正常 |
| AC-1.3 | WHEN HiLog 输出日志 THEN tag 字符串来自 g_DOMAIN_CONTENTS_MAP，该 map 包含 102 条 AceLogTag 到 C 字符串的映射。来源：`adapter/ohos/osal/log_wrapper.cpp:42-145` | 正常 |
| AC-1.4 | WHEN 枚举值 ACE_INDICATOR=91 或 ACE_IMAGE_GENERATION=99 被用于 PRINT_LOG THEN g_DOMAIN_CONTENTS_MAP 中无对应条目，`g_DOMAIN_CONTENTS_MAP.at(tag)` 调用将抛出 `std::out_of_range` 异常。来源：`adapter/ohos/osal/log_wrapper.cpp:42-145` 缺失这两项 | 异常 |

### US-2: 编译期宏展开链

- As a 框架开发者
- I want LOGD/LOGI/LOGW/LOGE/LOGF 宏按固定链路展开为 HiLog 调用或跨平台 fallback
- So that 业务代码使用统一宏接口，编译期自动选择后端

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 未定义 STRIP_RELEASE_LOG THEN LOGD(fmt,...) 展开为 TAG_LOGD(ACE_DEFAULT_DOMAIN, fmt,...)，TAG_LOGD(tag,fmt,...) 展开为 PRINT_LOG(DEBUG, tag, fmt,...)。来源：`log_wrapper.h:80,92` | 正常 |
| AC-2.2 | WHEN LOGE/LOGF 被使用 THEN 无论 STRIP_RELEASE_LOG 是否定义，LOGE 展开为 TAG_LOGE（`log_wrapper.h:84`），LOGF 展开为 TAG_LOGF（`log_wrapper.h:85`），即 ERROR/FATAL 级别不被裁剪。来源：`log_wrapper.h:84-85,96-97` | 正常 |
| AC-2.3 | WHEN 定义了 STRIP_RELEASE_LOG THEN LOGD/LOGI/LOGW 展开为 `((void)0)`（`log_wrapper.h:76-78`），TAG_LOGD/TAG_LOGI/TAG_LOGW 也展开为 `((void)0)`（`log_wrapper.h:88-90`）。来源：`log_wrapper.h:76-78,88-90` | 边界 |
| AC-2.4 | WHEN 定义了 USE_HILOG THEN PRINT_LOG(level, tag, fmt,...) 展开为 HILOG_IMPL(LOG_CORE, LOG_##level, (tag + ACE_DOMAIN), g_DOMAIN_CONTENTS_MAP.at(tag), ACE_FMT_PREFIX fmt, ...)，其中 ACE_FMT_PREFIX 为 `"[%{public}s(%{public}d)] "` 或 release 版本的 private 变体。来源：`log_wrapper.h:44-55` | 正常 |
| AC-2.5 | WHEN 未定义 USE_HILOG THEN PRINT_LOG(level, tag, fmt,...) 展开为 do-while 块，先调用 LogWrapper::JudgeLevel 判断级别，通过后调用 LogWrapper::PrintLog(FRAMEWORK, level, tag, ...)。来源：`log_wrapper.h:61-68` | 正常 |

### US-3: 日志级别判断

- As a 框架维护者
- I want LogWrapper::JudgeLevel 对 DEBUG 级别实施额外运行时门控，其余级别仅比较 level_ 阈值
- So that DEBUG 日志在非调试构建中被抑制，INFO 以上日志受全局 level_ 控制

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN JudgeLevel(LogLevel::DEBUG) 被调用 THEN 返回 SystemProperties::GetDebugEnabled() 的值，不检查 level_。来源：`log_wrapper.cpp:27-28` | 正常 |
| AC-3.2 | WHEN JudgeLevel(LogLevel::INFO) 被调用（level_ 为默认值 DEBUG=0） THEN 因 level_(0) <= INFO(1) 返回 true。来源：`log_wrapper.cpp:30` | 正常 |
| AC-3.3 | WHEN SetLogLevel(LogLevel::ERROR) 后调用 JudgeLevel(LogLevel::WARN) THEN 因 level_(3) <= WARN(2) 为 false，返回 false。来源：`log_wrapper.cpp:30,33-36` | 正常 |
| AC-3.4 | WHEN LogWrapper::level_ 未被显式设置 THEN 初始值为 LogLevel::DEBUG（即 0）。来源：`adapter/ohos/osal/log_wrapper.cpp:147` | 边界 |

### US-4: APP_LOG 与 TAG_LOG 域分离

- As a JS 应用日志消费者
- I want APP_LOGD-APP_LOGF 使用 APP_DOMAIN(0xC0D0) 和 LOG_APP 类型，与框架 TAG_LOG* 的 ACE_DOMAIN(0xD003900) 和 LOG_CORE 类型完全分离
- So that JS 应用日志可通过独立域过滤，不与框架日志混淆

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 定义了 USE_HILOG THEN PRINT_APP_LOG(level, fmt,...) 展开为 HILOG_IMPL(LOG_APP, LOG_##level, APP_DOMAIN, "JSAPP", fmt,...)，其中 APP_DOMAIN=0xC0D0（`log_wrapper.h:39`）。来源：`log_wrapper.h:56,39` | 正常 |
| AC-4.2 | WHEN APP_LOGD 被使用 THEN 展开链为 APP_LOGD -> PRINT_APP_LOG(DEBUG, fmt,...) -> HILOG_IMPL(LOG_APP, LOG_DEBUG, 0xC0D0, "JSAPP", fmt,...)。来源：`log_wrapper.h:113,56` | 正常 |
| AC-4.3 | WHEN TAG_LOG*(tag, fmt,...) 被使用 THEN 使用 LOG_CORE 类型与 ACE_DOMAIN(0xD003900) + tag 的域；APP_LOG* 使用 LOG_APP 类型与 APP_DOMAIN(0xC0D0)。两者域 ID 和日志类型均不同。来源：`log_wrapper.h:44-56` | 正常 |
| AC-4.4 | WHEN 未定义 USE_HILOG THEN PRINT_APP_LOG 展开为 LogWrapper::PrintLog(LogDomain::JS_APP, level, ACE_DEFAULT_DOMAIN, fmt,...)，domain 参数为 JS_APP 而非 FRAMEWORK。来源：`log_wrapper.h:70-73` | 正常 |

### US-5: CallbackLogger crash 上下文生命周期

- As a 崩溃分析工程师
- I want LOG_CALLBACK 宏在回调执行期间通过 DFX_SetCrashObj 注册 crash 上下文，回调结束后自动清除
- So that 崩溃发生时 crash 报告能包含最后执行的回调信息

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN LOG_CALLBACK(callback) 宏展开 THEN 创建 CallbackLogger 局部对象，构造参数为 (__FUNCTION__, reinterpret_cast<uintptr_t>(callback))。来源：`log_wrapper.h:100` | 正常 |
| AC-5.2 | WHEN CallbackLogger 构造函数执行 THEN 拼接 msg_ 为 `"[<funcName>] crash occured on callback: 0x<callback_hex>"`，并通过 dlsym("DFX_SetCrashObj") 获取函数指针调用 SetCrashObj(0, msg_.c_str())，返回值存入 lastObjAddr_。来源：`adapter/ohos/osal/log_wrapper.cpp:217-223` | 正常 |
| AC-5.3 | WHEN CallbackLogger 析构函数执行 THEN 调用 ResetCrashObj(lastObjAddr_)，其内部通过 dlsym("DFX_ResetCrashObj") 获取函数指针并调用。来源：`adapter/ohos/osal/log_wrapper.cpp:225-227,203-215` | 正常 |
| AC-5.4 | WHEN _GNU_SOURCE 未定义或 dlsym 未找到 "DFX_SetCrashObj" 符号 THEN SetCrashObj 返回 0（`adapter/ohos/osal/log_wrapper.cpp:197-200`），ResetCrashObj 直接返回不做操作（`adapter/ohos/osal/log_wrapper.cpp:211-214`）。来源：`adapter/ohos/osal/log_wrapper.cpp:189-201,203-215` | 异常 |

### US-6: GetBriefFileName 路径截取

- As a 框架开发者
- I want PrintLog 自动将完整文件路径截取为纯文件名，避免日志中出现过长的路径前缀
- So that 日志可读性高且不泄露完整构建路径

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN GetBriefFileName("/path/to/file.cpp") 被调用 THEN 使用 strrchr(name, '/') 查找最后一个分隔符，返回 "file.cpp"。来源：`log_wrapper.cpp:43-48` | 正常 |
| AC-6.2 | WHEN GetBriefFileName("file.cpp") 被调用（无路径分隔符） THEN strrchr 返回 nullptr，直接返回原始 name 指针 "file.cpp"。来源：`log_wrapper.cpp:46-47` | 正常 |
| AC-6.3 | WHEN GetSeparatorCharacter() 被调用 THEN 返回 '/'（`adapter/ohos/osal/log_wrapper.cpp:149-152`）。GetBriefFileName 中 separator 为 static 变量，仅初始化一次。来源：`adapter/ohos/osal/log_wrapper.cpp:149-152`, `log_wrapper.cpp:45` | 正常 |

### US-7: LOGF_ABORT 致命中止

- As a 框架开发者
- I want LOGF_ABORT 宏在输出 FATAL 日志后立即调用 abort() 终止进程
- So that 不可恢复的编程错误能被立即发现并阻止继续执行

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN LOGF_ABORT(fmt,...) 被调用 THEN 先执行 LOGF(fmt,...) 输出 FATAL 级别日志，随后调用 abort() 终止进程。来源：`log_wrapper.h:102-106` | 异常 |
| AC-7.2 | WHEN LOGF_ABORT 在 STRIP_RELEASE_LOG 已定义的场景下被调用 THEN LOGF 仍然生效（`log_wrapper.h:85` 未被 STRIP_RELEASE_LOG 裁剪），abort() 仍然执行。来源：`log_wrapper.h:85,102-106` | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-01 | 代码评审 | 代码审查 |
| AC-1.2 | R-1 / R-2 | TASK-01 | 代码评审 + hilog 域过滤验证 | 代码审查 |
| AC-1.3 | R-2 | TASK-01 | 代码评审 + g_DOMAIN_CONTENTS_MAP 条目统计 | 代码审查 |
| AC-1.4 | R-12 | TASK-01 | 代码评审（已知缺陷） | 代码审查 |
| AC-2.1 | R-3 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-2.2 | R-4 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-2.3 | R-5 | TASK-01 | 编译变体验证 | 代码审查 |
| AC-2.4 | R-6 | TASK-01 | 代码评审 + HiLog 输出验证 | 代码审查 |
| AC-2.5 | R-7 | TASK-01 | 代码评审 | 代码审查 |
| AC-3.1 | R-8 | TASK-01 | 单元测试 | 代码审查 |
| AC-3.2 | R-9 | TASK-01 | 单元测试 | 代码审查 |
| AC-3.3 | R-9 | TASK-01 | 单元测试 | 代码审查 |
| AC-3.4 | R-10 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.1 | R-11 | TASK-01 | 代码评审 + HiLog 输出验证 | 代码审查 |
| AC-4.2 | R-11 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-4.3 | R-11 / R-2 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.4 | R-11 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.1 | R-13 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-5.2 | R-13 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.3 | R-14 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.4 | R-15 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.1 | R-16 | TASK-01 | 单元测试 | 代码审查 |
| AC-6.2 | R-16 | TASK-01 | 单元测试 | 代码审查 |
| AC-6.3 | R-17 | TASK-01 | 代码评审 | 代码审查 |
| AC-7.1 | R-18 | TASK-01 | 代码评审 | 代码审查 |
| AC-7.2 | R-4 / R-18 | TASK-01 | 编译变体验证 | 代码审查 |

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | AceLogTag 枚举定义 | 每个 tag 值加上 ACE_DOMAIN(0xD003900) 构成 HiLog 子域 ID。枚举值 0-103 连续，FORM_RENDER=255 为末位保留。 | FORM_RENDER=255 注释标注 "do not add"。 | AC-1.1 / AC-1.2 |
| R-2 | 行为 | PRINT_LOG 宏展开（USE_HILOG 定义时） | HILOG_IMPL 的 domain 参数为 `tag + ACE_DOMAIN`，tag 参数为 `g_DOMAIN_CONTENTS_MAP.at(tag)`。 | 若 tag 不在 map 中则 .at() 抛出 std::out_of_range。 | AC-1.2 / AC-1.3 |
| R-3 | 行为 | LOGD/LOGI/LOGW 宏使用 | 默认展开为 TAG_LOG*(ACE_DEFAULT_DOMAIN, fmt,...)，即使用 ACE_DEFAULT_DOMAIN=0 子域。 | LOGE/LOGF 同理使用 ACE_DEFAULT_DOMAIN。 | AC-2.1 |
| R-4 | 行为 | LOGE/LOGF / TAG_LOGE / TAG_LOGF 宏使用 | ERROR 和 FATAL 级别不受 STRIP_RELEASE_LOG 裁剪，始终展开为 PRINT_LOG。 | 无例外。 | AC-2.2 / AC-7.2 |
| R-5 | 边界 | STRIP_RELEASE_LOG 已定义 | LOGD/LOGI/LOGW 和 TAG_LOGD/TAG_LOGI/TAG_LOGW 展开为 `((void)0)` 空操作。 | APP_LOGD/APP_LOGI/APP_LOGW 同样被裁剪。 | AC-2.3 |
| R-6 | 行为 | PRINT_LOG 在 USE_HILOG + 非 IS_RELEASE_VERSION 下展开 | HILOG_IMPL 调用附加 ACE_FMT_PREFIX 前缀，包含 GetBriefFileName(__FILE__) 和 __LINE__。 | IS_RELEASE_VERSION 时前缀变为固定 "[(%{public}s)] " + GetIdWithReason()。 | AC-2.4 |
| R-7 | 行为 | PRINT_LOG 在非 USE_HILOG 下展开 | 先调用 JudgeLevel 判断，通过后调用 LogWrapper::PrintLog(FRAMEWORK, level, tag, ...) 走跨平台 fallback。 | fallback 路径需要平台实现 PrintLog va_list 变体。 | AC-2.5 |
| R-8 | 行为 | JudgeLevel(DEBUG) | 返回 SystemProperties::GetDebugEnabled()，不受 level_ 控制。 | DEBUG 级别有独立运行时开关。 | AC-3.1 |
| R-9 | 行为 | JudgeLevel(INFO/WARN/ERROR/FATAL) | 返回 `level_ <= level`，即当前全局阈值小于等于请求级别时输出。 | level_ 默认为 DEBUG(0)，所有级别均通过。 | AC-3.2 / AC-3.3 |
| R-10 | 边界 | LogWrapper::level_ 初始化 | 静态成员 level_ 初始值为 LogLevel::DEBUG(0)。 | 定义在 adapter/ohos/osal/log_wrapper.cpp:147。 | AC-3.4 |
| R-11 | 行为 | APP_LOG* 宏使用 | 使用 APP_DOMAIN(0xC0D0) + LOG_APP 类型 + 固定 tag "JSAPP"；TAG_LOG* 使用 ACE_DOMAIN(0xD003900) + LOG_CORE 类型 + g_DOMAIN_CONTENTS_MAP tag 字符串。 | 两套宏的 domain/type/tag 三维完全独立。 | AC-4.1 / AC-4.2 / AC-4.3 / AC-4.4 |
| R-12 | 异常 | g_DOMAIN_CONTENTS_MAP 查找不存在的 tag | ACE_INDICATOR(91) 和 ACE_IMAGE_GENERATION(99) 在枚举中存在但在 map 中缺失，调用 .at() 会抛出 std::out_of_range。 | 已知缺陷，新增枚举值时必须同步更新 map。 | AC-1.4 |
| R-13 | 行为 | CallbackLogger 构造 | 拼接 "[funcName] crash occured on callback: 0x<hex>" 消息，通过 dlsym("DFX_SetCrashObj") 注册 crash 上下文。 | 消息存储于 msg_ 成员，lastObjAddr_ 保存返回句柄。 | AC-5.1 / AC-5.2 |
| R-14 | 行为 | CallbackLogger 析构 | 调用 ResetCrashObj(lastObjAddr_)，通过 dlsym("DFX_ResetCrashObj") 清除 crash 上下文。 | RAII 模式，作用域结束自动清除。 | AC-5.3 |
| R-15 | 异常 | dlsym 未找到 DFX 符号 | SetCrashObj 返回 0，ResetCrashObj 无操作。不影响程序正常运行。 | _GNU_SOURCE 未定义或系统无 DFX 库时走此路径。 | AC-5.4 |
| R-16 | 行为 | GetBriefFileName 调用 | 使用 strrchr 查找 GetSeparatorCharacter() 返回的分隔符('/')，返回最后一个分隔符之后的部分；无分隔符则返回原始指针。 | separator 为 static 变量，仅初始化一次。 | AC-6.1 / AC-6.2 |
| R-17 | 行为 | GetSeparatorCharacter 调用 | OHOS 平台返回 '/'。 | 跨平台接口，其他平台可返回不同值。 | AC-6.3 |
| R-18 | 异常 | LOGF_ABORT 调用 | 先执行 LOGF 输出 FATAL 日志，再调用 abort() 终止进程。LOGF 不受 STRIP_RELEASE_LOG 裁剪。 | 不可恢复，进程必定终止。 | AC-7.1 / AC-7.2 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1 / R-1 | 代码评审 | log_wrapper.h:149-256 枚举定义对照 |
| VM-2 | AC-1.2 / R-1 / R-2 | hilog 输出验证 | hilog -D AceText 过滤 C03913 域 |
| VM-3 | AC-1.3 / R-2 | 代码评审 + 条目统计 | adapter/ohos/osal/log_wrapper.cpp:42-145（102 条） |
| VM-4 | AC-1.4 / R-12 | 代码评审 | g_DOMAIN_CONTENTS_MAP 缺失 ACE_INDICATOR/ACE_IMAGE_GENERATION |
| VM-5 | AC-2.1..2.5 / R-3..R-7 | 宏展开验证 + 编译变体验证 | 预处理器输出对照 |
| VM-6 | AC-3.1..3.4 / R-8..R-10 | 单元测试 | test/unittest/core/base/log_wrapper_test.cpp（JudgeLevel / SetLogLevel） |
| VM-7 | AC-4.1..4.4 / R-11 | 代码评审 + hilog 输出验证 | APP_LOG* vs TAG_LOG* 域/类型/tag 对照 |
| VM-8 | AC-5.1..5.4 / R-13..R-15 | 代码评审 | CallbackLogger 构造/析构 + dlsym 路径 |
| VM-9 | AC-6.1..6.3 / R-16 / R-17 | 单元测试 | test/unittest/core/base/log_wrapper_test.cpp（GetBriefFileName） |
| VM-10 | AC-7.1..7.2 / R-18 | 代码评审 | LOGF_ABORT 宏展开对照 |

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
| 三层调用链单向依赖 | 宏 → LogWrapper → HiLog 三层调用链严格自上而下，不允许反向依赖 | AC-1.1 |
| 日志输出必须使用框架宏 | 框架内所有日志输出必须使用 LOGD/LOGI/LOGW/LOGE/LOGF / TAG_LOG* / APP_LOG* 宏，禁止直接调用 printf 或 std::cout | AC-1.2 |
| USE_HILOG 编译开关 | OHOS 构建中默认启用（ace_config.gni 中 use_hilog 默认 true），Preview 构建关闭 | AC-2.1 |
| LogWrapper 不可实例化 | LogWrapper 为 final class，构造和析构函数均为 delete，所有方法为静态方法 | AC-1.1 |
| CallbackLogger 仅 RAII | CallbackLogger 为 final class，拷贝构造和赋值操作符为 delete，仅支持 RAII 局部对象使用 | AC-3.1 |
| g_DOMAIN_CONTENTS_MAP 编译期固定 | ACE_FORCE_EXPORT 全局常量，编译期固定，运行时不可修改 | AC-4.1 |

## 非功能性需求

- 性能：USE_HILOG 模式下 PRINT_LOG 直接内联展开为 HILOG_IMPL 宏，无额外函数调用开销；非 USE_HILOG 模式下 JudgeLevel 为内联级别判断，未通过时零开销。
- 可观测：每条框架日志携带 AceLogTag 子域（102 种）和文件名:行号前缀（非 release 版本），支持 `hilog -D <tag>` 精确过滤。
- 鲁棒性：dlsym 获取 DFX 符号失败时 CallbackLogger 静默降级，不影响程序正常运行。
- 安全：IS_RELEASE_VERSION 构建中将文件名和行号标记为 `%{public}s`，ACE_INSTANCE_LOG 模式下实例 ID 使用 `%{public}s` 暴露。

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 本 Feat 为框架内部日志基础设施 | — |
| 大字体 | 不适用 | 无影响 — 日志输出不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — 日志输出不涉及颜色主题 | — |
| 多窗口 | 不适用 | 无影响 — 日志基础设施与窗口数量无关 | — |
| 多用户 | 不适用 | 无影响 — 框架日志不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | 新增子域需在枚举和 g_DOMAIN_CONTENTS_MAP 同步注册（R-12） | AceLogTag 扩展 |

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
    query: "ACE_INSTANCE_LOG 条件编译前缀定义 (log_wrapper.h:28-34)"
  - repo: "openharmony/ace_engine"
    query: "USE_HILOG include 与 ACE_DOMAIN=0xD003900 / APP_DOMAIN=0xC0D0 常量 (log_wrapper.h:36-39)"
  - repo: "openharmony/ace_engine"
    query: "IS_RELEASE_VERSION 分支下的 PRINT_LOG 宏定义 (log_wrapper.h:40-55)"
  - repo: "openharmony/ace_engine"
    query: "PRINT_APP_LOG 宏定义 (log_wrapper.h:56)"
  - repo: "openharmony/ace_engine"
    query: "非 USE_HILOG 分支下的 PRINT_LOG / PRINT_APP_LOG 宏定义 (log_wrapper.h:57-74)"
  - repo: "openharmony/ace_engine"
    query: "STRIP_RELEASE_LOG 条件下的 LOGD-LOGF / TAG_LOGD-TAG_LOGF 宏定义 (log_wrapper.h:75-97)"
  - repo: "openharmony/ace_engine"
    query: "LOG_FUNCTION 宏定义 (log_wrapper.h:99)"
  - repo: "openharmony/ace_engine"
    query: "LOG_CALLBACK 宏定义 (log_wrapper.h:100)"
  - repo: "openharmony/ace_engine"
    query: "LOGF_ABORT 宏定义 (log_wrapper.h:102-106)"
  - repo: "openharmony/ace_engine"
    query: "STRIP_RELEASE_LOG 条件下的 APP_LOGD-APP_LOGF 宏定义 (log_wrapper.h:108-118)"
  - repo: "openharmony/ace_engine"
    query: "AceLogTag 枚举完整定义，105 个枚举值 (log_wrapper.h:149-256)"
  - repo: "openharmony/ace_engine"
    query: "g_DOMAIN_CONTENTS_MAP extern 声明 (log_wrapper.h:258)"
  - repo: "openharmony/ace_engine"
    query: "LogDomain 枚举：FRAMEWORK=0, JS_APP (log_wrapper.h:260-263)"
  - repo: "openharmony/ace_engine"
    query: "LogLevel 枚举：DEBUG=0, INFO, WARN, ERROR, FATAL (log_wrapper.h:265-271)"
  - repo: "openharmony/ace_engine"
    query: "LogWrapper 类声明 (log_wrapper.h:273-298)"
  - repo: "openharmony/ace_engine"
    query: "LogBacktrace 函数声明 (log_wrapper.h:300)"
  - repo: "openharmony/ace_engine"
    query: "CallbackLogger 类声明 (log_wrapper.h:302-311)"
  - repo: "openharmony/ace_engine"
    query: "JudgeLevel 实现：DEBUG 门控 + level_ 比较 (log_wrapper.cpp:25-31)"
  - repo: "openharmony/ace_engine"
    query: "SetLogLevel / GetLogLevel 实现 (log_wrapper.cpp:33-41)"
  - repo: "openharmony/ace_engine"
    query: "GetBriefFileName 实现：strrchr 路径截取 (log_wrapper.cpp:43-48)"
  - repo: "openharmony/ace_engine"
    query: "StripFormatString / ReplaceFormatString 实现 (log_wrapper.cpp:50-62)"
  - repo: "openharmony/ace_engine"
    query: "非 USE_HILOG 下 PrintLog(va_list) 转发实现 (log_wrapper.cpp:64-72)"
  - repo: "openharmony/ace_engine"
    query: "g_DOMAIN_CONTENTS_MAP 定义，102 条映射 (adapter/ohos/osal/log_wrapper.cpp:42-145)"
  - repo: "openharmony/ace_engine"
    query: "LogWrapper::level_ 静态成员初始化为 DEBUG (adapter/ohos/osal/log_wrapper.cpp:147)"
  - repo: "openharmony/ace_engine"
    query: "GetSeparatorCharacter 返回 '/' (adapter/ohos/osal/log_wrapper.cpp:149-152)"
  - repo: "openharmony/ace_engine"
    query: "ACE_INSTANCE_LOG 下 GetId / GetIdWithReason 实现 (adapter/ohos/osal/log_wrapper.cpp:154-167)"
  - repo: "openharmony/ace_engine"
    query: "LogBacktrace 实现：dlsym('GetTrace') + mutex (adapter/ohos/osal/log_wrapper.cpp:169-187)"
  - repo: "openharmony/ace_engine"
    query: "SetCrashObj 实现：dlsym('DFX_SetCrashObj') (adapter/ohos/osal/log_wrapper.cpp:189-201)"
  - repo: "openharmony/ace_engine"
    query: "ResetCrashObj 实现：dlsym('DFX_ResetCrashObj') (adapter/ohos/osal/log_wrapper.cpp:203-215)"
  - repo: "openharmony/ace_engine"
    query: "CallbackLogger 构造/析构实现 (adapter/ohos/osal/log_wrapper.cpp:217-228)"
```

**关键文档：**
- [design.md](03-engine-framework/08-dfx-foundation/01-logging/design.md)
