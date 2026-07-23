# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 绘制与视效适配 |
| 特性编号 | Func-02-02-01-Feat-02 |
| 所属 Epic | 跨平台适配层 |
| 优先级 | P1 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 全新特性补录，无存量变更。本节跳过。

## 输入文档

- 源码路径：`frameworks/core/components_ng/render/adapter/` + `frameworks/core/components_ng/image/`
- 设计文档：`02-cross-platform/02-render-backend-adapter/01-render-backend-adapter/design.md`

## 用户故事

### US-1: CanvasImage 基类与 RS 命名耦合适配

作为一个 ACE 引擎开发者，我希望 CanvasImage 基类通过 DrawToRSCanvas 方法定义绘制接口，PixelMapImage 和 SkImageHolder 提供像素级图片数据适配，使渲染后端能通过统一的图片基类获取绘制数据。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN CanvasImage 基类定义 THEN 提供 DrawToRSCanvas(RSCanvas&, float) 虚方法，基类为空操作 | 正常 |
| AC-1.2 | WHEN PixelMapImage 继承 CanvasImage THEN DrawToRSCanvas 通过 Rosen Drawing API 绘制 PixelMap 数据 | 正常 |
| AC-1.3 | WHEN SkImageHolder 继承 CanvasImage THEN 持有 sk_sp<SkImage> 并在 DrawToRSCanvas 中绘制 | 正常 |
| AC-1.4 | WHEN ACE_UNITTEST 编译 THEN DrawToRSCanvas 参数中的 RSCanvas 替换为 Testing::TestingCanvas（drawing_mock.h 84 alias） | 边界 |
| AC-1.5 | WHEN 基类方法名含 RS 前缀 THEN 标记为已知 RS 命名耦合风险（DrawToRSCanvas），新后端适配时需注意 | 边界 |

### US-2: Modifier 适配器模式（Content/Overlay/Extended）

作为一个 ACE 引擎开发者，我希望 RosenModifierAdapter 通过 Content/Overlay/Extended 三种模式将 NG 层的 Modifier 属性适配为 RS 层的 RSExtModifier，使组件视效属性能分层次注入 RS 渲染管线。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN ModifierAdapter::Create(modifierType=CONTENT) THEN 创建 RosenContentModifierAdapter | 正常 |
| AC-2.2 | WHEN ModifierAdapter::Create(modifierType=OVERLAY) THEN 创建 RosenOverlayModifierAdapter | 正常 |
| AC-2.3 | WHEN ModifierAdapter::Create(modifierType=EXTENDED) THEN 创建 RosenExtendedModifierAdapter | 正常 |
| AC-2.4 | WHEN RosenContentModifierAdapter::Apply THEN 将 NG Modifier 属性转换为 RSExtModifier 并 Apply 到 RSNode | 正常 |
| AC-2.5 | WHEN #ifndef ENABLE_ROSEN_BACKEND THEN fake_modifier_adapter.cpp RemoveModifier 为空操作 stub | 边界 |

### US-3: Transition 适配器模式

作为一个 ACE 引引擎开发者，我希望 RosenTransitionAdapter 将 NG 层的 Transition 动效属性适配为 RS 层的 RSTransition，使组件转场动效能映射到 RS 渲染管线。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN TransitionAdapter 初始化 THEN 注册 Transition 效果到对应 RSNode | 正常 |
| AC-3.2 | WHEN Transition 效果类型包括 FADE/SLIDE/EXPAND/DEPLACE THEN 映射到对应 RS Transition 效果 | 正常 |
| AC-3.3 | WHEN #ifndef ENABLE_ROSEN_BACKEND THEN Transition 适配层为空操作 | 边界 |

### US-4: Effect 适配器与毛玻璃材质预设

作为一个 ACE 引擎开发者，我希望 RosenEffectAdapter 将 NG 层的 Effect 属性适配为 RS 层的 RSEffect，包括 Background/Foreground/Bar 毛玻璃材质的 Regular/Dark 预设参数映射。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN EffectAdapter::Apply THEN 将 NG Blur/Color/Radius 等属性映射到 RSEffect 参数 | 正常 |
| AC-4.2 | WHEN BackgroundBlur 预设为 Regular THEN 使用 BlurStyle::REGULAR + LIGHT 映射 STYLE_CARD_LIGHT；预设参数（radius/saturation/brightness/maskColor）由外部系统主题资源文件加载（不在 ace_engine 仓内），字段名为 maskColor（非 lightMode/darkMode） | 正常 |
| AC-4.3 | WHEN BackgroundBlur 预设为 Dark THEN 使用 BlurStyle::REGULAR + DARK 映射 STYLE_CARD_DARK；参数由主题资源加载 | 正常 |
| AC-4.4 | WHEN BarBlur 预设 THEN 区分 Regular/Dark 两套预设参数 | 正常 |
| AC-4.5 | WHEN ForegroundBlur THEN 区分 Regular/Dark 两套预设参数 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~5 | TASK-F02-01 | 单测+编译检查 | canvas_image.h, pixel_map_image.cpp |
| AC-2.1~2.5 | R-6~10 | TASK-F02-02 | 单测 | rosen_modifier_adapter.cpp |
| AC-3.1~3.3 | R-11~13 | TASK-F02-03 | 单测 | rosen_transition_adapter.cpp |
| AC-4.1~4.5 | R-14~18 | TASK-F02-04 | 单测 | rosen_effect_adapter.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | CanvasImage 基类 DrawToRSCanvas | 默认空操作虚方法 | 方法名含 RS 前缀 | AC-1.1 |
| R-2 | 行为 | PixelMapImage DrawToRSCanvas | 通过 Rosen Drawing API 绘制 | PixelMap 数据源 | AC-1.2 |
| R-3 | 行为 | SkImageHolder DrawToRSCanvas | sk_sp<SkImage> 绘制 | Skia 图片数据源 | AC-1.3 |
| R-4 | 边界 | ACE_UNITTEST 编译 | RSCanvas→TestingCanvas | 编译时替换 | AC-1.4 |
| R-5 | 边界 | 基类 RS 命名耦合 | 标记为风险，新后端需注意 | DrawToRSCanvas 方法名 | AC-1.5 |
| R-6 | 行为 | ModifierAdapter::Create(CONTENT) | 创建 RosenContentModifierAdapter | 三种模式之一 | AC-2.1 |
| R-7 | 行为 | ModifierAdapter::Create(OVERLAY) | 创建 RosenOverlayModifierAdapter | 三种模式之一 | AC-2.2 |
| R-8 | 行为 | ModifierAdapter::Create(EXTENDED) | 创建 RosenExtendedModifierAdapter | 三种模式之一 | AC-2.3 |
| R-9 | 行为 | ContentModifierAdapter::Apply | NG Modifier→RSExtModifier→Apply RSNode | 属性转换链 | AC-2.4 |
| R-10 | 边界 | #ifndef ENABLE_ROSEN_BACKEND | RemoveModifier 空操作 stub | 编译链接守卫 | AC-2.5 |
| R-11 | 行为 | TransitionAdapter 初始化 | 注册 Transition 到 RSNode | 转场动效映射 | AC-3.1 |
| R-12 | 行为 | Transition 类型映射 | FADE/SLIDE/EXPAND/DEPLACE→RS 效果 | 4 种基本类型 | AC-3.2 |
| R-13 | 边界 | #ifndef ENABLE_ROSEN_BACKEND | Transition 适配空操作 | 无后端时 | AC-3.3 |
| R-14 | 行为 | EffectAdapter::Apply | NG Blur/Color→RSEffect | 视效属性映射 | AC-4.1 |
| R-15 | 行为 | BackgroundBlur Regular | BlurStyle::REGULAR+LIGHT→STYLE_CARD_LIGHT；maskColor 由主题资源加载 | 预设参数不在 ace_engine 仓内 | AC-4.2 |
| R-16 | 行为 | BackgroundBlur Dark | BlurStyle::REGULAR+DARK→STYLE_CARD_DARK；参数由主题资源加载 | 预设参数 | AC-4.3 |
| R-17 | 行为 | BarBlur 预设 | Regular/Dark 两套参数 | 标题栏毛玻璃 | AC-4.4 |
| R-18 | 行为 | ForegroundBlur 预设 | Regular/Dark 两套参数 | 前景毛玻璃 | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.5 CanvasImage 基类 | 单测+编译检查 | no-op 默认、RS 命名耦合风险、Testing 替换 |
| VM-2 | AC-2.1~2.5 Modifier 适配器 | 单测 | 三种模式创建、Apply 属性转换、空操作 stub |
| VM-3 | AC-3.1~3.3 Transition 适配器 | 单测 | 效果映射、空操作 fallback |
| VM-4 | AC-4.1~4.5 Effect 适配器 | 单测 | 毛玻璃预设参数映射 |

## API 变更分析

N/A，框架内部适配层，无 SDK API 变更。

## 接口规格

### 接口定义

**CanvasImage::DrawToRSCanvas**

| 属性 | 值 |
|------|-----|
| 函数签名 | `virtual void CanvasImage::DrawToRSCanvas(RSCanvas& canvas, float dimension)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| canvas | RSCanvas& | 是 | N/A | ACE_UNITTEST 时替换为 TestingCanvas |
| dimension | float | 是 | 0.0 | >0 表示绘制区域尺寸 |

**ModifierAdapter::Create**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<ModifierAdapter> ModifierAdapter::Create(ModifierType type)` |
| 返回值 | `RefPtr<ModifierAdapter>` — RosenModifierAdapter 或空操作 stub |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** InnerApi

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 基类 RS 耦合 | CanvasImage::DrawToRSCanvas 方法名含 RS 前缀 | AC-1.1, AC-1.5 |
| 三模式 Modifier | Content/Overlay/Extended 分层注入 RS 渲染管线 | AC-2.1~2.4 |
| 毛玻璃预设 | Regular/Dark 两套预设参数由外部系统主题资源加载（不在 ace_engine 仓内） | AC-4.2~4.5 |
| 空操作 Stub | fake_modifier_adapter 在无后端时提供空操作 | AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Modifier Apply ≤0.5ms/次 | 单测计时 | rosen_modifier_adapter.cpp |
| 内存 | ModifierAdapter 持 1 RSExtModifier + 属性数据 | 内存分析 | rosen_modifier_adapter.h |
| 可测试性 | CanvasImage 可通过 Testing 假类测试 | 单测覆盖率 | UT 报告 |

## 多设备适配声明

无差异。所有设备类型使用相同的绘制与视效适配代码。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 适配层不直接影响 | N/A |
| 大字体 | 否 | 适配层不直接影响 | N/A |
| 深色模式 | 是 | 毛玻璃预设区分 Regular/Dark | AC-4.2~4.5 |
| 多窗口/分屏 | 否 | 适配层不直接影响 | N/A |
| 版本升级 | 否 | 适配层内部变更 | N/A |
| 生态兼容 | 是 | CROSS_PLATFORM 编译控制适配层选择 | AC-2.5 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "CanvasImage 基类 DrawToRSCanvas 方法与 RS 前缀命名耦合设计"
  - repo: "openharmony/ace_engine"
    query: "RosenModifierAdapter Content/Overlay/Extended 三模式适配器设计"
  - repo: "openharmony/ace_engine"
    query: "RosenEffectAdapter 毛玻璃材质 Regular/Dark 预设参数映射"
  - repo: "openharmony/ace_engine"
    query: "fake_modifier_adapter.cpp 空操作 stub 与 ENABLE_ROSEN_BACKEND 宏守卫"
```

**关键文档：** ace_engine `frameworks/core/components_ng/render/adapter/`
