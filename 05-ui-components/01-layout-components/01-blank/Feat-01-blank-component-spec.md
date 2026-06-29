# 特性规格

> Func-05-01-01-Feat-01 Blank 组件：固化空白占位组件的构造参数、color/min/height 三个自有属性、自动 Flex 布局行为的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Blank 组件 (Blank Component) |
| 特性编号 | Func-05-01-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 10 有核心行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/01-layout-components/01-blank/design.md` | Baselined |
| SDK API | `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | — |
| SDK 组件 | `docs/sdk/Component_API_Knowledge_Base_CN.md` | — |

---

## 用户故事

### US-1: 创建空白占位组件

**作为** 应用开发者,
**我想要** 使用 `Blank()` 创建一个自动填充父容器剩余空间的空白占位组件,
**以便** 在 Row/Column/Flex 布局中实现弹性间距。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Blank()` 无参数 THEN 创建一个最小尺寸为 0 的空白占位组件 | 边界 |
| AC-1.2 | WHEN 调用 `Blank(min?: number \| string)` 传入 min 参数 THEN 组件的最小尺寸被设置为 min 值 |
| AC-1.3 | WHEN min 参数为负数 THEN 值被静默钳位为 0.0 VP，不报错 | 异常 |
| AC-1.4 | WHEN Blank 组件不允许拥有子组件 THEN `allowChildCount()` 返回 0 | 正常 |
| AC-1.5 | WHEN API < 10 THEN Blank 创建时自动设置 FlexGrow=1.0、FlexShrink=0.0、AlignSelf=STRETCH、Height=0.0VP | 边界 |
| AC-1.6 | WHEN API >= 10 THEN Blank 创建时仅重置 CalcMinSize，Flex 属性由 BeforeCreateLayoutWrapper 动态计算 | 边界 |

### US-2: 设置空白占位的背景颜色

**作为** 应用开发者,
**我想要** 通过 `.color()` 设置 Blank 组件的背景颜色,
**以便** 让空白占位区域具有可见的填充色。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.color(value: ResourceColor)` THEN 空白占位区域渲染为指定颜色 | 正常 |
| AC-2.2 | WHEN 未设置 color 或调用 resetColor THEN 默认颜色为 Color::TRANSPARENT | 异常 |
| AC-2.3 | WHEN color 值解析失败 THEN 回退为 Color::TRANSPARENT | 异常 |
| AC-2.4 | WHEN color 为 Resource 类型 THEN 支持资源引用及配置变更时自动刷新 | 正常 |

### US-3: 设置空白占位的显式高度

**作为** 应用开发者,
**我想要** 通过 `.height()` 设置 Blank 组件的显式高度,
**以便** 在需要时覆盖自动布局计算的高度值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.height(value: Length)`（继承自 CommonMethod，内部被 Blank 覆写）THEN 组件高度被设置到 BlankLayoutProperty::propHeight_ | 正常 |
| AC-3.2 | WHEN 调用 resetBlankHeight THEN 清除通用 LayoutProperty 的 selfIdealSize.Height（通过 `ViewAbstract::ClearWidthOrHeight`），BeforeCreateLayoutWrapper 依据 selfIdealSize 判断是否设置 AlignSelf=STRETCH。注意：此操作不清除 BlankLayoutProperty::propHeight_（见风险表） | 正常 |
| AC-3.3 | WHEN 设置了显式 height 且 API >= 10 THEN 该高度值存入 BlankLayoutProperty::propHeight_ | 边界 |

### US-4: 自动 Flex 布局行为（API >= 10）

**作为** 应用开发者,
**我想要** Blank 组件自动根据父容器方向填充剩余空间,
**以便** 无需手动设置 Flex 属性即可实现弹性占位效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN API >= 10 且父容器为 Row THEN FlexGrow=1.0、FlexShrink=1.0（仅当未显式设置主轴尺寸时） | 边界 |
| AC-4.2 | WHEN API >= 10 且父容器为 Column THEN FlexGrow=1.0、FlexShrink=1.0（仅当未显式设置主轴尺寸时） | 边界 |
| AC-4.3 | WHEN API >= 10 且未显式设置交叉轴尺寸 THEN AlignSelf=STRETCH | 边界 |
| AC-4.4 | WHEN API >= 10 且显式设置了主轴/交叉轴尺寸 THEN 对应 Flex 属性不被设置（保持 Reset 后的默认值） | 边界 |
| AC-4.5 | WHEN API >= 10 且设置了 min 参数 THEN min 值被转换为 CalcMinSize 沿父容器主轴方向生效 | 边界 |
| AC-4.6 | WHEN API >= 10 且已存在 CalcMinSize 对应轴的值 THEN 不覆盖（保留显式设置的约束） | 边界 |
| AC-4.7 | WHEN API >= 10 且父容器为 Flex THEN 根据 Flex 的 flexDirection 判断主轴方向 | 边界 |
| AC-4.8 | WHEN API >= 10 且父容器为非 Row/Column/Flex 的其他容器 THEN 按 ROW 方向处理（默认行为） | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 || R-3 | 单元测试 BlankFrameNodeCreator001 | 正常 |
| AC-1.2 || R-4 | 单元测试 BlankFrameNodeCreator001 | 正常 |
| AC-1.3 || R-20 | 单元测试 BlankFrameNodeCreator002 | 正常 |
| AC-1.4 || R-5 | 代码审查 ArkBlank.ts:89 | 正常 |
| AC-1.5 || R-6, R-1 | 代码审查 blank_model_ng.cpp:33-37（注：BlankFrameNodeCreator001 仅验证 MinSize，未断言 Flex 属性） | 正常 |
| AC-1.6 || R-7, R-1 | 代码审查 blank_model_ng.cpp:38-40（注：同上） | 正常 |
| AC-2.1 || R-8 | 单元测试 SetColorTest1 | 正常 |
| AC-2.2 || R-9 | 代码审查 blank_paint_property.h:42 | 正常 |
| AC-2.3 || R-21 | 代码审查 js_blank.cpp:76 | 正常 |
| AC-2.4 || R-10 | 代码审查 blank_model_ng.cpp:103-128（注：SetColorTest1 仅验证缓存键存在性，未验证配置变更回调路径） | 正常 |
| AC-3.1 || R-11 | 单元测试 BlankFrameNodeCreator003 | 正常 |
| AC-3.2 || R-12 | 代码审查 blank_modifier.cpp:50-54 + view_abstract.cpp:6954-6963 | 正常 |
| AC-3.3 || R-11 | 代码审查 blank_layout_property.h:53 | 正常 |
| AC-4.1 || R-13, R-2 | 单元测试 BlankPatternTest001/002 | 正常 |
| AC-4.2 || R-13, R-2 | 单元测试 BlankPatternTest002 | 正常 |
| AC-4.3 || R-14 | 单元测试 BlankPatternTest001/002 | 正常 |
| AC-4.4 || R-15 | 代码审查 blank_pattern.cpp:86-100 | 正常 |
| AC-4.5 || R-16 | 代码审查 blank_pattern.cpp:101-114 | 正常 |
| AC-4.6 || R-17 | 代码审查 blank_pattern.cpp:103-113 | 正常 |
| AC-4.7 || R-18 | 单元测试 BlankPatternTest003/004 | 正常 |
| AC-4.8 || R-19 | 代码审查 blank_pattern.cpp:34-35 | 正常 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | Blank 组件在 API < 10 和 API >= 10 之间有核心行为差异：API < 10 在创建时静态设置 Flex 属性（FlexGrow=1.0, FlexShrink=0.0），API >= 10 在每次布局前动态计算 Flex 属性且 FlexShrink=1.0 | — | — |
| R-2 | 行为 | — | Blank 组件在 API >= 10 的自动布局行为取决于父容器类型（Row/Column/Flex），根据主轴/交叉轴方向动态分配 FlexGrow/FlexShrink/AlignSelf | — | — |
| R-3 | 行为 | `js_blank.cpp:45` | Blank() 无参创建时，默认 min=0.0 VP | — | — |
| R-4 | 行为 | `blank_model_ng.cpp:71` | Blank(min) 创建时，min 参数存储到 BlankLayoutProperty::propMinSize_ | — | — |
| R-5 | 行为 | `ArkBlank.ts:89` | Blank 组件不允许子组件，allowChildCount()=0 | — | — |
| R-6 | 行为 | `blank_model_ng.cpp:33-37` | API < 10：创建时设置 FlexGrow=1.0, FlexShrink=0.0, AlignSelf=STRETCH, Height=0.0VP | — | — |
| R-7 | 行为 | `blank_model_ng.cpp:38-40` | API >= 10：创建时仅 ResetCalcMinSize，Flex 属性由 BeforeCreateLayoutWrapper 动态设置 | — | — |
| R-8 | 行为 | `blank_paint_property.h:42` | color 属性存储在 BlankPaintProperty::propColor_，触发 PROPERTY_UPDATE_RENDER | — | — |
| R-9 | 行为 | `blank_paint_property.h:42` (GetColorValue 默认参数) | color 默认值为 Color::TRANSPARENT | — | — |
| R-10 | 行为 | `blank_model_ng.cpp:103-128` | color 支持 Resource 对象引用，通过 resCacheMap 缓存解析结果，键为 "blank.color" | — | — |
| R-11 | 行为 | `blank_layout_property.h:53` | height 属性存储在 BlankLayoutProperty::propHeight_，触发 PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT | — | — |
| R-12 | 行为 | `blank_modifier.cpp:50-54`, `view_abstract.cpp:6954-6963` | resetBlankHeight 调用 `ViewAbstract::ClearWidthOrHeight(frameNode, false)` 清除通用 LayoutProperty 的 selfIdealSize.Height，不影响 BlankLayoutProperty::propHeight_ | — | — |
| R-13 | 行为 | `blank_pattern.cpp:97-99` | API >= 10：当未显式设置主轴尺寸时，FlexGrow=1.0 且 FlexShrink=1.0 | — | — |
| R-14 | 行为 | `blank_pattern.cpp:94-96` | API >= 10：当未显式设置交叉轴尺寸时，AlignSelf=STRETCH | — | — |
| R-15 | 行为 | `blank_pattern.cpp:83-85` | API >= 10：每次 BeforeCreateLayoutWrapper 先 ResetAlignSelf/ResetFlexGrow/ResetFlexShrink，再按条件设置 | — | — |
| R-16 | 行为 | `blank_pattern.cpp:103-113` | API >= 10：min 值被转换为 CalcMinSize，Row 父容器设置 Width，Column 父容器设置 Height | — | — |
| R-17 | 行为 | `blank_pattern.cpp:104-106, 109-111` | API >= 10：如果 CalcMinSize 对应轴已有值，不覆盖 | — | — |
| R-18 | 行为 | `blank_pattern.cpp:37-41` | API >= 10：Flex 父容器通过 FlexLayoutProperty::GetFlexDirection() 获取方向 | — | — |
| R-19 | 行为 | `blank_pattern.cpp:34-35` | 非 Row/Column/Flex 的父容器，默认按 ROW 方向处理 | — | — |
| R-20 | 异常 | — | min 参数为负数时，静默钳位为 0.0 VP，不抛出异常 | `blank_model_ng.cpp:67-70` | — |
| R-21 | 异常 | — | color 值解析失败时，回退为 Color::TRANSPARENT | `js_blank.cpp:76` | — |
| R-22 | 异常 | — | Blank 无父容器时，BeforeCreateLayoutWrapper 因 parent==nullptr 直接返回 | `blank_pattern.cpp:74-75` | — |
| R-23 | 异常 | — | API < 10 时，BeforeCreateLayoutWrapper 直接返回（不执行动态 Flex 计算） | `blank_pattern.cpp:78-80` | — |
| R-24 | 异常 | — | min 参数为百分比时被重置为 0.0 VP（JS 桥接层校验） | `js_blank.cpp:52` | — |
| R-25 | 恢复 | — | color 设置 Resource 后，配置变更时通过 ResourceObject 回调自动重新解析并更新渲染（键 "blank.color"） | — | — |
| R-26 | 恢复 | — | ResetColor 恢复颜色为 TRANSPARENT；resetBlankHeight 清除通用 LayoutProperty 的 selfIdealSize.Height（使 BeforeCreateLayoutWrapper 判定"无交叉轴显式尺寸"从而恢复 AlignSelf=STRETCH），但不清除 BlankLayoutProperty::propHeight_ | — | — |

---

## 验证映射

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 单元测试 | `test/unittest/core/pattern/blank/blank_test_ng.cpp` BlankFrameNodeCreator001 |
| AC-1.2 | 单元测试 | `test/unittest/core/pattern/blank/blank_test_ng.cpp` BlankFrameNodeCreator001 |
| AC-1.3 | 单元测试 | `test/unittest/core/pattern/blank/blank_test_ng.cpp` BlankFrameNodeCreator002 |
| AC-1.4 | 代码审查 | `frameworks/bridge/declarative_frontend/ark_component/src/ArkBlank.ts:89` |
| AC-1.5 | 代码审查 | `frameworks/core/components_ng/pattern/blank/blank_model_ng.cpp:33-37`（单元测试 BlankFrameNodeCreator001 未覆盖 Flex 属性断言） |
| AC-1.6 | 代码审查 | `frameworks/core/components_ng/pattern/blank/blank_model_ng.cpp:38-40`（同上） |
| AC-2.1 | 单元测试 | `test/unittest/core/pattern/blank/blank_test_ng.cpp` SetColorTest1 |
| AC-2.2 | 代码审查 | `frameworks/core/components_ng/pattern/blank/blank_paint_property.h:42` |
| AC-2.3 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_blank.cpp:76` |
| AC-2.4 | 代码审查 | `frameworks/core/components_ng/pattern/blank/blank_model_ng.cpp:103-128`（单元测试 SetColorTest1 未覆盖配置变更回调路径） |
| AC-3.1 | 单元测试 | `test/unittest/core/pattern/blank/blank_test_ng.cpp` BlankFrameNodeCreator003 |
| AC-3.2 | 代码审查 | `frameworks/core/interfaces/native/node/blank_modifier.cpp:50-54` → `frameworks/core/components_ng/base/view_abstract.cpp:6954-6963` |
| AC-3.3 | 代码审查 | `frameworks/core/components_ng/pattern/blank/blank_layout_property.h:53` |
| AC-4.1 | 单元测试 | `test/unittest/core/pattern/blank/blank_test_ng.cpp` BlankPatternTest001 |
| AC-4.2 | 单元测试 | `test/unittest/core/pattern/blank/blank_test_ng.cpp` BlankPatternTest002 |
| AC-4.3 | 单元测试 | `test/unittest/core/pattern/blank/blank_test_ng.cpp` BlankPatternTest001/002 |
| AC-4.4 | 代码审查 | `frameworks/core/components_ng/pattern/blank/blank_pattern.cpp:86-100` |
| AC-4.5 | 代码审查 | `frameworks/core/components_ng/pattern/blank/blank_pattern.cpp:101-114` |
| AC-4.6 | 代码审查 | `frameworks/core/components_ng/pattern/blank/blank_pattern.cpp:103-113` |
| AC-4.7 | 单元测试 | `test/unittest/core/pattern/blank/blank_test_ng.cpp` BlankPatternTest003/004 |
| AC-4.8 | 代码审查 | `frameworks/core/components_ng/pattern/blank/blank_pattern.cpp:34-35` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/blank.d.ts`

#### 组件构造（BlankInterface）

```typescript
// blank.d.ts:55-96
interface BlankInterface {
  (min?: number | string): BlankAttribute;
}
declare const Blank: BlankInterface;
```

- **min**: 可选，类型 `number | string`（注意：SDK 公开类型不含 Resource），默认 0.0 VP
- **@since**: API 7（基础）、API 9（@form）、API 10（@crossplatform @form）、API 11（@atomicservice）

#### BlankAttribute（Blank 专有属性）

```typescript
// blank.d.ts:132-173
declare class BlankAttribute extends CommonMethod<BlankAttribute> {
  color(value: ResourceColor): BlankAttribute;
}
```

| 方法签名 | 返回类型 | 说明 | @since | 脏标记 |
|----------|----------|------|--------|--------|
| `color(value: ResourceColor): BlankAttribute` | BlankAttribute | 设置背景颜色，默认 Color.Transparent | API 7 | PROPERTY_UPDATE_RENDER |

> **SDK-vs-源码偏差**: BlankAttribute 在 SDK 中仅声明 `color()`。`height()` 继承自 CommonMethod（SDK 视角为通用方法），但内部 `ArkBlankComponent` 覆写了 height，将值存储到 `BlankLayoutProperty::propHeight_` 而非通用 LayoutProperty（`ArkBlank.ts:77-80`）。此偏差已在风险表登记。

#### 继承自 CommonMethod 的通用方法

Blank 继承 CommonMethod\<BlankAttribute\>，拥有 padding/margin/backgroundColor/onClick/height 等通用属性和事件。

**关联类型定义：**

| 类型 | 定义 | 用途 |
|------|------|------|
| `BlankLayoutProperty` | 继承 LayoutProperty，持有 MinSize(Dimension) 和 Height(Dimension) | 布局属性存储 |
| `BlankPaintProperty` | 继承 PaintProperty，持有 Color(Color) | 渲染属性存储 |
| `BlankPattern` | 继承 Pattern，实现 BeforeCreateLayoutWrapper 自动布局逻辑 | 组件模式 |
| `BlankPaintMethod` | 继承 NodePaintMethod，绘制带颜色的矩形 | 渲染方法 |

---

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API < 10 | FlexShrink=0.0（Blank 不会收缩），在创建时一次性设置 Flex 属性 | Blank 在空间不足时不会收缩，可能导致溢出 | API >= 10 默认 FlexShrink=1.0，如需保持旧行为需显式设置 `.flexShrink(0)` |
| API < 10 | FlexBasis 由 min 参数设置 | min 参数同时影响 FlexBasis | API >= 10 不再设置 FlexBasis，改用 CalcMinSize |
| API < 10 | 创建时设置 Height=0.0VP | Blank 默认高度为 0 | API >= 10 不设置默认高度，由自动布局决定 |
| API >= 10 | FlexShrink=1.0（Blank 会收缩），每次布局前动态计算 Flex 属性 | Blank 在空间不足时会等比收缩 | 如需固定尺寸，显式设置 `.flexShrink(0)` |
| API >= 10 | min 参数转换为 CalcMinSize（沿父容器主轴方向） | min 约束沿主轴生效 | 无需迁移 |
| API >= 10 | BeforeCreateLayoutWrapper 每次布局前重置并重新计算 Flex 属性 | 外部显式设置的 Flex 属性会在每次布局前被重置 | 如需自定义 Flex 行为，应在 OnModifyDone 或更高优先级处设置 |
| API 7 | SDK 构造参数类型为 `number \| string`（不含 Resource），但内部 JS 桥接层通过 `JsBlank::Create` 接受任意 Dimension 解析 | JS 层可能接受 SDK 类型签名以外的值（如 Resource） | 依赖 Resource 传 min 属于未定义行为，不应使用 |
| API 7 | SDK 中 BlankAttribute 仅声明 `color()`；`height()` 继承自 CommonMethod。但内部覆写了 height 存入 BlankLayoutProperty::propHeight_ | 开发者无法从 SDK 类型定义判断 height 具有 Blank 专有行为 | 功能上正常可用（CommonMethod.height 被覆写），但语义上属于实现细节 |
| API 7 | SetBlankHeight 写入 BlankLayoutProperty::propHeight_；resetBlankHeight 清除通用 LayoutProperty::selfIdealSize.Height（两条不同属性路径） | resetBlankHeight 后 propHeight_ 残留但 BeforeCreateLayoutWrapper 不检查它，无实际布局影响 | 残留值仅影响 ToJsonValue/DumpInfo 序列化输出 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 属性分层 | 布局属性（MinSize/Height）存入 BlankLayoutProperty；渲染属性（Color）存入 BlankPaintProperty |
| height 双路径 | SetBlankHeight 写入 BlankLayoutProperty::propHeight_；resetBlankHeight 清除通用 LayoutProperty::selfIdealSize.Height。BeforeCreateLayoutWrapper 仅依据 selfIdealSize 判断，不检查 BlankLayoutProperty::propHeight_ |
| 脏标记 | MinSize/Height 变更触发 PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT（需父节点重新测量）；Color 变更仅触发 PROPERTY_UPDATE_RENDER |
| 父容器耦合 | Blank 的自动布局行为依赖父容器类型（Row/Column/Flex），非 Flex 系容器按 ROW 方向处理 |
| API 版本门控 | 核心自动布局逻辑受 Container::LessThanAPIVersion(PlatformVersion::VERSION_TEN) 门控 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | BeforeCreateLayoutWrapper 每次布局前执行，开销应保持 O(1)（仅读写属性，无遍历） |
| 可调试性 | 提供 DumpInfo（min 值）、ToJsonValue（color 值）用于 Inspector 诊断 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| Flex 布局 | Blank 组件通过动态设置 FlexGrow/FlexShrink/AlignSelf 影响 Flex 容器的布局计算 |
| Inspector | Blank 组件通过 BlankComposedElement 暴露 min/color 属性供 DevTools 检查 |
| 资源管理 | color 属性支持 ResourceObject 引用和配置变更回调，参与全局资源管理流程 |

---

## 行为场景

### 场景 1: Blank 在 Row 中自动填充水平空间（API >= 10）

```
Given 一个 Row 容器包含 Blank 组件
  And API 版本 >= 10
  And Blank 未设置显式 width
When 执行布局
Then Blank 的 FlexGrow 被设置为 1.0
  And Blank 的 FlexShrink 被设置为 1.0
  And Blank 自动填充 Row 的剩余水平空间
```

### 场景 2: Blank 在 Column 中自动填充垂直空间（API >= 10）

```
Given 一个 Column 容器包含 Blank 组件
  And API 版本 >= 10
  And Blank 未设置显式 height
When 执行布局
Then Blank 的 FlexGrow 被设置为 1.0
  And Blank 的 FlexShrink 被设置为 1.0
  And Blank 自动填充 Column 的剩余垂直空间
```

### 场景 3: Blank 显式设置交叉轴高度时不拉伸

```
Given 一个 Row 容器包含 Blank 组件
  And API 版本 >= 10
  And Blank 设置了显式 height
When 执行布局
Then Blank 的 AlignSelf 不被设置为 STRETCH
  And Blank 高度为显式设置的值
```

### 场景 4: Blank 负值 min 钳位

```
Given 调用 Blank(-10) 创建组件
When 创建过程执行
Then min 值被钳位为 0.0 VP
  And 不抛出任何异常
```

### 场景 5: Blank 设置颜色

```
Given 一个 Blank 组件
When 调用 .color(Color.Red)
Then 空白区域渲染为红色
  And 属性变更触发 PROPERTY_UPDATE_RENDER
```

### 场景 6: API < 10 的静态 Flex 行为

```
Given API 版本 < 10
When 创建 Blank 组件
Then FlexGrow 被设置为 1.0
  And FlexShrink 被设置为 0.0
  And AlignSelf 被设置为 STRETCH
  And Height 被设置为 0.0 VP
  And BeforeCreateLayoutWrapper 不执行动态 Flex 计算
```

### 场景 7: Blank 在 Flex 容器中

```
Given 一个 Flex 容器设置 flexDirection=FlexDirection.Column
  And 包含 Blank 组件
  And API 版本 >= 10
When 执行布局
Then 通过 FlexLayoutProperty 获取 flexDirection
  And FlexGrow=1.0/FlexShrink=1.0 沿 Column 方向（垂直）生效
```

### 场景 8: Blank 的 min 约束在 Row 中生效

```
Given 一个 Row 容器包含 Blank(20) 组件
  And API 版本 >= 10
  And 未显式设置 CalcMinSize.Width
When 执行 BeforeCreateLayoutWrapper
Then CalcMinSize.Width 被设置为 20 VP
  And Blank 最小宽度为 20 VP
```

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 业务规则/功能规则/异常规则/恢复契约编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义文件（blank.d.ts）
- [x] 兼容性声明标注 API 版本差异
- [x] 行为场景使用 Gherkin Given/When/Then 格式，覆盖关键路径
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/pattern/blank/blank_pattern.cpp` | Pattern 层，自动布局逻辑 |
| `frameworks/core/components_ng/pattern/blank/blank_layout_property.h` | 布局属性定义（MinSize/Height） |
| `frameworks/core/components_ng/pattern/blank/blank_paint_property.h` | 渲染属性定义（Color） |
| `frameworks/core/components_ng/pattern/blank/blank_paint_method.cpp` | 绘制逻辑 |
| `frameworks/core/components_ng/pattern/blank/blank_model_ng.cpp` | NG Model 层，API 版本分支 |
| `frameworks/bridge/declarative_frontend/jsview/js_blank.cpp` | JS 桥接层 |
| `frameworks/bridge/declarative_frontend/ark_component/src/ArkBlank.ts` | ArkTS 组件定义 |
| `frameworks/core/components_v2/inspector/blank_composed_element.cpp` | Inspector 支持 |
| `interface/sdk-js/api/@internal/component/ets/blank.d.ts` | SDK 公开 API 定义 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/blank/blank_test_ng.cpp` | NG 单元测试（12 用例） |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | SDK API 知识库 |
| `docs/sdk/Component_API_Knowledge_Base_CN.md` | 组件 API 知识库 |
