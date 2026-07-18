# 特性规格

> Func-05-01-09-Feat-03 Row 多范式接口与版本兼容：固化 Dynamic、Static、AttributeModifier、Native C API、legacy/NG 分派及 API 7–26 边界。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Row 多范式接口与版本兼容 |
| 特性编号 | Func-05-01-09-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Row 的公开能力通过 Classic Dynamic、AttributeModifier、Static/generated 和 Native C API 汇入 RowModelNG；legacy pipeline 继续保留旧 RowModelImpl。Row 特有的 alignItems/justifyContent Native 属性与 Row/Column 共用的 `NODE_LINEAR_LAYOUT_SPACE/REVERSE` 分别分派。本文按通道记录 set/reset/get 和版本事实，不跨通道强行归一。证据见 `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:23-145`、`frameworks/bridge/declarative_frontend/ark_component/src/ArkRow.ts:16-165`、`frameworks/core/interfaces/native/implementation/row_modifier.cpp:27-183` 和 `interfaces/native/node/style_modifier.cpp:20466-20540,23049-23077`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Dynamic/Modifier 规格 | 覆盖构造、属性增量更新、Resource、reverse 和 pipeline 分派 |
| ADDED | Static/ExtendableRow 规格 | 覆盖 Static 创建、attribute/component/style builder、setRowOptions 和 API 26 扩展 |
| ADDED | Native/版本矩阵 | 覆盖四类属性 set/reset/get、错误码和 API 7/8/11/12/18/20/23/26 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/09-row/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/row.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/row.static.d.ets` | 已核对 |
| Modifier SDK | `interface/sdk-js/api/arkui/RowModifier.d.ts`; `interface/sdk-js/api/arkui/RowModifier.static.d.ets` | 已核对 |
| Native API | `interfaces/native/native_node.h`; `interfaces/native/node/style_modifier.cpp` | 已核对 |

## 用户故事

### US-1: 使用 Dynamic 和 AttributeModifier

**作为** ArkTS Dynamic 开发者  
**我想要** 创建并增量更新 Row  
**以便** 保持既有声明式应用兼容

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Dynamic 调用 `Row(options)` THEN 解析 space/Resource 和内部 useAlign，选择当前 NG/legacy RowModel 创建水平容器 | 正常 |
| AC-1.2 | WHEN Dynamic 调用 alignItems/justifyContent/reverse THEN 经当前 Model 写相应属性；API 10+ 非法 align/justify 回退 Center/Start | 正常 |
| AC-1.3 | WHEN NG pipeline 生效 THEN 创建 ROW FrameNode；WHEN legacy pipeline 生效 THEN RowModelImpl 创建旧 Flex component 并使用水平 MIN/MIN 策略 | 正常 |
| AC-1.4 | WHEN AttributeModifier 首次设置或值变化 THEN ArkRow 按属性生成 modifier 并调用 ArkTS Native Bridge set；WHEN modifier 被移除 THEN 调用对应 reset | 正常 |
| AC-1.5 | WHEN API 18+ Dynamic space 是 Resource THEN modifier/Model 管理资源更新对象；切换普通值/reset 后不得由旧资源再次覆盖 | 边界 |

### US-2: 使用 Static Row 和扩展构建器

**作为** Static ArkTS 开发者  
**我想要** 用强类型 API 创建、更新和扩展 Row  
**以便** 获得编译期接口约束

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN API 23+ 调用 Static `Row(options, content_)` THEN converter 将 options 转到 RowModelNG，执行 content builder 构建子项 | 正常 |
| AC-2.2 | WHEN Static 调用 alignItems/justifyContent/reverse/pointLight THEN generated modifier 转换 Optional/union 并调用对应既有 Model/RenderContext 路径 | 正常 |
| AC-2.3 | WHEN Static 属性为 undefined/Optional 空值 THEN 使用该属性的 generated reset/default 路径，不读取空 union | 边界 |
| AC-2.4 | WHEN API 23+ 使用 attributeModifier/component builder THEN 类型为 Static RowAttribute/RowModifier，并在目标版本内可见 | 正常 |
| AC-2.5 | WHEN API 26+ 使用 style builder、`setRowOptions` 或 ExtendableRow THEN 能通过现有 Static options/构建链工作；API<26 不依赖这些签名 | 边界 |

### US-3: 通过 Native C API 设置 Row

**作为** Native UI 开发者  
**我想要** 设置、重置和读取 Row 属性  
**以便** 在 C/C++ 中复现 ArkTS 配置

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `NODE_ROW_ALIGN_ITEMS` 或 `NODE_ROW_JUSTIFY_CONTENT` 接收合法 AttributeItem THEN 校验并更新 Row 对应交叉/主轴属性，get 返回当前值 | 正常 |
| AC-3.2 | WHEN 共用 `NODE_LINEAR_LAYOUT_SPACE` 或 `NODE_LINEAR_LAYOUT_REVERSE` 应用于 Row THEN 分派到 Row node modifier，更新/读取 space 或 reverse | 正常 |
| AC-3.3 | WHEN Native 调用属性 reset THEN 使用各属性注册的 resetter，后续 getter 反映 reset 后通道默认状态 | 边界 |
| AC-3.4 | WHEN 参数数量不足、数据指针为空、单位或枚举越界 THEN 返回 `PARAM_INVALID` 且不执行正常写入 | 异常 |
| AC-3.5 | WHEN 节点类型不匹配或生命周期失效 THEN 公共 Node API 前置保护阻止无效解引用 | 异常 |

### US-4: 按正式版本注册使用能力

**作为** 跨版本维护者  
**我想要** 使用仓库中正式登记的 Row 版本边界  
**以便** 避免从中间实现注记推断错误 API

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 目标 API 为 7/8 THEN Dynamic Row/alignItems 与 justifyContent 分别按其 `@since` 可见 | 正常 |
| AC-4.2 | WHEN 目标 API 为 11/12 THEN PointLight System API 与 reverse/RowModifier 分别按其 `@since` 可见 | 正常 |
| AC-4.3 | WHEN 目标 API 为 18 THEN RowOptions/V2 正式命名且 V2 Resource space 可见；历史匿名 options 起始版本仍保留 | 正常 |
| AC-4.4 | WHEN 目标 API 为 20 THEN Dynamic RowModifier 获得 cross-platform 契约；不把该注记解释为能力首次出现 | 边界 |
| AC-4.5 | WHEN 目标 API 为 23/26 THEN Static Row/Static modifier 与 style builder/setRowOptions/ExtendableRow 分别可见 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | Dynamic/Modifier/pipeline UT | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:23-145`; `frameworks/bridge/declarative_frontend/ark_component/src/ArkRow.ts:16-165` |
| AC-2.1~AC-2.5 | R-6~R-10 | 已有实现 | Static SDK 编译 + generated UT | `interface/sdk-js/api/arkui/component/row.static.d.ets:31-225`; `frameworks/core/interfaces/native/implementation/row_modifier.cpp:27-183` |
| AC-3.1~AC-3.5 | R-11~R-15 | 已有实现 | C API set/reset/get UT + fuzz | `interfaces/native/node/style_modifier.cpp:20466-20540,23049-23077`; `test/unittest/capi/modifiers/row_modifier_test.cpp:61-144` |
| AC-4.1~AC-4.5 | R-16~R-20 | 已有实现 | API level 编译矩阵 | `interface/sdk-js/api/@internal/component/ets/row.d.ts:21-229`; `interface/sdk-js/api/arkui/RowModifier.d.ts:24-57`; `interface/sdk-js/api/arkui/component/row.static.d.ets:31-225` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Dynamic Row 构造 | 解析 options 并调用当前 RowModel | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:23-70` | AC-1.1 |
| R-2 | 行为 | Dynamic 属性调用 | align/justify/reverse 经 Model 更新，非法值按 API 10 回退 | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:78-145` | AC-1.2 |
| R-3 | 行为 | pipeline 分派 | NG 用 RowModelNG，legacy 用 RowModelImpl | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:23-40`; `frameworks/bridge/declarative_frontend/jsview/models/row_model_impl.cpp:25-64` | AC-1.3 |
| R-4 | 行为 | Modifier diff/remove | 分别调用属性 set/reset | `frameworks/bridge/declarative_frontend/ark_component/src/ArkRow.ts:16-165` | AC-1.4 |
| R-5 | 恢复 | Resource space 切普通值/reset | 清理 keyed 资源对象，避免旧更新 | `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp:24-139`; `frameworks/core/interfaces/native/node/row_modifier.cpp:20-135` | AC-1.5 |
| R-6 | 行为 | Static Row 创建 | converter 解析 options 并调用模型/content builder | `frameworks/core/interfaces/native/implementation/row_modifier.cpp:27-74` | AC-2.1 |
| R-7 | 行为 | Static 属性 | generated modifier 映射 align/justify/reverse/PointLight | `frameworks/core/interfaces/native/implementation/row_modifier.cpp:77-183` | AC-2.2 |
| R-8 | 边界 | Optional/union 空值 | 进入对应 reset/default，不读空值 | 同上 | AC-2.3 |
| R-9 | 边界 | API 23 builder/modifier | 使用 Static Row 类型 | `interface/sdk-js/api/arkui/component/row.static.d.ets:112-172`; `interface/sdk-js/api/arkui/RowModifier.static.d.ets:24-32` | AC-2.4 |
| R-10 | 边界 | API 26 扩展入口 | style builder/setRowOptions/ExtendableRow 可见 | `interface/sdk-js/api/arkui/component/row.static.d.ets:138-225` | AC-2.5 |
| R-11 | 行为 | 合法 Row align 属性 | style_modifier 分派 Row node modifier set/get | `interfaces/native/node/style_modifier.cpp:23049-23077` | AC-3.1 |
| R-12 | 行为 | 合法共用 linear 属性 | Row node modifier 设置/读取 space/reverse | `interfaces/native/node/style_modifier.cpp:20466-20540` | AC-3.2 |
| R-13 | 恢复 | Native reset | 调用属性 resetter并由 getter反映当前值 | `frameworks/core/interfaces/native/node/row_modifier.cpp:20-135` | AC-3.3 |
| R-14 | 异常 | Native 参数/范围非法 | 返回 PARAM_INVALID，不进入正常写入 | `interfaces/native/node/style_modifier.cpp:20466-20540` | AC-3.4 |
| R-15 | 异常 | 节点类型/生命周期非法 | 公共 Node API 保护后退出 | Native 分派前置检查 | AC-3.5 |
| R-16 | 边界 | API 7/8 | Row/alignItems 与 justifyContent 按版本开放 | `interface/sdk-js/api/@internal/component/ets/row.d.ts:95-196` | AC-4.1 |
| R-17 | 边界 | API 11/12 | PointLight 与 reverse/RowModifier 按版本开放 | `interface/sdk-js/api/@internal/component/ets/row.d.ts:197-229`; `interface/sdk-js/api/arkui/RowModifier.d.ts:24-57` | AC-4.2 |
| R-18 | 边界 | API 18 | RowOptions/V2 命名规范化和 Resource 可见 | `interface/sdk-js/api/@internal/component/ets/row.d.ts:21-145` | AC-4.3 |
| R-19 | 边界 | API 20 | Dynamic RowModifier cross-platform 注记开放 | `interface/sdk-js/api/arkui/RowModifier.d.ts:24-57` | AC-4.4 |
| R-20 | 边界 | API 23/26 | Static 基础与扩展入口分别开放 | `interface/sdk-js/api/arkui/component/row.static.d.ets:31-225` | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | Dynamic/Modifier/Resource UT | pipeline、非法值、diff/reset、Resource 清理 |
| VM-2 | R-6~R-10, AC-2.1~AC-2.5 | Static SDK 编译 + generated UT | Optional、builder、ExtendableRow、API 23/26 |
| VM-3 | R-11~R-15, AC-3.1~AC-3.5 | Native C API UT/fuzz | Row 特有/共用 ID、set/reset/get、错误码 |
| VM-4 | R-16~R-20, AC-4.1~AC-4.5 | API level 编译矩阵 | 7/8/11/12/18/20/23/26 正式注册 |

## API 变更分析

> 所列均为历史已有能力，不表示本次文档任务新增代码 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Dynamic `Row(options?)` | Public | RowOptions/V2 | RowAttribute | N/A | API 7 Dynamic 入口 | AC-1.1~AC-1.3, AC-4.1 |
| Dynamic `RowModifier` | Public | AttributeModifier<RowAttribute> | modifier | N/A | API 12 增量属性入口 | AC-1.4, AC-4.2~AC-4.4 |
| Static `Row(options, content_)` | Public | options + builder | RowAttribute | N/A | API 23 Static 入口 | AC-2.1~AC-2.4 |
| `setRowOptions` / ExtendableRow | Public | Static options/factory/builders | this/实例 | N/A | API 26 Static 扩展 | AC-2.5, AC-4.5 |
| Row/LinearLayout Native 属性 | Public C API | AttributeItem | error/item | NO_ERROR/PARAM_INVALID | Native set/reset/get | AC-3.1~AC-3.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| anonymous Row constructor options | API 18 命名规范化 | 类型文档与 Resource V2 | 使用 RowOptions/RowOptionsV2；历史调用兼容 | AC-4.3 |

## 接口规格

### 接口定义

| 通道 | 入口 | set | reset | get | 版本 |
|------|------|-----|-------|-----|------|
| Dynamic | `Row(options?)` + attributes | Classic JS bridge | 省略/非法按 Dynamic 路径 | 无专有公开 getter | API 7+ |
| AttributeModifier | RowModifier | ArkRow diff → Native Bridge | modifier remove → 属性 reset | 内部阶段值 | API 12+ |
| Static | `Row(options, content_)` | generated converter/Model | undefined → generated reset | 属性链返回 this | API 23+ |
| Static 扩展 | style builder/setRowOptions/ExtendableRow | Static options/builders | Optional 空值 | 返回 this/实例 | API 26+ |
| Native | Row/LinearLayout 属性 ID | AttributeItem set | 属性 reset | AttributeItem get | public native header |

| Native 属性 | 归属 | 功能 | 关联 AC |
|-------------|------|------|---------|
| NODE_ROW_ALIGN_ITEMS | Row | 垂直交叉轴对齐 | AC-3.1 |
| NODE_ROW_JUSTIFY_CONTENT | Row | 水平主轴分布 | AC-3.1 |
| NODE_LINEAR_LAYOUT_SPACE | Row/Column 共用 | 固定子项间距 | AC-3.2 |
| NODE_LINEAR_LAYOUT_REVERSE | Row/Column 共用 | 主轴反向 | AC-3.2~AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；API 18 为正式命名规范化并新增 V2 类型表达。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic API 7；能力按 8/11/12/18/20/23/26 递增。
- **API 版本号策略:** 以仓库 canonical SDK 和 public native header 的正式注册为准。

| 风险 | 当前证据 | 兼容处理 |
|------|----------|----------|
| Dynamic direct reverse(undefined)=true，modifier/native reset=false | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:119-128`; `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_row_bridge.cpp:119-143` | 分通道验收，迁移显式传 boolean |
| Dynamic/Static/Native 的 default、非法值和 fresh/reset getter 不完全统一 | 各桥接、static model、style_modifier | 不跨通道推断；建立独立 set/reset/get 测试 |
| Native justify 连续范围可能覆盖 SDK 枚举空洞 | `interfaces/native/node/style_modifier.cpp:20466-20540` | 公开契约只接受 SDK 声明值；空洞作为风险输入 |
| Resource 生命周期在直接构造、modifier 和 Static 路径存在清理差异可能 | RowModelNG/Bridge/Static reset 路径 | 用 Resource→number→reset 序列定界，不在本次修改 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 多入口同模型 | 合法值最终进入 RowModelNG/LayoutProperty，入口自管校验/reset | AC-1.1~AC-3.3 |
| SDK 注册权威 | 不以中间文件注记替代正式 canonical 版本 | AC-4.1~AC-4.5 |
| Native ID 复用 | space/reverse 使用 LinearLayout 共用 ID | AC-3.2~AC-3.3 |
| pipeline 兼容 | legacy 与 NG 分派继续由容器环境决定 | AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 属性更新不新增额外布局遍历 | Trace | Model/Property dirty path |
| 功耗 | 不新增后台任务或定时器 | 代码审查 | VM-1~VM-4 |
| 内存 | modifier/Resource 状态随节点释放，回调不强持有 FrameNode | 生命周期 UT | AC-1.5 |
| 安全 | Native 参数在转换/写入前校验 | fuzz | AC-3.4~AC-3.5 |
| 可靠性 | 非法值、Optional 空、reset、节点失效不得崩溃 | 异常 UT | VM-1~VM-3 |
| 可测试性 | 每通道可检查最终 Property、getter 和错误码 | 追溯审查 | VM-1~VM-4 |
| 自动化维测 | 复用 Native error code 与布局 dump | Native/Inspector UT | style_modifier/Pattern |
| 定界定位 | 按 SDK→Bridge→Modifier→Model→Algorithm 分层 | 源码定位 | `05-ui-components/01-layout-components/09-row/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无接口专有差异 | 合法同值经各通道进入同一模型 | 通道对照测试 | AC-1.1, AC-2.1, AC-3.1 |
| 平板 | 无接口专有差异 | 窗口约束不改变版本可见性 | 编译+可变窗口测试 | AC-4.1~AC-4.5 |
| 折叠屏 | 无接口专有差异 | 状态变化后当前属性重新布局 | 折叠态回归 | AC-1.4~AC-1.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 间接 | 通道差异不应改变合法同值的语义树 | AC-1.1~AC-3.2 |
| 大字体 | 间接 | 最终布局由共享模型响应子项尺寸 | AC-1.1, AC-2.1 |
| 深色模式 | 否 | 本 Feat 不涉及光效细节 | N/A |
| 多窗口/分屏 | 间接 | 各通道配置由同一算法响应约束变化 | AC-1.3 |
| 多用户 | 否 | 无持久用户状态 | N/A |
| 版本升级 | 是 | 8 个版本节点是核心矩阵 | AC-4.1~AC-4.5 |
| 生态兼容 | 是 | Dynamic/Static/Native reset/default 差异需显式处理 | AC-1.2~AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Row 多范式接口与版本兼容
  Scenario: 合法配置跨通道一致
    Given Dynamic Static Native 分别创建 Row
    When 三者设置等价的 space align justify 和 reverse
    Then 最终 Row LayoutProperty 表达相同合法值

  Scenario: Native 参数非法
    Given 一个有效 Row Native 节点
    When NODE_ROW_ALIGN_ITEMS 参数数量不足
    Then 返回 PARAM_INVALID
    And 原属性不经正常写入路径覆盖

  Scenario: 正式 API 版本隔离
    Given 目标 API 为 23
    When 编译 Static Row component builder
    Then API 23 能力可见
    And API 26 ExtendableRow 不作为 API 23 契约依赖
```

## Spec 自审清单

- [x] 无占位文本
- [x] Dynamic、Modifier、Static、Native、legacy/NG 均覆盖
- [x] 版本信息来自正式 canonical SDK/Native header
- [x] 实现偏差仅列风险，未写成理想契约
- [x] AC、规则、VM、接口矩阵闭环

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Row Dynamic Static ArkRow RowModifier native NODE_ROW NODE_LINEAR_LAYOUT reset"
  - repo: "openharmony/interface_sdk-js"
    query: "RowModifier Row static ExtendableRow API 7 8 11 12 18 20 23 26"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/row.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/row.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/09-row/design.md`
