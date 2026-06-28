# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 系统能力（数据检测、隐私敏感、震感反馈） |
| 特性编号 | Feat-06 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 11 起支持（数据检测），API 12（隐私敏感），API 13（震感反馈），持续演进至 API 24+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 存量补录，无增量变更。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 数据检测子能力规格 | enableDataDetector / enableSelectedDataDetector / dataDetectorConfig 完整行为规格 |
| ADDED | 隐私敏感子能力规格 | privacySensitive 双机制（内容替换 + 视觉遮蔽）完整行为规格 |
| ADDED | 震感反馈子能力规格 | enableHapticFeedback 完整行为规格 |

## 输入文档

| 文档 | 位置 |
|------|------|
| 架构设计 | `specs/05-ui-components/09-text-components/04-text/design.md` |
| SDK 动态版 API 声明 | `interface/sdk-js/api/@internal/component/ets/text.d.ts` |
| SDK 静态版 API 声明 | `interface/sdk-js/api/arkui/component/text.static.d.ets` |
| SDK 类型声明（TextDataDetectorConfig） | `interface/sdk-js/api/@internal/component/ets/text_common.d.ts` / `interface/sdk-js/api/arkui/component/textCommon.static.d.ets` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 智能数据检测

**作为** 应用开发者，**我想要** 在 Text 组件中自动识别电话号码、URL、邮箱、地址、日期时间等实体，**以便** 用户可以直接点击实体执行对应操作（拨号、跳转、发邮件等）。

- **AC-1.1** WHEN `enableDataDetector(true)` 且设备支持文本识别 THEN Text 组件内的电话号码、URL、邮箱、地址、日期时间实体被自动标记并高亮
- **AC-1.2** WHEN `enableDataDetector(true)` 但未设置 `dataDetectorConfig` THEN 所有类型实体均被识别，实体样式为 `color: '#ff007dff'`, `decoration: { type: Underline, color: '#ff007dff', style: SOLID }`
- **AC-1.3** WHEN `dataDetectorConfig({ types: [PHONE_NUMBER, URL] })` THEN 仅识别电话号码和 URL，其他实体类型被忽略
- **AC-1.4** WHEN 触摸或右键点击已识别实体 THEN 弹出对应实体类型的操作菜单；WHEN 鼠标左键点击 THEN 直接执行菜单第一个选项
- **AC-1.5** WHEN `textOverflow` 设为 `TextOverflow.MARQUEE` THEN 数据检测不生效
- **AC-1.6** WHEN `copyOption` 设为 `CopyOptions.None` THEN 实体点击菜单不提供文本选择、复制、翻译、分享功能
- **AC-1.7** WHEN `copyOption` 非 `None` 且 `textSelectable` 设为 `UNSELECTABLE` THEN 实体仍有复制功能但无文本选择功能
- **AC-1.8** WHEN `dataDetectorConfig` 设置 `color` 和 `decoration` THEN 识别实体使用自定义样式，覆盖默认蓝色下划线
- **AC-1.9** WHEN `dataDetectorConfig` 设置 `enablePreviewMenu(true)` THEN 实体支持预览菜单
- **AC-1.10** WHEN `dataDetectorConfig` 设置 `onDetectResultUpdate` 回调 THEN AI 检测完成后回调返回 JSON 格式的检测结果
- **AC-1.11** WHEN 实体 A 是实体 B 的子集（A ⊂ B）THEN 保留 B；WHEN A 不是 B 的子集且 B 不是 A 的子集，且 A.start < B.start THEN 保留 A
- **AC-1.12** WHEN 设备不支持文本识别（`DataDetectorInterface::IsDataDetectorSupported()` 返回 false）THEN `enableDataDetector(true)` 静默不生效

### US-2: 选中文本数据检测

**作为** 应用开发者，**我想要** 对选中文本单独启用/禁用数据检测，**以便** 精细控制交互行为。

- **AC-2.1** WHEN `enableSelectedDataDetector(true)` THEN 选中文本区域内的实体被识别并可操作
- **AC-2.2** WHEN `enableSelectedDataDetector(false)` THEN 选中文本内不执行实体检测
- **AC-2.3** WHEN 未设置 `enableSelectedDataDetector` THEN 默认启用（`selectDetectEnabled_ = true`）

### US-3: 隐私敏感内容保护

**作为** 应用开发者，**我想要** 在敏感场景（卡片后台、锁屏等）下自动遮蔽 Text 组件内容，**以便** 保护用户隐私数据。

- **AC-3.1** WHEN `privacySensitive(true)` 且系统触发敏感模式 THEN 文本所有字符（除换行符 `\n`）被替换为 `-`（减号）
- **AC-3.2** WHEN `privacySensitive(true)` 但系统未触发敏感模式 THEN 文本正常显示，不做遮蔽
- **AC-3.3** WHEN `privacySensitive(null)` 或 `privacySensitive(false)` THEN 禁用隐私模式，系统触发敏感模式时文本不受影响
- **AC-3.4** WHEN 隐私模式激活 THEN 文本选择、AI 数据检测、文本复制/搜索功能被禁用
- **AC-3.5** WHEN 隐私模式从激活恢复为非激活 THEN 文本内容恢复原始显示，选择/检测/复制功能恢复

### US-4: obscured 视觉遮蔽（与 privacySensitive 共存的独立机制）

**作为** 应用开发者，**我想要** 通过 `.obscured([ObscuredReasons.PLACEHOLDER])` 在渲染层绘制遮蔽覆盖层，**以便** 在文本上方显示半透明遮罩。

- **AC-4.1** WHEN `renderContext.obscured` 包含 `ObscuredReasons.PLACEHOLDER` 且无 Span 子节点 THEN 在文本每行上绘制 20% alpha、2vp 圆角的半透明矩形遮蔽
- **AC-4.2** WHEN `obscured` 设置但包含 Span 子节点 THEN `IsSetObscured()` 返回 false，不绘制遮蔽矩形
- **AC-4.3** WHEN `privacySensitive` 和 `obscured` 同时启用 THEN 两套机制独立工作：内容替换发生在布局阶段，视觉遮蔽发生在绘制阶段

### US-5: 震感反馈

**作为** 应用开发者，**我想要** 在文本选择操作时提供触觉反馈，**以便** 增强用户的操作感知。

- **AC-5.1** WHEN `enableHapticFeedback(true)` 或未设置（默认 true）且用户长按文本触发选择 THEN 触发 `longPress.light` 类型振动
- **AC-5.2** WHEN `enableHapticFeedback(true)` 或未设置且用户拖动选择手柄使字符索引变化 THEN 触发 `slide` 类型振动
- **AC-5.3** WHEN `enableHapticFeedback(false)` THEN 长按和拖动手柄均不触发振动
- **AC-5.4** WHEN 父 `SelectionContainer` 设置 `enableHapticFeedback(false)` 且 Text 自身未显式设置 THEN Text 继承容器设置，不触发振动
- **AC-5.5** WHEN 父 `SelectionContainer` 设置 `enableHapticFeedback(false)` 但 Text 自身显式设置 `enableHapticFeedback(true)` THEN Text 使用自身设置，触发振动（`hapticFeedbackFlagByUser_` 优先级机制）

## 验收追溯

| AC ID | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 | FR-1 | TASK-6 | 手动测试 + XTS | 设备端验证实体高亮 |
| AC-1.2 | FR-2 | TASK-6 | 手动测试 | 默认样式验证 |
| AC-1.3 | FR-3 | TASK-6 | 单测 | 类型过滤验证 |
| AC-1.4 | FR-4 | TASK-6 | 手动测试 | 菜单弹出验证 |
| AC-1.5 | EX-1 | TASK-6 | 单测 | MARQUEE 模式下 AI 不启动 |
| AC-1.6 | FR-5 | TASK-6 | 手动测试 | 菜单项缺失验证 |
| AC-1.7 | FR-6 | TASK-6 | 手动测试 | 复制可用/选择不可用 |
| AC-1.8 | FR-7 | TASK-6 | 手动测试 | 自定义实体样式 |
| AC-1.9 | FR-8 | TASK-6 | 手动测试 | 预览菜单验证 |
| AC-1.10 | FR-9 | TASK-6 | 单测 | 回调 JSON 验证 |
| AC-1.11 | BR-1 | TASK-6 | 单测 | 实体重叠消歧 |
| AC-1.12 | EX-2 | TASK-6 | 单测 | 不支持设备静默回退 |
| AC-2.1 | FR-10 | TASK-6 | 单测 | 选中文本检测 |
| AC-2.2 | FR-10 | TASK-6 | 单测 | 选中文本检测禁用 |
| AC-2.3 | FR-10 | TASK-6 | 代码审查 | 默认值验证 |
| AC-3.1 | FR-11, BR-2 | TASK-6 | 手动测试 | 卡片后台场景 |
| AC-3.2 | FR-11 | TASK-6 | 手动测试 | 前台正常显示 |
| AC-3.3 | FR-12 | TASK-6 | 单测 | 禁用隐私模式 |
| AC-3.4 | BR-3 | TASK-6 | 单测 | 功能禁用验证 |
| AC-3.5 | RC-1 | TASK-6 | 手动测试 | 恢复后功能正常 |
| AC-4.1 | FR-13 | TASK-6 | 手动测试 | 遮蔽矩形绘制 |
| AC-4.2 | EX-4 | TASK-6 | 单测 | Span 节点时不绘制 |
| AC-4.3 | BR-4 | TASK-6 | 手动测试 | 双机制共存 |
| AC-5.1 | FR-14 | TASK-6 | 手动测试 | 长按振动 |
| AC-5.2 | FR-15 | TASK-6 | 手动测试 | 滑动振动 |
| AC-5.3 | FR-16 | TASK-6 | 单测 | 禁用振动 |
| AC-5.4 | BR-5 | TASK-6 | 单测 | 容器继承 |
| AC-5.5 | BR-5 | TASK-6 | 单测 | 用户显式设置优先 |

## 业务规则

| 规则 ID | 规则描述 | 关联 AC |
|---------|----------|---------|
| BR-1 | 实体重叠消歧策略：子集关系保留超集；非子集关系保留起始位置靠前者 | AC-1.11 |
| BR-2 | privacySensitive 内容替换规则：所有字符（除 `\n`）替换为 `-`，在布局阶段 `TextLayoutAlgorithm::UpdateSensitiveContent()` 执行（`text_layout_algorithm.cpp:1277-1284`） | AC-3.1 |
| BR-3 | privacySensitive 激活时的功能禁用：文本选择（`text_pattern.cpp:1623`）、AI 检测（`text_pattern.cpp:6801`）、复制/搜索（`text_pattern.cpp:5837,6285,8311`）均被禁止 | AC-3.4 |
| BR-4 | privacySensitive 与 obscured 双机制共存：privacySensitive 在布局阶段替换文本内容（`UpdateSensitiveContent`），obscured 在绘制阶段覆盖半透明矩形（`TextContentModifier::DrawObscuration`）；两者触发条件和视觉效果独立 | AC-4.3 |
| BR-5 | 震感反馈容器继承优先级：Text 未显式设置时继承父 SelectionContainer 的 `enableHapticFeedback`；显式设置时（`hapticFeedbackFlagByUser_=true`）不受容器覆盖（`text_pattern.cpp:2884-2914`） | AC-5.4, AC-5.5 |

## 功能规则

| 规则 ID | 规则描述 | 关联 AC |
|---------|----------|---------|
| FR-1 | `enableDataDetector(true)` 在设备支持时启动 AI 实体检测，通过 `DataDetectorAdapter::StartAITask()` 异步执行（`data_detector_adapter.h:105`） | AC-1.1 |
| FR-2 | 默认实体样式：`entityColor='#ff007dff'`, `entityDecorationType=Underline`, `entityDecorationColor='#ff007dff'`, `entityDecorationStyle=SOLID` | AC-1.2 |
| FR-3 | `dataDetectorConfig.types` 传入类型数组，转为逗号分隔字符串存储在 `DataDetectorAdapter::textDetectTypes_`（`text_pattern.cpp:5892`） | AC-1.3 |
| FR-4 | 触摸/右键弹出实体菜单：`DataDetectorAdapter::ShowAIEntityMenu()`（`data_detector_adapter.h:118`）；鼠标左键直接执行 `ResponseBestMatchItem()`（`data_detector_adapter.h:124`） | AC-1.4 |
| FR-5 | `copyOption=None` 时实体菜单仅保留实体操作项，移除选择/复制/翻译/分享 | AC-1.6 |
| FR-6 | `copyOption!=None` + `textSelectable=UNSELECTABLE` 时，实体保留复制功能但无选择功能 | AC-1.7 |
| FR-7 | `dataDetectorConfig.color` 和 `dataDetectorConfig.decoration` 自定义实体样式，通过 `DataDetectorAdapter` 的 `entityColor_`/`entityDecorationType_`/`entityDecorationColor_`/`entityDecorationStyle_` 存储 | AC-1.8 |
| FR-8 | `dataDetectorConfig.enablePreviewMenu=true` 启用实体预览菜单（`DataDetectorAdapter::enablePreviewMenu_`） | AC-1.9 |
| FR-9 | `dataDetectorConfig.onDetectResultUpdate` 注册结果回调，AI 检测完成后通过 `DataDetectorAdapter::onResult_` 返回 JSON 格式检测结果 | AC-1.10 |
| FR-10 | `enableSelectedDataDetector` 控制选中文本的独立检测，通过 `TextPattern::selectDetectorAdapter_` 管理，默认启用（`selectDetectEnabled_=true`，`text_pattern.h:675`） | AC-2.1, AC-2.2, AC-2.3 |
| FR-11 | `privacySensitive(true)` 注册到 `PrivacySensitiveManager`（`frame_node.cpp:3375`）；系统触发时 `PipelineContext::ChangeSensitiveNodes(true)` → `FrameNode::ChangeSensitiveStyle(true)` → `TextPattern::OnSensitiveStyleChange(true)` 设置 `isSensitive_=true` 并触发 `PROPERTY_UPDATE_MEASURE` | AC-3.1, AC-3.2 |
| FR-12 | `privacySensitive(false)` 或 `null` 从 `PrivacySensitiveManager` 中移除节点 | AC-3.3 |
| FR-13 | obscured 遮蔽绘制：`TextPaintMethod::UpdateObscuredRects()` 从段落管理器获取每行矩形，`TextContentModifier::DrawObscuration()` 以文本颜色 20% alpha 填充 2vp 圆角矩形（`text_content_modifier.cpp:765-809`，常量 `OBSCURED_ALPHA=0.2f`） | AC-4.1 |
| FR-14 | 长按触发 `longPress.light` 振动：`TextPattern::StartVibratorByLongPress()` → `VibratorUtils::StartVibraFeedback("longPress.light")`（`text_pattern.cpp:685-688`） | AC-5.1 |
| FR-15 | 选择手柄拖动触发 `slide` 振动：`TextPattern::StartVibratorByIndexChange()` → `VibratorUtils::StartVibraFeedback("slide")`（`text_pattern.cpp:7019-7022`），仅当字符索引变化时触发 | AC-5.2 |
| FR-16 | `enableHapticFeedback(false)` 禁用振动：`isEnableHapticFeedback_=false`（`text_pattern.h:845`），两个振动入口均前置检查此标记 | AC-5.3 |

## 异常/豁免规则

| 规则 ID | 规则描述 | 关联 AC |
|---------|----------|---------|
| EX-1 | `textOverflow=TextOverflow.MARQUEE` 时数据检测不生效：跑马灯模式禁用 AI 检测任务 | AC-1.5 |
| EX-2 | 设备不支持文本识别时 `enableDataDetector(true)` 静默不生效：`DataDetectorInterface::IsDataDetectorSupported()` 返回 false 时 `CanStartAITask()` 返回 false（`text_pattern.cpp:3029`） | AC-1.12 |
| EX-3 | privacySensitive 需要卡片框架支持：`IsSensitiveEnable()` 判断 `isSensitive_ && host->IsPrivacySensitive()`，系统未触发敏感模式时即使属性为 true 也不遮蔽 | AC-3.2 |
| EX-4 | obscured 仅在无 Span 子节点时绘制遮蔽矩形：`IsSetObscured()` 检查 `spans_` 为空（`text_pattern.cpp:7576-7585`） | AC-4.2 |

## 恢复契约

| 规则 ID | 规则描述 | 关联 AC |
|---------|----------|---------|
| RC-1 | 隐私模式恢复：`OnSensitiveStyleChange(false)` 设置 `isSensitive_=false` 并触发 `PROPERTY_UPDATE_MEASURE`，下一帧布局恢复原始文本内容，选择/检测/复制功能恢复（`text_pattern.cpp:7505-7511`） | AC-3.5 |
| RC-2 | 数据检测取消与重启：`DataDetectorAdapter::CancelAITask()` 可取消进行中的检测任务；`enableDataDetector` 从 false 切换为 true 时重新触发 `StartAITask()` | AC-1.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.12 | 手动测试 + 单测 | 各类型实体识别、菜单弹出、自定义样式、模式互斥 |
| VM-2 | AC-2.1 ~ AC-2.3 | 单测 | 选中文本检测启用/禁用、默认值 |
| VM-3 | AC-3.1 ~ AC-3.5 | 手动测试（卡片场景）+ 单测 | 内容替换为 `-`、功能禁用、恢复 |
| VM-4 | AC-4.1 ~ AC-4.3 | 手动测试 + 单测 | 遮蔽矩形绘制、Span 豁免、双机制共存 |
| VM-5 | AC-5.1 ~ AC-5.5 | 手动测试 | 长按/滑动振动、禁用、容器继承 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `enableDataDetector(enable: boolean): TextAttribute` | Public | 启用/禁用 AI 实体检测 | AC-1.1 |
| `dataDetectorConfig(config: TextDataDetectorConfig): TextAttribute` | Public | 配置数据检测类型、样式、回调 | AC-1.3, AC-1.8, AC-1.9, AC-1.10 |
| `enableSelectedDataDetector(enable: boolean \| undefined): TextAttribute` | Public | 控制选中文本的数据检测 | AC-2.1 |
| `privacySensitive(supported: boolean): TextAttribute` | Public | 启用/禁用隐私敏感模式 | AC-3.1 |
| `enableHapticFeedback(isEnabled: boolean): TextAttribute` | Public | 启用/禁用震感反馈 | AC-5.1 |

### 变更/废弃 API

无。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 11（enableDataDetector/dataDetectorConfig）、API 12（privacySensitive/dataDetectorConfig.color/decoration）、API 13（enableHapticFeedback）、API 20（dataDetectorConfig.enablePreviewMenu）、API 22（enableSelectedDataDetector）
- **API 版本号策略:**
  - enableDataDetector: @since 11（动态版初始），@since 12 dynamic（+@atomicservice），@since 23 static
  - dataDetectorConfig: @since 11（动态版初始），@since 12 dynamic（+@atomicservice，+color/decoration 字段），@since 20 dynamic（+enablePreviewMenu 字段），@since 23 static（+enablePreviewMenu @since 24 static）
  - enableSelectedDataDetector: @since 22 dynamic，@since 24 static
  - privacySensitive: @since 12 dynamic（+@form +@atomicservice），@since 23 static
  - enableHapticFeedback: @since 13 dynamic（+@crossplatform +@atomicservice），@since 23 static
  - C-API `ArkUI_TextDataDetectorType` 枚举: @since 12
  - C-API `NODE_TEXT_ENABLE_SELECTED_DATA_DETECTOR`: @since 22
  - C-API `OH_ArkUI_TextDataDetectorConfig` 结构体全套 API: @since 24

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 数据检测依赖设备端 AI 能力 | `DataDetectorInterface` 通过动态加载获取实现（`data_detector_loader.h`），设备不支持时静默回退 | AC-1.12 |
| 隐私敏感依赖系统/卡片框架触发 | `PrivacySensitiveManager` 由 `PipelineContext::ChangeSensitiveNodes()` 统一调度，需要系统侧调用 `UIContentImpl::ChangeSensitiveNodes()` 触发 | AC-3.1, AC-3.2 |
| 震感反馈依赖设备振动器 | `VibratorUtils::StartVibraFeedback()` 需要设备硬件支持 | AC-5.1, AC-5.2 |
| 数据检测属性存储在 TextPattern 成员变量 | 不使用 LayoutProperty/PaintProperty 属性组机制，通过 `DataDetectorAdapter` 管理运行时状态 | AC-1.1 |
| 隐私敏感属性存储在 FrameNode | `isPrivacySensitive_` 是 FrameNode 级属性（`frame_node.h:681`），由 `ViewAbstract::SetPrivacySensitive()` 设置 | AC-3.1 |
| 震感反馈属性存储在 TextPattern 成员变量 | `isEnableHapticFeedback_` 和 `hapticFeedbackFlagByUser_` 直接存储在 TextPattern（`text_pattern.h:845-846`） | AC-5.1 |
| enableHapticFeedback 无独立 C-API NODE 枚举 | C-API 通过内部 `node_text_modifier.cpp` 桥接，无 `NODE_TEXT_ENABLE_HAPTIC_FEEDBACK` 公开枚举 | AC-5.1 |
| 跨子能力互斥 | privacySensitive 激活时禁用数据检测和文本选择；MARQUEE 模式禁用数据检测 | AC-1.5, AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 数据检测为异步 AI 任务，不阻塞 UI 线程；检测完成通过 `TaskExecutor` Post 回 UI 线程更新 | 性能测试 | 异步执行链路 |
| 性能 | privacySensitive 切换触发 `PROPERTY_UPDATE_MEASURE`，仅脏节点重测量 | 帧率分析 | 脏标记机制 |
| 性能 | 震感反馈仅在索引变化时触发 `slide`，非每帧触发 | 手动测试 | 条件判断 `currentIndex != preIndex` |
| 内存 | DataDetectorAdapter 懒创建（`MakeRefPtr<DataDetectorAdapter>()`，`text_pattern.cpp:8820-8828`） | 内存分析 | 未启用时不分配 |
| 安全 | 隐私模式替换文本内容，不泄露原始数据到渲染管线 | 代码审查 | 布局阶段替换 |
| 可靠性 | AI 检测失败时 `ParseAIResult` 处理错误码，不影响文本正常显示 | 单测 | 错误路径覆盖 |
| 问题定位 | Inspector dump 输出 `enableDataDetector`/`enableSelectedDataDetector`/`dataDetectorConfig`/`privacySensitive`/`enableHapticFeedback`（`text_pattern.cpp:4859`，`text_layout_property.cpp:267`） | 调试验证 | dump 输出 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | privacySensitive 激活时无障碍读屏应读取遮蔽内容而非原始文本 | AC-3.1 |
| 大字体 | 否 | 三个子能力不受系统字体缩放影响 | — |
| 深色模式 | 是 | 数据检测实体默认样式 `#ff007dff` 不随深色模式变化；obscured 使用文本颜色 20% alpha 自动适配 | AC-1.2, AC-4.1 |
| 多窗口/分屏 | 否 | 无特殊影响 | — |
| 多用户 | 否 | 无特殊影响 | — |
| 版本升级 | 是 | 数据检测从 API 11 到 API 24 持续演进，需注意各版本字段可用性；见兼容性声明 | 全部 |
| 生态兼容 | 是 | 数据检测能力依赖设备厂商 AI 实现（`DataDetectorInterface`），不同设备支持程度可能不同 | AC-1.12 |

## 行为场景（Gherkin）

```gherkin
Feature: Text 数据检测
  作为 应用开发者
  我想要 自动识别文本中的实体
  以便 用户可以直接操作

  Scenario: 默认数据检测启用
    Given Text 组件内容为 "请拨打 10086 或访问 https://example.com"
    And enableDataDetector(true) 已设置
    And 设备支持文本识别
    When 组件完成布局和 AI 检测
    Then "10086" 显示为蓝色下划线样式 (#ff007dff, Underline)
    And "https://example.com" 显示为蓝色下划线样式

  Scenario: 限定检测类型
    Given Text 组件内容包含电话、URL、邮箱
    And dataDetectorConfig({ types: [PHONE_NUMBER] }) 已设置
    When AI 检测完成
    Then 仅电话号码被高亮
    And URL 和邮箱保持普通文本样式

  Scenario: 自定义实体样式
    Given enableDataDetector(true) 已设置
    And dataDetectorConfig({ types: [URL], color: '#FF0000', decoration: { type: Overline, style: DASHED } })
    When AI 检测完成
    Then URL 实体显示红色 + 虚线上划线

  Scenario: 实体重叠消歧——子集规则
    Given 文本 "call 13812345678 now"
    And 实体 A="138" (PHONE_NUMBER), 实体 B="13812345678" (PHONE_NUMBER)
    When A ⊂ B
    Then 保留 B

  Scenario: MARQUEE 模式禁用检测
    Given enableDataDetector(true) 和 textOverflow(TextOverflow.MARQUEE) 同时设置
    When 组件布局
    Then AI 检测任务不启动

  Scenario: 检测结果回调
    Given enableDataDetector(true) 已设置
    And dataDetectorConfig({ onDetectResultUpdate: callback })
    When AI 检测完成
    Then callback 收到 JSON 格式的检测结果字符串

Feature: Text 隐私敏感
  作为 应用开发者
  我想要 保护敏感文本内容
  以便 在卡片/后台场景隐藏用户数据

  Scenario: 隐私模式激活
    Given Text 组件内容为 "余额: ¥10,000"
    And privacySensitive(true) 已设置
    When 系统触发敏感模式（卡片进入后台）
    Then 显示文本变为 "-------------"（除换行符外全部替换为 '-'）

  Scenario: 隐私模式恢复
    Given 隐私模式已激活，文本显示为 "---"
    When 系统取消敏感模式（卡片恢复前台）
    Then 文本恢复原始内容 "余额: ¥10,000"
    And 文本选择和 AI 检测功能恢复

  Scenario: 隐私模式下功能禁用
    Given privacySensitive(true) 且系统敏感模式已激活
    When 用户尝试长按选择文本
    Then 选择操作不响应
    And AI 数据检测不执行

  Scenario: obscured 独立绘制
    Given renderContext.obscured 包含 ObscuredReasons.PLACEHOLDER
    And 无 Span 子节点
    When 组件绘制
    Then 每行文本上方绘制 20% alpha 半透明圆角矩形（2vp 圆角）

  Scenario: 双机制共存
    Given privacySensitive(true) 和 obscured([PLACEHOLDER]) 同时设置
    When 系统触发敏感模式
    Then 布局阶段文本被替换为 '-'
    And 绘制阶段在替换后的文本上方绘制半透明遮蔽矩形

Feature: Text 震感反馈
  作为 应用开发者
  我想要 在文本选择操作时获得触觉反馈
  以便 增强操作感知

  Scenario: 长按触发振动
    Given Text 组件文本可选择
    And enableHapticFeedback 为默认值 (true)
    When 用户长按文本触发选择
    Then 设备触发 "longPress.light" 类型振动

  Scenario: 拖动手柄触发振动
    Given 文本已选中，选择手柄可见
    And enableHapticFeedback(true)
    When 用户拖动选择手柄且字符索引从 5 变为 8
    Then 设备触发 "slide" 类型振动

  Scenario: 拖动手柄索引未变不振动
    Given 文本已选中
    When 用户拖动选择手柄但字符索引未变化
    Then 不触发振动

  Scenario: 禁用震感
    Given enableHapticFeedback(false)
    When 用户长按文本或拖动手柄
    Then 不触发任何振动

  Scenario: 容器继承
    Given SelectionContainer 设置 enableHapticFeedback(false)
    And Text 未显式设置 enableHapticFeedback
    When 用户长按 Text 触发选择
    Then 不触发振动

  Scenario: 用户设置优先于容器
    Given SelectionContainer 设置 enableHapticFeedback(false)
    And Text 显式设置 enableHapticFeedback(true)
    When 用户长按 Text 触发选择
    Then 设备触发 "longPress.light" 振动
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "TextPattern 数据检测 AI 实体识别流程（DataDetectorAdapter/StartAITask/ParseAIResult）"
  - repo: "openharmony/arkui_ace_engine"
    query: "PrivacySensitiveManager 敏感节点注册与触发链路（ChangeSensitiveNodes/OnSensitiveStyleChange）"
  - repo: "openharmony/arkui_ace_engine"
    query: "VibratorUtils 震感反馈触发（longPress.light/slide 振动类型）"
  - repo: "openharmony/arkui_ace_engine"
    query: "TextContentModifier::DrawObscuration 遮蔽绘制实现"
```

**关键文档：**
- SDK 动态版 API: `interface/sdk-js/api/@internal/component/ets/text.d.ts`
- SDK 静态版 API: `interface/sdk-js/api/arkui/component/text.static.d.ets`
- 数据检测类型: `interface/sdk-js/api/@internal/component/ets/text_common.d.ts`
- C-API: `interfaces/native/native_node.h`, `interfaces/native/native_type.h`
