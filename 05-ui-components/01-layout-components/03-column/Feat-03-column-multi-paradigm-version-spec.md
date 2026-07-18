# 特性规格

> Func-05-01-03-Feat-03：固化 Column ArkTS、Native 与 legacy 接口边界和偏差。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Column 多范式接口与版本兼容 |
| 特性编号 | Func-05-01-03-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本规格只定义接口、错误码、版本和兼容风险。布局见 Feat-01/02；PointLight 实现见 Feat-04。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArkTS 多范式契约 | Dynamic、Static、AttributeModifier、ColumnModifier、ExtendableColumn |
| ADDED | Native Node 契约 | 四项属性的 set/reset/get、参数范围和错误码 |
| ADDED | API 7–26 矩阵 | SDK 版本、legacy 差异和已知偏差，不改变实现 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/03-column/design.md` | 已核对 |
| Dynamic/Modifier SDK | `interface/sdk-js/api/@internal/component/ets/column.d.ts`; `interface/sdk-js/api/arkui/ColumnModifier.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/column.static.d.ets`; `interface/sdk-js/api/arkui/ColumnModifier.static.d.ets` | 已核对 |
| Native API | `interfaces/native/native_node.h`; `interfaces/native/node/style_modifier.cpp` | 已核对 |

## 用户故事

### US-1: 在 ArkTS 多范式中配置 Column

**作为** ArkTS 框架开发者  
**我想要** 按目标版本选择 Dynamic、Static 或 Modifier 入口  
**以便** 获得明确的属性应用和缺省语义

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN API 11+ 设置 `attributeModifier` THEN 接受 `AttributeModifier<ColumnAttribute>`；WHEN API 12+ 使用 `ColumnModifier.applyNormalAttribute` THEN 合并实例属性 | 正常 |
| AC-1.2 | WHEN Dynamic modifier 值变为 `undefined/null` THEN 走 reset；`reverse` reset 写 false，而 direct `reverse(undefined)` 写 true | 边界 |
| AC-1.3 | WHEN API 23 Static 调用 `Column(options?, content_?)` THEN 返回 `ColumnAttribute`；属性传 undefined 时 align/justify/reverse 分别写 Center/Start/true | 正常 |
| AC-1.4 | WHEN API 26 调用 `setColumnOptions(undefined)` THEN 保留旧 space；WHEN 传 `{}` THEN reset space | 边界 |
| AC-1.5 | WHEN API 26 使用 style-builder 或 `ExtendableColumn` factory THEN 创建/配置扩展实例；API 23 不开放这些入口 | 正常 |

### US-2: 通过 Native Node 管理 Column

**作为** Native 接入者  
**我想要** 设置、重置并读取 Column 属性  
**以便** 合法值成功、非法值返回明确错误

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN align item 的 size ≥ 1 且 i32 为 0..2 THEN 返回 0 并映射 Start/Center/End；WHEN 缺参或越界 THEN 返回 401 | 正常 |
| AC-2.2 | WHEN justify i32 为 1..8 THEN 当前入口返回 0 并原样写入；WHEN 缺参或超界 THEN 返回 401 | 边界 |
| AC-2.3 | WHEN fresh Column 直接 get justify THEN 返回 AUTO(0)；WHEN reset 后 get THEN 返回 START(1) | 边界 |
| AC-2.4 | WHEN API 23 linear space 恰有一个参数 THEN 负值钳 0 并返回 0；WHEN 参数数不是 1 THEN 返回 401 | 异常 |
| AC-2.5 | WHEN API 23 linear reverse 恰有一个非负整数 THEN 0 写 false、非 0 写 true 并返回 0；WHEN 缺参或负数 THEN 返回 401 | 异常 |

### US-3: 跨版本和 legacy 使用 Column

**作为** 兼容性维护者  
**我想要** 识别 API 7–26 和旧管线边界  
**以便** 避免下放未发布或仅 NG 支持的能力

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 目标为 API 7/8/11/12/18 THEN 仅使用各版本已发布的基础/justify/pointLight/reverse 与 Modifier/Resource options；PointLight 见 Feat-04 | 边界 |
| AC-3.2 | WHEN 目标为 API 23 THEN 可使用 Static 和 Native linear space/reverse，但不使用 API 26 扩展入口 | 边界 |
| AC-3.3 | WHEN legacy pipeline 调用 reverse 或 ResourceObject 构造 THEN 当前空实现不产生 NG 对应行为 | 边界 |
| AC-3.4 | WHEN 工具解析 ColumnModifier 跨平台版本或 Resource space THEN 以 Column SDK 为契约，并保留 12/20 注记冲突及中间类型缺口 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.2 | R-1~R-3 | 已有实现 | Modifier UT | `interface/sdk-js/api/@internal/component/ets/common.d.ts:25178-25201`; `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:118-159` |
| AC-1.3~AC-1.5 | R-4~R-6 | 已有实现 | Static UT | `interface/sdk-js/api/arkui/component/column.static.d.ets:71-232`; `frameworks/core/interfaces/native/implementation/column_modifier.cpp:101-188` |
| AC-2.1~AC-2.3 | R-7~R-9 | 已有实现 | Native UT | `interfaces/native/node/style_modifier.cpp:12589-12695`; `frameworks/core/interfaces/native/node/column_modifier.cpp:25-73` |
| AC-2.4~AC-2.5 | R-10~R-11 | 已有实现 | Native异常UT | `interfaces/native/node/style_modifier.cpp:20466-20573` |
| AC-3.1~AC-3.4 | R-12~R-14 | 已有SDK/实现 | 版本与源码审查 | `interface/sdk-js/api/@internal/component/ets/column.d.ts:110-226`; `frameworks/bridge/declarative_frontend/jsview/models/column_model_impl.h:24-30` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | API 11+ 设置 attributeModifier | 向 `ColumnAttribute` 实例应用状态回调 | Stage/atomic 注记见 `interface/sdk-js/api/@internal/component/ets/common.d.ts:25178-25201` | AC-1.1 |
| R-2 | 行为 | API 12+ ColumnModifier 实现 normal 回调 | `applySetOnChange` 后合并属性 | `frameworks/bridge/declarative_frontend/ark_modifier/src/column_modifier.ts:16-26` | AC-1.1 |
| R-3 | 恢复 | Modifier staged value 为 undefined/null | peer 以 reset=true 执行；reverse reset=false | direct undefined=true；`frameworks/bridge/declarative_frontend/ark_component/src/ArkColumn.ts:147-190`; `frameworks/core/interfaces/native/node/column_modifier.cpp:106-110` | AC-1.2 |
| R-4 | 行为 | API 23 Static 构造或设属性 | 返回 ColumnAttribute；缺省 align/justify/reverse 写 Center/Start/true | `frameworks/core/interfaces/native/implementation/column_modifier.cpp:119-188` | AC-1.3 |
| R-5 | 恢复 | API 26 setColumnOptions 传 undefined 或空对象 | undefined no-op；空对象 reset space | `frameworks/core/interfaces/native/implementation/column_modifier.cpp:101-116`; `frameworks/core/components_ng/pattern/linear_layout/column_model_ng_static.cpp:23-30` | AC-1.4 |
| R-6 | 行为 | API 26 调用 style-builder/ExtendableColumn | style 接收属性实例，factory 返回 T | API23不可用；`interface/sdk-js/api/arkui/component/column.static.d.ets:162-232` | AC-1.5 |
| R-7 | 异常 | Native align 缺参或值不在 0..2 | 返回401；合法值加1写内部枚举 | reset Center/get减1；`interfaces/native/node/style_modifier.cpp:12589-12640` | AC-2.1 |
| R-8 | 边界 | Native justify 值在 1..8 | 返回0并写raw值 | SDK有效值仅1/2/3/6/7/8；`interfaces/native/node/style_modifier.cpp:12643-12662` | AC-2.2 |
| R-9 | 边界 | fresh 或 reset 后 get justify | 分别返回 AUTO(0)/Start(1) | `frameworks/core/components_ng/pattern/linear_layout/column_model_ng.cpp:180-184`; `frameworks/core/interfaces/native/node/column_modifier.cpp:32-37` | AC-2.3 |
| R-10 | 异常 | linear space 参数数不为1 | 返回401；单个负值钳0并返回0 | API23，默认单位vp；`interfaces/native/node/style_modifier.cpp:20466-20519` | AC-2.4 |
| R-11 | 异常 | linear reverse 缺参或值<0 | 返回401；非负值转 ArkUI_Bool 并返回0 | reset=false；`interfaces/native/node/style_modifier.cpp:20522-20573` | AC-2.5 |
| R-12 | 边界 | 按目标 API 裁剪接口 | Dynamic节点7/8/11/12/18，Static 23，扩展26 | `interface/sdk-js/api/@internal/component/ets/column.d.ts:110-226`; `interface/sdk-js/api/arkui/component/column.static.d.ets:71-232` | AC-3.1, AC-3.2 |
| R-13 | 边界 | legacy 调用 Resource 构造或 reverse | 基类 Resource Create 和 legacy SetIsReverse 为空 | `frameworks/core/components_ng/pattern/linear_layout/column_model.h:37-44`; `frameworks/bridge/declarative_frontend/jsview/models/column_model_impl.h:24-30` | AC-3.3 |
| R-14 | 边界 | 解析 Modifier 版本和 Resource 类型 | SDK为契约，12/20及中间类型差异列风险 | `interface/sdk-js/api/arkui/ColumnModifier.d.ts:22-43`; `frameworks/bridge/declarative_frontend/ark_component/src/ArkColumn.ts:50-66,164-173` | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.5, R-1~R-6 | Dynamic/Static UT | apply/reset、options与API26入口 |
| VM-2 | AC-2.1~AC-2.3, R-7~R-9 | Native UT | align/justify的set-reset-get与401 |
| VM-3 | AC-2.4~AC-2.5, R-10~R-11 | Native边界UT | 参数数、负数和布尔转换 |
| VM-4 | AC-3.1~AC-3.4, R-12~R-14 | SDK/legacy审查 | 版本门槛、空实现和元数据偏差 |

## API 变更分析

本次不新增 API；下表是存量接口清单。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Dynamic AttributeModifier/ColumnModifier | Public | modifier/instance | ColumnAttribute/void | N/A | API11/12动态修改 | AC-1.1, AC-1.2 |
| Static Column/ExtendableColumn | Public | options/style/factory/content | ColumnAttribute/T/this | N/A | API23构造、API26扩展 | AC-1.3~AC-1.5 |
| Native四项属性 | Public C API | i32/f32 | set/reset/get | 0/401 | 对齐及API23 space/reverse | AC-2.1~AC-2.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 仅补录存量行为 | 按目标API使用兼容矩阵 | AC-3.1, AC-3.2 |

## 接口规格

### 接口定义

**ArkTS 多范式入口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `attributeModifier(modifier)`; `Column(options?, content_?)`; `Column(style, content_?)`; `ExtendableColumn.$_instantiate(factory, options?, content_?)` |
| 返回值 | `ColumnAttribute/T/this/void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.5 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| modifier | `AttributeModifier<ColumnAttribute>` | 是 | 无 | Dynamic Stage only |
| options/content_ | ColumnOptions(V2)/CustomBuilder | 否 | undefined | Static API 23 |
| style/factory | CustomBuilderT/ConstructorT | 对应重载是 | 无 | API 26 static only |

**Native Column attributes**

| 属性 | 值 |
|------|-----|
| 函数签名 | `NODE_COLUMN_ALIGN_ITEMS`; `NODE_COLUMN_JUSTIFY_CONTENT`; `NODE_LINEAR_LAYOUT_SPACE`; `NODE_LINEAR_LAYOUT_REVERSE` |
| 返回值 | 通用属性API执行set/reset/get，getter返回ArkUI_AttributeItem |
| 开放范围 | Public C API |
| 错误码 | `ARKUI_ERROR_CODE_NO_ERROR(0)` / `ARKUI_ERROR_CODE_PARAM_INVALID(401)` |
| 关联 AC | AC-2.1~AC-2.5 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| align/justify | i32 | set时是 | Center/Start | align 0..2；justify当前校验1..8 |
| space/reverse | f32/i32 | set时是 | 0vp/false | API23；各恰一个参数，reverse>=0 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Dynamic direct 与 modifier 分别收到 undefined/null | direct 采用入口默认值，modifier 执行 reset | AC-1.2 |
| 2 | Native set/reset/get 收到合法值或非法参数 | 返回 0/401，并保留 fresh getter 与 reset 默认值差异 | AC-2.1~AC-2.5 |
| 3 | 按 API 7–26 或 legacy pipeline 选择入口 | 仅开放目标版本已发布能力，legacy 空实现不模拟 NG 行为 | AC-3.1~AC-3.4 |

布局结果引用 Feat-01/02；PointLight 细节引用 Feat-04。

## 兼容性声明

- **已有 API 行为变更:** 否；本次不修改实现，API 7/8/11/12/18/23/26 的增量开放作为既有版本边界保留。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** ArkTS以canonical SDK标注为准，Native以公开头文件为准。

| 版本 | 能力与证据 |
|------|------------|
| 7–11 | Column/align自7、justify自8、form自9、cross自10、atomic及pointLight自11；`column.d.ts:110-211` |
| 11/12 | attributeModifier自11，reverse/ColumnModifier自12；`common.d.ts:25178-25201`; `ColumnModifier.d.ts:22-55` |
| 18 | V2 options接受Resource；`column.d.ts:21-108,145-159` |
| 23 | Static Column/Modifier及Native linear space/reverse；`column.static.d.ets:71-177`; `native_node.h:8412-8435` |
| 26 | setColumnOptions、style-builder、ExtendableColumn；`column.static.d.ets:123-232` |

| 风险 | 当前实现/契约影响 | 证据 |
|------|-------------------|------|
| reverse undefined/reset | direct=true，modifier reset=false | `js_column.cpp:113-119`; `ArkComponent.ts:125-159`; `native/node/column_modifier.cpp:106-110` |
| fresh justify getter | fresh=AUTO(0)，reset=Start(1) | `column_model_ng.cpp:180-184`; `native/node/column_modifier.cpp:32-37` |
| 非法枚举 | justify接受空洞4/5，部分底层路径可写raw值 | `style_modifier.cpp:12643-12662`; `native/node/column_modifier.cpp:39-52` |
| legacy缺口 | reverse/Resource构造为空实现 | `column_model_impl.h:24-30`; `column_model.h:37-44` |
| 元数据/类型 | ColumnModifier crossplatform注记12/20冲突，ArkColumn.ts未列Resource | `ColumnModifier.d.ts:22-43`; `@ohos.arkui.modifier.d.ts:79-86`; `ArkColumn.ts:50-66` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| SDK权威 | ArkTS签名以canonical SDK为准，源码扩展只列风险 | AC-1.1~AC-1.5, AC-3.4 |
| 通道分层 | Dynamic、Static、Native写同一NG属性，但校验/reset不同 | AC-1.2~AC-2.5 |
| Native枚举映射 | HorizontalAlign 0..2映射内部1..3；FlexAlign有效值有4/5空洞 | AC-2.1~AC-2.3 |
| 共享边界 | 布局引用Feat-01/02，PointLight引用Feat-04 | AC-1.3, AC-3.1 |
| 实现即规格 | legacy和getter偏差不得在补录中修正 | AC-2.2, AC-2.3, AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增运行路径或性能指标 | 代码审查 | `column_modifier.ts:16-26` |
| 功耗 | 不新增后台任务 | 代码审查 | 同步set/reset路径 |
| 内存 | 不新增持久数据 | Modifier UT | `ArkColumn.ts:16-66` |
| 安全 | Native公开入口校验参数数/范围 | 异常UT | `style_modifier.cpp:12589-12662,20466-20540` |
| 可靠性 | 合法SDK输入不得返回401或崩溃 | 对照UT | VM-1~VM-3 |
| 可测试性 | 每个通道至少覆盖正常与边界 | 追溯审查 | VM-1~VM-4 |
| 自动化维测 | Native get可读取提交值 | Native UT | `style_modifier.cpp:12625-12695,20505-20573` |
| 定界定位 | 按SDK/bridge/style/node modifier分层 | 代码审查 | `design.md`调用链 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无 | 按目标API选择入口 | 版本测试 | AC-3.1, AC-3.2 |
| 平板 | 无 | reset/get及错误码一致 | Native UT | AC-2.1~AC-2.5 |
| 折叠屏 | 无 | 折叠状态不改变接口范围 | 场景UT | AC-2.1~AC-3.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不改变节点语义 | N/A |
| 大字体 | 否 | 尺寸行为见Feat-01 | N/A |
| 深色模式 | 否 | PointLight见Feat-04 | N/A |
| 多窗口/分屏 | 否 | 不改变签名和错误码 | AC-2.1~AC-2.5 |
| 多用户 | 否 | 无用户级状态 | N/A |
| 版本升级 | 是 | 按版本矩阵裁剪 | AC-3.1, AC-3.2 |
| 生态兼容 | 是 | 多范式和legacy差异影响接入 | AC-1.2, AC-2.3, AC-3.3, AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Column 多范式接口与版本兼容
  Scenario: Dynamic direct 与 modifier reset 分流
    Given Column reverse 为 false
    When 比较 direct reverse(undefined) 与 Modifier undefined
    Then 前者写 true，后者 reset 为 false
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有AC使用WHEN/THEN格式，可独立测试
- [x] AC与规则双向关联；规则满足五项质量检查
- [x] 权威声明已核对；源码偏差仅列风险

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Column multi-paradigm Native legacy behavior"
  - repo: "openharmony/interface_sdk-js"
    query: "Column API 7-26 contracts"
```

**关键文档：** `05-ui-components/01-layout-components/03-column/design.md`。
