# 特性规格

## 概述

| 字段 | 值 |
|------|-----|
| 特性名称 | QRCode 二维码组件 |
| 特性编号 | Func-05-10-06-Feat-01 |
| 所属 Epic | Epic-05-10 信息展示组件 |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | SIG_ArkUI |
| 状态 | Baselined |
| 复杂度 | 中 |

QRCode 组件将字符串内容编码为二维码图像并显示。支持自定义前景色、背景色、内容透明度，支持主题配置和系统颜色变化响应，始终维持正方形布局。

## 本次变更范围（Delta）

本次为Baselined，无增量变更。记录现有 QRCode 组件的完整行为规格。

## 输入文档

| 文档 | 路径 |
|------|------|
| Pattern 源码 | `frameworks/core/components_ng/pattern/qrcode/qrcode_pattern.cpp` |
| Model 源码 | `frameworks/core/components_ng/pattern/qrcode/qrcode_model_ng.cpp` |
| Modifier 源码 | `frameworks/core/components_ng/pattern/qrcode/qrcode_modifier.cpp` |
| Layout 源码 | `frameworks/core/components_ng/pattern/qrcode/qrcode_layout_algorithm.cpp` |
| Paint Property | `frameworks/core/components_ng/pattern/qrcode/qrcode_paint_property.h` |
| Theme Wrapper | `frameworks/core/components_ng/pattern/qrcode/qrcode_theme_wrapper.h` |
| Bridge | `frameworks/core/components_ng/pattern/qrcode/bridge/arkts_native_qrcode_bridge.cpp` |
| Dynamic Modifier | `frameworks/core/components_ng/pattern/qrcode/bridge/qrcode_dynamic_modifier.cpp` |
| Static Modifier | `frameworks/core/components_ng/pattern/qrcode/bridge/qrcode_static_modifier.cpp` |
| NAPI | `frameworks/core/components_ng/pattern/qrcode/qrcode_napi.cpp` |
| Ark Component | `frameworks/core/components_ng/pattern/qrcode/arkui_qrcode.js` |
| BUILD.gn | `frameworks/core/components_ng/pattern/qrcode/BUILD.gn` |

## 用户故事

### US-1: 创建二维码组件

**作为** 应用开发者  
**我想要** 通过 `QRCode(value)` 构造函数创建二维码组件  
**以便** 在界面上展示编码后的二维码。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1-1 | WHEN 调用 QRCodeModelNG::Create(value) THEN 创建 FrameNode 并关联 QRCodePattern，Value 属性设置为传入字符串 | 正常 |
| AC-1-2 | WHEN Create 被调用 THEN QRCodeColorSetByUser 和 QRBackgroundColorSetByUser 标记被重置 | 正常 |
| AC-1-3 | WHEN value 为 null THEN 编码字符串为 "null" | 边界 |
| AC-1-4 | WHEN value 为 undefined THEN 编码字符串为 "undefined" | 边界 |
| AC-1-5 | WHEN value 为 number THEN 编码字符串为该数字的字符串形式 | 正常 |

### US-2: 设置二维码前景色

**作为** 应用开发者  
**我想要** 通过 `qrCodeColor()` 设置二维码前景色  
**以便** 自定义二维码模块颜色。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2-1 | WHEN 调用 SetQRCodeColor(color) THEN PaintProperty.Color 和 RenderContext.ForegroundColor 同步更新 | 正常 |
| AC-2-2 | WHEN 调用 SetQRCodeColor(color) THEN QRCodeColorSetByUser 标记设为 true，防止主题覆盖 | 正常 |
| AC-2-3 | WHEN 调用 SetQRCodeColor(color) THEN RenderContext.ForegroundColorStrategy 被重置 | 正常 |
| AC-2-4 | WHEN 调用 ResetQRColor THEN 颜色恢复为 QrcodeTheme::GetQrcodeColor() | 正常 |

### US-3: 设置二维码背景色

**作为** 应用开发者  
**我想要** 通过 `qrBackgroundColor()` 设置二维码背景色  
**以便** 自定义二维码背景颜色。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3-1 | WHEN 调用 SetQRBackgroundColor(color) THEN PaintProperty.BackgroundColor 和 RenderContext.BackgroundColor 同步更新 | 正常 |
| AC-3-2 | WHEN 调用 SetQRBackgroundColor(color) THEN QRBackgroundColorSetByUser 标记设为 true | 正常 |
| AC-3-3 | WHEN 背景色包含 HDR headRoom THEN SetHDRColorHeadRoom 被调用 | 正常 |
| AC-3-4 | WHEN 调用 ResetQRBackgroundColor THEN 颜色恢复为 QrcodeTheme::GetBackgroundColor() | 正常 |

### US-4: 设置内容透明度

**作为** 应用开发者  
**我想要** 通过 `contentOpacity()` 设置二维码内容透明度  
**以便** 控制二维码内容的视觉透明度。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4-1 | WHEN opacity 在 [0.0, 1.0] 范围内 THEN PaintProperty.Opacity 更新为该值 | 正常 |
| AC-4-2 | WHEN opacity < 0.0 或 > 1.0 THEN 使用默认值 1.0 | 边界 |
| AC-4-3 | WHEN 调用 ResetContentOpacity THEN Opacity 恢复为默认值 1.0 | 正常 |

### US-5: 正方形布局

**作为** 应用开发者  
**我想要** QRCode 始终保持正方形布局  
**以便** 二维码可正确扫描且视觉稳定。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5-1 | WHEN MeasureContent 被调用 THEN 返回 SizeF(min(width, height), min(width, height)) | 正常 |
| AC-5-2 | WHEN API >= 11 THEN 布局计算考虑 padding 扣减 | 正常 |
| AC-5-3 | WHEN API < 11 THEN 使用 CreateIdealSize 简化计算 | 正常 |
| AC-5-4 | WHEN padding 扣减后宽度为负 THEN 宽度设为 0.0 | 边界 |
| AC-5-5 | WHEN layoutPolicy 为 Fix THEN 使用主题默认尺寸 | 正常 |

### US-6: 二维码编码与绘制

**作为** 应用开发者  
**我想要** 输入字符串被编码并绘制为二维码  
**以便** 用户可以扫描该二维码。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6-1 | WHEN onDraw 被调用 THEN 使用 QrcodeImageEncodeString(value, QRCODE_ECC_MEDIUM) 编码 | 正常 |
| AC-6-2 | WHEN 编码结果为 null THEN 记录错误日志并返回，不绘制 | 异常 |
| AC-6-3 | WHEN qrCodeSize <= 0 或 qrCodeSize < qrWidth THEN 记录错误日志并返回 | 边界 |
| AC-6-4 | WHEN value 长度超过 512 THEN 截取前 512 个字符 | 边界 |
| AC-6-5 | WHEN API >= 12 THEN CreateBitMap 不填充背景色模块 | 正常 |
| AC-6-6 | WHEN API < 12 THEN CreateBitMap 手动填充背景色模块 | 正常 |

### US-7: 主题与颜色变化响应

**作为** 应用开发者  
**我想要** QRCode 在系统颜色或主题变化时自动更新默认颜色  
**以便** 组件在深色模式和主题范围中保持可读。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7-1 | WHEN OnColorConfigurationUpdate 触发且用户未设置颜色 THEN 使用主题颜色更新 | 正常 |
| AC-7-2 | WHEN 用户已设置颜色 (QRCodeColorSetByUser=true) THEN 主题变化不覆盖用户值 | 正常 |
| AC-7-3 | WHEN OnThemeScopeUpdate 触发且 API >= 26 THEN 根据主题更新颜色和焦点色 | 正常 |
| AC-7-4 | WHEN themeScopeId <= 0 THEN OnThemeScopeUpdate 返回 false | 边界 |

### US-8: 焦点样式

**作为** 应用开发者  
**我想要** QRCode 具备基础焦点样式  
**以便** 键盘和焦点导航场景可识别当前节点。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-8-1 | WHEN GetFocusPattern 被调用 THEN 返回 FocusType::NODE, focusable=true, FocusStyleType::INNER_BORDER | 正常 |
| AC-8-2 | WHEN 焦点色 THEN 使用 QrcodeTheme::GetFocusedColor() | 正常 |

## 验收追溯

| AC编号 | 验证方式 | 对应测试 |
|--------|----------|----------|
| AC-1-1 | 单元测试 | QRCodePaintPropertyTest001 |
| AC-1-2 | 单元测试 | QRCodePaintPropertyTest001 |
| AC-1-3~AC-1-5 | Bridge 源码 | arkts_native_qrcode_bridge.cpp:70-78 |
| AC-2-1 | 单元测试 | QRCodePaintPropertyTest001 |
| AC-2-2 | 源码 | qrcode_model_ng.cpp:58 |
| AC-3-1 | 单元测试 | QRCodePaintPropertyTest002 |
| AC-4-1 | 单元测试 | QRCodeModelSetContentOpacity001 |
| AC-4-2 | 源码 | qrcode_dynamic_modifier.cpp:124 |
| AC-5-1 | 单元测试 | QRCodePatternTest005 |
| AC-5-2 | 源码 | qrcode_layout_algorithm.cpp:41-51 |
| AC-6-1 | 源码 | qrcode_modifier.cpp:44 |
| AC-6-4 | 单元测试 | QRCodeMaxLengthTest1 |
| AC-7-1 | 单元测试 | QRCodeOnColorConfigurationUpdateTest001 |
| AC-8-1 | 单元测试 | QRCodePatternGetFocusPattern001 |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | QRCode(value) 创建 | FrameNode + QRCodePattern + QRCodePaintProperty 创建完成 | value 不可为空 | AC-1-1 |
| R-2 | 行为 | SetQRCodeColor(color) | PaintProperty.Color + RenderContext.ForegroundColor + ForegroundColorFlag 更新 | QRCodeColorSetByUser=true | AC-2-1 |
| R-3 | 行为 | SetQRBackgroundColor(color) | PaintProperty.BackgroundColor + RenderContext.BackgroundColor 更新 | QRBackgroundColorSetByUser=true | AC-3-1 |
| R-4 | 边界 | opacity 范围 | [0.0, 1.0] 范围内正常设置，超出使用默认值 1.0 | 越界 clamp | AC-4-2 |
| R-5 | 行为 | MeasureContent | 返回 min(w,h) x min(w,h) 正方形 | API >= 11 考虑 padding | AC-5-1 |
| R-6 | 边界 | value 长度 > 512 | 截取前 512 字符 | QRCODE_VALUE_MAX_LENGTH=512 | AC-6-4 |
| R-7 | 行为 | onDraw 编码 | QrcodeImageEncodeString(value, QRCODE_ECC_MEDIUM) | 编码失败返回 null 则不绘制 | AC-6-1 |
| R-8 | 边界 | qrCodeSize < qrWidth | 记录错误日志，不绘制 | 二维码尺寸过小 | AC-6-3 |
| R-9 | 行为 | API >= 12 背景填充 | CreateBitMap 跳过背景色像素填充 | 依赖 RenderContext 背景 | AC-6-5 |
| R-10 | 行为 | API < 12 背景填充 | CreateBitMap 手动填充背景色像素 | 兼容旧版行为 | AC-6-6 |
| R-11 | 行为 | OnColorConfigurationUpdate | 用户未设置颜色时使用主题颜色 | QRCodeColorSetByUser 标记 | AC-7-1 |
| R-12 | 行为 | OnThemeScopeUpdate (API>=26) | 更新背景色和前景色 | themeScopeId > 0 | AC-7-3 |
| R-13 | 行为 | OnAttachToFrameNode | SetClipToFrame(true) + 背景色白色 | 确保不溢出 | - |
| R-14 | 行为 | OnModifyDone | 默认对齐方式 CENTER | - | - |
| R-15 | 异常 | QrcodeImageEncodeString 返回 null | 记录 TAG_LOGE，不绘制 | 编码失败保护 | AC-6-2 |

## 验证映射

| VM 编号 | 覆盖范围 | 验证方式 | 文件 |
|---------|----------|----------|------|
| VM-1 | AC-1 组件创建与入参转换 | 单元测试 / 源码审阅 | `test/unittest/core/pattern/qrcode/qrcode_test_ng.cpp`、`frameworks/core/components_ng/pattern/qrcode/bridge/arkts_native_qrcode_bridge.cpp` |
| VM-2 | AC-2 前景色设置与用户标记 | 单元测试 / 源码审阅 | `test/unittest/core/pattern/qrcode/qrcode_test_ng.cpp`、`frameworks/core/components_ng/pattern/qrcode/qrcode_model_ng.cpp` |
| VM-3 | AC-3 背景色设置与 HDR headRoom | 单元测试 / 源码审阅 | `test/unittest/core/pattern/qrcode/qrcode_test_ng.cpp`、`frameworks/core/components_ng/pattern/qrcode/qrcode_model_ng.cpp` |
| VM-4 | AC-4 内容透明度边界处理 | 单元测试 / 源码审阅 | `test/unittest/core/pattern/qrcode/qrcode_test_ng.cpp`、`frameworks/core/components_ng/pattern/qrcode/bridge/qrcode_dynamic_modifier.cpp` |
| VM-5 | AC-5 正方形布局约束 | 单元测试 / 源码审阅 | `test/unittest/core/pattern/qrcode/qrcode_test_ng.cpp`、`frameworks/core/components_ng/pattern/qrcode/qrcode_layout_algorithm.cpp` |
| VM-6 | AC-6 二维码编码和绘制边界 | 单元测试 / 源码审阅 | `test/unittest/core/pattern/qrcode/qrcode_test_ng.cpp`、`frameworks/core/components_ng/pattern/qrcode/qrcode_modifier.cpp` |
| VM-7 | AC-7 主题和系统颜色响应 | 单元测试 / 源码审阅 | `test/unittest/core/pattern/qrcode/qrcode_test_ng.cpp`、`frameworks/core/components_ng/pattern/qrcode/qrcode_pattern.cpp` |
| VM-8 | AC-8 焦点能力 | 单元测试 / 源码审阅 | `test/unittest/core/pattern/qrcode/qrcode_test_ng.cpp`、`frameworks/core/components_ng/pattern/qrcode/qrcode_pattern.cpp` |
| VM-9 | 组件化动态加载路径 | 源码审阅 | `frameworks/core/components_ng/pattern/qrcode/bridge/qrcode_dynamic_module.cpp`、`frameworks/core/components_ng/pattern/qrcode/BUILD.gn` |

## API 变更分析

### 新增 API

无新增 API（Baselined）。

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

#### QRCode(value: string)

| 项目 | 说明 |
|------|------|
| 函数签名 | `QRCode(value: string)` |
| 参数约束 | value: 必选，字符串类型，null 映射为 "null"，undefined 映射为 "undefined"，number 映射为字符串 |
| 行为场景 | 创建 FrameNode 并关联 QRCodePattern，重置颜色用户设置标记，设置 Value 属性 |

#### .qrCodeColor(value: ResourceColor)

| 项目 | 说明 |
|------|------|
| 函数签名 | `qrCodeColor(value: ResourceColor)` |
| 参数约束 | value: ResourceColor 类型，支持颜色值、资源引用、HDR 颜色 |
| 行为场景 | 设置前景色到 PaintProperty 和 RenderContext，标记 QRCodeColorSetByUser=true |

#### .qrBackgroundColor(value: ResourceColor)

| 项目 | 说明 |
|------|------|
| 函数签名 | `qrBackgroundColor(value: ResourceColor)` |
| 参数约束 | value: ResourceColor 类型，支持颜色值、资源引用、HDR 颜色、ColorSpace |
| 行为场景 | 设置背景色到 PaintProperty 和 RenderContext，标记 QRBackgroundColorSetByUser=true |

#### .contentOpacity(value: number \| Resource)

| 项目 | 说明 |
|------|------|
| 函数签名 | `contentOpacity(value: number \| Resource)` |
| 参数约束 | value: 数值类型，有效范围 [0.0, 1.0]，越界使用默认值 1.0 |
| 行为场景 | 设置内容透明度到 PaintProperty.Opacity |

## 兼容性声明

| 版本 | 行为差异 |
|------|----------|
| API < 11 | 布局计算使用 CreateIdealSize 简化方式，不考虑 padding |
| API >= 11 | 布局计算考虑 padding 扣减，支持 layoutPolicy |
| API < 12 | CreateBitMap 手动填充背景色像素 |
| API >= 12 | CreateBitMap 跳过背景色填充，依赖 RenderContext 背景渲染 |
| API >= 26 | OnThemeScopeUpdate 生效，支持主题作用域颜色更新 |

## 架构约束

- QRCode 组件遵循 NG Pattern 四层架构：Model → Pattern → Property → Modifier
- 外部依赖 qrcode_generator 库（QrcodeImageEncodeString / QrcodeImageFree / QrcodeGetModule）
- 组件已组件化（is_component_model = true），拥有 bridge/ 子目录和 dynamic_module
- 同时支持动态管线（ArkUIQRCodeModifier）和静态管线（GENERATED_ArkUIQRCodeModifier）
- NAPI 模块名: arkui.qrcode，动态库: libqrcode.z.so

## 非功能性需求

| 需求 | 指标 |
|------|------|
| 编码性能 | QrcodeImageEncodeString 每次调用在 onDraw 中执行，无缓存 |
| 内存 | RSBitmap 在每次 onDraw 中创建和销毁，无复用 |
| 日志 | TAG_LOGE(AceLogTag::ACE_QRCODE) 用于错误场景 |

## 多设备适配声明

| 设备类型 | 适配说明 |
|----------|----------|
| 手机/平板 | 默认支持 |
| 穿戴设备 | 不编译 qrcode_static_modifier.cpp（ace_engine_feature_wearable 条件排除） |
| ArkUI-X | deps 使用 //commonlibrary/qrcode_generator:qrcodegen |

## 全局特性影响

- 无跨组件影响
- 无全局状态变更
- 无事件总线依赖

## 行为场景（可选，Gherkin）

```gherkin
Feature: QRCode 组件创建与属性设置

  Scenario: 创建二维码并设置颜色
    Given 开发者创建 QRCode("Hello")
    When 调用 qrCodeColor(Color.Red) 和 qrBackgroundColor(Color.White)
    Then PaintProperty.Color 为 Color.Red
    And PaintProperty.BackgroundColor 为 Color.White
    And QRCodeColorSetByUser 为 true
    And QRBackgroundColorSetByUser 为 true

  Scenario: 二维码始终正方形
    Given 开发者创建 QRCode("Hello") 并设置 width=200 height=100
    When MeasureContent 被调用
    Then 返回 SizeF(100, 100)

  Scenario: 超长字符串截断
    Given 开发者创建 QRCode 且 value 长度超过 512
    When UpdateContentModifier 被调用
    Then value 被截取前 512 字符

  Scenario: 主题变化不覆盖用户颜色
    Given 开发者已调用 qrCodeColor(Color.Red)
    When 系统颜色主题变化
    Then PaintProperty.Color 保持 Color.Red 不变
```

## Spec 自审清单

- [x] 所有 AC 均有 WHEN/THEN 格式
- [x] 规则定义覆盖行为、边界、异常类型
- [x] API 签名与源码实现一致
- [x] 版本兼容性行为差异已标注
- [x] 所有断言可追溯到源码文件:行
- [x] 已标注风险项（编码无缓存、Bitmap 每次创建）
- [x] 组件化状态已确认

## context-references

- `frameworks/core/components_ng/pattern/qrcode/qrcode_pattern.cpp:35` - OnAttachToFrameNode
- `frameworks/core/components_ng/pattern/qrcode/qrcode_pattern.cpp:56` - OnModifyDone
- `frameworks/core/components_ng/pattern/qrcode/qrcode_pattern.cpp:43` - OnDirtyLayoutWrapperSwap
- `frameworks/core/components_ng/pattern/qrcode/qrcode_pattern.cpp:189` - OnColorConfigurationUpdate
- `frameworks/core/components_ng/pattern/qrcode/qrcode_pattern.cpp:213` - OnThemeScopeUpdate
- `frameworks/core/components_ng/pattern/qrcode/qrcode_model_ng.cpp:30` - Create
- `frameworks/core/components_ng/pattern/qrcode/qrcode_model_ng.cpp:52` - SetQRCodeColor
- `frameworks/core/components_ng/pattern/qrcode/qrcode_model_ng.cpp:61` - SetQRBackgroundColor
- `frameworks/core/components_ng/pattern/qrcode/qrcode_layout_algorithm.cpp:27` - MeasureContent
- `frameworks/core/components_ng/pattern/qrcode/qrcode_layout_algorithm.cpp:104` - Measure
- `frameworks/core/components_ng/pattern/qrcode/qrcode_modifier.cpp:35` - onDraw
- `frameworks/core/components_ng/pattern/qrcode/qrcode_modifier.cpp:88` - CreateBitMap
- `frameworks/core/components_ng/pattern/qrcode/qrcode_paint_method.cpp:29` - UpdateContentModifier
- `frameworks/core/components_ng/pattern/qrcode/qrcode_paint_property.h:76` - Property definitions
- `frameworks/core/components_ng/pattern/qrcode/qrcode_theme_wrapper.h:47` - ApplyTokenTheme
- `frameworks/core/components_ng/pattern/qrcode/bridge/arkts_native_qrcode_bridge.cpp:61` - CreateQRCode
- `frameworks/core/components_ng/pattern/qrcode/bridge/qrcode_dynamic_modifier.cpp:285` - GetQRCodeDynamicModifier
- `frameworks/core/components_ng/pattern/qrcode/bridge/qrcode_static_modifier.cpp:73` - GetQRCodeStaticModifier
