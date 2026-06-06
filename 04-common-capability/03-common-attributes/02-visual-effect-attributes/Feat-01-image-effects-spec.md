# 特性规格

> Func-04-03-02-Feat-01 图像效果：固化 opacity、基础滤镜和模糊特效通用属性的存量行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 图像效果 (Image Effects) |
| 特性编号 | Func-04-03-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | dynamic API 7 起支持，API 11/12/18/19 有版本差异；static API 23 起支持；Native `NODE_BACKDROP_BLUR` API 15 起支持 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 图像效果存量规格 | 补录 `opacity`、基础滤镜、模糊特效的 SDK/API/实现/Native 行为 |
| ADDED | 初始设计文档 | 新建 `specs/04-common-capability/03-common-attributes/02-visual-effect-attributes/design.md` 作为本功能域 baseline |
| MODIFIED | `specs/index.md` | 将 `Feat-01 图像效果` 从 Draft 更新为 Baselined |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/02-visual-effect-attributes/design.md` | Baselined |
| SDK dynamic | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核验 |
| SDK static | `interface/sdk-js/api/arkui/component/common.static.d.ets` | 已核验 |
| ArkTS dynamic bridge | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | 已核验 |
| Framework API | `frameworks/core/components_ng/base/view_abstract.cpp` | 已核验 |
| RenderContext | `frameworks/core/components_ng/render/render_context.h`, `frameworks/core/components_ng/render/render_property.h` | 已核验 |
| Rosen adapter | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp` | 已核验 |
| Native C API | `interfaces/native/native_node.h`, `interfaces/native/node/style_modifier.cpp`, `frameworks/core/interfaces/native/node/node_common_modifier.cpp` | 已核验 |

> 需求基线、不涉及项、受影响子系统与仓库详见 design.md。本文档为存量特性补录，不提出代码修复。

## 用户故事

### US-1: 设置组件透明度

**作为** 应用开发者,  
**我想要** 通过 `opacity` 设置组件透明度,  
**以便** 控制组件及其子内容的整体 alpha 混合效果。

**验收标准：**

- **AC-1.1:** WHEN ArkTS dynamic 调用 `.opacity(value)` 且 value 可解析为 number 或 Resource THEN 属性写入 RenderContext `Opacity` 并最终在 Rosen 中更新 alpha。
- **AC-1.2:** WHEN ArkTS dynamic `opacity` 参数不可解析 THEN 写入默认透明度 `1.0`。
- **AC-1.3:** WHEN target API >= 11 且 `opacity` 数值超出 `[0,1]` THEN 数值被 clamp 到 `[0,1]`。
- **AC-1.4:** WHEN target API < 11 且 `opacity` 数值小于 `0` 或大于 `1` THEN 数值回退为 `1.0`。
- **AC-1.5:** WHEN Native public `NODE_OPACITY` 传入小于 `0` 或大于 `1` 的值 THEN `style_modifier` 返回 `ERROR_CODE_PARAM_INVALID`，不进入 common modifier 写入。
- **AC-1.6:** WHEN Native common modifier reset opacity THEN 移除 `viewAbstract.opacity` ResourceObject 并写入 `1.0f`。

### US-2: 设置基础滤镜

**作为** 应用开发者,  
**我想要** 通过 `brightness/contrast/grayscale/colorBlend/saturate/sepia/invert/hueRotate` 设置基础图像滤镜,  
**以便** 直接调整组件内容的亮度、对比度、灰度、混色、饱和度、褐色、反色和色相。

**验收标准：**

- **AC-2.1:** WHEN 设置 `brightness` THEN 属性写入 `GraphicsProperty::FrontBrightness` 并由 Rosen 调用 `SetBrightness`。
- **AC-2.2:** WHEN ArkTS dynamic `brightness` 参数不可解析 THEN 当前 JS 实现写入 `1.0`；WHEN common modifier 收到负值 THEN clamp 到 `0`。
- **AC-2.3:** WHEN 设置 `contrast` 或 `saturate` 且传入负值 THEN ArkTS dynamic/common modifier clamp 到 `0`；reset 值为 `1.0`。
- **AC-2.4:** WHEN 设置 `grayscale` THEN 数值 clamp 到 `[0,1]`；reset 值为 `0`。
- **AC-2.5:** WHEN 设置 `sepia` THEN 负值 clamp 到 `0`；reset 值为 `0`。
- **AC-2.6:** WHEN 设置 `invert(number)` THEN 数值 clamp 到 `[0,1]`；WHEN 设置 `InvertOptions` THEN `low/high/threshold/thresholdRange` 分别 clamp 到 `[0,1]` 并由 Rosen 走 `SetAiInvert`。
- **AC-2.7:** WHEN 设置 `hueRotate(number|string)` THEN 实现将角度归一化到 `[0,360)`；非法输入 reset 为 `0`。
- **AC-2.8:** WHEN `colorBlend` 为 undefined 或 target API >= 12 且颜色解析失败 THEN 写入 `Color::TRANSPARENT`；WHEN target API < 12 且解析失败 THEN return 不更新。
- **AC-2.9:** WHEN Native public 基础滤镜属性收到 `style_modifier` 定义的越界值 THEN 返回 `ERROR_CODE_PARAM_INVALID`。

### US-3: 设置内容模糊和背景模糊

**作为** 应用开发者,  
**我想要** 通过 `blur` 和 `backdropBlur` 设置内容/背景模糊,  
**以便** 区分组件自身内容模糊和组件背后内容模糊。

**验收标准：**

- **AC-3.1:** WHEN ArkTS dynamic 调用 `blur(radius, options, sysOptions)` 且 radius 可解析 THEN 使用 PX 半径写入前景模糊并更新 front blur filter。
- **AC-3.2:** WHEN ArkTS dynamic `blur` 无参数或 radius 不可解析 THEN return，不写入新值；WHEN ArkTS native bridge 解析失败 THEN 调用 resetBlur。
- **AC-3.3:** WHEN common modifier 设置 `blur` 且半径小于或等于 `0` THEN 写入 `0px`；resetBlur 也写入 `0px`。
- **AC-3.4:** WHEN ArkTS dynamic 调用 `backdropBlur` 且 radius 解析失败并 target API < 12 THEN return；WHEN target API >= 12 THEN 以默认 `0` 半径继续设置。
- **AC-3.5:** WHEN 设置 `backdropBlur` THEN 清理已有 `backgroundEffect` 和 `backgroundBlurStyle`，再更新背景模糊。
- **AC-3.6:** WHEN 设置 `blur` THEN 清理已有 `foregroundBlurStyle`，再更新前景模糊。
- **AC-3.7:** WHEN Native public `NODE_BACKDROP_BLUR` 参数数量或灰度范围非法 THEN 返回 `ERROR_CODE_PARAM_INVALID`。

### US-4: 设置渐变模糊和运动模糊

**作为** 应用开发者,  
**我想要** 通过 `linearGradientBlur` 和 `motionBlur` 设置更复杂的模糊效果,  
**以便** 实现渐变方向模糊和运动过程模糊。

**验收标准：**

- **AC-4.1:** WHEN `linearGradientBlur` 参数少于 2 个 THEN ArkTS dynamic return，不写入新值。
- **AC-4.2:** WHEN `linearGradientBlur` 的 `fractionStops` 缺失、长度不足或位置非递增 THEN 回退默认 stops `[(0,0),(0,1)]`。
- **AC-4.3:** WHEN `linearGradientBlur` 的 direction 非法 THEN 回退 `BOTTOM`；WHEN common modifier 半径为负 THEN clamp 到 `0`。
- **AC-4.4:** WHEN resetLinearGradientBlur THEN 写入 `0px + [(0,0),(0,1)] + BOTTOM`。
- **AC-4.5:** WHEN `motionBlur` 参数不是 object THEN ArkTS dynamic return；WHEN radius 解析失败或小于 `0` THEN radius 为 `0`。
- **AC-4.6:** WHEN `motionBlur.anchor.x/y` 缺失、为负或大于 `1` THEN 缺失默认 `0`，越界 clamp 到 `[0,1]`。
- **AC-4.7:** WHEN resetMotionBlur THEN radius、anchor.x、anchor.y 均写入 `0`。

### US-5: 按入口区分 API 契约

**作为** API 维护者,  
**我想要** 区分 SDK dynamic/static、ArkTS bridge、Native public `NODE_*` 与内部 common modifier 的契约,  
**以便** 下游 SDD 流程能识别公开 API 与实现入口的差异。

**验收标准：**

- **AC-5.1:** WHEN 记录外部 ArkTS API THEN 以 `interface/sdk-js/api/@internal/component/ets/common.d.ts` 和 `interface/sdk-js/api/arkui/component/common.static.d.ets` 为签名单一真源。
- **AC-5.2:** WHEN 记录 Native public API THEN 仅把 `native_node.h` 中存在的 `NODE_*` 作为公开属性。
- **AC-5.3:** WHEN 源码行为与 SDK 注释不一致 THEN 规格同时记录 SDK 契约和源码偏差风险。
- **AC-5.4:** WHEN common modifier 中存在函数表入口但 `native_node.h` 没有同级公开枚举 THEN 标记为内部 modifier 覆盖，不写成公开 C API。

## 验收追溯

| AC ID | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~AC-1.6 | BR-1, FR-1, EX-1, RC-1 | 已有实现 | 单测/源码审查 | `js_view_abstract.cpp:2198`, `node_common_modifier.cpp:2128`, `view_abstract.cpp:7511`, `rosen_render_context.cpp:2285` |
| AC-2.1~AC-2.9 | BR-2, FR-2~FR-9, EX-2~EX-5, RC-2 | 已有实现 | 单测/源码审查 | `js_view_abstract.cpp:9221`, `js_view_abstract.cpp:9241`, `js_view_abstract.cpp:9253`, `js_view_abstract.cpp:9269`, `js_view_abstract.cpp:9285`, `js_view_abstract.cpp:9301`, `js_view_abstract.cpp:9353`, `rosen_render_context.cpp:5580` |
| AC-3.1~AC-3.7 | BR-3, FR-10~FR-13, EX-6~EX-8, RC-3 | 已有实现 | 单测/源码审查 | `js_view_abstract.cpp:6124`, `js_view_abstract.cpp:6242`, `view_abstract.cpp:5101`, `view_abstract.cpp:5192`, `node_common_modifier.cpp:2196`, `node_common_modifier.cpp:2402`, `style_modifier.cpp:1017` |
| AC-4.1~AC-4.7 | BR-4, FR-14~FR-17, EX-9~EX-10, RC-4 | 已有实现 | 单测/源码审查 | `js_view_abstract.cpp:6150`, `js_view_abstract.cpp:6271`, `js_view_abstract.cpp:6308`, `node_common_modifier.cpp:2805`, `node_common_modifier.cpp:4328`, `rosen_render_context.cpp:5659`, `rosen_render_context.cpp:5327` |
| AC-5.1~AC-5.4 | BR-5, FR-18, EX-11, RC-5 | 已有实现 | SDK/C API 审查 | `common.d.ts:25580`, `common.static.d.ets:11853`, `native_node.h:365`, `native_node.h:2001`, `node_common_modifier.cpp:2223`, `node_common_modifier.cpp:2805`, `node_common_modifier.cpp:4328` |

## 业务规则

| 编号 | 规则描述 | 约束条件 | 关联 AC |
|------|----------|----------|---------|
| BR-1 | `opacity` 控制组件整体 alpha，外部契约范围为 `[0,1]` | ArkTS dynamic/static、Native public `NODE_OPACITY` | AC-1.1~AC-1.6 |
| BR-2 | 基础滤镜均为前景图像效果，最终由 Rosen 对 RSNode 设置对应滤镜属性 | 适用于 brightness/contrast/grayscale/colorBlend/saturate/sepia/invert/hueRotate | AC-2.1~AC-2.8 |
| BR-3 | `blur` 是内容/前景模糊，`backdropBlur` 是背景模糊，两者存储和更新路径不同 | 前景/背景属性分层 | AC-3.1~AC-3.7 |
| BR-4 | `linearGradientBlur` 和 `motionBlur` 属于模糊特效增强能力，参数非法时回退当前实现定义的默认值或 return | dynamic/static API，内部 common modifier | AC-4.1~AC-4.7 |
| BR-5 | 外部 API 签名以 SDK 类型定义为准，源码偏差必须记录为风险 | dynamic/static API 和 Native C API | AC-5.1~AC-5.4 |

## 功能规则

| 编号 | 规则描述 | 触发条件 | 作用对象 | 关联 AC |
|------|----------|----------|----------|---------|
| FR-1 | `opacity` 写入 RenderContext 独立 `Opacity` 属性，Rosen `OnOpacityUpdate` 更新 alpha | 设置 opacity | RenderContext/RosenRenderContext | AC-1.1 |
| FR-2 | `brightness` 写入 `FrontBrightness`，Rosen 调用 `SetBrightness` | 设置 brightness | GraphicsProperty | AC-2.1 |
| FR-3 | `contrast/saturate` reset 为 `1.0`，负值在 ArkTS 实现中 clamp 为 `0` | 设置或 reset | GraphicsProperty | AC-2.3 |
| FR-4 | `grayscale` 范围归一到 `[0,1]`，reset 为 `0` | 设置或 reset | GraphicsProperty | AC-2.4 |
| FR-5 | `sepia` 负值归一为 `0`，reset 为 `0` | 设置或 reset | GraphicsProperty | AC-2.5 |
| FR-6 | `invert` 支持 number 和 `InvertOptions`，Rosen 分别调用 `SetInvert` 或 `SetAiInvert` | 设置 invert | GraphicsProperty/RosenRenderContext | AC-2.6 |
| FR-7 | `hueRotate` 角度按 360 取模，负角度加 360 | 设置 hueRotate | GraphicsProperty | AC-2.7 |
| FR-8 | `colorBlend` reset 和 API >= 12 无效输入均写透明色 | 设置 colorBlend | GraphicsProperty | AC-2.8 |
| FR-9 | 基础滤镜在 `ViewAbstract` 入口写入 `GraphicsProperty` | 任一基础滤镜变更 | RenderContext | AC-2.1~AC-2.8 |
| FR-10 | `blur` 写入前景模糊半径和 sysOptions，并更新 front blur filter | 设置 blur | ForegroundProperty/RosenRenderContext | AC-3.1~AC-3.3 |
| FR-11 | `backdropBlur` 写入背景模糊半径和 sysOptions，并更新 back blur filter | 设置 backdropBlur | BackgroundProperty/RosenRenderContext | AC-3.4~AC-3.7 |
| FR-12 | 设置 `backdropBlur` 会清理 `backgroundEffect` 和 `backgroundBlurStyle` | 设置 backdropBlur | RenderContext | AC-3.5 |
| FR-13 | 设置 `blur` 会清理 `foregroundBlurStyle` | 设置 blur | RenderContext | AC-3.6 |
| FR-14 | `linearGradientBlur` 使用半径、fractionStops 和 direction 构造 `LinearGradientBlurPara` | 设置 linearGradientBlur | GraphicsProperty/RosenRenderContext | AC-4.1~AC-4.4 |
| FR-15 | `motionBlur` 使用 radius 与 anchor 构造 `MotionBlurOption` | 设置 motionBlur | ForegroundProperty/RosenRenderContext | AC-4.5~AC-4.7 |
| FR-16 | Native public `style_modifier` 在进入 common modifier 前执行参数校验 | Native `NODE_*` 设置 | C API 入口 | AC-1.5, AC-2.9, AC-3.7 |
| FR-17 | Native common modifier reset 使用具体无效果值恢复属性 | reset common modifier | ViewAbstract/RenderContext | AC-1.6, AC-3.3, AC-4.4, AC-4.7 |
| FR-18 | 未在 `native_node.h` 找到的内部 common modifier 能力不得写成公开 C API | 文档补录 | API 规格 | AC-5.2, AC-5.4 |

## 异常/豁免规则

| 编号 | 规则描述 | 触发条件 | 处理结果 | 关联 AC |
|------|----------|----------|----------|---------|
| EX-1 | opacity 越界版本差异 | target API >= 11 或 < 11 | >= 11 clamp；< 11 回退 `1.0` | AC-1.3, AC-1.4 |
| EX-2 | brightness dynamic SDK 与 JS 实现差异 | `brightness(undefined)` 或不可解析 | SDK Optional 注释称 reset 到 `0`；当前 JS 实现解析失败写 `1.0` | AC-2.2, AC-5.3 |
| EX-3 | grayscale 越界 | 值小于 `0` 或大于等于/大于 `1` | ArkTS clamp 到 `[0,1]`；Native public 入口返回错误码 | AC-2.4, AC-2.9 |
| EX-4 | colorBlend 解析失败版本差异 | target API >= 12 或 < 12 | >= 12 写透明；< 12 return | AC-2.8 |
| EX-5 | Native public 基础滤镜越界 | `style_modifier` 判定非法 | 返回 `ERROR_CODE_PARAM_INVALID` | AC-2.9 |
| EX-6 | blur 参数缺失或不可解析 | ArkTS dynamic `blur` | return，不写入新值 | AC-3.2 |
| EX-7 | backdropBlur 参数不可解析版本差异 | target API >= 12 或 < 12 | >= 12 以 0 继续；< 12 return | AC-3.4 |
| EX-8 | Native public backdropBlur 非法 | 参数个数不在 1~3 或灰度不在 `[0,127]` | 返回 `ERROR_CODE_PARAM_INVALID` | AC-3.7 |
| EX-9 | linearGradientBlur stops 非法 | stops 不足或位置非递增 | 回退默认 stops `[(0,0),(0,1)]` | AC-4.2 |
| EX-10 | motionBlur 参数非法 | 非 object 或半径/anchor 越界 | 非 object return；半径为 0；anchor clamp | AC-4.5, AC-4.6 |
| EX-11 | 公开 C API 未覆盖全部内部 modifier | `native_node.h` 未找到同级枚举 | 规格标注为内部 modifier 覆盖，不作为 Public C API | AC-5.4 |

## 恢复契约

| 编号 | 触发条件 | 恢复策略 | 恢复结果 | 约束 |
|------|----------|----------|----------|------|
| RC-1 | opacity reset 或解析失败 | 写入 `1.0`，资源对象路径移除 `viewAbstract.opacity` | 组件恢复完全不透明 | API < 11 越界同样回 `1.0` |
| RC-2 | 基础滤镜 reset | 按无效果值恢复：brightness/contrast/saturate=`1`，grayscale/sepia/invert/hueRotate=`0`，colorBlend=透明 | 组件恢复无对应滤镜效果 | `brightness(undefined)` SDK/JS 差异单独标注 |
| RC-3 | blur/backdropBlur reset | 写入 `0px` 半径和默认 `BlurOption` | 前景/背景模糊关闭 | backdropBlur 仍执行互斥清理路径 |
| RC-4 | linearGradientBlur/motionBlur reset | linearGradientBlur 写 `0px + 默认 stops + BOTTOM`；motionBlur 写 radius/x/y 为 `0` | 特效关闭 | 内部 common modifier 路径 |
| RC-5 | Native public 参数非法 | 返回错误码，不进入属性写入 | 现有属性不被本次非法调用更新 | 仅适用于 `style_modifier` 公开入口 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.6 | 单测/C API 单测/源码审查 | opacity 版本分支、Resource reset、Rosen alpha 更新 |
| VM-2 | AC-2.1~AC-2.9 | 单测/C API 单测/SDK 审查 | 基础滤镜默认值、clamp、错误码、SDK 偏差 |
| VM-3 | AC-3.1~AC-3.7 | 单测/集成/XTS | blur/backdropBlur 前景背景分层和互斥清理 |
| VM-4 | AC-4.1~AC-4.7 | 单测/源码审查 | linearGradientBlur stops/direction 默认值，motionBlur anchor/radius 归一 |
| VM-5 | AC-5.1~AC-5.4 | SDK/C API 审查 | dynamic/static/C API 公开面和内部 modifier 区分 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `opacity` | Public ArkTS / Public C API | 设置组件整体透明度 | AC-1.1~AC-1.6 |
| `brightness` | Public ArkTS / Public C API | 设置亮度滤镜 | AC-2.1, AC-2.2, AC-2.9 |
| `contrast` | Public ArkTS / Public C API | 设置对比度滤镜 | AC-2.3, AC-2.9 |
| `grayscale` / `NODE_GRAY_SCALE` | Public ArkTS / Public C API | 设置灰度滤镜 | AC-2.4, AC-2.9 |
| `colorBlend` | Public ArkTS / Public C API | 设置混色滤镜 | AC-2.8, AC-2.9 |
| `saturate` / `NODE_SATURATION` | Public ArkTS / Public C API | 设置饱和度滤镜 | AC-2.3, AC-2.9 |
| `sepia` | Public ArkTS / Public C API | 设置褐色滤镜 | AC-2.5, AC-2.9 |
| `invert` | Public ArkTS / Public C API | 设置反色滤镜 | AC-2.6, AC-2.9 |
| `hueRotate` | Public ArkTS / Internal Native modifier | 设置色相旋转 | AC-2.7, AC-5.4 |
| `blur` | Public ArkTS / Public C API | 设置内容/前景模糊 | AC-3.1~AC-3.3 |
| `backdropBlur` / `NODE_BACKDROP_BLUR` | Public ArkTS / Public C API | 设置背景模糊 | AC-3.4~AC-3.7 |
| `linearGradientBlur` | Public ArkTS / Internal Native modifier | 设置线性渐变模糊 | AC-4.1~AC-4.4, AC-5.4 |
| `motionBlur` | Public ArkTS / Internal Native modifier | 设置运动模糊 | AC-4.5~AC-4.7, AC-5.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| `opacity` dynamic | 变更 | API 18 增加 `Optional<number \| Resource>` 重载；源码 target API 11 有越界处理差异，关联 AC-1.3, AC-1.4 |
| `blur` / `backdropBlur` dynamic | 变更 | API 18 增加 Optional 重载，API 19 增加 `SystemAdaptiveOptions` 重载，关联 AC-3.1~AC-3.4 |
| `linearGradientBlur` / `motionBlur` dynamic | 变更 | API 18 增加 Optional 重载，关联 AC-4.1~AC-4.7 |
| `brightness/contrast/grayscale/colorBlend/saturate/sepia/invert/hueRotate` dynamic | 变更 | API 18 增加 Optional 重载，关联 AC-2.1~AC-2.8 |
| static common attributes | 变更 | API 23 static 引入对应签名，关联 AC-5.1 |
| 废弃 API | 废弃 | 无废弃 API |

## 兼容性声明

- **已有 API 行为变更:** 是。存量实现已存在版本差异：`opacity` target API 11 前后越界行为不同；`colorBlend` target API 12 前后无效颜色行为不同；`backdropBlur` target API 12 前后不可解析半径行为不同；dynamic API 18/19 增加 Optional/SystemAdaptiveOptions 重载；static API 23 提供静态签名。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。仍使用 RenderContext 独立 `Opacity`、`GraphicsProperty`、`ForegroundProperty`、`BackgroundProperty`。
- **最低支持版本:** dynamic API 7；ArkTS widgets/form 能力按 SDK 标注从 API 9/10/11 扩展；Native `NODE_BACKDROP_BLUR` API 15；static API 23。
- **API 版本号策略:** 外部 ArkTS 签名以 `interface/sdk-js/api/@internal/component/ets/common.d.ts` 和 `interface/sdk-js/api/arkui/component/common.static.d.ets` 的 `@since` 为准；源码版本分支以 `JSViewAbstract`/`node_common_modifier` 实际 target API 判断为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 单一真源 | 外部 ArkTS API 签名、参数类型、`@since` 以 SDK 类型定义为准 | AC-5.1, AC-5.3 |
| RenderContext 分层 | 图像效果不写 LayoutProperty；按透明度、图形属性、前景属性、背景属性分层 | AC-1.1, AC-2.1, AC-3.1, AC-3.4, AC-4.1 |
| 互斥清理 | `backdropBlur` 与 backgroundEffect/backgroundBlurStyle 互斥，`blur` 与 foregroundBlurStyle 互斥 | AC-3.5, AC-3.6 |
| Native 错误码 | Public Native `NODE_*` 属性入口必须保留 `style_modifier` 错误码行为 | AC-1.5, AC-2.9, AC-3.7 |
| 内部/公开 API 区分 | common modifier 函数表不自动等同于公开 `NODE_*` 属性 | AC-5.2, AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 图像效果属性不触发 Measure/Layout；仅更新渲染属性或 filter | 单测/源码审查 | `view_abstract.cpp:5809`, `render_property.h:227`, `rosen_render_context.cpp:5580` |
| 内存 | ResourceObject 仅在 opacity/colorBlend 资源路径持有，reset 移除对应资源对象 | 单测/源码审查 | `node_common_modifier.cpp:2128`, `node_common_modifier.cpp:2306` |
| 安全 | 无额外权限；Native public 非法参数返回错误码 | C API 单测 | `style_modifier.cpp:1017`, `style_modifier.cpp:2244` |
| 可靠性 | reset 使用确定的无效果值恢复 | 单测 | `node_common_modifier.cpp:2154`, `node_common_modifier.cpp:2213`, `node_common_modifier.cpp:2394`, `node_common_modifier.cpp:2419` |
| 问题定位 | SDK/源码偏差在风险表中显式记录 | 文档审查 | design.md 风险表 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 图像效果不改变语义树；透明度可能影响可视性但不改变 accessibility node | US-1 |
| 大字体 | 否 | 不参与字体度量和布局 | US-2 |
| 深色模式 | 间接 | `invert`、`colorBlend`、`backdropBlur` 视觉结果可能随背景变化；本规格仅固化属性管线 | US-2, US-3 |
| 多窗口/分屏 | 否 | 无窗口尺寸相关布局计算；`SystemAdaptiveOptions` 仅传递系统自适应选项 | US-3 |
| 多用户 | 否 | 无用户级持久化状态 | 全部 |
| 版本升级 | 是 | 需关注 API 11/12/18/19/23/15 差异 | US-1~US-5 |
| 生态兼容 | 是 | Native public `NODE_*` 与 ArkTS API 覆盖不完全一致 | US-5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 图像效果通用属性
  作为 ArkUI 应用开发者
  我想要设置透明度、基础滤镜和模糊特效
  以便控制组件的最终视觉效果

  Scenario: opacity 在 API 11 及以上 clamp 越界值
    Given target API 大于等于 11
    When 调用 opacity(-0.5)
    Then RenderContext Opacity 写入 0
    And Rosen alpha 使用 0

  Scenario: opacity 在 API 11 以下回退非法值
    Given target API 小于 11
    When 调用 opacity(2.0)
    Then RenderContext Opacity 写入 1.0

  Scenario: 基础滤镜 reset 为无效果值
    Given 组件已设置 brightness、contrast、grayscale、invert、colorBlend
    When 通过 common modifier reset 对应属性
    Then brightness 和 contrast 恢复为 1
    And grayscale 和 invert 恢复为 0
    And colorBlend 恢复为透明色

  Scenario: backdropBlur 清理样式类背景效果
    Given RenderContext 已存在 backgroundEffect 或 backgroundBlurStyle
    When 调用 backdropBlur(20)
    Then backgroundEffect 被清理
    And backgroundBlurStyle 被清理
    And BackgroundProperty 写入 20px 背景模糊半径

  Scenario: linearGradientBlur 使用默认 stops
    Given fractionStops 缺失或位置非递增
    When 调用 linearGradientBlur(10, options)
    Then fractionStops 回退为 [(0,0),(0,1)]
    And 非法 direction 回退为 BOTTOM

  Scenario: Native public 属性拒绝非法参数
    Given ArkUI_NodeHandle 有效
    When 设置 NODE_OPACITY 为 -0.1
    Then style_modifier 返回 ERROR_CODE_PARAM_INVALID
    And common modifier 不写入新 opacity
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/foundation_arkui_ace_engine"
    query: "opacity brightness contrast grayscale colorBlend saturate sepia invert hueRotate blur backdropBlur linearGradientBlur motionBlur JSViewAbstract ViewAbstract RenderContext"
  - repo: "OpenHarmony/interface_sdk-js"
    query: "CommonMethod image effect attributes common.d.ts common.static.d.ets"
```

**关键文档：**

- `specs/04-common-capability/03-common-attributes/02-visual-effect-attributes/design.md`
- `interface/sdk-js/api/@internal/component/ets/common.d.ts`
- `interface/sdk-js/api/arkui/component/common.static.d.ets`
- `interfaces/native/native_node.h`
