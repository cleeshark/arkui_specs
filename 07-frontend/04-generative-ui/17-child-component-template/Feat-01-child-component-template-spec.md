# 特性规格

> Func-07-04-17-Feat-01 子组件模板声明与实例化：固化容器组件 `children` 的二态声明（静态 ID 数组 `string[]` 与动态模板对象 `{componentId,path,indexVar?,itemVar?}`）、模板数组数据源绑定、eager（Row/Column/Stack/Custom）与 lazy（List/Grid NodeAdapter）两种展开策略、模板延迟展开重试语义（`pendingTemplateContainers_`）、模板实例 ID 自动生成（`<arrayPath><templateComponentId>:<itemIndex>:<originalId>`）与数据路径重写。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 子组件模板声明与实例化 |
| 特性编号 | Func-07-04-17-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 + 鸿蒙扩展协议 1.0.0 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-17 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/17-child-component-template/design.md` | Baselined |
| 模板解析（C++） | `genui/src/main/cpp/composition/ChildListParser.cpp`、`ChildListDescriptor.h` | — |
| 模板实例化（C++） | `genui/src/main/cpp/composition/TemplateAdapterNode.cpp/.h`、`TemplateInstantiator.cpp` | — |
| eager 展开（C++） | `genui/src/main/cpp/components/Component.cpp/.h` | — |
| lazy 展开（C++） | `genui/src/main/cpp/components/A2UI/list/ListComponent.cpp`、`components/extended/ExtendedListComponent.cpp`、`ExtendedGridComponent.cpp` | — |
| 容器策略（C++） | `genui/src/main/cpp/components/A2UI/row/RowComponent.cpp`、`column/ColumnComponent.cpp`、`extended/ExtendedStackComponent.cpp`、`custom/CustomComponent.cpp` | — |
| 延迟展开（C++） | `genui/src/main/cpp/SurfaceSlot.cpp/.h` | — |
| 使用参考（Docs） | `guides/creating-components-with-templates.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: children 声明解析（静态 vs 模板）

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别 `children` 的静态 ID 数组与动态模板对象两种声明,
**以便** 容器根据声明类型正确创建子组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `children` 为 `string[]`（如 `["a","b",""]`） THEN `ChildListParser::ParseChildren` 返回 `STATIC_IDS`，`staticChildIds` 仅含非空元素（`ChildListParser.cpp:66-75`） | 正常 |
| AC-1.2 | WHEN `children` 为对象且 `componentId` 与 `path` 均非空 THEN 返回 `TEMPLATE_PATH`，`templateComponentId`/`templatePath` 被填写（`ChildListParser.cpp:78-87`） | 正常 |
| AC-1.3 | WHEN `children` 为对象但 `componentId` 或 `path` 为空/缺失 THEN 返回 `INVALID`（`ChildListParser.cpp:88-91`） | 异常 |
| AC-1.4 | WHEN `children` 非数组且非对象（标量/null） THEN 返回 `INVALID`（`ChildListParser.cpp:90-91`） | 异常 |
| AC-1.5 | WHEN 数组含空串元素 THEN 空串被过滤，不进入 `staticChildIds`（`ChildListParser.cpp:70-74`） | 边界 |
| AC-1.6 | WHEN `ChildListDescriptor::IsValid()` 且 type=`TEMPLATE_PATH` THEN 要求 `templateComponentId` 与 `templatePath` 均非空（`ChildListDescriptor.h:49-58`） | 边界 |

### US-2: 模板数据源绑定与循环变量

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `componentId`/`path` 绑定模板与数组数据并自定义循环变量,
**以便** 模板实例按数据项字段取值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 模板对象含合法且互异的 `indexVar`/`itemVar` THEN `resolvedIndexVarName`/`resolvedItemVarName` 设为自定义名且 `useDefault*`=false（`ChildListParser.cpp:50-57`） | 正常 |
| AC-2.2 | WHEN `indexVar` 或 `itemVar` 非法（非 `IsValidLocalVariableName`） THEN 回落默认 `index`/`item` 并打 warn（`ChildListParser.cpp:35-41`） | 异常 |
| AC-2.3 | WHEN `indexVar` 与 `itemVar` 同名 THEN 二者回落默认 `index`/`item` 并打 warn（`ChildListParser.cpp:43-48`） | 边界 |
| AC-2.4 | WHEN 模板 `path` 指向的 DataModel 节点存在但非数组 THEN 发 `SCHEMA_ERROR_CODE_TYPE_MISMATCH` schema warning 并返回 false（`Component.cpp:963-971`） | 异常 |
| AC-2.5 | WHEN 模板描述符（`templateComponentId`）不存在于 descriptor store THEN `ResolveEagerTemplateArray` 返回 false 并打 warn（`Component.cpp:938-943`） | 异常 |

### US-3: eager 模板展开

**作为** 生成式 UI 宿主开发者,
**我想要** Row/Column/Stack/Custom 容器按数组数据立即生成全部模板实例,
**以便** 数据量小的布局容器一次性构建子组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 模板数组 itemCount=N 且模板描述符与数据就绪 THEN `ExpandTemplateChildrenEager` 逐项生成 N 个实例 childIds 且 `allItemsBuilt=true`（`Component.cpp:925-931`） | 正常 |
| AC-3.2 | WHEN 任一项 `BuildEagerTemplateChild` 因描述符缺失失败 THEN `allItemsBuilt=false`（`Component.cpp:857-871,926-930`） | 异常 |
| AC-3.3 | WHEN Row/Column/Stack/Custom 收到 `TEMPLATE_PATH` THEN `ExpandTemplateChildren` 直调 eager（`RowComponent.cpp:149-153`、`ColumnComponent.cpp:150-154`、`ExtendedStackComponent.cpp:98-102`、`CustomComponent.cpp:487-490`） | 正常 |
| AC-3.4 | WHEN 模板路径 `GetNode(templatePath)` 无值 THEN `ReportMissingPath(DEFER_UNTIL_DATA_UPDATE)` 并返回 false（`Component.cpp:950-960`） | 异常 |
| AC-3.5 | WHEN 某索引实例生成成功 THEN `childIds` 追加 `generatedInstanceId`（`Component.cpp:903`） | 正常 |

### US-4: lazy 模板展开（List/Grid）

**作为** 生成式 UI 宿主开发者,
**我想要** List/Grid 通过 NodeAdapter 懒加载模板实例,
**以便** 大列表避免创建离屏节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN List 收到 `TEMPLATE_PATH` 且模板/绝对路径数组就绪 THEN `SetupLazyAdapter` 创建 `ListAdapterNode` 并 `Initialize(templateId,path,itemCount)`（`ListComponent.cpp:184-202`、`TemplateAdapterNode.cpp:437-451`） | 正常 |
| AC-4.2 | WHEN List 模板 `path` 为相对路径（不以 `/` 开头） THEN `ResolveLazyAdapterItemCount` 返回 0，留待运行时解析（`ListComponent.cpp:146-151`） | 边界 |
| AC-4.3 | WHEN List 数据路径缺失 THEN 建空 adapter（itemCount=0）并 `ReportMissingPath`（`ListComponent.cpp:159-170`） | 异常 |
| AC-4.4 | WHEN List 数据路径非数组 THEN 建空 adapter（itemCount=0）（`ListComponent.cpp:172-177`） | 异常 |
| AC-4.5 | WHEN ExtendedGrid `SetupLazyAdapter` 失败 THEN 回退 `EAGER` 模式展开（`ExtendedGridComponent.cpp:653-658`） | 边界 |
| AC-4.6 | WHEN List/ExtendedList `ExpandTemplateChildren` 执行 THEN 恒返回 false（懒加载不挂载静态子项）（`ListComponent.cpp:233`、`ExtendedListComponent.cpp:276`） | 正常 |

### US-5: 模板延迟展开

**作为** 生成式 UI 宿主开发者,
**我想要** 模板描述符或数据暂缺时延迟展开并自动重试,
**以便** 流式渲染分批下发描述符/数据后子项能自动补齐。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 模板未就绪触发 Deferred THEN containerId 插入 `pendingTemplateContainers_`（`SurfaceSlot.cpp:666-671`） | 正常 |
| AC-5.2 | WHEN 模板就绪触发 Resolved THEN 擦除 containerId（`SurfaceSlot.cpp:673-678`） | 正常 |
| AC-5.3 | WHEN `UpdateComponents` 后 `ProcessPendingTemplateContainers` 且模板子树完整 THEN `BuildChildren` 并移出 pending（`SurfaceSlot.cpp:520,680-728`） | 正常 |
| AC-5.4 | WHEN 容器不在 `allComponents_` 或非 `TEMPLATE_PATH` THEN 移出 pending 跳过（`SurfaceSlot.cpp:688-701`） | 边界 |
| AC-5.5 | WHEN 模板描述符仍缺失 THEN 保留 pending 等待下次（`SurfaceSlot.cpp:703-709`） | 边界 |
| AC-5.6 | WHEN 模板子树含缺失引用 id THEN 保留 pending 重插（`SurfaceSlot.cpp:713-726`） | 边界 |
| AC-5.7 | WHEN `Dispose` 执行 THEN `pendingTemplateContainers_` 清空（`SurfaceSlot.cpp:775`） | 正常 |

### US-6: 模板实例 ID 生成与数据路径重写

**作为** 生成式 UI 宿主开发者,
**我想要** 框架自动生成唯一实例 ID 并重写模板内相对路径,
**以便** 多模板/嵌套模板不冲突且正确取到数组项字段。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 生成模板实例 THEN 实例 id 为 `<arrayPath><templateComponentId>:<itemIndex>:<originalId>`（`TemplateAdapterNode.cpp:311`） | 正常 |
| AC-6.2 | WHEN 模板内 `path` 以 `/` 开头 THEN 重写为 `prefix + path`（`prefix=arrayPath/itemIndex`）（`TemplateAdapterNode.cpp:155-156`） | 正常 |
| AC-6.3 | WHEN 模板内 `path` 不以 `/` 开头 THEN 重写为 `prefix + "/" + path`（`TemplateAdapterNode.cpp:156`） | 正常 |
| AC-6.4 | WHEN 模板含嵌套 `children`/`childrenIf`/`childrenElse`/`child` THEN 递归生成子实例 id（`TemplateAdapterNode.cpp:392-406`） | 正常 |
| AC-6.5 | WHEN `CollectReferencedDescriptorIds(rootId)` 调用 THEN 返回模板子树全部引用 id 集合（`TemplateAdapterNode.cpp:293-300`） | 正常 |

### US-7: 数据更新驱动的模板刷新

**作为** 生成式 UI 宿主开发者,
**我想要** `updateDataModel` 命中懒加载适配器路径时自动刷新列表,
**以便** 流式数据更新后列表项数与内容实时变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `updateDataModel` UPDATE 命中某 lazy adapter 的 `dataPath` THEN `RefreshLazyAdapterFromDataModel` 重算 itemCount 并 `UpdateItemCount`+`ReloadAllItems`（`SurfaceSlot.cpp:577`、`A2UIComponent.cpp:395-413`） | 正常 |
| AC-7.2 | WHEN `updateDataModel` REPLACE 整模型（path 空） THEN `RefreshLazyAdapters("", true)` 全量刷新（`SurfaceSlot.cpp:592`） | 正常 |
| AC-7.3 | WHEN changedPath 等于 `/` 或为适配器路径的 `/` 边界前缀 THEN 命中刷新（`SurfaceSlot.cpp:97-107`） | 边界 |
| AC-7.4 | WHEN changedPath 与适配器路径无关 THEN `ShouldRefreshLazyAdapter` 返回 false，不刷新（`SurfaceSlot.cpp:92-108`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2,R-3,R-4 | T-1 | C++ UT：`ChildListParser::ParseChildren` | `ChildListParser.cpp:62-109` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-5,R-6,R-7,R-8 | T-1 | C++ UT：循环变量校验 + 数据源校验 | `ChildListParser.cpp:25-58`、`Component.cpp:934-972` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-9,R-10 | T-1 | C++ UT：`ExpandTemplateChildrenEager` | `Component.cpp:857-932` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 | R-11,R-12,R-13 | T-1 | C++ UT：`SetupLazyAdapter`/`ResolveLazyAdapterItemCount` | `ListComponent.cpp:127-202`、`ExtendedGridComponent.cpp:649-665` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 | R-14 | T-1 | C++ UT：`ProcessPendingTemplateContainers` | `SurfaceSlot.cpp:666-728` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 | R-15,R-16 | T-1 | C++ UT：`RewriteDataPaths`/`BuildTemplateInstanceTreeDescriptors` | `TemplateAdapterNode.cpp:115-408` |
| AC-7.1,AC-7.2,AC-7.3,AC-7.4 | R-17 | T-1 | C++ UT：`RefreshLazyAdapters` | `SurfaceSlot.cpp:92-108,1041-1058`、`A2UIComponent.cpp:381-417` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `children` 为数组 | 识别 `STATIC_IDS`，收集非空子项 id | 空串过滤 | AC-1.1,AC-1.5 |
| R-2 | 行为 | `children` 为对象且 componentId/path 非空 | 识别 `TEMPLATE_PATH` | 二者缺一即非模板 | AC-1.2 |
| R-3 | 异常 | `children` 无法识别（非数组/非对象/字段缺失） | 返回 `INVALID` | `IsValid()` 为 false | AC-1.3,AC-1.4,AC-1.6 |
| R-4 | 边界 | 数组元素为空串 | 过滤空串 | 保持其余顺序 | AC-1.5 |
| R-5 | 行为 | indexVar/itemVar 合法且互异 | 采用自定义循环变量名 | `IsValidLocalVariableName` | AC-2.1 |
| R-6 | 边界 | indexVar/itemVar 非法或同名 | 回落默认 `index`/`item` | 打 warn | AC-2.2,AC-2.3 |
| R-7 | 异常 | 模板 path 指向非数组 | 发 `SCHEMA_ERROR_CODE_TYPE_MISMATCH` warning | 返回 false | AC-2.4 |
| R-8 | 异常 | 模板描述符缺失 | 堆叠延迟（eager 返回 false / lazy 空 adapter） | 后续重试补齐 | AC-2.5,AC-5.5 |
| R-9 | 行为 | eager 容器收到 TEMPLATE_PATH | 遍历数组逐项实例化 | 任一项失败即整体 false | AC-3.1,AC-3.2,AC-3.3,AC-3.5 |
| R-10 | 异常 | 模板数据路径缺失 | `ReportMissingPath(DEFER_UNTIL_DATA_UPDATE)` 返回 false | 非数组同样拒绝 | AC-3.4 |
| R-11 | 行为 | lazy 容器数据就绪 | 创建 adapter 并 `Initialize` | NodeAdapter 事件驱动 | AC-4.1 |
| R-12 | 边界 | lazy 模板 path 为相对路径 | itemCount=0，运行时解析 | 以 `/` 前缀判定 | AC-4.2 |
| R-13 | 异常 | lazy 数据路径缺失/非数组 | 建空 adapter（itemCount=0） | 缺失打 `ReportMissingPath` | AC-4.3,AC-4.4 |
| R-14 | 行为 | 模板 Deferred/Resolved | 插入/擦除 `pendingTemplateContainers_` | Dispose 清空 | AC-5.1,AC-5.2,AC-5.3,AC-5.7 |
| R-15 | 行为 | 生成模板实例 | id=`<arrayPath><templateComponentId>:<itemIndex>:<originalId>` | 递归子树同规则 | AC-6.1 |
| R-16 | 行为 | 重写模板内路径 | 绝对加前缀，相对补 `/` | `prefix=arrayPath/itemIndex` | AC-6.2,AC-6.3 |
| R-17 | 行为 | updateDataModel 命中 adapter 路径 | 刷新 itemCount 并 Reload | `/` 前缀匹配规则 | AC-7.1,AC-7.2,AC-7.3,AC-7.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 children 解析 | C++ UT | 二态识别、空串过滤、INVALID |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 数据源绑定/循环变量 | C++ UT | componentId/path、indexVar/itemVar 校验回落、type mismatch |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 eager 展开 | C++ UT | 全量实例化、失败短路、策略分发 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 lazy 展开 | C++ UT | NodeAdapter 创建、相对路径、空 adapter、Grid 回退 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 延迟展开 | C++ UT | pending 登记/重试/Dispose |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 实例 ID/路径重写 | C++ UT | ID 格式、绝对/相对重写、递归 |
| VM-7 | AC-7.1,AC-7.2,AC-7.3,AC-7.4 数据驱动刷新 | C++ UT | 路径匹配、全量刷新 |

## API 变更分析

> 存量补录，无新增/变更公开 API。本节列出受影响内部接口与协议字段。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `children`（协议字段，`string[]`） | 既有 | 静态子项声明 | 稳定，宿主无迁移 | AC-1.1,AC-1.5 |
| `children`（协议字段，`{componentId,path,indexVar?,itemVar?}`） | 既有 | 动态模板声明 | 稳定，宿主无迁移 | AC-1.2,AC-2.1,AC-2.2,AC-2.3 |
| `ChildListDescriptor`/`ChildListParser`（C++ 内部） | 既有 | 声明解析 | 不对外暴露 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| `TemplateAdapterNode`/`ListAdapterNode`/`GridAdapterNode`（C++ 内部） | 既有 | 懒加载适配器 | 不对外暴露 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5 |

> d.ts 位置：无新增（C++ 内部接口）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ChildListParser::ParseChildren(childrenValue)`（C++ 内部，`ChildListParser.cpp:62`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static ChildListDescriptor ParseChildren(const JsonValue& childrenValue)` |
| 返回值 | `ChildListDescriptor` — `type` 为 `INVALID`/`STATIC_IDS`/`TEMPLATE_PATH` |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（错误经 `INVALID` 表达） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3 |

**`Component::ExpandTemplateChildrenEager(childList, surfaceSlot, childIds)`（C++ 内部，`Component.cpp:907`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool ExpandTemplateChildrenEager(const ChildListDescriptor&, SurfaceSlot&, std::list<std::string>&)` |
| 返回值 | `bool` — 是否所有数组项实例化成功 |
| 开放范围 | 内部 |
| 错误码 | N/A（失败经返回值 false + schema warning） |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

**`TemplateAdapterNode::BuildTemplateInstanceTreeDescriptors(id, context)`（C++ 内部，`TemplateAdapterNode.cpp:373`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static std::string BuildTemplateInstanceTreeDescriptors(std::string& id, const TemplateInstanceBuildContext&)` |
| 返回值 | `std::string` — 生成实例根 id；空串表示失败 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

**`SurfaceSlot::ProcessPendingTemplateContainers()`（C++ 内部，`SurfaceSlot.cpp:680`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ProcessPendingTemplateContainers()` |
| 返回值 | `void` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-5.3,AC-5.4,AC-5.5,AC-5.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| childrenValue | JsonValue | 是 | — | 数组/对象/其他；数组元素需非空串，对象需 componentId+path 非空 |
| templatePath | string | 是（模板对象） | — | 绝对 `/` 开头；嵌套模板可用相对路径 |
| indexVar/itemVar | string | 否 | `index`/`item` | 合法局部变量名且互异，否则回落默认 |
| itemIndex | int32 | 是（实例化） | — | `[0, itemCount)` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | children 为 string[] | STATIC_IDS，过滤空串 | AC-1.1,AC-1.5 |
| 2 | children 为 `{componentId,path}` | TEMPLATE_PATH | AC-1.2 |
| 3 | children 非法 | INVALID | AC-1.3,AC-1.4 |
| 4 | templatePath 非数组 | type mismatch warning + false | AC-2.4 |
| 5 | 模板描述符缺失 | 延迟/空 adapter | AC-2.5,AC-5.5 |
| 6 | eager 数据就绪 | 遍历生成实例 | AC-3.1,AC-3.5 |
| 7 | lazy 路径相对 | itemCount=0 运行时解析 | AC-4.2 |
| 8 | changedPath 命中 adapter | 刷新 itemCount | AC-7.1,AC-7.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9 + 鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 模板对象字段（`componentId`/`path`/`indexVar`/`itemVar`）为扩展协议既有字段；实例 ID 格式 `<arrayPath><templateComponentId>:<itemIndex>:<originalId>` 为框架内部约定，无 `@since` 标注。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| children 二态 | 静态数组与模板对象区分，解析层不决策渲染策略 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| 实例 ID 唯一 | 框架自动生成，DSL 编写者免维护 ID 唯一 | AC-6.1 |
| eager/lazy 分化 | Row/Column/Stack/Custom eager；List/Grid lazy | AC-3.3,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |
| 延迟展开重试 | 描述符/数据未就绪登记 pending 后续重试 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6,AC-5.7 |
| 数据路径前缀规则 | `/` 前缀判定绝对/相对，重写统一 | AC-6.2,AC-6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | lazy 列表仅按需创建可见项，避免离屏节点创建 | ohosTest | `ListComponent.cpp:127-202` |
| 可靠性 | 模板/数据缺失不崩溃，走延迟/空 adapter 降级 | C++ UT | `SurfaceSlot.cpp:680-728` |
| 内存 | 空 adapter itemCount=0，不泄漏未用节点 | C++ UT | `ListComponent.cpp:159-177` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 模板声明/展开设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 模板机制层不涉及，组件层关注 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 模板机制设备无关 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议字段稳定，实例 ID 为内部约定 | 兼容性声明 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 + 扩展协议 1.0.0 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 子组件模板声明与实例化
  作为 生成式 UI 宿主开发者
  我想要 用模板对象从 DataModel 数组生成子组件
  以便 数据驱动地渲染列表/布局容器

  Scenario: 静态 children 解析
    Given DSL 组件描述符 children 为 ["a","b"]
    When 调用 ChildListParser.ParseChildren
    Then 返回 type=STATIC_IDS，staticChildIds=["a","b"]

  Scenario: 模板对象解析
    Given children 为 {"componentId":"row","path":"/items"}
    When 调用 ChildListParser.ParseChildren
    Then 返回 type=TEMPLATE_PATH，templateComponentId="row"，templatePath="/items"

  Scenario Outline: 模板非法解析失败
    Given children 为 <children>
    When 调用 ChildListParser.ParseChildren
    Then 返回 type=INVALID

    Examples:
      | children |
      | "" |
      | {"componentId":"","path":"/items"} |
      | {"componentId":"row","path":""} |
      | {"componentId":"row"} |

  Scenario: List 懒加载适配器
    Given children.componentId="productRow" 且 DataModel["/products"] 为 3 项数组
    When List 组件 BuildChildren 分发到 ExpandTemplateChildren
    Then 创建 ListAdapterNode 且 itemCount=3，函数返回 false（不挂载静态子项）

  Scenario: 模板延迟重试
    Given 模板描述符 productRow 尚未下发
    When List 组件展开失败触发 OnTemplateExpansionDeferred
    Then 组件 id 进入 pendingTemplateContainers_
    And 后续 updateComponents 补发 productRow 后 ProcessPendingTemplateContainers 完成挂载

  Scenario: 实例 ID 与路径重写
    Given 模板 path="/products"，itemIndex=1，模板内 content.path="name"
    When 生成模板实例
    Then 实例 id="/productsproductRow:1:productRow"，content.path 重写为 "/products/1/name"
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（声明解析/绑定/展开策略/延迟/实例 ID/刷新；组件语义归 07-04-02~16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每条规则至少关联一个 AC，每个 AC 至少关联一条规则）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ChildListParser ParseChildren ChildListDescriptor 二态解析 TEMPLATE_PATH STATIC_IDS"
  - repo: "GenerativeUI/A2UIRender"
    query: "Component ExpandTemplateChildrenEager BuildEagerTemplateChild eager 模板展开"
  - repo: "GenerativeUI/A2UIRender"
    query: "TemplateAdapterNode BuildTemplateInstanceTreeDescriptors RewriteDataPaths 实例 ID 生成"
  - repo: "GenerativeUI/A2UIRender"
    query: "ListComponent ExtendedListComponent SetupLazyAdapter NodeAdapter 懒加载"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceSlot OnTemplateExpansionDeferred ProcessPendingTemplateContainers 延迟展开"
```

**关键文档：** `genui/src/main/cpp/composition/ChildListParser.cpp`、`ChildListDescriptor.h`、`TemplateAdapterNode.cpp`、`components/Component.cpp`、`components/A2UI/list/ListComponent.cpp`、`SurfaceSlot.cpp`、`render_docs/guides/creating-components-with-templates.md`