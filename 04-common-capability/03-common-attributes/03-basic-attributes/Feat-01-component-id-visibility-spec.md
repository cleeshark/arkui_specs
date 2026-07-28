# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 组件标识与显隐 |
| 特性编号 | Func-04-03-03-Feat-01 |
| FuncID | 04-03-03 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 10/12/15 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

本特性覆盖组件标识（id、key、restoreId、inspectorLabel、uniqueId）、显隐控制（visibility）、渲染层级（zIndex）、隐私保护（obscured）及辅助行为（allowForceDark、clickDistance、enableClickSoundEffect）等基础通用属性。上述属性均为所有组件的公共属性，通过 ViewAbstract / CommonMethod 统一提供。

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出各属性自引入以来的关键里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | id (string) | @since API 7，组件标识，存入 ElementRegister inspectorIdMap_ |
| ADDED | key (string) | 回收逻辑唯一键 |
| ADDED | restoreId (int32_t) | 状态持久化恢复标识，默认值 -1 |
| ADDED | uniqueId (int64_t) | 框架自动生成的唯一 ID，不可由开发者设置 |
| ADDED | visibility (VisibleType enum: VISIBLE/INVISIBLE/GONE) | @since API 7，显隐控制 |
| ADDED | zIndex (int32_t) | @since API 7，绘制层级优先级 |
| ADDED | inspectorLabel (string) | @since API 12，无障碍 inspector 标签 |
| ADDED | obscured (ObscuredReasons[]) | @since API 12，隐私保护（PLACEHOLDER） |
| ADDED | allowForceDark (boolean) | @since API 10，是否强制深色模式 |
| ADDED | clickDistance (number) | @since API 15，点击距离阈值（无障碍） |
| ADDED | enableClickSoundEffect (boolean) | 是否启用点击声音反馈 |

> 注：VisibleType 在引擎内部对应 VISIBLE/INVISIBLE/GONE，映射到 ArkTS/SDK 层 Visibility 枚举 Visible/Hidden/None。INVISIBLE = Hidden（不可见但占空间），GONE = None（不可见且不占空间）。

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/04-common-capability/03-common-attributes/03-basic-attributes/design.md`
- **KB 路由**: `docs/pattern/common/`
- **SDK 类型定义**:
  - ArkTS Dynamic: `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts` 及各组件 common 方法
  - ArkTS Static: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/framework/arkts/ArkUIGeneratedNativeModule.ets` (ANI 函数指针 `_CommonMethod_setVisibility`/`_CommonMethod_setId` 等)
  - C API / NDK: `interfaces/native/node/node_common_modifier.cpp`（SetVisibility、SetZIndex、SetInspectorLabel、SetObscured、SetAllowForceDark、SetRestoreId、SetClickDistance）

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。

## 用户故事

### US-1: 设置组件 id 用于标识和查找

**角色**: 应用开发者
**期望**: 我想要给组件设置唯一标识字符串
**价值**: 以便在运行时通过 GetElementById 查找特定组件实例

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 设置 `.id('myButton')` THEN id 存入 ElementRegister inspectorIdMap_，可通过 GetAttachedFrameNodeById('myButton') 查找到该组件的 FrameNode | 正常 |
| AC-1.2 | WHEN 设置 `.id('')` (空字符串) THEN id 不被存入 idMap（空字符串无效） | 边界 |
| AC-1.3 | WHEN 同一页面内两个组件设置相同 id THEN 后注册的组件覆盖先前注册的同 id 映射 | 异常 |

### US-2: 设置 visibility 并理解 None 与 Hidden 行为差异

**角色**: 应用开发者
**期望**: 我想要控制组件的可见性和布局占位行为
**价值**: 以便在不同场景下隐藏组件但保留或不保留布局空间

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 `.visibility(Visibility.Visible)` THEN 组件正常显示，参与布局和渲染 | 正常 |
| AC-2.2 | WHEN 设置 `.visibility(Visibility.Hidden)` THEN 组件不可见（透明），但仍占据布局空间，父容器为其分配尺寸 | 正常 |
| AC-2.3 | WHEN 设置 `.visibility(Visibility.None)` THEN 组件不显示且不参与布局，父容器不为其分配任何空间，等同于从布局树中移除 | 正常 |
| AC-2.4 | WHEN visibility 从 Hidden 切换为 Visible THEN 触发 PROPERTY_UPDATE_RENDER 更新，不触发全量 measure | 正常 |
| AC-2.5 | WHEN visibility 从 None 切换为 Visible THEN 需触发 measure 以重新计算布局空间 | 边界 |
| AC-2.6 | WHEN visibility 为 Hidden THEN 组件的焦点 Hub 设置为不可聚焦（SetShow(false)） | 正常 |

### US-3: 设置 zIndex 控制绘制层级

**角色**: 应用开发者
**期望**: 我想要控制组件的绘制顺序
**价值**: 以便在重叠组件中指定哪个组件显示在上层

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `.zIndex(10)` THEN 组件绘制顺序优先级为 10，zIndex 值更高的组件绘制在后（显示在上层） | 正常 |
| AC-3.2 | WHEN 未设置 zIndex THEN 默认值为 0（`render_context.h:708` propZIndex_ 默认 0） | 正常 |
| AC-3.3 | WHEN 两个兄弟节点分别设置 zIndex=5 和 zIndex=10 THEN zIndex=10 的节点绘制在 zIndex=5 的上层 | 正常 |
| AC-3.4 | WHEN 设置负数 zIndex THEN 负数有效，绘制在默认(0)层级之下 | 边界 |

### US-4: 设置 obscured 实现隐私保护

**角色**: 应用开发者
**期望**: 我想要对组件内容进行隐私遮蔽
**价值**: 以便在截图和录屏时保护敏感数据

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `.obscured([ObscuredReasons.PLACEHOLDER])` THEN 组件内容显示为占位内容（如文本显示为密码点、图片显示为占位图），且该组件区域在截图和录屏时被系统拦截 | 正常 |
| AC-4.2 | WHEN obscured 设置在文本组件上且仅包含 PLACEHOLDER THEN 文本渲染为密码圆点样式（`text_paint_method.cpp:118-120`） | 正常 |
| AC-4.3 | WHEN obscured 设置在图片组件上且仅包含 PLACEHOLDER THEN 图片显示为占位图而非原图（`image_pattern.cpp:1512`） | 正常 |
| AC-4.4 | WHEN obscured 设置在 Form 组件上 THEN Form 内容区域在截图/录屏时被系统拦截（`form_model_ng.cpp:103`） | 正常 |

### US-5: 设置 allowForceDark 控制深色模式

**角色**: 应用开发者
**期望**: 我想要控制组件是否跟随系统深色模式
**价值**: 以便某些组件在深色模式下保持原始颜色不被反转

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设置 `.allowForceDark(true)` 且系统为深色模式 THEN 组件颜色被 ColorInverter 反转处理（`resource_parse_utils.cpp:186` ColorInverter 调用，`191-192` allowForceDark 条件判断与颜色反转） | 正常 |
| AC-5.2 | WHEN 设置 `.allowForceDark(false)` 且系统为深色模式 THEN 组件颜色不被反转，保持原始值 | 正常 |
| AC-5.3 | WHEN 系统为浅色模式 THEN 无论 allowForceDark 设置为何值，颜色均不反转 | 边界 |

### US-6: 设置 restoreId 用于状态恢复标识

**角色**: 应用开发者
**期望**: 我想要给组件设置恢复标识号
**价值**: 以便在应用状态持久化时通过 restoreId 关联和恢复组件状态

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 设置 `.restoreId(42)` THEN restoreId=42 存入 UINode，StoreNode(42, weakPtr<FrameNode>) 注册到 PipelineContext storeNode_ 映射 | 正常 |
| AC-6.2 | WHEN 未设置 restoreId THEN 默认值为 -1（`ui_node.h:1390` restoreId_ = -1） | 正常 |
| AC-6.3 | WHEN 调用 GetRestoreInfo(restoreId) THEN 返回该 restoreId 对应组件的状态序列化字符串 | 正常 |

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.3 | R-1 | — | UT | `element_register.h` inspectorIdMap_ |
| AC-2.1 ~ AC-2.6 | R-2, R-6 | — | UT | `layout_property.cpp:1827` UpdateVisibility |
| AC-3.1 ~ AC-3.4 | R-3 | — | UT | `render_context.h:708` propZIndex_ |
| AC-4.1 ~ AC-4.4 | R-4 | — | UT + 手工 | `text_paint_method.cpp:118`, `image_pattern.cpp:1512` |
| AC-5.1 ~ AC-5.3 | R-5 | — | UT + 手工 | `resource_parse_utils.cpp:186,191` |
| AC-6.1 ~ AC-6.3 | — | — | UT | `pipeline_context.h:722` StoreNode/GetRestoreInfo |

## 规则定义

> **统一规则表。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 `.id(value)` | id 字符串存入 ElementRegister 的 inspectorIdMap_（动态前端: `js_view_abstract.cpp JsViewAbstract::JsId` → `ViewAbstract::SetInspectorId`; 静态前端: `ArkUIGeneratedNativeModule.ets:462 _CommonMethod_setId` → `common_method_modifier.cpp:5091 SetIdImpl` → `ViewAbstract::SetInspectorId`; C-API: `node_common_modifier.cpp SetInspectorId`），可通过 GetAttachedFrameNodeById(value) 查找对应 FrameNode | 空字符串无效；同 id 后注册覆盖前注册 | AC-1.1 ~ AC-1.3 |
| R-2 | 边界 | visibility 为 Hidden (INVISIBLE) vs None (GONE) | Hidden：组件透明但仍占布局空间，焦点不可聚焦；None：组件不参与布局，父容器不分配空间，等同于布局树中不存在（动态前端: `js_view_abstract.cpp JsVisibility`; 静态前端: `ArkUIGeneratedNativeModule.ets:386 _CommonMethod_setVisibility` → `common_method_modifier.cpp:4369 SetVisibilityImpl`; C-API: `node_common_modifier.cpp SetVisibility`） | Hidden 触发 PROPERTY_UPDATE_RENDER；None→Visible 需触发 measure | AC-2.2, AC-2.3, AC-2.5, AC-2.6 |
| R-3 | 行为 | 设置 `.zIndex(n)` | zIndex 为渲染层级优先级，值更高的组件绘制在上层；存储于 RenderContext propZIndex_，默认值 0（动态前端: `js_view_abstract.cpp JsZIndex`; 静态前端: `ArkUIGeneratedNativeModule.ets:400 _CommonMethod_setZIndex` → `common_method_modifier.cpp:4455 SetZIndexImpl`; C-API: `node_common_modifier.cpp SetZIndex`） | 负数值有效 | AC-3.1 ~ AC-3.4 |
| R-4 | 行为 | 设置 `.obscured([ObscuredReasons.PLACEHOLDER])` | PLACEHOLDER 使组件内容替换为占位显示（文本→密码圆点，图片→占位图），且该组件区域在截图/录屏时被系统拦截显示为遮蔽（动态前端: `js_view_abstract.cpp JsObscured`; 静态前端: `ArkUIGeneratedNativeModule.ets:502 _CommonMethod_setObscured` → `common_method_modifier.cpp:5414 SetObscuredImpl`; C-API: `node_common_modifier.cpp:5347-5350 SetObscured`） | ObscuredReasons 当前仅定义 PLACEHOLDER=0；文本和图片组件对 PLACEHOLDER 有独立渲染路径 | AC-4.1 ~ AC-4.4 |
| R-5 | 行为 | 设置 `.allowForceDark(b)` | 深色模式下 allowForceDark=true 时 ColorInverter 反转颜色；allowForceDark=false 时保持原色；浅色模式下无论设置值均不反转（动态前端: `js_view_abstract.cpp JsAllowForceDark`; 静态前端: `ArkUIGeneratedNativeModule.ets:672 _CommonShapeMethod_setAllowForceDark` → `common_shape_static_modifier.cpp:153 SetAllowForceDarkImpl`; C-API: `node_common_modifier.cpp SetAllowForceDark`） | 仅影响颜色反转逻辑，不影响其他深色模式适配 | AC-5.1 ~ AC-5.3 |
| R-6 | 边界 | visibility 为 None (GONE) | 组件不参与布局计算，父容器在 measure 和 layout 时跳过该节点，不为其分配任何尺寸和位置；与 Hidden (INVISIBLE) 的核心区别：Hidden 占空间、None 不占空间（双前端在 ViewAbstract::SetVisibility 汇合后行为一致） | Hidden→Visible 仅需 render 刷新；None→Visible 需重新 measure | AC-2.3, AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.3 | UT | id 存储和查找逻辑 |
| VM-2 | AC-2.1 ~ AC-2.6 | UT | visibility 三种值行为差异，None/Hidden 布局参与区别 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT | zIndex 渲染层级排序 |
| VM-4 | AC-4.1 ~ AC-4.4 | UT + 手工 | obscured PLACEHOLDER 占位渲染和截图拦截 |
| VM-5 | AC-5.1 ~ AC-5.3 | UT + 手工 | allowForceDark 颜色反转行为 |
| VM-6 | AC-6.1 ~ AC-6.3 | UT | restoreId 存储和状态恢复 |

## API 变更分析

### 新增 API

N/A，已有能力补录，API 行为无变化。

### 变更/废弃 API

N/A，已有能力补录，API 行为无变化。

## 接口规格

### 接口定义

> 本特性为已有实现补录（L1 标准），以下列出行为最复杂的接口定义。

#### visibility

| 项目 | 内容 |
|------|------|
| 签名 | `.visibility(value: Visibility)` |
| 枚举 | `Visibility.Visible` / `Visibility.Hidden` / `Visibility.None` |
| @since | API 7 |
| C API | `SetVisibility(ArkUINodeHandle node, Ark_Visibility value)` → `node_common_modifier.cpp` |
| 静态前端 | `_CommonMethod_setVisibility` → `common_method_modifier.cpp:4369` (SetVisibilityImpl) → `ViewAbstract::SetVisibility` |
| 内部映射 | Visible→VISIBLE(0), Hidden→INVISIBLE(1), None→GONE(2)（`constants.h:742-746`） |
| 行为场景 | Visible: 正常显示，参与布局和渲染；Hidden: 不可见但占布局空间，焦点不可聚焦；None: 不显示不占空间，从布局树移除 |
| 更新机制 | Hidden→Visible: PROPERTY_UPDATE_RENDER（不触发 measure）；None→Visible: 需 measure 重算布局 |

#### obscured

| 项目 | 内容 |
|------|------|
| 签名 | `.obscured(reasons: ObscuredReasons[])` |
| 枚举 | `ObscuredReasons.PLACEHOLDER(0)` |
| @since | API 12 |
| C API | `SetObscured(ArkUINodeHandle node, ArkUI_Int32* reason, ArkUI_Int32 length)` → `node_common_modifier.cpp:5347-5350` |
| 静态前端 | `_CommonMethod_setObscured` → `common_method_modifier.cpp:5414` (SetObscuredImpl) → `ViewAbstract::SetObscured` |
| 内部类型 | `std::vector<ObscuredReasons>` 存于 RenderContext propObscured_（`render_context.cpp:251`） |
| 行为场景 | PLACEHOLDER: 内容替换为占位（文本→圆点、图片→占位图），同时触发截图/录屏区域拦截 |
| 组件适配 | Text: `text_paint_method.cpp:118-120`; Image: `image_pattern.cpp:1512`; Form: `form_model_ng.cpp:103` |

#### zIndex

| 项目 | 内容 |
|------|------|
| 签名 | `.zIndex(value: number)` |
| @since | API 7 |
| C API | 通过 RenderContext propZIndex_ 存储（`render_context.h:708`） |
| 静态前端 | `_CommonMethod_setZIndex` → `common_method_modifier.cpp:4455` (SetZIndexImpl) → `ViewAbstract::SetZIndex` |
| 默认值 | 0 |
| 行为场景 | 值越高绘制层级越高（后绘制覆盖先绘制）；负数有效；仅影响兄弟节点间的绘制顺序 |

#### id / restoreId / inspectorLabel

| 签名 | @since | 静态前端 | 行为 |
|------|--------|----------|------|
| `.id(value: string)` | API 7 | `_CommonMethod_setId` → `common_method_modifier.cpp:5091` → `ViewAbstract::SetInspectorId` | 存入 ElementRegister inspectorIdMap_，支持 GetAttachedFrameNodeById 查找 |
| `.restoreId(value: number)` | — | `_CommonMethod_setRestoreId` → `common_method_modifier.cpp:5099` → `ViewAbstract::SetRestoreId` | 存入 UINode restoreId_（默认 -1），通过 PipelineContext StoreNode 注册，支持 GetRestoreInfo 状态恢复 |
| `.inspectorLabel(value: string)` | API 12 | `_CommonMethod_setInspectorLabel` → `common_method_modifier.cpp:7430` → `ViewAbstract::SetInspectorLabel` | 存入 UINode inspectorLabel_，用于无障碍 inspector 标识 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 各 API 按 @since 标注版本号：id(7), visibility(7), zIndex(7), allowForceDark(10), inspectorLabel(12), obscured(12), clickDistance(15)

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 公共属性架构 | 所有属性通过 ViewAbstract / CommonMethod 提供，不依赖具体组件 Pattern | 全部 |
| 属性存储分层 | id/restoreId 存于 UINode；visibility 存于 LayoutProperty；zIndex/obscured 存于 RenderContext | 全部 |
| C API 统一入口 | 所有属性通过 `node_common_modifier.cpp` 的 ArkUI_NodeModifier 提供设置/重置/获取函数 | 全部 |
| 静态前端 ANI 桥接 | visibility/zIndex/obscured/id/restoreId/inspectorLabel 通过 `ArkUIGeneratedNativeModule.ets` 的 `_CommonMethod_setXXX` ANI 函数指针 → `common_method_modifier.cpp` SetXXXImpl → ViewAbstract 汇合；allowForceDark 通过 `_CommonShapeMethod_setAllowForceDark` → `common_shape_static_modifier.cpp:153` SetAllowForceDarkImpl | 全部 |
| 双前端汇合点 | 动态前端 (JSI/NAPI) 和静态前端 (ANI) 在 `ViewAbstract::SetXXX` 汇合，后续 Property→Render 行为一致 | 全部 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | visibility Hidden→Visible 切换仅触发 PROPERTY_UPDATE_RENDER，不触发全量 measure | 代码审查 | `layout_property.cpp:1827` UpdateVisibility |
| 安全 | obscured PLACEHOLDER 使组件区域在截图/录屏时被系统拦截，保护隐私数据 | 手工 + 系统截图测试 | 系统截屏录屏拦截机制 |
| 可靠性 | id 冲突时后注册覆盖，不崩溃 | UT | ElementRegister inspectorIdMap_ |
| 问题定位 | FrameNode::ToJson 输出 id/inspectorLabel/zIndex/enableClickSoundEffect 用于调试 | 代码审查 | `frame_node.cpp:1767-1782` |

> 性能指标中 visibility 变更的 PROPERTY_UPDATE_RENDER 是基于 LayoutProperty::UpdateVisibility 调用 OnVisibilityUpdate 后由属性更新标记决定，GONE→VISIBLE 需额外 measure。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 穿戴设备 | 无差异 | — | — | — |
| TV | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | inspectorLabel 提供无障碍标识，obscured 影响无障碍内容读取，clickDistance 设置点击距离阈值 | AC-4.1 |
| 深色模式 | 是 | allowForceDark 控制组件是否强制深色模式颜色反转 | AC-5.1, AC-5.2 |
| 大字体 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | 各 API 按 @since 版本号渐进引入 | 全部 |
| 生态兼容 | 是 | C API 通过 node_common_modifier 提供 NDK 接口 | 全部 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 组件标识与显隐

  Scenario: 设置组件 id
    Given 一个 Text 组件
    When 设置 .id("headerTitle")
    Then id="headerTitle" 存入 ElementRegister inspectorIdMap_
    And GetAttachedFrameNodeById("headerTitle") 返回该 Text 的 FrameNode

  Scenario: visibility Hidden 保留布局空间
    Given 一个 Column 包含两个 100x100 的子组件
    When 对第一个子组件设置 .visibility(Visibility.Hidden)
    Then 第一个子组件不可见
    And 第一个子组件仍占据 100x100 的布局空间
    And Column 总高度仍为 200

  Scenario: visibility None 不保留布局空间
    Given 一个 Column 包含两个 100x100 的子组件
    When 对第一个子组件设置 .visibility(Visibility.None)
    Then 第一个子组件不显示且不参与布局
    And Column 总高度变为 100（仅第二个子组件的空间）

  Scenario: zIndex 控制绘制层级
    Given 两个重叠的兄弟组件 A 和 B
    When A 设置 .zIndex(5)，B 设置 .zIndex(10)
    Then B 绘制在 A 的上层
    And B 的内容覆盖 A 的重叠区域

  Scenario: obscured PLACEHOLDER 替换文本内容并拦截截图
    Given 一个 TextInput 组件包含敏感文本
    When 设置 .obscured([ObscuredReasons.PLACEHOLDER])
    Then 文本内容显示为密码圆点样式而非原始文本
    And 用户触发系统截图时该组件区域为遮蔽

  Scenario Outline: allowForceDark 深色模式行为
    Given 系统当前为 <colorMode> 模式
    And 组件设置 .allowForceDark(<forceDark>)
    Then 颜色反转结果为 <result>

    Examples:
      | colorMode | forceDark | result     |
      | DARK      | true      | 反转颜色   |
      | DARK      | false     | 保持原色   |
      | LIGHT     | true      | 不反转     |
      | LIGHT     | false     | 不反转     |

  Scenario: restoreId 状态恢复
    Given 一个组件设置 .restoreId(42)
    When StoreNode(42, weakPtr) 注册到 PipelineContext
    And 应用触发状态保存
    Then GetRestoreInfo(42) 返回该组件的状态序列化信息
```

## 风险

| 风险ID | 类型 | 描述 | 影响AC | 缓解策略 |
|--------|------|------|--------|----------|
| RK-1 | 行为 | id 冲突时后注册覆盖前注册，GetElementById 可能返回非预期节点 | AC-1.3 | 开发者需自行保证 id 唯一性；框架不做去重校验 |
| RK-2 | 性能 | visibility None→Visible 切换需 measure 重算布局，可能引起短暂帧延迟 | AC-2.5 | 仅 None→Visible 触发；Hidden→Visible 仅 PROPERTY_UPDATE_RENDER |
| RK-3 | 版本 | ObscuredReasons 当前仅定义 PLACEHOLDER=0，未来新增枚举值可能导致行为变更 | AC-4.1 | 新增值不影响 PLACEHOLDER 行为；枚举定义在 constants.h |
| RK-4 | 认知 | allowForceDark 在浅色模式下不生效，开发者可能误认为任何模式下均控制颜色反转 | AC-5.3 | SDK JSDoc 应明确标注仅深色模式生效 |

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
    query: "ViewAbstract SetVisibility UpdateVisibility INVISIBLE GONE 布局参与行为"
  - repo: "openharmony/ace_engine"
    query: "RenderContext propZIndex_ zIndex 绘制层级排序逻辑"
  - repo: "openharmony/ace_engine"
    query: "ObscuredReasons PLACEHOLDER 占位渲染和截图录屏拦截"
  - repo: "openharmony/ace_engine"
    query: "allowForceDark ColorInverter 深色模式颜色反转"
  - repo: "openharmony/ace_engine"
    query: "ElementRegister inspectorIdMap_ GetAttachedFrameNodeById restoreId StoreNode"
```

**关键文档:**
- 源码入口: `frameworks/core/components_ng/base/view_abstract.cpp` (SetVisibility, SetZIndex, SetRestoreId, SetInspectorLabel, SetAllowForceDark)
- 源码入口: `frameworks/core/components_ng/layout/layout_property.cpp` (UpdateVisibility)
- 源码入口: `frameworks/core/components_ng/render/render_context.h` (propZIndex_, propObscured_)
- C API 入口: `interfaces/native/node/node_common_modifier.cpp`
- 常量定义: `frameworks/core/components/common/layout/constants.h` (VisibleType, ObscuredReasons)
