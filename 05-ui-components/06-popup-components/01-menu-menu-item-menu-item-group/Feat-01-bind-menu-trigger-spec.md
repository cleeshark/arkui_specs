# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Menu 绑定与触发机制 (bindMenu/bindContextMenu) |
| 特性编号 | Func-05-06-01-Feat-01 |
| FuncID | 05-06-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 7 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | bindMenu(content, options?) 属性方法 | @since 7，注册在 CommonMethod 上，点击触发 |
| ADDED | bindContextMenu(content, responseType, options?) 属性方法 | @since 8，长按/右键触发 |
| ADDED | bindMenu(isShow, content, options?) 条件显示形式 | @since 11，支持 boolean 控制显示/隐藏 |
| ADDED | bindContextMenu(isShown, content, options?) 条件显示形式 | @since 12 |
| ADDED | bindContextMenuWithResponse(content, options?) 属性方法 | @since 23，builder 内部判断响应类型 |
| ADDED | bindContextMenuByResponseType/bindContextMenuByIsShow 属性方法 | @since 26，支持 Array\<MenuElement\> 内容形式 |
| ADDED | bindContextMenuWithResponse 数组形式重载 | @since 26 |
| MODIFIED | bindContextMenu(content, responseType, options?) 新增数组形式重载 | API 26 原签名保持兼容 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/design.md`
- **KB 路由**: `docs/kb/components/overlay/menu.md`
- **SDK 类型定义**:
  - Dynamic (bindMenu/bindContextMenu/MenuElement/MenuOptions/ContextMenuOptions): `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: bindMenu 绑定与显示

**角色**: 应用开发者
**期望**: 我想要通过 bindMenu 将菜单绑定到任意组件上，点击时显示菜单
**价值**: 以便为组件提供下拉菜单交互能力

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在组件上调用 `bindMenu(content: Array<MenuElement>, options?: MenuOptions)` THEN 点击组件时显示菜单，菜单内容为 MenuElement 数组对应的 MenuItem 列表（`common.d.ts:24214`，`js_popups.cpp` JsBindMenu → `ViewAbstract::BindMenuWithItems()`） | 正常 |
| AC-1.2 | WHEN 在组件上调用 `bindMenu(content: CustomBuilder, options?: MenuOptions)` THEN 点击组件时显示菜单，菜单内容为 CustomBuilder 构建的自定义节点（`common.d.ts:24214`，`ViewAbstract::BindMenuWithCustomNode()`） | 正常 |
| AC-1.3 | WHEN bindMenu content 为空数组或无效 CustomBuilder THEN 菜单不显示或显示空菜单 | 异常 |
| AC-1.4 | WHEN bindMenu 未设置 options.placement THEN 默认使用 Placement.BottomLeft 定位（`common.d.ts:16947`） | 正常 |
| AC-1.5 | WHEN 调用 `bindMenu(isShow: boolean, content, options?)` (API 11+) THEN isShow=true 时显示菜单，isShow=false 时隐藏菜单（`common.d.ts:24229`） | 正常 |
| AC-1.6 | WHEN isShow 在页面构造完成前设置为 true THEN 菜单可能显示异常（位置错误/不显示），SDK 文档已提示此限制（`common.d.ts:24303-24306` 注释） | 边界 |

### US-2: bindContextMenu 绑定与触发

**角色**: 应用开发者
**期望**: 我想要通过 bindContextMenu 将上下文菜单绑定到组件上，长按或右键时显示
**价值**: 以便提供上下文菜单交互

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `bindContextMenu(content: CustomBuilder, responseType: ResponseType.LONG_PRESS, options?)` THEN 长按组件时显示上下文菜单（`common.d.ts:24245`，`js_popups.cpp` JsBindContextMenu → 注册 LongPressGesture） | 正常 |
| AC-2.2 | WHEN 调用 `bindContextMenu(content: CustomBuilder, responseType: ResponseType.RIGHT_CLICK, options?)` THEN 右键点击组件时显示上下文菜单（`common.d.ts:24245`，注册 SetOnMouseId 检测右键释放） | 正常 |
| AC-2.3 | WHEN responseType 为 LONG_PRESS 且使用鼠标设备 THEN 长按不支持（SDK 注释明确限制，`common.d.ts:24237`） | 边界 |
| AC-2.4 | WHEN 调用 `bindContextMenu(isShown: boolean, content: CustomBuilder, options?)` (API 12+) THEN isShown=true 显示菜单，isShown=false 隐藏菜单（`common.d.ts:24318`） | 正常 |
| AC-2.5 | WHEN bindContextMenu 未设置 options.placement THEN responseType 形式默认在点击位置显示（`common.d.ts:16949`），isShown 形式默认 Placement.BottomLeft（`common.d.ts:16950`） | 正常 |
| AC-2.6 | WHEN 调用 `bindContextMenuWithResponse(content: CustomBuilderT<ResponseType>, options?)` (API 23+) THEN builder 内部根据 ResponseType 判断响应类型并构建内容（`common.d.ts:24279`） | 正常 |
| AC-2.7 | WHEN 调用 `bindContextMenuByResponseType(content: CustomBuilder \| Array<MenuElement>, responseType, options?)` (API 26+) THEN 支持数组形式内容（`common.d.ts:24262`） | 正常 |
| AC-2.8 | WHEN 调用 `bindContextMenuByIsShow(isShow: boolean, content: CustomBuilder \| Array<MenuElement>, options?)` (API 26+) THEN 支持数组形式内容 + 条件显示（`common.d.ts:24340`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1, R-2 | TASK-MENU-01 | UT + 手工 | `test/unittest/core/pattern/menu/` |
| AC-1.2 | R-1, R-2 | TASK-MENU-01 | UT + 手工 | `test/unittest/core/pattern/menu/` |
| AC-1.3 | R-8 | TASK-MENU-01 | UT | — |
| AC-1.4 | R-3 | TASK-MENU-01 | UT | `menu_layout_algorithm.cpp` PLACEMENT_STATES |
| AC-1.5 | R-2 | TASK-MENU-01 | UT + 手工 | `common.d.ts:24229` |
| AC-1.6 | R-9 | TASK-MENU-01 | 手工 | SDK 文档注释 |
| AC-2.1 | R-4 | TASK-MENU-01 | UT + 手工 | `js_popups.cpp` JsBindContextMenu |
| AC-2.2 | R-4 | TASK-MENU-01 | UT + 手工 | `js_popups.cpp` JsBindContextMenu |
| AC-2.3 | R-10 | TASK-MENU-01 | 手工 | SDK 文档注释 |
| AC-2.4 | R-5 | TASK-MENU-01 | UT + 手工 | `common.d.ts:24318` |
| AC-2.5 | R-3 | TASK-MENU-01 | UT | `common.d.ts:16949-16950` |
| AC-2.6 | R-6 | TASK-MENU-01 | 手工 | `common.d.ts:24279` |
| AC-2.7 | R-7 | TASK-MENU-01 | 手工 | `common.d.ts:24262` |
| AC-2.8 | R-7 | TASK-MENU-01 | 手工 | `common.d.ts:24340` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 bindMenu(content, options?) content 为 Array\<MenuElement\> | 点击触发，显示 MenuItem 列表 | content 非空 | AC-1.1 |
| R-2 | 行为 | 调用 bindMenu(isShow, content, options?) (API 11+) | isShow=true 显示，isShow=false 隐藏 | 页面构造完成后调用 | AC-1.2, AC-1.5 |
| R-3 | 行为 | bindMenu/bindContextMenu 未设置 placement | bindMenu 默认 BottomLeft，bindContextMenu(responseType) 默认点击位置，bindContextMenu(isShown) 默认 BottomLeft | undefined/null/空使用默认值 | AC-1.4, AC-2.5 |
| R-4 | 行为 | 调用 bindContextMenu(content, responseType, options?) | 按 responseType 触发：LONG_PRESS 长按、RIGHT_CLICK 右键 | 鼠标设备不支持 LONG_PRESS | AC-2.1, AC-2.2 |
| R-5 | 行为 | 调用 bindContextMenu(isShown, content, options?) (API 12+) | isShown=true 显示，isShown=false 隐藏 | 页面构造完成后调用 | AC-2.4 |
| R-6 | 行为 | 调用 bindContextMenuWithResponse(content, options?) (API 23+) | builder 内部根据 ResponseType 判断响应类型 | content=undefined 表示解绑 | AC-2.6 |
| R-7 | 行为 | 调用 bindContextMenuByResponseType/bindContextMenuByIsShow (API 26+) | 支持 CustomBuilder 或 Array\<MenuElement\> 内容形式 | — | AC-2.7, AC-2.8 |
| R-8 | 异常 | bindMenu content 为空数组或无效 CustomBuilder | 菜单不显示或显示空菜单 | — | AC-1.3 |
| R-9 | 边界 | isShow/isShown 在页面构造前设置为 true | 菜单可能显示异常（位置错误/不显示） | SDK 文档已提示 | AC-1.6 |
| R-10 | 边界 | bindContextMenu responseType=LONG_PRESS 且鼠标设备 | 长按不支持 | SDK 注释明确限制 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.6 | UT + 手工 | bindMenu 两种形式（基础/条件）的触发和显示 |
| VM-2 | AC-2.1 ~ AC-2.8 | UT + 手工 | bindContextMenu 全形态（responseType/isShown/withResponse/byResponseType/byIsShow）触发 |

## API 变更分析

> 涉及 API 变更时必填。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| bindMenu(content, options?) | Public | content: Array\<MenuElement\> \| CustomBuilder, options?: MenuOptions | T | 无 | 点击触发显示菜单 | AC-1.1, AC-1.2 |
| bindMenu(isShow, content, options?) | Public | isShow: boolean, content: Array\<MenuElement\> \| CustomBuilder, options?: MenuOptions | T | 无 | 条件显示控制菜单 | AC-1.5 |
| bindContextMenu(content, responseType, options?) | Public | content: CustomBuilder, responseType: ResponseType, options?: ContextMenuOptions | T | 无 | 长按/右键触发上下文菜单 | AC-2.1, AC-2.2 |
| bindContextMenu(isShown, content, options?) | Public | isShown: boolean, content: CustomBuilder, options?: ContextMenuOptions | T | 无 | 条件显示上下文菜单 | AC-2.4 |
| bindContextMenuByResponseType(content, responseType, options?) | Public | content: CustomBuilder \| Array\<MenuElement\>, responseType: ResponseType, options?: ContextMenuOptions | T | 无 | responseType + 数组/CustomBuilder 形式 | AC-2.7 |
| bindContextMenuWithResponse(content, options?) | Public | content: CustomBuilderT\<ResponseType\> \| undefined, options?: ContextMenuOptions | T | 无 | builder 内部判断响应类型 | AC-2.6 |
| bindContextMenuWithResponse(content, options?) [数组重载] | Public | content: CustomBuilderT\<ResponseType\> \| Array\<MenuElement\> \| undefined, options?: ContextMenuOptions | T | 无 | 数组形式 + 响应类型 builder | AC-2.7 |
| bindContextMenuByIsShow(isShow, content, options?) | Public | isShow: boolean, content: CustomBuilder \| Array\<MenuElement\>, options?: ContextMenuOptions | T | 无 | 条件显示 + 数组/CustomBuilder 形式 | AC-2.8 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| bindContextMenu(content: CustomBuilder, responseType, options?) | 变更 | API 26 新增数组形式重载 bindContextMenuByResponseType，原签名保持兼容 | 需要数组内容时使用新 API | AC-2.7 |

> API 签名、d.ts 位置、权限要求等实现细节见 design.md "API 签名、Kit 与权限" 章节。

## 接口规格

### 接口定义

**bindMenu (基础形式)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bindMenu(content: Array<MenuElement> \| CustomBuilder, options?: MenuOptions): T` |
| 返回值 | `T` — 链式调用返回 CommonMethod 子类型 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content | Array\<MenuElement\> \| CustomBuilder | 是 | — | 数组非空或有效 builder；空数组/无效 builder 不显示菜单 |
| options | MenuOptions | 否 | — | placement 默认 BottomLeft；title 仅数组形式有效 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 点击绑定组件，content 为 Array\<MenuElement\> | 显示菜单，内容为 MenuItem 列表 | AC-1.1 |
| 2 | 点击绑定组件，content 为 CustomBuilder | 显示菜单，内容为自定义节点 | AC-1.2 |
| 3 | content 为空数组 | 菜单不显示或显示空菜单 | AC-1.3 |

---

**bindMenu (条件显示形式)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bindMenu(isShow: boolean, content: Array<MenuElement\> \| CustomBuilder, options?: MenuOptions): T` |
| 返回值 | `T` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isShow | boolean | 是 | false | true 显示，false 隐藏；页面构造前设为 true 可能显示异常 |
| content | Array\<MenuElement\> \| CustomBuilder | 是 | — | 同基础形式 |
| options | MenuOptions | 否 | — | 同基础形式 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | isShow 从 false 变为 true | 显示菜单 | AC-1.5 |
| 2 | isShow 从 true 变为 false | 隐藏菜单 | AC-1.5 |
| 3 | 页面构造前 isShow=true | 菜单可能显示异常 | AC-1.6 |

---

**bindContextMenu (responseType 形式)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bindContextMenu(content: CustomBuilder, responseType: ResponseType, options?: ContextMenuOptions): T` |
| 返回值 | `T` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content | CustomBuilder | 是 | — | 有效 builder |
| responseType | ResponseType | 是 | — | LONG_PRESS / RIGHT_CLICK；LONG_PRESS 鼠标设备不支持 |
| options | ContextMenuOptions | 否 | — | placement 默认点击位置；preview 对 RIGHT_CLICK 无效 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | responseType=LONG_PRESS，长按组件 | 显示上下文菜单 | AC-2.1 |
| 2 | responseType=RIGHT_CLICK，右键点击组件 | 显示上下文菜单 | AC-2.2 |
| 3 | responseType=LONG_PRESS + 鼠标设备 | 长按不支持 | AC-2.3 |

---

**bindContextMenu (isShown 形式)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bindContextMenu(isShown: boolean, content: CustomBuilder, options?: ContextMenuOptions): T` |
| 返回值 | `T` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isShown | boolean | 是 | false | true 显示，false 隐藏；页面构造前设为 true 可能显示异常 |
| content | CustomBuilder | 是 | — | 有效 builder |
| options | ContextMenuOptions | 否 | — | placement 默认 BottomLeft |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | isShown 从 false 变为 true | 显示上下文菜单 | AC-2.4 |
| 2 | isShown 从 true 变为 false | 隐藏上下文菜单 | AC-2.4 |
| 3 | 未设置 placement | 默认 Placement.BottomLeft | AC-2.5 |

---

**bindContextMenuWithResponse (API 23+)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bindContextMenuWithResponse(content: CustomBuilderT<ResponseType> \| undefined, options?: ContextMenuOptions): T` |
| 返回值 | `T` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content | CustomBuilderT\<ResponseType\> \| undefined | 是 | — | builder 内部根据 ResponseType 判断响应类型；undefined 表示解绑 |
| options | ContextMenuOptions | 否 | — | 同 bindContextMenu |

---

**bindContextMenuByResponseType (API 26+)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bindContextMenuByResponseType(content: CustomBuilder \| Array<MenuElement>, responseType: ResponseType, options?: ContextMenuOptions): T` |
| 返回值 | `T` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content | CustomBuilder \| Array\<MenuElement\> | 是 | — | 支持 CustomBuilder 或 MenuElement 数组 |
| responseType | ResponseType | 是 | — | LONG_PRESS / RIGHT_CLICK |
| options | ContextMenuOptions | 否 | — | 同 bindContextMenu |

---

**bindContextMenuByIsShow (API 26+)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bindContextMenuByIsShow(isShow: boolean, content: CustomBuilder \| Array<MenuElement>, options?: ContextMenuOptions): T` |
| 返回值 | `T` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isShow | boolean | 是 | false | true 显示，false 隐藏 |
| content | CustomBuilder \| Array\<MenuElement\> | 是 | — | 支持 CustomBuilder 或 MenuElement 数组 |
| options | ContextMenuOptions | 否 | — | 同 bindContextMenu |

## 兼容性声明

- **已有 API 行为变更:** 是，bindContextMenu 新增 API 26 数组形式重载（原签名保持兼容）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（bindMenu）、API 8（bindContextMenu）
- **API 版本号策略:** 各 API 按 @since 标注版本引入，通过 Container::LessThanAPIVersion/GreatOrEqualAPIVersion 条件分支实现兼容

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| MenuWrapperPattern 继承 PopupBasePattern | 全屏容器模式，管理菜单生命周期和点击区域外消失 | AC-2.1 |
| 绑定接口与内容组件分离 | bindMenu/bindContextMenu 在 CommonMethod 上，菜单内容走组件化 Bridge 路径 | AC-1.1, AC-1.2 |
| 调用链自上而下 | SDK → JS Bridge → ViewAbstract → OverlayManager → Bridge → Model → View → Pattern → Layout → Paint | 全部 AC |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 菜单显示响应时间 ≤ 100ms（从触发到 onAppear） | 手工测试 + trace | — |
| 可测试性 | UT 覆盖 bindMenu/bindContextMenu JsBindMenu/JsBindContextMenu 分发链路 | UT | `test/unittest/core/pattern/menu/` |
| 自动化维测 | 支持 DumpLog 状态导出 | hilog | MenuWrapperPattern Dump |

## 多设备适配声明

> bindMenu/bindContextMenu 绑定与触发行为在所有设备类型上一致，无差异。

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | bindMenu/bindContextMenu 触发的菜单支持无障碍操作 | AC-1.1, AC-2.1 |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 是 | bindContextMenu 长按/右键触发的菜单在子窗口中显示 | AC-2.1 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 7~26 多版本兼容，废弃/变更 API 保持可用 | AC-2.7 |
| 生态兼容 | 否 | 无差异 | — |

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
  - repo: "openharmony/arkui_ace_engine"
    query: "bindMenu/bindContextMenu js_popups.cpp ViewAbstractModel 分发链路"
  - repo: "openharmony/arkui_ace_engine"
    query: "bindContextMenuWithResponse/bindContextMenuByResponseType API 26 数组形式重载实现"
```

**关键文档：**
- 设计文档: `specs/05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/design.md`
- KB 路由: `docs/kb/components/overlay/menu.md`
- SDK (bindMenu/bindContextMenu): `interface/sdk-js/api/@internal/component/ets/common.d.ts`
