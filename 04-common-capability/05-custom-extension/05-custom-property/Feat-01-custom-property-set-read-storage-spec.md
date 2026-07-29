# 特性规格

> Func-04-05-05-Feat-01 自定义属性设置读取与双存储：固化 `.customProperty(name, value)` 设置、`FrameNode.getCustomProperty(name)` 读取、FrameNode 双存储（customPropertyMap_ + extraCustomPropertyMap_）+ 懒加载物化、C-API Add/Remove/GetCustomProperty、API 26.0.0 自定义组件支持、transferDynamic 100031 边界的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自定义属性设置读取与双存储 (Custom Property Set/Read & Dual Storage) |
| 特性编号 | Func-04-05-05-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | customProperty/getCustomProperty 动态 @since 12、静态 @since 23；C-API Add/Remove @since 13、Get+handle @since 14；API 26.0.0 起自定义组件支持 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/05-custom-property/design.md` | Baselined |

---

## 用户故事

### US-1: 通过 customProperty 设置自定义属性

**作为** 应用开发者,
**我想要** 通过 `.customProperty(name, value)` 为组件附加任意键值对,
**以便** 存储非框架预定义的自定义数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.customProperty(name, value)` 且 value 为非 undefined Object THEN 经 JsCustomProperty→SetJSCustomProperty 写入 JS Map __elementIdToCustomProperties__，并置 customPropertyMap_ flag "0"（stale）（frame_node.cpp:8371/8426） | 正常 |
| AC-1.2 | WHEN value 为 undefined THEN 触发 __removeCustomProperty__(nodeId, key) 移除该键（ArkComponent.ts:6758 分发） | 异常 |
| AC-1.3 | WHEN 设置成功 THEN 注册 SetRemoveCustomProperties teardown 回调，节点销毁时调 __removeCustomProperties__(nodeId) 清理 JS Map（js_view_abstract.cpp:13117） | 正常 |
| AC-1.4 | WHEN CNode 节点设置 THEN SetJSCustomProperty 不缓存 getCustomProperty_/getCustomPropertyMapFunc_（frame_node.cpp:8375 IsCNode 提前 return） | 边界 |

### US-2: 通过 getCustomProperty 读取自定义属性

**作为** 应用开发者,
**我想要** 通过 `FrameNode.getCustomProperty(name)` 读回自定义属性,
**以便** 在运行时获取先前设置的数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 getCustomProperty(name) THEN 先读 JS Map __getCustomProperty__(nodeId, key)（frame_node.ts:781） | 正常 |
| AC-2.2 | WHEN JS Map miss THEN 回退原生 getCustomPropertyCapiByKey（frame_node.ts:783）→ GetCapiCustomProperty 直读 customPropertyMap_[key][0]（frame_node.cpp:8403） | 正常 |
| AC-2.3 | WHEN 原生读 GetJSCustomProperty 遇 flag "0" THEN 经 getCustomProperty_(key) 回调向 JS Map 重取、缓存、置 flag "1"（懒物化，frame_node.cpp:8393-8397） | 正常 |
| AC-2.4 | WHEN 原生读 GetJSCustomProperty 遇 flag "1" THEN 直接返回缓存 [0]，不经回调（:8390-8391） | 正常 |
| AC-2.5 | WHEN 键不存在 THEN getCustomProperty 返回 undefined（FrameNode.d.ts:991） | 异常 |
| AC-2.6 | WHEN FrameNode 由 transferDynamic 创建 THEN getCustomProperty 抛 BusinessError 100031（trans_frame_node.ts:30） | 异常 |

### US-3: C-API 读写自定义属性

**作为** NDK 开发者,
**我想要** 通过 C-API 添加/移除/读取自定义属性,
**以便** 在 native 侧管理自定义属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 OH_ArkUI_NodeUtils_AddCustomProperty(node, name, value) THEN 经 frame_node_modifier AddCustomProperty→ViewAbstract→frameNode->AddCustomProperty 直写 customPropertyMap_[key]={value,"1"}（frame_node.cpp:8413），@since 13 | 正常 |
| AC-3.2 | WHEN 调用 OH_ArkUI_NodeUtils_RemoveCustomProperty(node, name) THEN customPropertyMap_ erase 该键（frame_node.cpp:8418），@since 13 | 正常 |
| AC-3.3 | WHEN 调用 OH_ArkUI_NodeUtils_GetCustomProperty(node, name, handle) THEN 先 GetCapiCustomProperty 后 GetJSCustomProperty，包装 ArkUI_CustomProperty{value}，@since 14 | 正常 |
| AC-3.4 | WHEN 参数无效（node/name null）THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID（native_node.h:13767） | 异常 |
| AC-3.5 | WHEN 读到的 handle THEN 调用方须用 OH_ArkUI_CustomProperty_Destroy 释放（native_type.h:3515，@since 14）；OH_ArkUI_CustomProperty_GetStringValue 取值（:3524） | 正常 |

### US-4: API 26.0.0 自定义组件支持

**作为** 应用开发者,
**我想要** 了解 API 26.0.0 起自定义组件支持自定义属性,
**以便** 在自定义组件上使用 customProperty。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN API ≥ 26.0.0 THEN 自定义组件（@Component）支持设置与读取自定义属性（动态 common.d.ts:19567-19571 文档） | 正常 |
| AC-4.2 | WHEN API < 26.0.0 THEN SDK 文档声明自定义组件不支持 customProperty（common.d.ts:19567-19571），但 JsCustomProperty（js_view_abstract.cpp:13137）**无运行时 API 版本检查或组件类型检查**——实际可设置（无运行时强制，文档声明与实现不一致） | 边界 |
| AC-4.3 | WHEN 静态范式 THEN common.static.d.ets:11482 仍注明 "does not work for custom components"（文档未同步至 26.0.0 变更） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | 单测 | `frame_node.cpp:8371/8426`, `ArkComponent.ts:6758` |
| AC-2.1~2.6 | R-5~R-10 | 已有实现 | 单测 | `frame_node.ts:770`, `frame_node.cpp:8386-8411` |
| AC-3.1~3.5 | R-11~R-15 | 已有实现 | 单测/XTS | `native_node.h:13745-13767`, `node_utils.cpp:244-268` |
| AC-4.1~4.3 | R-16~R-18 | 已有实现 | XTS/契约 | `common.d.ts:19567-19571`, `common.static.d.ets:11482` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | customProperty(name, value) 且 value 非 undefined | 写 JS Map + 置 customPropertyMap_ flag "0"（stale） | 经 SetJSCustomProperty | AC-1.1 |
| R-2 | 异常 | value === undefined | 触发 __removeCustomProperty__ 移除该键 | Optional<Object> | AC-1.2 |
| R-3 | 行为 | 设置成功 | 注册 teardown 回调，节点销毁清理 JS Map | SetRemoveCustomProperties | AC-1.3 |
| R-4 | 边界 | CNode 节点设置 | 不缓存 getCustomProperty_/getCustomPropertyMapFunc_ | IsCNode 提前 return | AC-1.4 |
| R-5 | 行为 | getCustomProperty(name) | 先读 JS Map | __getCustomProperty__ | AC-2.1 |
| R-6 | 行为 | JS Map miss | 回退原生 GetCapiCustomProperty 直读 | getCustomPropertyCapiByKey | AC-2.2 |
| R-7 | 行为 | GetJSCustomProperty 遇 flag "0" | 经 getCustomProperty_ 回调重取、缓存、置 "1" | 懒物化 | AC-2.3 |
| R-8 | 行为 | GetJSCustomProperty 遇 flag "1" | 直接返回缓存 [0] | 不经回调 | AC-2.4 |
| R-9 | 异常 | 键不存在 | 返回 undefined | — | AC-2.5 |
| R-10 | 异常 | transferDynamic FrameNode | 抛 BusinessError 100031 | 不可读 | AC-2.6 |
| R-11 | 行为 | OH_ArkUI_NodeUtils_AddCustomProperty | 直写 customPropertyMap_ {value,"1"} | @since 13 | AC-3.1 |
| R-12 | 行为 | OH_ArkUI_NodeUtils_RemoveCustomProperty | erase 该键 | @since 13 | AC-3.2 |
| R-13 | 行为 | OH_ArkUI_NodeUtils_GetCustomProperty | 先 Capi 后 JS，包装 handle | @since 14 | AC-3.3 |
| R-14 | 异常 | node/name null | 返回 ARKUI_ERROR_CODE_PARAM_INVALID | — | AC-3.4 |
| R-15 | 恢复 | handle 使用后 | 调用方用 OH_ArkUI_CustomProperty_Destroy 释放 | @since 14 | AC-3.5 |
| R-16 | 行为 | API ≥ 26.0.0 + 自定义组件 | 支持设置与读取 | 动态文档 | AC-4.1 |
| R-17 | 边界 | API < 26.0.0 + 自定义组件 | SDK 文档声明不支持，但 JsCustomProperty 无运行时 API 门控或组件类型检查——实际可设置 | 文档声明，非运行时强制 | AC-4.2 |
| R-18 | 边界 | 静态范式 | common.static.d.ets 仍注明不支持自定义组件 | 文档未同步 | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~1.4 | 单测 | 设置链与 JS Map/stale flag |
| VM-2 | R-5~R-10, AC-2.1~2.6 | 单测 | 读取链与懒物化、transferDynamic 边界 |
| VM-3 | R-11~R-15, AC-3.1~3.5 | 单测/XTS | C-API 读写与 handle 生命周期 |
| VM-4 | R-16~R-18, AC-4.1~4.3 | XTS/契约 | API 26 自定义组件支持 |
| VM-5 | 全量 | XTS/集成 | 端到端设置读取一致 |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `customProperty(name: string, value: Optional<Object>): T` (动态 @since 12) / `default customProperty(name: string, value: CustomProperty): this` (静态 @since 23) | Public | name: string, value: Object\|undefined | T/this | 无 | 设置自定义属性；undefined 移除 | AC-1.1, AC-1.2 |
| `getCustomProperty(name: string): Object \| undefined` (动态 @since 12) / `getCustomProperty(name: string): CustomProperty` (静态 @since 23) | Public | name: string | Object\|undefined / CustomProperty | 无 | 读取自定义属性 | AC-2.1~2.6 |
| `OH_ArkUI_NodeUtils_AddCustomProperty(node, name, value)` (C-API @since 13) | Public | node, name: char*, value: char* | void | 无 | native 设置 | AC-3.1 |
| `OH_ArkUI_NodeUtils_RemoveCustomProperty(node, name)` (C-API @since 13) | Public | node, name: char* | void | 无 | native 移除 | AC-3.2 |
| `OH_ArkUI_NodeUtils_GetCustomProperty(node, name, handle)` (C-API @since 14) | Public | node, name: char*, handle** | int32_t | ARKUI_ERROR_CODE_NO_ERROR/_PARAM_INVALID | native 读取 | AC-3.3, AC-3.4 |
| `OH_ArkUI_CustomProperty_Destroy(handle)` / `GetStringValue(handle)` (C-API @since 14) | Public | handle | void / char* | 无 | handle 释放/取值 | AC-3.5 |

### 变更/废弃 API

无。

> **d.ts 交叉验证：** customProperty `common.d.ts:19582`/`common.static.d.ets:11491`；getCustomProperty `FrameNode.d.ts:991`/`FrameNode.static.d.ets:801`；CustomProperty 类型 `common.static.d.ets:11431`。C-API `native_node.h:13745-13767` + `native_type.h:276/3515/3524`，manifest `libace.ndk.json:1514-1532` 确认 first_introduced。

---

## 接口规格

### 接口定义

**customProperty**

| 属性 | 值 |
|------|-----|
| 函数签名 | `customProperty(name: string, value: Optional<Object>): T`（动态）/ `default customProperty(name: string, value: CustomProperty): this`（静态） |
| 返回值 | `T` / `this` — 链式 |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1, AC-1.2 |

**getCustomProperty**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getCustomProperty(name: string): Object \| undefined`（动态）/ `getCustomProperty(name: string): CustomProperty`（静态） |
| 返回值 | `Object \| undefined` / `CustomProperty` |
| 开放范围 | Public |
| 错误码 | 动态无；transferDynamic 抛 BusinessError 100031 |
| 关联 AC | AC-2.1~2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| name | string | 是 | 无 | 任意非空字符串；键无约束 |
| value | Object \| undefined | 否（动态）/ 是（静态） | undefined | 非 undefined 写入；undefined 移除 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 非 undefined | 写 JS Map + stale flag | AC-1.1 |
| 2 | value undefined | 移除键 | AC-1.2 |
| 3 | 读取 flag "0" | 懒物化重取置 "1" | AC-2.3 |
| 4 | 读取 flag "1" | 返回缓存 | AC-2.4 |
| 5 | transferDynamic | 抛 100031 | AC-2.6 |
| 6 | C-API Add | 直写 {value,"1"} | AC-3.1 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。customProperty/getCustomProperty 自动态 12/静态 23 起稳定。API 26.0.0 自定义组件支持为既有演进。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态 customProperty/getCustomProperty @since 12，静态 @since 23；C-API Add/Remove @since 13、Get+handle @since 14
- **API 版本号策略:** 动态 @since 12、静态 @since 23；C-API Add/Remove @since 13、Get @since 14

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双存储 | JS Map（Object 源）+ customPropertyMap_（字符串化+flag）+ extraCustomPropertyMap_（指针） | AC-1.1, AC-2.3 |
| 懒物化 | flag "0" → 回调重取置 "1" | AC-2.3 |
| C-API 直写 | AddCustomProperty flag 恒 "1" | AC-3.1 |
| transferDynamic 不可读 | 抛 100031 | AC-2.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 懒物化避免每次读取跨 JS | 单测 | frame_node.cpp:8390 |
| 内存 | customPropertyMap_ 随 FrameNode 回收；teardown 清 JS Map | 单测 | frame_node.cpp:8413, js_view_abstract.cpp:13117 |
| 可靠性 | C-API handle 须显式 Destroy 释放 | 单测 | native_type.h:3515 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 自定义属性不影响无障碍语义 | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 26.0.0 自定义组件支持；C-API 13/14 分阶段 | AC-4.1~4.3 |
| 生态兼容 | 是 | @crossplatform；C-API NDK 跨范式 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（customProperty 设置/读取/双存储/C-API/自定义组件支持）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode customPropertyMap_ extraCustomPropertyMap_ SetJSCustomProperty GetJSCustomProperty 懒物化"
  - repo: "openharmony/arkui_ace_engine"
    query: "OH_ArkUI_NodeUtils_AddCustomProperty GetCustomProperty C-API frame_node_modifier"
  - repo: "openharmony/interface/sdk-js"
    query: "customProperty getCustomProperty CustomProperty 类型 @since 版本"
```

**关键文档：** design.md（DESIGN-Func-04-05-05），SDK `common.d.ts:19582`、`FrameNode.d.ts:991`、`common.static.d.ets:11431`
