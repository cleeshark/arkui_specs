# 特性规格

> Func-04-04-08-Feat-04 手写编辑命令与文本组件协同：固化系统手写服务 13 类命令到 TextInput/TextArea/Search/RichEditor 的路由、文本操作、几何手势编辑、线程调度和现有异常行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 手写编辑命令与文本组件协同 |
| 特性编号 | Func-04-04-08-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 内部手写服务命令协同能力；无公开 ArkTS/NDK 版本声明 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | L3（关键） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 命令路由 | 补录 REQUEST_FOCUS、CLEAR_HIT、SET/GET_TEXT、UNDO/REDO、CANUNDO/CANREDO、DELETE/CHOICE/SPACE/MOVE_CURSOR、INVALID |
| ADDED | 组件支持矩阵 | 补录 TextField/Search 与 RichEditor 的命令差异 |
| ADDED | 几何编辑 | 补录全局坐标逆变换、glyph 索引、文本边界求交、选择/删除/空格/光标行为 |
| ADDED | 线程与异常 | 补录同步/异步 UI Task、callback、错误返回、最近 node 状态和测试缺口 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/08-stylus-capability/design.md` | 共享设计，增量合并 |
| 命令接口 | `interfaces/inner_api/ace/stylus/stylus_detector_interface.h:25` | 已核对 |
| 命令路由 | `adapter/ohos/osal/stylus_detector_callback.cpp:37` | 已核对 |
| TextField 操作 | `frameworks/core/components_ng/pattern/text_input/bridge/text_input_dynamic_modifier.cpp:4887` | 已核对 |
| RichEditor 操作 | `frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.cpp:13709` | 已核对 |
| 管理器当前状态 | `frameworks/core/common/stylus/stylus_detector_mgr.h:65`、`adapter/ohos/osal/stylus_detector_mgr.cpp:154` | 已核对 |

## 用户故事

### US-1: 将服务命令路由到最近命中的文本组件

**作为** 系统手写服务，  
**我想要** 对最近落笔命中的文本组件执行编辑命令，  
**以便** 将手写手势转换为组件操作。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN原生 PEN DOWN 命中合格文本组件并 Notify THEN管理器保存该 FrameNode id 和 LayoutInfo；后续命令不携带节点 id，使用这份最近状态 | 正常 |
| AC-1.2 | WHEN `OnDetector` 或 `OnDetectorSync` 读取到 nodeId=0、Current Container/Pipeline/TaskExecutor 为空 THEN返回 `-1` 或 false，不执行组件操作 | 异常 |
| AC-1.3 | WHEN命令到达 THEN通过 Current Container 的 TaskExecutor 将操作派发到 UI 线程；几何/焦点命令同步等待，文本 set/get/undo/redo 异步投递 | 正常 |
| AC-1.4 | WHEN收到 COMMAND_CLEAR_HIT THEN当前实现直接返回 `-1`，不清除 nodeId、layoutInfo 或选择去重状态 | 边界 |
| AC-1.5 | WHEN收到 COMMAND_INVALID 或未知命令 THEN返回 `-1` | 异常 |

实现证据：`stylus_detector_mgr.cpp:154-172`、`stylus_detector_mgr.h:65-105`、`stylus_detector_callback.cpp:371-443`。

### US-2: 执行焦点、文本读写和撤销重做

**作为** 系统手写服务，  
**我想要** 请求焦点并读取或替换文本、控制撤销栈，  
**以便** 完成识别文本回填和编辑历史操作。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN REQUEST_FOCUS 面向 TextInput/TextArea/SearchField THEN请求正确 FocusHub，并以 STYLUS_DETECTOR 原因请求键盘；面向 RichEditor THEN只请求焦点并返回 0 | 正常 |
| AC-2.2 | WHEN SET_TEXT 面向 TextField 类且 text 非空 THEN转换并覆盖全部文本、将 caret 更新到 `std::string::size()`、标记 measure dirty，并在 callback 存在时回调 | 正常 |
| AC-2.3 | WHEN SET_TEXT 的 text 为空字符串 THEN不清空现有内容，但 callback 仍可被调用 | 边界 |
| AC-2.4 | WHEN SET_TEXT 面向 RichEditor THEN异步任务直接返回，不修改文本且不回调 | 边界 |
| AC-2.5 | WHEN GET_TEXT 面向 TextField 类 THEN回调当前文本；WHEN节点不存在或为 RichEditor THEN回调空字符串 | 正常 |
| AC-2.6 | WHEN GET_TEXT 面向其他不匹配 tag THEN当前异步路径可能不回调 | 边界 |
| AC-2.7 | WHEN UNDO/REDO 面向 TextField 类 THEN关闭选择浮层、执行对应动作并标记 measure dirty；面向 RichEditor THEN直接短路 | 正常 |
| AC-2.8 | WHEN CANUNDO/CANREDO 面向 TextField 类 THEN同步返回栈状态；面向 RichEditor THEN返回 false | 正常 |

实现证据：`stylus_detector_callback.cpp:37-155,416-443`、`text_input_dynamic_modifier.cpp:4887-4959`。

### US-3: 根据手写几何执行删除与选择

**作为** 手写笔用户，  
**我想要** 用划线或框选手势删除、选择文本，  
**以便** 不依赖键盘完成编辑。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN DELETE_TEXT 接收矩形 THEN取左右边中点映射 glyph 索引，与 `[0,textLength]` 求交；交集非空时调用 TextInputClient::DeleteRange 并返回 0 | 正常 |
| AC-3.2 | WHEN删除矩形与文本范围无交集、data 为空、节点/Pattern/Client 无效 THEN返回 `-1` | 异常 |
| AC-3.3 | WHEN CHOICE_TEXT 接收矩形 THEN以同样方式映射并裁剪范围，调用 SetSelection | 正常 |
| AC-3.4 | WHEN CHOICE_TEXT 的 start/end/showMenu 与管理器最近状态完全相同 THEN不重复更新选择并返回 `-1` | 边界 |
| AC-3.5 | WHEN showMenu=false THEN menuPolicy=HIDE；WHEN showMenu=true THEN menuPolicy=SHOW 且 forceShowHandle=true | 正常 |

实现证据：`stylus_detector_callback.cpp:157-234,306-358`。

### US-4: 插删空格并移动光标

**作为** 手写笔用户，  
**我想要** 在手势位置插删空格或移动光标，  
**以便** 调整词间距和输入位置。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN INSERT_SPACE 接收矩形 THEN取矩形中心映射 glyph 索引并调用 TextInputClient::InsertOrDeleteSpace；成功返回 0，失败返回 `-1` | 正常 |
| AC-4.2 | WHEN RichEditor 索引位置或前一位置已有普通空格 THEN删除对应空格并以 STYLUS 变更原因上报；否则插入一个空格 | 正常 |
| AC-4.3 | WHEN MOVE_CURSOR 接收点坐标且映射索引位于闭区间 `[0,textLength]` THEN设置 caret、标记 measure dirty 并返回 0 | 正常 |
| AC-4.4 | WHEN MOVE_CURSOR 映射索引越界或无 TextBase/TextInputClient THEN返回 `-1` | 异常 |
| AC-4.5 | WHEN MoveCursorOption.showHandle 为 true 或 false THEN当前 HandleMoveCursor 均不使用该参数，只移动 caret | 边界 |

实现证据：`stylus_detector_callback.cpp:236-304`、`rich_editor_pattern.cpp:13709-13754`。

### US-5: 支持 TextField 与 RichEditor 的差异化命令

**作为** 文本组件维护者，  
**我想要** 明确每类组件实际支持的命令，  
**以便** 服务端不把部分支持误认为完全支持。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN目标为 TextInput/TextArea/Search/SearchField THEN支持 focus、set/get、undo/redo、canUndo/canRedo 以及几何 delete/choice/space/move | 正常 |
| AC-5.2 | WHEN目标为 RichEditor THEN支持 focus 和几何 delete/choice/space/move，但 set/get/undo/redo/canUndo/canRedo 被短路或返回空/false | 边界 |
| AC-5.3 | WHEN RichEditor 执行 INSERT_SPACE THEN TextChangeReason 为 STYLUS；WHEN通过默认 DeleteRange 执行矩形删除 THEN默认 TextChangeReason 为 INPUT | 边界 |
| AC-5.4 | WHEN SET_TEXT 写入非 ASCII UTF-8 文本 THEN caret 使用 UTF-8 字节数，而内容转换为 UTF-16，当前可能产生字节数与 UTF-16 索引不一致 | 边界 |

实现证据：`stylus_detector_callback.cpp:37-304,416-443`、`text_input_dynamic_modifier.cpp:4897-4959`、`rich_editor_pattern.cpp:13709-13754`、`text_field_pattern.h:549-553`。

### US-6: 处理坐标、结果回调和异常输入

**作为** 框架维护者，  
**我想要** 明确坐标映射和错误回调的实际边界，  
**以便** 为服务命令建立可验证的失败行为。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN全局点映射文本索引 THEN减去节点全局绘制偏移；存在 render transform 时执行逆变换 | 正常 |
| AC-6.2 | WHEN局部 Y 小于 textRect.top 或大于 textRect.bottom THEN返回无效索引；WHEN X 超出 textContentRect THEN将 X clamp 到左右边界后继续映射 | 边界 |
| AC-6.3 | WHEN矩形索引与文本边界部分相交 THEN裁剪到 `[0,textLength]`；横向越界仍可能编辑边界文本 | 边界 |
| AC-6.4 | WHEN SET_TEXT 的 data 为空 THEN当前实现在空指针校验前解引用，规格将其记录为异常风险，不承诺稳定返回码 | 异常 |
| AC-6.5 | WHEN SET_TEXT/GET_TEXT 创建 ResultData THEN errorCode/errorMessage 未显式初始化；callback 不得依赖稳定错误码或错误消息 | 边界 |

实现证据：`stylus_detector_callback.cpp:70-119,306-358`、`stylus_detector_interface.h:33-37`。

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-5 | 已有实现 | Command 路由单测 | `stylus_detector_callback.cpp:371-443` |
| AC-2.1~2.8 | R-6~R-13 | 已有实现 | TextField/RichEditor 单测 | callback + dynamic modifier |
| AC-3.1~3.5 | R-14~R-18 | 已有实现 | 几何选择/删除单测 | `stylus_detector_callback.cpp:157-234,306-358` |
| AC-4.1~4.5 | R-19~R-22 | 已有实现 | TextInputClient/RichEditor 单测 | `rich_editor_delete_test_ng.cpp:1088` |
| AC-5.1~5.4 | R-23~R-26 | 已有实现 | 组件矩阵测试 | TextField/RichEditor tests |
| AC-6.1~6.5 | R-27~R-31 | 已有实现 | 坐标/异常故障注入 | `stylus_detector_callback.cpp:306-358` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Notify 保存原生目标 | nodeId/layoutInfo 覆盖为最近命中节点 | 命令本身不携带 node id | AC-1.1 |
| R-2 | 异常 | nodeId=0 或 Container/Pipeline/Executor 空 | 返回 -1/false | 不派发 UI task | AC-1.2 |
| R-3 | 行为 | 命令进入 callback | focus/geometry 用 PostSyncTask，text/history 用 PostTask，canUndo/Redo 用 PostSyncTask | 均执行于 UI TaskType | AC-1.3 |
| R-4 | 边界 | COMMAND_CLEAR_HIT | 返回 -1 | 不清管理器状态 | AC-1.4 |
| R-5 | 异常 | COMMAND_INVALID/未知 | 返回 -1 | 记录 invalid 日志 | AC-1.5 |
| R-6 | 行为 | REQUEST_FOCUS | 请求焦点；TextField 类按 STYLUS_DETECTOR 请求键盘 | RichEditor 不走显式键盘请求 | AC-2.1 |
| R-7 | 行为 | TextField SET_TEXT 非空 | 覆盖文本、caret=text.size、measure dirty、可选 callback | UTF-8 size 用作 UTF-16 caret | AC-2.2, AC-5.4 |
| R-8 | 边界 | SET_TEXT 空字符串 | 不修改文本 | callback 仍执行 | AC-2.3 |
| R-9 | 边界 | RichEditor SET_TEXT | 异步 no-op | 不回调 | AC-2.4 |
| R-10 | 行为 | GET_TEXT | TextField 回调文本；节点不存在/RichEditor 回调空串 | 其他 tag 可能无回调 | AC-2.5, AC-2.6 |
| R-11 | 行为 | TextField UNDO/REDO | 关闭浮层、执行动作、measure dirty | 异步立即返回 0 | AC-2.7 |
| R-12 | 边界 | RichEditor UNDO/REDO | 直接短路 | 异步接口仍先返回 0 | AC-2.7 |
| R-13 | 行为 | CANUNDO/CANREDO | TextField 返回栈状态，RichEditor=false | 仅 OnDetectorSync | AC-2.8 |
| R-14 | 行为 | DELETE_TEXT 有效矩形 | 左右中点→glyph→边界交集→DeleteRange | 交集必须 start<end | AC-3.1 |
| R-15 | 异常 | data/节点/Pattern/Client 无效或无交集 | 返回 -1 | 不执行删除 | AC-3.2 |
| R-16 | 行为 | CHOICE_TEXT 有效矩形 | 设置裁剪后的选择范围 | 使用 TextInputClient | AC-3.3 |
| R-17 | 边界 | 选择三元组未变化 | 不重复更新，返回 -1 | 全局管理器保存去重状态 | AC-3.4 |
| R-18 | 行为 | showMenu false/true | HIDE 或 SHOW+forceShowHandle | 只影响 ChoiceText | AC-3.5 |
| R-19 | 行为 | INSERT_SPACE | 中心点→glyph→InsertOrDeleteSpace | 成功=0，失败=-1 | AC-4.1 |
| R-20 | 行为 | RichEditor 插删空格 | 邻近空格则删除，否则插入 | 变更原因为 STYLUS | AC-4.2 |
| R-21 | 行为 | MOVE_CURSOR 索引 `[0,length]` | SetCaretOffset + measure dirty | 闭区间包含 length | AC-4.3, AC-4.4 |
| R-22 | 边界 | MoveCursorOption.showHandle 任意值 | 当前不影响行为 | HandleMoveCursor 参数未使用 | AC-4.5 |
| R-23 | 行为 | TextField/Search 目标 | 支持全部已实现命令 | tag 集合见 IsTextCategoryComponent | AC-5.1 |
| R-24 | 边界 | RichEditor 目标 | 仅 focus + 四类几何命令 | 文本/撤销栈命令短路 | AC-5.2 |
| R-25 | 边界 | RichEditor 空格与删除 | 空格=STYLUS，默认 DeleteRange=INPUT | 变更原因不统一 | AC-5.3 |
| R-26 | 边界 | SET_TEXT 非 ASCII | caret 使用 UTF-8 字节数 | 内容存储为 UTF-16 | AC-5.4 |
| R-27 | 行为 | 全局坐标映射 | 减全局 paint offset，并按需逆变换 | 使用最近 layoutInfo | AC-6.1 |
| R-28 | 边界 | Y 越界/X 越界 | Y 无效；X clamp 后映射 | X 越界可命中边界 glyph | AC-6.2 |
| R-29 | 边界 | 矩形与文本部分相交 | 裁剪到 `[0,length]` | start<end 才成功 | AC-6.3 |
| R-30 | 异常 | SET_TEXT data=null | 当前先解引用 | 不承诺稳定错误码；不得以该输入验证正常返回 | AC-6.4 |
| R-31 | 边界 | ResultData 未显式初始化 | callback 可获得未初始化 errorCode | 只保证 resultData 在部分路径赋值 | AC-6.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.5, R-1~R-5 | Callback 路由单测 | 最近 node、Current Container、CLEAR_HIT/INVALID、同步/异步线程 |
| VM-2 | AC-2.1~2.8, R-6~R-13 | TextField/RichEditor 单测 | focus、键盘、空 SET、GET 空串、撤销栈支持矩阵 |
| VM-3 | AC-3.1~3.5, R-14~R-18 | 几何命令单测 | 矩形中点、交集、选择去重、菜单/手柄 |
| VM-4 | AC-4.1~4.5, R-19~R-22 | TextInputClient 单测 | 空格前后、caret 0/length/越界、showHandle 无效 |
| VM-5 | AC-5.1~5.4, R-23~R-26 | 组件矩阵测试 | RichEditor 部分支持、变更原因、非 ASCII caret |
| VM-6 | AC-6.1~6.5, R-27~R-31 | 坐标/故障注入 | render transform、Y reject/X clamp、null data、ResultData |

## API 变更分析

> 本特性不新增 Public ArkTS/NDK API。CommandType 和回调仅为系统手写服务与 ace_engine 的 Inner API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `IStylusDetectorCallback::OnDetector` | InnerApi | CommandType, void* data, callback | int32；0/-1 为主 | 无结构化错误码 | 执行 focus、文本、撤销、几何命令 | AC-1.1~6.5 |
| `IStylusDetectorCallback::OnDetectorSync` | InnerApi | CommandType | bool | N/A | 查询 CANUNDO/CANREDO | AC-2.8 |
| `CommandType` | InnerApi | 13 个枚举项 | enum | N/A | 描述服务命令 | 全部 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录现有 Inner API | 无迁移要求 | 全部 |

## 接口规格

### 接口定义

**IStylusDetectorCallback 命令接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OnDetector(const CommandType& command, void* data, std::shared_ptr<IAceStylusCallback> callback)` |
| 函数签名 | `bool OnDetectorSync(const CommandType& command)` |
| 返回值 | 同步命令通常成功 0/失败 -1；异步命令投递成功即返回 0；能力查询返回 bool |
| 开放范围 | InnerApi |
| 错误码 | 无结构化错误码；ResultData.errorCode 当前未稳定初始化 |
| 关联 AC | AC-1.1~6.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| command | CommandType | 是 | INVALID | OnDetector 不处理 CANUNDO/CANREDO；OnDetectorSync 只处理这两类 |
| data | void* | 依命令 | 无 | SET_TEXT 需要 std::string*；几何命令需要对应 option/rect；null 多数返回 -1，SET_TEXT 当前先解引用 |
| callback | shared_ptr | SET/GET 可选/需要 | null | SET_TEXT callback 可选；GET_TEXT 首先要求 callback 非空 |
| nodeId | manager 隐式状态 | 是 | 0 | 必须来自最近原生 Notify；命令不显式携带 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 同步 focus/geometry 命令 | UI 任务完成后返回实际 0/-1 | AC-1.3, AC-2.1, AC-3.1~4.5 |
| 2 | 异步 set/get/undo/redo | 投递后立即返回 0，实际结果通过组件状态/callback 观察 | AC-1.3, AC-2.2~2.7 |
| 3 | RichEditor 文本/撤销栈命令 | no-op、空回调结果或 false | AC-5.2 |
| 4 | CLEAR_HIT/INVALID | 返回 -1 | AC-1.4, AC-1.5 |

## 兼容性声明

- **已有 API 行为变更:** 否；本规格补录现有 Inner API 命令行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；当前 node/layout/selection 是进程内单例状态。
- **最低支持版本:** 无公开 ArkTS/NDK 版本；Inner API 无 `@since`。
- **API 版本号策略:** 不向应用公开，不承诺跨版本二进制稳定性。
- **组件兼容:** RichEditor 仅支持 focus 和几何命令；GET_TEXT 空串不表示内容真实为空。
- **行为兼容:** SET_TEXT 空字符串不清空；MOVE_CURSOR showHandle 无效；CLEAR_HIT 不清状态。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Inner API 隔离 | CommandType/void* data 只用于系统服务内部协同 | 全部 |
| UI 线程执行 | 所有组件读写通过 Current Container TaskExecutor 在 UI 线程执行 | AC-1.2, AC-1.3 |
| 最近目标路由 | 命令绑定 manager 最近 nodeId/layoutInfo，而不是命令参数 | AC-1.1, AC-1.4 |
| 组件能力分层 | TextField 类支持完整命令，RichEditor 只支持 focus+几何命令 | AC-5.1, AC-5.2 |
| 坐标到索引 | 几何命令统一经过 transform、TextDragBase、LayoutInfo 和边界求交 | AC-3.1~4.5, AC-6.1~6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每个同步几何命令只执行一次坐标映射和一次组件操作 | Trace | callback.cpp |
| 功耗 | 无后台任务；命令由服务回调触发 | 源码审查 | OnDetector/Sync |
| 内存 | 不复制持久文本模型；异步 SET_TEXT 捕获一份 std::string | 内存检查 | `adapter/ohos/osal/stylus_detector_callback.cpp:70-91` |
| 安全 | 密码/OTP 资格由 Feat-03 在命令建立前阻断 | 集成测试 | Feat-03 AC-2.3 |
| 可靠性 | 无效 node/坐标/范围返回失败，不越界调用 TextInputClient | 边界单测 | R-2, R-15, R-21, R-28~R-29 |
| 可测试性 | 命令、TextInputClient 和 LayoutInfo 可构造/Mock | 单元测试 | callback 分层函数 |
| 自动化维测 | ACE_STYLUS 日志记录矩形、点、文本长度和越界原因 | 日志测试 | callback.cpp:157-358 |
| 定界定位 | 异步接口返回 0 不代表组件操作完成，需通过 callback/状态观察 | 集成测试 | AC-1.3, AC-2.2~2.7 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 取决于系统手写服务是否下发命令 | 命令矩阵不因设备类型变化 | 真机测试 | Inner API |
| 平板 | 主要支持形态 | 覆盖富文本、非 ASCII、render transform 和几何边界 | 真机测试 | R-23~R-29 |
| 折叠屏 | 全局到局部坐标受窗口/变换影响 | 每次命令按当前 FrameNode 逆变换 | 折叠态测试 | AC-6.1 |
| Preview | Feat-03 不注册服务，因此通常无外部命令入口 | 不作为系统命令协同能力证明 | Preview 测试 | Preview manager false/no-op |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 命令不新增无障碍 action | 无 |
| 大字体 | 是 | 字形布局和文本矩形变化影响坐标映射 | AC-3.1, AC-6.1~6.3 |
| 深色模式 | 否 | 不涉及颜色 | 无 |
| 多窗口/分屏 | 是 | 命令使用 Current Container，但 nodeId 来自进程单例最近目标 | AC-1.1~1.3 |
| 多用户 | 否 | 命令不显式区分用户 | 无 |
| 版本升级 | 是 | Inner API 不承诺应用兼容，组件部分支持行为需回归 | AC-5.1~5.4 |
| 生态兼容 | 是 | 非 ASCII caret、RichEditor 空 GET、异步返回 0 都可能影响服务端解释 | AC-2.5, AC-5.2, AC-5.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 手写编辑命令与文本组件协同
  Scenario: TextField 设置非空文本
    Given 最近命中节点为 TextInput
    When 服务发送 SET_TEXT 且文本非空
    Then OnDetector 异步投递 UI task 并立即返回 0
    And TextInput 内容被全量覆盖并标记 measure dirty

  Scenario: RichEditor 部分支持
    Given 最近命中节点为 RichEditor
    When 服务依次发送 GET_TEXT 和 INSERT_SPACE
    Then GET_TEXT callback 收到空字符串
    And INSERT_SPACE 按几何位置插入或删除空格

  Scenario: 横向越界矩形裁剪到文本边界
    Given 手势矩形 Y 位于 textRect 内且 X 超出 textContentRect
    When 执行 DELETE_TEXT
    Then X 被 clamp 到文本边界并映射 glyph
    And 与文本范围有交集时仍执行边界删除

  Scenario: CLEAR_HIT 不清最近目标
    Given manager 已保存 nodeId 和选择状态
    When 服务发送 CLEAR_HIT
    Then 返回 -1
    And manager 中最近目标状态保持不变
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 覆盖 13 类命令、组件矩阵、坐标映射、线程和异常路径
- [x] RichEditor 部分支持、非 ASCII caret、showHandle、ResultData 和 CLEAR_HIT 风险均显式记录
- [x] 每个 AC 关联规则、验证方式和源码证据
- [x] 同步/异步返回语义分离
- [x] 现有异常行为仅补录，不提出实现修复

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "StylusDetectorCallBack CommandType 命令路由、UI TaskExecutor 和最近 nodeId 状态"
  - repo: "openharmony/arkui_ace_engine"
    query: "TextInput TextArea Search RichEditor 对 set get undo redo delete choice space move cursor 的支持矩阵"
  - repo: "openharmony/arkui_ace_engine"
    query: "手写几何命令全局坐标逆变换、glyph position、文本边界求交和 TextChangeReason STYLUS"
```

**关键文档：** `adapter/ohos/osal/stylus_detector_callback.cpp`、`frameworks/core/components_ng/pattern/text_input/bridge/text_input_dynamic_modifier.cpp`、`frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.cpp`。
