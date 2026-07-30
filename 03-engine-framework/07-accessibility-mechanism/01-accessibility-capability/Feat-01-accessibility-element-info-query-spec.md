# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍元素信息查询响应 |
| 特性编号 | Func-03-07-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 13 起（NDK Provider 基线） |
| SIG 归属 | SIG_ApplicationFramework |
| 状态 | Draft |
| 复杂度 | 复杂 |

> 本特性为**框架内部能力补录**：当前实现即契约。所有行为结论均可溯源至 ace_engine 源码（标注 `file:line`）。存疑行为仅以风险记录，不提议修改。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无障碍元素信息查询响应能力规格化 | 将既有实现固化为可追溯契约，覆盖 OSAL 组装方向与 NDK Provider 方向两条查询响应链路、ElementInfo 字段来源优先级、节点查询过滤规则与坐标基准 |

## 输入文档

- 设计文档：`03-engine-framework/07-accessibility-mechanism/01-accessibility-capability/design.md`
- 源码定位：`adapter/ohos/osal/js_accessibility_manager.cpp`、`frameworks/core/components_ng/property/accessibility_property.cpp`、`frameworks/core/accessibility/native_interface_accessibility_impl.cpp`、`interfaces/native/native_interface_accessibility.h`
- 知识库：`docs/kb/architecture/accessibility.md`（func_id 03-07-01）

> 需求基线、不涉及项详见 design.md。design.md 与本文档并行产出。

## 用户故事

### US-1: 系统无障碍服务按 ID 查询组件元素信息

作为系统无障碍服务（屏幕阅读器）
我想要按 elementId 查询 ArkUI 组件树元素信息
以便朗读组件内容、状态与位置

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN SA 以合法 elementId 与 `PREFETCH_RECURSIVE_CHILDREN` 模式查询 THEN 返回该节点自身及可见子树的 ElementInfo 列表 | 正常 |
| AC-1.2 | WHEN elementId 为 -1 THEN 以根节点的 accessibilityId 作为查询起点 | 边界 |
| AC-1.3 | WHEN mode 不含 `PREFETCH_RECURSIVE_CHILDREN(_REDUCED)` 位 THEN 仅返回节点自身，不下钻子树 | 边界 |
| AC-1.4 | WHEN 节点 `IsInternal()` 为真 THEN 该节点不参与查询结果（遍历跳过） | 边界 |
| AC-1.5 | WHEN 节点 `IsActive()` 为假 THEN 该节点不参与查询结果 | 边界 |
| AC-1.6 | WHEN 查询请求到达 THEN 在 UI 线程执行搜索，结果在 BACKGROUND 线程回传 callback | 正常 |

### US-2: 应用自绘组件经 NDK Provider 按需提供元素信息

作为 Native 应用自绘组件（XComponent/Custom）
我想要通过 NDK Provider 回调自行填充并按需提供元素信息
以便读屏能朗读自绘内容

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 应用自绘组件注册的 7 个 Provider 回调全部非空 THEN 注册成功 | 正常 |
| AC-2.2 | WHEN 注册回调表中任一回调为 null THEN 注册失败并返回错误码 | 异常 |
| AC-2.3 | WHEN 应用自绘组件在回调内 `OH_ArkUI_AddAndGetAccessibilityElementInfo` 后填充各字段 THEN 该 ElementInfo 经加锁拷贝回传 SA | 正常 |
| AC-2.4 | WHEN `OH_ArkUI_NativeModule_GetNativeAccessibilityProvider` 的节点类型非 `ARKUI_NODE_CUSTOM` THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID` | 异常 |
| AC-2.5 | WHEN 同时注册 WithInstance(@since15) 与普通(@since13) 回调 THEN WithInstance 优先被调用 | 正常 |

### US-3: 元素信息字段来源与优先级

作为读屏消费者
我想要组件提供的 role/文本/状态有稳定的取值优先级
以便获得可预测的朗读结果

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 节点设置了 customProperty.role 或 accessibilityRole THEN componentType 取该 role 值 | 正常 |
| AC-3.2 | WHEN 节点未设置任何 role THEN componentType 回退为 `node->GetTag()` | 边界 |
| AC-3.3 | WHEN 节点设置了 accessibilityText THEN 朗读文本优先取该值 | 正常 |
| AC-3.4 | WHEN 节点为 group 且 textPreferred THEN 文本走 `GetGroupPreferAccessibilityText` 聚合 | 正常 |
| AC-3.5 | WHEN accessibilityLevel 为 `no-hide-descendants` THEN 该节点整棵子树的文本聚合与查询结果均被跳过 | 边界 |
| AC-3.6 | WHEN 设置 userChecked/userRange/userTextValue（C API/Modifier 注入）THEN 优先于组件自身 getter 取值 | 正常 |

### US-4: 元素坐标基准

作为读屏消费者
我想要元素坐标是屏幕绝对坐标
以便准确定位与触达

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 查询可见节点坐标 THEN 返回屏幕绝对坐标（含窗口偏移、祖先 transform 累加、scale/rotate 后的轴对齐外包矩形） | 正常 |
| AC-4.2 | WHEN 节点不可见 THEN 不为其设置 Rect | 边界 |
| AC-4.3 | WHEN 窗口存在旋转 THEN Rect 取旋转后的外包矩形（min/max 修正移序） | 正常 |

### US-5: 动作集提供

作为读屏消费者
我想要元素提供其支持的动作集合
以便提供可执行的交互操作

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 节点 Enabled 且满足 clickable/longClickable/focusable THEN 返回对应的 CLICK/LONG_CLICK/FOCUS 动作 | 正常 |
| AC-5.2 | WHEN 节点 disabled（非 Enabled）THEN 其动作集为空 | 边界 |
| AC-5.3 | WHEN 组件通过 `SetSpecificSupportAction` 声明特异性动作（如 Slider 的滚动）THEN 该动作出现在返回的动作集合中 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1, R-3 | TASK-1 | 单测（SearchElementInfoByAccessibilityIdNG） | js_accessibility_manager.cpp:7040 |
| AC-1.2 | R-2 | TASK-1 | 单测 | js_accessibility_manager.cpp:7058 |
| AC-1.3 | R-3 | TASK-1 | 单测（mode 位判定） | js_accessibility_manager.cpp:2476 |
| AC-1.4 | R-4 | TASK-1 | 单测 | js_accessibility_manager.cpp:1006 |
| AC-1.5 | R-4 | TASK-1 | 单测 | js_accessibility_manager.cpp:999 |
| AC-1.6 | R-1 | TASK-1 | 单测（线程切换） | js_accessibility_manager.cpp:6231, 10143 |
| AC-2.1 | R-5 | TASK-1 | 单测 | native_interface_accessibility_provider.cpp:25-69 |
| AC-2.2 | R-6 | TASK-1 | 单测 | native_interface_accessibility_provider.cpp:123 |
| AC-2.3 | R-7 | TASK-1 | 单测 | native_interface_accessibility_impl.cpp:92 |
| AC-2.4 | R-8 | TASK-1 | 单测 | native_interface_accessibility.cpp:807 |
| AC-2.5 | R-5 | TASK-1 | 单测 | native_interface_accessibility_provider.cpp:159 |
| AC-3.1 | R-9 | TASK-1 | 单测 | js_accessibility_manager.cpp:1568 |
| AC-3.2 | R-9 | TASK-1 | 单测 | js_accessibility_manager.cpp:2095 |
| AC-3.3 | R-10 | TASK-1 | 单测 | accessibility_property_utils.cpp:147 |
| AC-3.4 | R-10 | TASK-1 | 单测 | accessibility_property.cpp:450 |
| AC-3.5 | R-11 | TASK-1 | 单测 | accessibility_property.cpp:918 |
| AC-3.6 | R-12 | TASK-1 | 单测 | js_accessibility_manager.cpp:1642 |
| AC-4.1 | R-13 | TASK-1 | 单测 | js_accessibility_manager.cpp:2011, 1939 |
| AC-4.2 | R-13 | TASK-1 | 单测 | js_accessibility_manager.cpp:2022 |
| AC-4.3 | R-13 | TASK-1 | 单测 | js_accessibility_manager.cpp:2026 |
| AC-5.1 | R-14 | TASK-1 | 单测 | js_accessibility_manager.cpp:1354, 1719 |
| AC-5.2 | R-14 | TASK-1 | 单测 | js_accessibility_manager.cpp:1719 |
| AC-5.3 | R-14 | TASK-1 | 单测 | accessibility_property.cpp:216 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | SA 发起 elementId 查询请求 | UI 线程定位节点并组装 ElementInfo，BACKGROUND 线程回 callback | requestId 唯一标识本次请求 | AC-1.1, AC-1.6 |
| R-2 | 边界 | elementId == -1 | 以根节点 accessibilityId 作为查询起点 | 仅合法窗口有效 | AC-1.2 |
| R-3 | 边界 | mode 取值不含 `PREFETCH_RECURSIVE_CHILDREN(_REDUCED)` | 仅返回节点自身，不递归子树 | REDUCED 位表示 reduce 模式 | AC-1.1, AC-1.3 |
| R-4 | 边界 | 节点 `IsInternal()==true` 或 `IsActive()==false` | 节点不参与查询结果，遍历跳过 | 引擎内部辅助节点永不返回 | AC-1.4, AC-1.5 |
| R-5 | 行为 | 应用自绘组件注册 Provider 回调表 | 7 个回调全非空则注册成功；WithInstance(@since15) 优先于普通(@since13) | WithInstance 每回调首参增 instanceId | AC-2.1, AC-2.5 |
| R-6 | 异常 | 注册回调表中任一回调为 null | 注册失败返回错误码（BAD_PARAMETER），触发 registerCallback_(false) | @since13 不短路全检；@since15 短路 | AC-2.2 |
| R-7 | 行为 | 应用自绘组件在回调内 AddAndGet 后填充字段 | ElementInfo 经 `std::mutex` 加锁拷贝（`std::list` 节点稳定）回传 SA | 回调内连续 add+填充前一指针有效 | AC-2.3 |
| R-8 | 异常 | `GetNativeAccessibilityProvider` 节点类型非 `ARKUI_NODE_CUSTOM` | 返回 `ARKUI_ERROR_CODE_PARAM_INVALID` | 错误码命名空间为 ARKUI_ERROR_CODE_* | AC-2.4 |
| R-9 | 行为 | 组装 componentType | 优先级：customProperty.role > accessibilityRole > node tag | tag 来自 `node->GetTag()` | AC-3.1, AC-3.2 |
| R-10 | 行为 | 组装朗读文本 | 优先级：userTextValue > group 文本（group+textPreferred 走 prefer 聚合，逗号分隔）> accessibilityText > GetText | 无 user 值且非 group 时取 accessibilityText | AC-3.3, AC-3.4 |
| R-11 | 边界 | accessibilityLevel == `no-hide-descendants` | 整棵子树不参与查询结果（文本聚合与可见性均跳过） | 非法值归一为 AUTO | AC-3.5 |
| R-12 | 行为 | 存在 user 系列 C API/Modifier 注入值（userChecked/userRange/userTextValue） | 优先于组件自身 getter（IsChecked/GetAccessibilityValue/GetCurrentIndex 等） | customProperty 优先级最高 | AC-3.6 |
| R-13 | 行为 | 组装 Rect（RectInScreen） | 屏幕绝对坐标：祖先 transform 矩阵累加（遇窗口边界停止）+ scale/rotate 后取 AABB + 窗口偏移 | 不可见节点不设置 Rect；旋转移序取 min/max | AC-4.1, AC-4.2, AC-4.3 |
| R-14 | 行为 | 组装动作集（仅 Enabled 节点） | focusable/clickable/longClickable 推导 FOCUS/CLICK/LONG_CLICK；组件 `SetSpecificSupportAction` 补特异性动作；user 自定义追加 | disabled 节点动作集为空 | AC-5.1, AC-5.2, AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.x（SA 查询链路） | 单元测试：`test/unittest/core/accessibility/js_accessibility_manager_*.cpp` | 查询返回范围、mode 预取、节点过滤、线程切换 |
| VM-2 | AC-2.x（NDK Provider） | 单元测试：`test/unittest/core/accessibility/` 下 Provider 相关用例 | 回调注册校验、WithInstance 优先、Custom 节点约束 |
| VM-3 | AC-3.x（字段优先级） | 单元测试：`accessibility_property` 与 element_info_osal 用例 | role/文本/状态/user 覆盖优先级 |
| VM-4 | AC-4.x（坐标） | 单元测试：含 transform/scale/rotate 的坐标用例 | 屏幕坐标正确性、不可见不设 Rect |
| VM-5 | AC-5.x（动作集） | 单元测试：`GetSupportAction` / `UpdateSupportAction` 用例 | 动作推导、disabled 空集、组件特异性动作 |
| VM-6 | 规则 R-4/R-11（过滤） | 单元测试 + HoverTest 集成 | level 四值语义、internal/active 过滤 |

## API 变更分析

> 补录，API 均为既有接口；本节列其契约归属，无新增/变更。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `OH_ArkUI_AccessibilityProviderRegisterCallback` (@since13) | Public | provider, callbacks | int32_t | ARKUI_ACCESSIBILITY_NATIVE_RESULT_* | 注册 7 回调表 | AC-2.1, AC-2.2 |
| `OH_ArkUI_AccessibilityProviderRegisterCallbackWithInstance` (@since15) | Public | instanceId, provider, callbacks | int32_t | 同上 | 注册带实例回调表 | AC-2.5 |
| `OH_ArkUI_AddAndGetAccessibilityElementInfo` (@since13) | Public | elementList | ElementInfo* | — | 追加并返回空 ElementInfo | AC-2.3 |
| `OH_ArkUI_NativeModule_GetNativeAccessibilityProvider` (@since23) | Public | node, provider* | int32_t | ARKUI_ERROR_CODE_* | 取 Provider（仅 Custom） | AC-2.4 |
| `OH_ArkUI_AccessibilityElementInfoSetComponentIdentifier` (@since24) | Public | elementInfo, id | int32_t | ARKUI_ACCESSIBILITY_NATIVE_RESULT_* | 设置组件标识符（>1024 截断） | AC-3.x |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

> 注：`interface_sdk-js` 仓未在当前工作区检出，上表 NDK 头以 `interfaces/native/native_interface_accessibility.h` 为准；应用侧 SDK 声明（.d.ts）未逐一核验，标注为待 SDK 核验。

## 接口规格

### 接口定义

**OH_ArkUI_AccessibilityProviderRegisterCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_AccessibilityProviderRegisterCallback(ArkUI_AccessibilityProvider* provider, ArkUI_AccessibilityProviderCallbacks* callbacks)` |
| 返回值 | `int32_t` — 0 成功，非 0 失败 |
| 开放范围 | Public (NDK, @since13) |
| 错误码 | ARKUI_ACCESSIBILITY_NATIVE_RESULT_* |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| provider | ArkUI_AccessibilityProvider* | 是 | — | nullptr 返回 BAD_PARAMETER |
| callbacks | ArkUI_AccessibilityProviderCallbacks* | 是 | — | 7 个回调字段任一为 null 则注册失败 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 7 回调全非空 | 注册成功，返回 0 | AC-2.1 |
| 2 | 任一回调为 null | 注册失败返回错误码，触发 registerCallback_(false) | AC-2.2 |

> L1 标准复杂度：其余接口（WithInstance/AddAndGet/GetNativeAccessibilityProvider/SetComponentIdentifier）行为同「API 变更分析」与上文规则，此处不重复展开。

## 兼容性声明

- **已有 API 行为变更:** 否（补录既有实现）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 13（NDK Provider 基线）
- **API 版本号策略:** 保留既有 @since 13/15/23/24 标注；本特性不引入新 since

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 跨进程边界隔离 | 应用自绘组件/扩展组件经 NDK Provider 与 SessionAdapter 隔离，不直接访问 FrameNode | AC-2.x |
| 无编译期跨仓依赖 | 引擎不对系统无障碍服务仓形成构建依赖，仅运行时回调 | 全部 |
| 双 ElementInfo 类型 | 系统级（OSAL 方向）与 NDK（应用自绘组件方向）为不同类型，字段集不同 | AC-1.x, AC-2.x |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次 elementId 查询响应在 UI 线程一帧内完成（不阻塞渲染） | trace `ArkUIAccessibilitySearchElementInfoById` | js_accessibility_manager.cpp:6231 |
| 可靠性 | Provider 回调未注册时返回 NOT_REGISTERED(-10001)，不崩溃 | 单测 | native_interface_accessibility_provider.cpp |
| 自动化维测 | HiDumper 可 dump 指定窗口/节点 ElementInfo | hidumper | adapter/ohos/osal/accessibility/accessibility_hidumper_osal.* |
| 可测试性 | 各层可独立单测（property/osal/provider） | 单测 | test/unittest/core/accessibility/ |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异（坐标随窗口 transform 计算） | 屏幕坐标含窗口偏移 | 单测 | AC-4.x |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本特性即无障碍本身 | 全部 |
| 大字体 | 否 | 不影响元素信息查询响应 | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 是 | 坐标含窗口偏移；pageId/treeId 编码处理子树 | AC-4.x, R-13 |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | NDK API 按 @since 13/15/23/24 分版本 | AC-2.x |
| 生态兼容 | 是 | 应用自绘组件可经 NDK Provider 接入 | AC-2.x |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 无障碍元素信息查询响应
  作为系统无障碍服务
  我想要查询 ArkUI 组件树元素信息
  以便朗读组件内容、状态与位置

  Scenario Outline: 按 elementId 与预取模式查询
    Given 组件树中存在可见节点 <nodeId>
    When SA 以 elementId=<nodeId> 与 mode=<mode> 查询
    Then 返回结果范围符合 <期望范围>

    Examples:
      | mode | 期望范围 |
      | PREFETCH_RECURSIVE_CHILDREN | 节点及可见子树 |
      | 不含 RECURSIVE 位 | 仅节点自身 |

  Scenario: accessibilityLevel 为 no-hide-descendants
    Given 节点 accessibilityLevel="no-hide-descendants"
    When 对其子树做文本聚合或查询判定
    Then 整棵子树被跳过
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（元素信息查询响应；不含动作执行/焦点/悬停/事件）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "JsAccessibilityManager::SearchElementInfoByAccessibilityIdNG 的节点定位与子树预取实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityProperty getter 契约与组件子类 override 模式"
  - repo: "openharmony/arkui_ace_engine"
    query: "ArkUI_AccessibilityElementInfo 字段集与 NDK Provider 回调分发"
  - repo: "openharmony/arkui_ace_engine"
    query: "accessibility_element_info_osal 的 StateController/ActionController 接管机制"
```

**关键文档：** design.md（同目录）、`docs/kb/architecture/accessibility.md`、`interfaces/native/native_interface_accessibility.h`
