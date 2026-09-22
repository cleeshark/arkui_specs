# 特性规格

> Func-07-04-03-Feat-02 Image 组件：固化 A2UI 标准展示组件 Image 的契约——图片数据源 `url`（必填，DynamicString）、无障碍文本 `description`、填充效果 `fit`（contain/cover/fill/none/scaleDown）与尺寸变体 `variant`（icon/avatar/smallFeature/mediumFeature/largeFeature/header）。基准实现：`@arkui-genius/genui`（A2UIRender，native C++ `ImageComponent`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Image 组件 |
| 特性编号 | Func-07-04-03-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 + 起始 API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 沿用 07-04-03 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/03-a2ui-standard-display-components/design.md` | Baselined |
| 组件实现（C++） | `genui/src/main/cpp/components/A2UI/image/ImageComponent.cpp` | — |
| 目录声明（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIImage.ets` | — |
| 协议 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Image.json` | — |
| 文档参考 | `render_docs/reference/standard-components/image.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 图片数据源（url）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `url` 属性声明图片来源,
**以便** 渲染引擎加载并显示图片。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `url` 为合法非空字符串 THEN 设置节点图片源为该 URL（`ImageComponent.cpp:170-176`） | 正常 |
| AC-1.2 | WHEN `url` 为空串 THEN 复位节点图片源（不设置 src）（`ImageComponent.cpp:172-175`） | 边界 |
| AC-1.3 | WHEN `url` 缺省 THEN 上报必填缺失警告并回落空串（`ImageComponent.cpp:159-162`、`Component.cpp:1364-1365`） | 异常 |
| AC-1.4 | WHEN `url` 为 DynamicString（绑定/函数返回 string） THEN 按动态值解析（`allowDynamic=true`，`ImageComponent.cpp:99`） | 正常 |

### US-2: 无障碍文本（description）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `description` 属性声明图片无障碍文本,
**以便** 无障碍辅助工具读取图片说明。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `description` 为合法非空字符串 THEN 设置节点图片 alt（`ImageComponent.cpp:183-190`） | 正常 |
| AC-2.2 | WHEN `description` 缺省 THEN 回落默认占位图 alt `resources/base/media/placeHolder_E5E5EA.png`（`ImageComponent.cpp:39,253-255`） | 边界 |
| AC-2.3 | WHEN `description` 为空串 THEN 复位 alt 且不设置（`ImageComponent.cpp:185-188`） | 边界 |
| AC-2.4 | WHEN `description` 为 DynamicString THEN 按动态值解析（`allowDynamic=true`，`ImageComponent.cpp:108`） | 正常 |

### US-3: 填充效果（fit）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `fit` 属性声明图片填充效果,
**以便** 控制图片在显示边界内的缩放方式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `fit` 为 `"contain"`/`"cover"`/`"fill"`/`"scaleDown"`/`"none"` 之一 THEN 映射为对应 `A2UIObjectFit`（`ImageComponent.cpp:192-207`） | 正常 |
| AC-3.2 | WHEN `fit` 缺省或非法 THEN 回落默认值：`variant==header` → `contain`，否则 `fill`（`ImageComponent.cpp:47-50,115-120,205-206`） | 边界 |
| AC-3.3 | WHEN `fit` 为非法字符串（非枚举）THEN `ParseObjectFit` 回落默认（非 header→`FILL`）并记录枚举回落 | 边界 |

### US-4: 尺寸变体（variant）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `variant` 属性声明图片尺寸变体,
**以便** 按语义尺寸预置显示图片。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `variant` 为 `"icon"`/`"avatar"`/`"smallFeature"`/`"mediumFeature"`/`"largeFeature"`/`"header"` 之一 THEN 设尺寸预置（`ImageComponent.cpp:214-245`） | 正常 |
| AC-4.2 | WHEN `variant` 为 `"icon"` THEN 宽高 32×32（`ImageComponent.cpp:22-23,217-221`） | 正常 |
| AC-4.3 | WHEN `variant` 为 `"avatar"` THEN 宽高 32×32 + 圆角 16（`ImageComponent.cpp:25-27,222-227`） | 正常 |
| AC-4.4 | WHEN `variant` 为 `"smallFeature"` THEN 宽高 50×50；`"mediumFeature"` 150×150；`"largeFeature"` 400×400（`ImageComponent.cpp:29-36,228-244`） | 正常 |
| AC-4.5 | WHEN `variant` 为 `"header"` THEN 仅设宽度百分比 100%（全宽，无高度约束）（`ImageComponent.cpp:38,238-241`） | 边界 |
| AC-4.6 | WHEN `variant` 缺省或非法 THEN 回落 `"mediumFeature"`（150×150）（`ImageComponent.cpp:131-134,243-244`） | 边界 |

### US-5: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Image 组件以 `component:"Image"` 注册到标准目录,
**以便** DSL 中的 Image 组件被正确路由到 native 渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 组件类型查询 THEN `ImageComponent::GetType()` 返回 `"Image"`（`ImageComponent.cpp:154-157`） | 正常 |
| AC-5.2 | WHEN 目录注册 THEN `A2UIImage.asCatalogItem()` 以 `type='Image'` 加载 `components/Image.json` 并标记 `A2UI_STANDARD` + `markInnerNative(true)`（`A2UIImage.ets:24-35`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1,R-2 | T-2 | C++ UT：`ImageComponentTddTest` | `ImageComponent.cpp:95-102,159-176` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-3 | T-2 | C++ UT：`ImageComponentTddTest` | `ImageComponent.cpp:104-111,183-190,253-255` |
| AC-3.1,AC-3.2,AC-3.3 | R-4 | T-2 | C++ UT + 静态映射比对 | `ImageComponent.cpp:47-50,113-124,192-207` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 | R-5 | T-2 | C++ UT：`ImageComponentTddTest` | `ImageComponent.cpp:126-135,214-245` |
| AC-5.1,AC-5.2 | R-6 | T-2 | 静态比对 | `ImageComponent.cpp:154-157`、`A2UIImage.ets:24-35` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `url` 非空字符串 | 设置节点图片源 | DynamicString 允许动态绑定 | AC-1.1,AC-1.4 |
| R-2 | 异常 | `url` 缺省 | 上报 `ERROR_CODE_REQUIRED_MISS` 回落空串；空串复位 src | 必填属性 `{"url"}` | AC-1.2,AC-1.3 |
| R-3 | 边界 | `description` 缺省/空串 | 回落占位图 alt；空串复位 alt | 默认占位图 `placeHolder_E5E5EA.png` | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-4 | 行为 | `fit` 缺省/非法 | 回落默认（header→contain，其余→fill） | 枚举集 {contain,cover,fill,none,scaleDown} | AC-3.1,AC-3.2,AC-3.3 |
| R-5 | 行为 | `variant` 缺省/非法 | 回落 mediumFeature（150×150）；合法按预置尺寸 | header 仅宽 100% | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |
| R-6 | 行为 | 组件类型/目录 | 类型 `"Image"`，标准目录 + native 标记 | — | AC-5.1,AC-5.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 url | C++ UT | 数据源设置、必填警告、空串复位 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 description | C++ UT | alt 设置、占位图回落、空串复位 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 fit | C++ UT + 静态映射比对 | fit 枚举映射、header→contain 特例 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 variant | C++ UT | 五种尺寸预置、header 全宽、回落 mediumFeature |
| VM-5 | AC-5.1,AC-5.2 类型/目录 | 静态比对 | GetType 与目录注册标记 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `CatalogItem`（`A2UIImage.asCatalogItem()`） | 既有 | 组件目录注册 | 不直接暴露给宿主 | AC-5.2 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIImage.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**Image 组件特有属性（descriptor 属性契约，非函数 API）**

| 属性 | 值 |
|------|-----|
| 属性声明 | `ImageComponent::GetPrivatePropertyDeclaration`（`ImageComponent.cpp:137-152`） |
| 必填属性 | `url`（`GetComponentDirectRequiredPropertyKeys`，`ImageComponent.cpp:159-162`） |
| 开放范围 | 协议 DSL（无 Public/System API） |
| 错误码 | schema warning `2001`；缺必填 `ERROR_CODE_REQUIRED_MISS` |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| url | DynamicString | 是 | `""` | 任意字符串；空串不设置 src |
| description | DynamicString | 否 | 占位图 alt | 缺省回落占位图；空串复位 |
| fit | string（enum） | 否 | 默认 `fill`（header→`contain`） | 枚举 {contain,cover,fill,none,scaleDown} |
| variant | string（enum） | 否 | `"mediumFeature"` | 枚举 {icon,avatar,smallFeature,mediumFeature,largeFeature,header} |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `url:"https://…/x.png"` | 设置图片源 | AC-1.1 |
| 2 | `url` 缺省/空串 | 必填警告 + 复位 src | AC-1.2,AC-1.3 |
| 3 | `description` 缺省 | 回落占位图 alt | AC-2.2 |
| 4 | `variant:"avatar",fit` 缺省 | 32×32 + 圆角 16，fit=fill | AC-3.2,AC-4.3 |
| 5 | `variant:"header",fit` 缺省 | 全宽 100%，fit=contain | AC-3.2,AC-4.5 |
| 6 | `variant` 非法 | 回落 mediumFeature（150×150） | AC-4.6 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9，起始 API Version 20。
- **API 版本号策略:** 协议 schema 版本由 `SchemaResourceLoader.loadA2UISchema(version, 'components/Image.json')` 声明（`A2UIImage.ets:26-28`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 必填属性 url | 缺省上报必填警告并回落默认 | AC-1.3 |
| fit 默认值特例 | header 变体回落 contain，其余回落 fill | AC-3.2 |
| variant 尺寸预置 | 五种固定尺寸 + header 全宽无高约束 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |
| weight 交互 | `weight>0` 时重置宽高（`ImageComponent.cpp:260-263`） | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法/缺省属性不抛异常，统一回落默认 + schema warning | C++ UT | `ImageComponent.cpp:247-264` |
| 性能 | 属性应用为单次节点 API 调用 | C++ UT | `ImageComponent.cpp:170-190` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 固定 VP 尺寸预置与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `description` 经 alt 暴露给无障碍辅助 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 大字体 | 否 | 图片尺寸固定，不受字体缩放影响 | — |
| 深色模式 | 否 | Image 无颜色特有属性 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议版本 v0.9 绑定 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 Image 语义对齐 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 组件
  作为 生成式 UI 宿主开发者
  我想要 通过 url/fit/variant 声明图片
  以便 渲染引擎正确显示图片

  Scenario: 图片数据源显示
    Given DSL 组件为 {"component":"Image","id":"i1","url":"https://a/b.png"}
    When 应用 descriptor
    Then 节点图片源为 "https://a/b.png"

  Scenario Outline: 尺寸变体预置
    Given DSL 组件为 {"component":"Image","id":"i1","url":"x","variant":<variant>}
    When 应用 descriptor
    Then 节点宽高为 <size>

    Examples:
      | variant       | size     |
      | icon          | 32×32    |
      | avatar        | 32×32    |
      | smallFeature  | 50×50    |
      | mediumFeature | 150×150  |
      | largeFeature  | 400×400  |
      | invalid       | 150×150  |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Image 特有属性 url/description/fit/variant；通用属性归 07-04-18）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ImageComponent GetPrivatePropertyDeclaration url description fit variant"
  - repo: "GenerativeUI/A2UIRender"
    query: "ImageComponent ApplyVariantPreset ApplyPrivateAttributes DEFAULT_IMAGE_PLACEHOLDER_ALT"
  - repo: "GenerativeUI/A2UIRender"
    query: "ImageComponent ParseObjectFit ResolveDefaultFitValueForVariant header contain fill"
```

**关键文档：** `genui/src/main/cpp/components/A2UI/image/ImageComponent.cpp`、`genui/src/main/ets/core/components/A2UI/A2UIImage.ets`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/Image.json`