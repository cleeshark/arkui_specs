# 特性规格

> Func-07-04-11-Feat-02 Image 扩展组件：固化 A2UI 扩展展示组件 Image 的契约——图片源属性 `src`（必填，ExtendedDynamicString，空串回落占位图）与 `styles.objectFit`（默认 `cover`）、`styles.fillColor`（SVG 才视觉染色）。基准实现：`@arkui-genius/genui`（A2UIRender，native C++ `ExtendedImageComponent`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Image 扩展组件 |
| 特性编号 | Func-07-04-11-Feat-02 |
| 优先级 | P0 |
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
| 组件实现（C++） | `genui/src/main/cpp/components/extended/ExtendedImageComponent.cpp` | — |
| 目录声明（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 协议 Schema | `genui/src/main/resources/rawfile/schema/Extended/components/ExtendedImage.json` | — |
| 文档参考 | `render_docs/reference/extended-components/image.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 图片源（src）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `src` 属性声明图片资源地址,
**以便** 渲染引擎加载本地/网络/资源图片。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `src` 为合法字符串（如 `"https://..."` 或资源路径） THEN 节点图片源为该值（`ExtendedImageComponent.cpp:116-128,235-247`） | 正常 |
| AC-1.2 | WHEN `src` 为 DynamicString（DataBinding/FunctionCall/Expression） THEN 引擎按动态值解析（`allowDynamic=true,allowExpression=true`，`ExtendedImageComponent.cpp:148-151`） | 正常 |
| AC-1.3 | WHEN `src` 缺省 THEN 上报 `SCHEMA_ERROR_CODE_INVALID_VALUE` 并回落空串（`ExtendedImageComponent.cpp:123-126`） | 异常 |
| AC-1.4 | WHEN `src` 为非 string/绑定的对象 THEN 上报 `SCHEMA_ERROR_CODE_TYPE_MISMATCH` 并 `RemoveBindingsForProperty` + 回落空串（`ExtendedImageComponent.cpp:129-135`） | 异常 |
| AC-1.5 | WHEN `src` 为空字符串 THEN 不设置节点图片源（`ResetNodeImageSrc`）（`ExtendedImageComponent.cpp:241-243`） | 边界 |

### US-2: 图片填充模式（objectFit）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.objectFit` 声明图片填充模式,
**以便** 控制图片在容器内的缩放与对齐。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `styles.objectFit` 为 16 种合法 token 之一（如 `contain`/`cover`/`center`） THEN 映射到对应 `A2UIObjectFit`（`IsSupportedObjectFitToken`，`ExtendedImageComponent.cpp:35-40,164-170`） | 正常 |
| AC-2.2 | WHEN `styles.objectFit` 缺省或非法 THEN 回落默认 `cover`（`DEFAULT_OBJECT_FIT=COVER`，`ExtendedImageComponent.cpp:30,181`） | 边界 |
| AC-2.3 | WHEN `styles` 整体非对象（标量/数组） THEN 上报 `TYPE_MISMATCH` 并回落 `objectFit=cover`（`ExtendedImageComponent.cpp:197-206`） | 异常 |

### US-3: 图片染色（fillColor）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.fillColor` 声明图片染色颜色,
**以便** 对 SVG 图标做色调切换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `styles.fillColor` 为合法十六进制颜色字符串（如 `"#FFFF0000"`） THEN 应用染色（`SetFillColor`，`ExtendedImageComponent.cpp:220-223,274-283`） | 正常 |
| AC-3.2 | WHEN `styles.fillColor` 为合法 number（ARGB 整数） THEN 源码同样接受并染色（`ExtendedImageComponent.cpp:211-214`） | 边界 |
| AC-3.3 | WHEN `styles.fillColor` 非法或类型错误 THEN 重置染色（`ResetFillColor`）并告警（`ExtendedImageComponent.cpp:213-231,285-294`） | 异常 |
| AC-3.4 | WHEN `styles.fillColor` 缺省 THEN 不应用染色，保留原始颜色（`ApplyComponentSpecificStyles` 未命中分支，`ExtendedImageComponent.cpp:210`） | 边界 |
| AC-3.5 | WHEN `fillColor` 为绑定描述符（path/call） THEN 跳过即时解析（`IsBindingDescriptorValue` 分支，`ExtendedImageComponent.cpp:211`） | 边界 |

### US-4: 占位图 alt

**作为** 生成式 UI 宿主开发者,
**我想要** Image 在无障碍场景有默认 alt 文本,
**以便** 屏幕阅读器可识别图片。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 应用私有属性后 THEN 恒设 `alt` 为占位图路径 `DEFAULT_IMAGE_PLACEHOLDER_ALT`（`ExtendedImageComponent.cpp:139,249-262`） | 正常 |

### US-5: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Image 扩展组件以 `component:"Image"` 注册到扩展目录,
**以便** DSL 中的扩展 Image 组件被正确路由到 native 渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 组件类型查询 THEN `ExtendedImageComponent::GetType()` 返回 `"Image"`（`ExtendedImageComponent.cpp:103-106`） | 正常 |
| AC-5.2 | WHEN 工厂注册 THEN `ExtendedComponentFactory::RegisterBuiltInComponents` 注册 `"Image"` → `ExtendedImageComponent`（`ExtendedComponentFactory.cpp:121`） | 正常 |
| AC-5.3 | WHEN 目录声明 THEN `A2UIExtendedComponents` 以 `Image` 加入 `EXTENDED_NATIVE_COMPONENT_NAMES` 并加载 `ExtendedImage.json`（`A2UIExtendedComponents.ets:28-45,47-64`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2,R-3 | T-2 | C++ UT | `ExtendedImageComponent.cpp:114-157,235-247` |
| AC-2.1,AC-2.2,AC-2.3 | R-4,R-5 | T-2 | C++ UT + 静态映射比对 | `ExtendedImageComponent.cpp:35-40,159-206` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-6,R-7 | T-2 | C++ UT | `ExtendedImageComponent.cpp:210-294,304-327` |
| AC-4.1 | R-8 | T-2 | C++ UT | `ExtendedImageComponent.cpp:139,249-262` |
| AC-5.1,AC-5.2,AC-5.3 | R-9 | T-2 | 静态比对 | `ExtendedComponentFactory.cpp:121`、`A2UIExtendedComponents.ets:28-64` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `src` 为合法字符串/绑定 | 设置节点图片源 | 空串 → `ResetNodeImageSrc` | AC-1.1,AC-1.2,AC-1.5 |
| R-2 | 异常 | `src` 缺省 | 上报 `INVALID_VALUE` 并回落空串 | 必填属性 | AC-1.3 |
| R-3 | 异常 | `src` 为非标量对象 | 上报 `TYPE_MISMATCH` 并移除绑定回落空串 | 仅接受 string/绑定 | AC-1.4 |
| R-4 | 行为 | `styles.objectFit` 合法 token | 映射 `A2UIObjectFit` | 16 取值（contain/cover/auto/fill/scaleDown/none/9 对齐/matrix） | AC-2.1 |
| R-5 | 边界 | `styles.objectFit` 缺省/非法/非对象 styles | 回落默认 `cover` | 默认 COVER | AC-2.2,AC-2.3 |
| R-6 | 行为 | `styles.fillColor` 合法（string/number） | 应用染色（`SetNodeImageFillColor`） | SVG 视觉生效，PNG/位图不染色 | AC-3.1,AC-3.2 |
| R-7 | 异常 | `styles.fillColor` 非法/类型错误/缺省 | 重置染色（`ResetFillColor`）或保持原色 | 缺省不应用 | AC-3.3,AC-3.4,AC-3.5 |
| R-8 | 行为 | 应用私有属性后 | 恒设 alt 为占位图路径 | `DEFAULT_IMAGE_PLACEHOLDER_ALT` | AC-4.1 |
| R-9 | 行为 | 组件类型/目录 | 类型 `"Image"`，native 工厂 + 扩展目录注册 | — | AC-5.1,AC-5.2,AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 src | C++ UT | 字符串/绑定/空串/缺省与类型警告 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 objectFit | C++ UT + 静态映射比对 | 16 token 映射、默认 cover 回落 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 fillColor | C++ UT | string/number 染色、非法重置、缺省不应用 |
| VM-4 | AC-4.1 alt | C++ UT | 占位图 alt 恒设 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 类型/目录 | 静态比对 | GetType 与工厂/目录注册 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `CatalogItem`（`A2UIExtendedComponents.allA2UIExtendedComponents()` 内 `Image` 项） | 既有 | 扩展目录注册 | 不直接暴露给宿主 | AC-5.3 |
| `ExtendedComponentFactory::RegisterBuiltInComponents()`（`"Image"`） | 既有 | native 工厂路由 | 不直接暴露给宿主 | AC-5.2 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**Image 扩展组件特有属性/样式（descriptor 属性契约，非函数 API）**

| 属性 | 值 |
|------|-----|
| 属性声明 | `ExtendedImageComponent::GetPrivatePropertyDeclaration`（`ExtendedImageComponent.cpp:142-157`） |
| 必填属性 | `src`（schema `ExtendedImage.json:19-22`） |
| 开放范围 | 协议 DSL（无 Public/System API） |
| 错误码 | schema warning `SCHEMA_ERROR_CODE_INVALID_VALUE`/`SCHEMA_ERROR_CODE_TYPE_MISMATCH`；扩展 schema warning（`ReportExtendedSchemaWarning`） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| src | ExtendedDynamicString | 是 | `""` | 任意字符串；空串不设置 src；缺省/非法回落空串 |
| styles.objectFit | enum | 否 | `"cover"` | {contain,cover,auto,fill,scaleDown,none,topStart,top,topEnd,start,center,end,bottomStart,bottom,bottomEnd,matrix} |
| styles.fillColor | string\|number | 否 | 不应用 | 0xARGB hex；SVG 视觉生效，PNG/位图仅解析 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `src:"https://x/y.png"` | 节点图片源 y.png | AC-1.1 |
| 2 | `src` 缺省 | INVALID_VALUE 告警 + 空串 | AC-1.3 |
| 3 | `src:""` | 不设置图片源（Reset） | AC-1.5 |
| 4 | `styles.objectFit:"contain"` | objectFit=contain | AC-2.1 |
| 5 | `styles.objectFit` 缺省 | objectFit=cover | AC-2.2 |
| 6 | `styles.fillColor:"#FFFF0000"` | 染色红色（SVG 生效） | AC-3.1 |
| 7 | `styles.fillColor:"invalid"` | 重置染色 + 告警 | AC-3.3 |
| 8 | `styles.fillColor` 缺省 | 不应用染色 | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 catalog `ohos.a2ui.extended.catalog`，起始 API Version 20。
- **API 版本号策略:** 协议 schema 版本由 `SchemaResourceLoader.loadSchema('schema/Extended/components/ExtendedImage.json')` 声明（`A2UIExtendedComponents.ets:150-157`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 必填属性 src | 缺省上报警告并回落空串；空串不设节点 src | AC-1.3,AC-1.5 |
| objectFit 默认 cover | 非法/缺省回落 cover，非扩展 schema 默认 contain | AC-2.2,AC-2.3 |
| fillColor 染色语义 | SVG 才视觉染色，PNG/位图仅解析（ArkUI 固有行为） | AC-3.1,AC-3.2 |
| native 组件路径 | Image 走 C++ 属性/样式管线 | AC-5.1,AC-5.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法/缺省属性不抛异常，统一回落默认 + schema warning | C++ UT | `ExtendedImageComponent.cpp:114-327` |
| 性能 | 属性/样式应用为单次节点 API 调用 | C++ UT | `ExtendedImageComponent.cpp:235-294` |
| 定界定位 | `LogImageDfxEvent` 记录 APPLIED/FALLBACK/PRESERVED 决策 | C++ UT | `ExtendedImageComponent.cpp:82-90` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | objectFit/fillColor 行为与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 恒设占位图 alt（`DEFAULT_IMAGE_PLACEHOLDER_ALT`） | AC-4.1 |
| 大字体 | 否 | 图片无文本，不涉及 | — |
| 深色模式 | 否 | Image 无颜色特有属性（fillColor 显式指定） | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 catalog 绑定 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 扩展协议 Image 语义对齐 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 扩展组件
  作为 生成式 UI 宿主开发者
  我想要 通过 src 与 styles.objectFit/fillColor 声明图片
  以便 渲染引擎正确加载并样式化图片

  Scenario: 图片源显示
    Given DSL 组件为 {"component":"Image","id":"i1","src":"https://x/y.png"}
    When 应用 descriptor
    Then 节点图片源为 "https://x/y.png"

  Scenario Outline: objectFit 回落
    Given DSL 组件为 {"component":"Image","id":"i1","src":"x.png","styles":{"objectFit":<fit>}}
    When 应用 styles
    Then objectFit 为 <expected>

    Examples:
      | fit          | expected |
      | "contain"    | contain  |
      | "invalid"    | cover    |
      | (缺省)       | cover    |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Image 扩展特有属性 src 与 `styles.objectFit`/`styles.fillColor`；通用属性归通用样式域）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedImageComponent ApplyPrivateAttributes src GetPrivatePropertyDeclaration"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedImageComponent ApplyObjectFitStyle IsSupportedObjectFitToken DEFAULT_OBJECT_FIT"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedImageComponent fillColor SetFillColor ResetFillColor ValidateFillColorSchema"
```

**关键文档：** `genui/src/main/cpp/components/extended/ExtendedImageComponent.cpp`、`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`genui/src/main/resources/rawfile/schema/Extended/components/ExtendedImage.json`