# 特性规格

> Func-07-04-11-Feat-04 Progress 扩展组件：固化 A2UI 扩展展示组件 Progress 的契约——进度值 `value`、进度总量 `total`（越界钳制）与 `styles.type`/`styles.color`/`styles.strokeWidth` 样式。基准实现：`@arkui-genius/genui`（A2UIRender，native C++ `ExtendedProgressComponent`/`ExtendedProgressTheme`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Progress 扩展组件 |
| 特性编号 | Func-07-04-11-Feat-04 |
| 优先级 | P1 |
| 目标版本 | A2UI 扩展协议 catalog `ohos.a2ui.extended.catalog` + 起始 API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 沿用 07-04-11 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/11-a2ui-extended-display-components/design.md` | Baselined |
| 组件实现（C++） | `genui/src/main/cpp/components/extended/ExtendedProgressComponent.cpp` | — |
| 主题映射（C++） | `genui/src/main/cpp/components/extended/ExtendedProgressTheme.cpp` | — |
| 目录声明（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 协议 Schema | `genui/src/main/resources/rawfile/schema/Extended/components/ExtendedProgress.json` | — |
| 文档参考 | `render_docs/reference/extended-components/progress.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 进度值（value）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `value` 属性声明当前进度值,
**以便** 展示任务完成进度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `value` 为合法数字（如 `50`） THEN 节点进度值设为 `50`（`ExtendedProgressComponent.cpp:167-178,274-278`） | 正常 |
| AC-1.2 | WHEN `value` 为 DynamicNumber（DataBinding/FunctionCall/Expression） THEN 引擎按动态值解析（`allowDynamic=true,allowExpression=true`，`ExtendedProgressComponent.cpp:217-219`） | 正常 |
| AC-1.3 | WHEN `value` 缺省 THEN 回落默认 `0` 并上报类型告警（`ApplyPrivateAttributes` 缺省分支，`ExtendedProgressComponent.cpp:171-174`） | 边界 |
| AC-1.4 | WHEN `value` 非法类型（非 number/string/绑定） THEN `RemoveBindingsForProperty` + 回落默认 `0` + `TYPE_MISMATCH`（`ExtendedProgressComponent.cpp:179-187`） | 异常 |
| AC-1.5 | WHEN `value < 0` THEN 钳制到 `0` 并上报 `INVALID_VALUE`（`ExtendedProgressComponent.cpp:192-198`） | 边界 |
| AC-1.6 | WHEN `value > total`（且 `total > 0`） THEN 钳制到 `total` 并上报 `INVALID_VALUE`（`ExtendedProgressComponent.cpp:200-208`） | 边界 |

### US-2: 进度总量（total）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `total` 属性声明进度总量,
**以便** 定义 100% 完成所对应的总值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `total` 为合法正数（如 `100`） THEN 节点进度总量设为 `100`（`ExtendedProgressComponent.cpp:127-154,280-284`） | 正常 |
| AC-2.2 | WHEN `total` 缺省 THEN 回落默认 `100`（`DEFAULT_PROGRESS_TOTAL`）并上报 `INVALID_VALUE`（`ExtendedProgressComponent.cpp:131-136`） | 边界 |
| AC-2.3 | WHEN `total` 非法（非正/非有限，如 `0`/`-5`/`NaN`） THEN 回落默认 `100`（`IsInvalidProgressTotal`，`ExtendedProgressComponent.cpp:63-66,139-147`） | 边界 |
| AC-2.4 | WHEN `total` 非法类型（非 number/string/绑定） THEN `RemoveBindingsForProperty` + 回落 `100` + `TYPE_MISMATCH`（`ExtendedProgressComponent.cpp:155-164`） | 异常 |

### US-3: 类型与前景色（style.type / style.color）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.type` 与 `styles.color` 声明进度样式与前景色,
**以便** 适配线性/环形等视觉形式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `styles.type` 为 `linear/ring/eclipse/scaleRing/capsule` 之一 THEN 映射到对应进度类型（`ParseProgressType`，`StyleApplyUtilsText.cpp:53-54,176-182`） | 正常 |
| AC-3.2 | WHEN `styles.type` 非法或缺省 THEN 回落默认 `linear`（`DEFAULT_PROGRESS_TYPE=0`，`ExtendedProgressComponent.cpp:37,356`） | 边界 |
| AC-3.3 | WHEN `styles.type` 变更且 `useDefaultColor_` THEN 重新按类型取默认前景色（`ApplyProgressTypeValue`，`ExtendedProgressComponent.cpp:336-360`） | 正常 |
| AC-3.4 | WHEN `styles.color` 为合法十六进制颜色 THEN 应用该前景色且 `useDefaultColor_=false`（`ApplyColorValue`，`ExtendedProgressComponent.cpp:314-334`） | 正常 |
| AC-3.5 | WHEN `styles.color` 非法或缺省 THEN 回落类型对应默认前景色（`ExtendedProgressTheme::GetDefaultColorByType`，`ExtendedProgressTheme.cpp:56-72`） | 边界 |

### US-4: 描边宽度（style.strokeWidth）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.strokeWidth` 声明描边宽度,
**以便** 控制线性/环形进度条粗细。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `styles.strokeWidth` 为合法数字（如 `8`） THEN 经 `CrossLanguageAttributeBridge::Dispatch` 下发描边宽度（`ApplyStrokeWidthValue`，`ExtendedProgressComponent.cpp:374-389`） | 正常 |
| AC-4.2 | WHEN `styles.strokeWidth` 缺省或非法类型 THEN 回落默认 `4`（`DEFAULT_PROGRESS_STROKE_WIDTH`，`ExtendedProgressComponent.cpp:36,387`） | 边界 |

### US-5: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Progress 扩展组件以 `component:"Progress"` 注册到扩展目录,
**以便** DSL 中的扩展 Progress 组件被正确路由到 native 渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 组件类型查询 THEN `ExtendedProgressComponent::GetType()` 返回 `"Progress"`（`ExtendedProgressComponent.cpp:104-107`） | 正常 |
| AC-5.2 | WHEN 工厂注册 THEN `ExtendedComponentFactory::RegisterBuiltInComponents` 注册 `"Progress"` → `ExtendedProgressComponent`（`ExtendedComponentFactory.cpp:123`） | 正常 |
| AC-5.3 | WHEN 目录声明 THEN `A2UIExtendedComponents` 以 `Progress` 加入 `EXTENDED_NATIVE_COMPONENT_NAMES` 并加载 `ExtendedProgress.json`（`A2UIExtendedComponents.ets:28-45,47-64`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2,R-3 | T-4 | C++ UT | `ExtendedProgressComponent.cpp:167-208` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-4,R-5 | T-4 | C++ UT | `ExtendedProgressComponent.cpp:127-165` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-6,R-7,R-8 | T-4 | C++ UT + 静态映射比对 | `StyleApplyUtilsText.cpp:53-54,176-182`、`ExtendedProgressTheme.cpp:56-72` |
| AC-4.1,AC-4.2 | R-9 | T-4 | C++ UT | `ExtendedProgressComponent.cpp:362-389` |
| AC-5.1,AC-5.2,AC-5.3 | R-10 | T-4 | 静态比对 | `ExtendedComponentFactory.cpp:123`、`A2UIExtendedComponents.ets:28-64` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `value` 为合法数字/绑定 | 设置进度值 | number/string/绑定 | AC-1.1,AC-1.2 |
| R-2 | 边界 | `value < 0` 或 `value > total` | 钳制到 `0`/`total` | [0,total] | AC-1.5,AC-1.6 |
| R-3 | 异常 | `value` 缺省/非法类型 | 回落 `0` + 告警 | 默认 0 | AC-1.3,AC-1.4 |
| R-4 | 行为 | `total` 合法正数 | 设置进度总量 | 正有限数 | AC-2.1 |
| R-5 | 边界 | `total` 缺省/非正/非有限 | 回落 `100` | 默认 100 | AC-2.2,AC-2.3,AC-2.4 |
| R-6 | 行为 | `styles.type` 合法枚举 | 映射进度类型 | {linear,line,ring,eclipse,scaleRing,capsule} | AC-3.1 |
| R-7 | 边界 | `styles.type` 非法/缺省 | 回落 `linear` | 默认 0 | AC-3.2 |
| R-8 | 边界 | `styles.color` 非法/缺省 | 回落类型对应默认前景色（随 ThemeMode 分流） | 按 type 取色，ring/capsule 回落 fallback | AC-3.3,AC-3.4,AC-3.5 |
| R-9 | 边界 | `styles.strokeWidth` 非法/缺省 | 回落 `4`（vp） | 仅 linear/ring/scaleRing 生效 | AC-4.1,AC-4.2 |
| R-10 | 行为 | 组件类型/目录 | 类型 `"Progress"`，native 工厂 + 扩展目录注册 | — | AC-5.1,AC-5.2,AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 value | C++ UT | value 应用、钳制 [0,total]、缺省/类型回落 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 total | C++ UT | total 应用、非正/非有限回落 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 type/color | C++ UT + 静态映射比对 | type 枚举映射、默认前景色分流 |
| VM-4 | AC-4.1,AC-4.2 strokeWidth | C++ UT | strokeWidth 下发与默认回落 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 类型/目录 | 静态比对 | GetType 与工厂/目录注册 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `CatalogItem`（`A2UIExtendedComponents.allA2UIExtendedComponents()` 内 `Progress` 项） | 既有 | 扩展目录注册 | 不直接暴露给宿主 | AC-5.3 |
| `ExtendedComponentFactory::RegisterBuiltInComponents()`（`"Progress"`） | 既有 | native 工厂路由 | 不直接暴露给宿主 | AC-5.2 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**Progress 扩展组件特有属性/样式（descriptor 属性契约，非函数 API）**

| 属性 | 值 |
|------|-----|
| 属性声明 | `ExtendedProgressComponent::GetPrivatePropertyDeclaration`（`ExtendedProgressComponent.cpp:211-240`） |
| 必填属性 | `value`（schema `ExtendedProgress.json:24-28`） |
| 开放范围 | 协议 DSL（无 Public/System API） |
| 错误码 | schema warning `SCHEMA_ERROR_CODE_INVALID_VALUE`/`SCHEMA_ERROR_CODE_TYPE_MISMATCH` |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ExtendedDynamicNumber | 是 | `0` | number；<0 钳 0，>total 钳 total |
| total | ExtendedDynamicNumber | 否 | `100` | 正有限数；否则回落 100 |
| styles.type | enum | 否 | `"linear"` | {linear,ring,eclipse,scaleRing,capsule}（源码含 `line` 别名） |
| styles.color | ExtendedDynamicString | 否 | 类型默认 | 十六进制；随 ThemeMode 分流 |
| styles.strokeWidth | ExtendedDynamicNumber | 否 | `4` | 有限数；仅 linear/ring/scaleRing 生效 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `value:50, total:100` | 进度值 50 | AC-1.1 |
| 2 | `value:-5` | 钳制到 0 + 告警 | AC-1.5 |
| 3 | `value:150, total:100` | 钳制到 100 + 告警 | AC-1.6 |
| 4 | `total` 缺省 | 总量回落 100 | AC-2.2 |
| 5 | `total:0` | 总量回落 100 + 告警 | AC-2.3 |
| 6 | `styles.type:"ring"` | 环形进度（type=1） | AC-3.1 |
| 7 | `styles.type` 缺省 | 线性进度（type=0） | AC-3.2 |
| 8 | `styles.color` 缺省（linear） | 前景色 0xFF0A59F7/0xFF317AF7 | AC-3.5 |
| 9 | `styles.strokeWidth` 缺省 | 描边 4 | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 catalog `ohos.a2ui.extended.catalog`，起始 API Version 20。
- **API 版本号策略:** 协议 schema 版本由 `SchemaResourceLoader.loadSchema('schema/Extended/components/ExtendedProgress.json')` 声明（`A2UIExtendedComponents.ets:150-157`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| value 有界钳制 | value 必须落在 [0,total]，越界钳制并告警 | AC-1.5,AC-1.6 |
| total 正数约束 | total 非正/非有限回落 100 | AC-2.3 |
| type 决定前景色 | type 变更触发默认前景色重解析 | AC-3.3,AC-3.5 |
| strokeWidth 类型限制 | 仅 linear/ring/scaleRing 生效（schema 声明），实现经 bridge 下发 | AC-4.1 |
| native 组件路径 | Progress 走 C++ 属性/样式管线 | AC-5.1,AC-5.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法/缺省属性不抛异常，统一回落默认 + schema warning | C++ UT | `ExtendedProgressComponent.cpp:127-389` |
| 性能 | 属性/样式应用为单次节点 API 调用（strokeWidth 经 bridge 下发） | C++ UT | `ExtendedProgressComponent.cpp:274-296,362-372` |
| 定界定位 | `LogProgressDfxEvent` 记录 APPLIED/FALLBACK/PRESERVED 决策 | C++ UT | `ExtendedProgressComponent.cpp:83-91` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 进度颜色/值/类型与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 走通用 `accessibility` 属性（归通用样式域） | — |
| 大字体 | 否 | 进度组件无文本，不涉及 | — |
| 深色模式 | 是 | 前景色按 `ThemeMode`+type 分流（`GetDefaultColorByType`） | AC-3.5 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 catalog 绑定 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 扩展协议 Progress 语义对齐 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Progress 扩展组件
  作为 生成式 UI 宿主开发者
  我想要 通过 value/total 与 styles.type/color 声明进度
  以便 渲染引擎正确显示进度

  Scenario: 进度值越界钳制
    Given DSL 组件为 {"component":"Progress","id":"p1","value":150,"total":100}
    When 应用 descriptor
    Then 进度值钳制为 100 且上报 INVALID_VALUE

  Scenario Outline: 类型映射
    Given DSL 组件为 {"component":"Progress","id":"p1","value":50,"styles":{"type":<type>}}
    When 应用 styles
    Then 进度类型为 <expected>

    Examples:
      | type         | expected |
      | "ring"       | ring     |
      | "invalid"    | linear   |
      | (缺省)       | linear   |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Progress 扩展特有属性 value/total 与 `styles.type`/`styles.color`/`styles.strokeWidth`；通用属性归通用样式域）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedProgressComponent ApplyPrivateAttributes value total clamp GetPrivatePropertyDeclaration"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedProgressComponent ApplyComponentSpecificStyles type color strokeWidth"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedProgressTheme GetDefaultColorByType linear ring eclipse scaleRing capsule fallback"
  - repo: "GenerativeUI/A2UIRender"
    query: "StyleApplyUtils ParseProgressType PROGRESS_TYPE_MAP"
```

**关键文档：** `genui/src/main/cpp/components/extended/ExtendedProgressComponent.cpp`、`genui/src/main/cpp/components/extended/ExtendedProgressTheme.cpp`、`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`genui/src/main/resources/rawfile/schema/Extended/components/ExtendedProgress.json`