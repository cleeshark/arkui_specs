# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 独立文本测量能力 |
| 特性编号 | Func-04-13-02-Feat-01 |
| 所属 Epic | 字体文本 - 文本测量 |
| 优先级 | P1 |
| 目标版本 | API 9 起动态版;API 12 起 UIContext.MeasureUtils;API 18 起模块级废弃;API 23 起静态版 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本特性规格覆盖"脱离组件的纯文本测量"能力,即不依赖任何 Text/TextField/RichEditor 组件实例、直接对一段文本 + 一组样式参数返回宽度/高度的 API 集合。组件级排版测量(段落级 `MeasureUtils.getParagraphs`)与组件级行级度量查询(`LayoutManager`)分别由 Feat-02、Feat-03 承接,不在本规格范围内。

## 本次变更范围（Delta）

> lineage: new-on-legacy — 本特性为已实现能力的补录,无新需求引入。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `@ohos.measure.MeasureText.measureText/measureTextSize` 规格 | 模块级测量 API,动态版 since 9/10,deprecated since 18 |
| ADDED | `UIContext.getMeasureUtils()` + `MeasureUtils.measureText/measureTextSize` 规格 | UI 上下文绑定测量 API,since 12,推荐替代 |
| ADDED | 静态 ArkTS `@ohos.measure.MeasureText.measureText/measureTextSize` 规格 | 静态版 since 23 static,未标 deprecated |
| ADDED | 内核 `MeasureUtil`/`MeasureContext`/`RosenFontCollection` 桥接规格 | 框架内部实现契约 |

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| 设计文档 | `specs/04-common-capability/13-font-text/02-text-measurement/design.md` |
| SDK 类型定义(动态) | `interface/sdk-js/api/@ohos.measure.d.ts`、`interface/sdk-js/api/@ohos.arkui.UIContext.d.ts` |
| SDK 类型定义(静态) | `interface/sdk-js/api/@ohos.measure.static.d.ets`、`interface/sdk-js/api/@ohos.arkui.UIContext.static.d.ets` |
| NAPI 实现 | `interfaces/napi/kits/measure/js_measure.cpp`、`measure.js`、`BUILD.gn` |
| 框架内核实现 | `frameworks/base/utils/measure_util.h`、`frameworks/base/utils/measure_util.cpp` |
| 委托实现 | `frameworks/bridge/declarative_frontend/ng/frontend_delegate_declarative_ng.cpp` |
| 字体集合共享 | `frameworks/core/components/font/rosen_font_collection.h`、`frameworks/core/components_ng/render/adapter/txt_font_collection.cpp` |
| 静态 ANI 桥 | `frameworks/core/interfaces/native/implementation/global_scope_ohos_measure_utils_accessor.cpp` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md,本文档不重复摘录。design.md 与本文档并行产出,互不依赖。

## 用户故事

### US-1: 测量单行文本宽度

**As a** 应用开发者
**I want** 给定一段文本与字体样式参数,获得其单行显示宽度(px)
**So that** 在不实例化 Text 组件的前提下预计算布局尺寸(如计算 Dialog 宽度、自适应 padding)

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 `MeasureText.measureText({textContent:"Hello", fontSize:16})` THEN 返回 `number`,值为以 16fp 字号渲染 "Hello" 的单行实际宽度向上取整(px),且不受 `constraintWidth`/`maxLines`/`textAlign`/`overflow` 等布局参数影响 | 正常 |
| AC-1.2 | WHEN `textContent` 含换行符 `\n`(多段)THEN 返回值为最长一行的单行宽度(px),而非各行宽度之和 | 正常 |
| AC-1.3 | WHEN `textContent` 为空字符串 THEN 返回 `0`(空段落 `GetActualWidth()` 为 0,`ceil(0)=0`) | 边界 |
| AC-1.4 | WHEN 入参为非对象类型(如 `measureText("Hello")` 传字符串,或 `measureText(undefined)`)THEN 返回 `null`/`undefined`,不抛异常、无错误码 | 异常 |
| AC-1.5 | WHEN `fontSize` 缺省 THEN 回退至当前 Pipeline 主题 `TextTheme::GetTextStyle().GetFontSize()` 的 px 值;若 Pipeline 不可得则 `MeasureTextInner` 经 `CHECK_NULL_RETURN` 返回 `0.0` | 边界 |
| AC-1.6 | WHEN 目标 API 版本 < 12 且 `fontSize` 以裸数字传入(无单位后缀)THEN 该数字按 VP 单位参与测量;WHEN 目标 API ≥ 12 THEN 同一裸数字按 FP 单位参与测量 | 正常 |
| AC-1.7 | WHEN 调用 `UIContext.getMeasureUtils().measureText(options)` THEN 行为与 `MeasureText.measureText(options)` 完全一致(同一 `MeasureUtil::MeasureText` 内核),且不受 `@deprecated since 18` 影响 | 正常 |
| AC-1.8 | WHEN 调用静态 ArkTS `MeasureText.measureText(options)` THEN 返回 `double`(而非动态版 `number`),数值与动态版一致;静态版未标 deprecated | 正常 |

### US-2: 测量受布局约束的文本宽高

**As a** 应用开发者
**I want** 给定文本 + 样式 + 布局约束(最大宽度、最大行数、对齐、溢出、行高、首行缩进等),获得文本实际占用的宽高(px)
**So that** 在固定宽度容器内预估文本块尺寸、判断是否会触发截断

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `measureTextSize({textContent, fontSize, constraintWidth:200})` 且文本在 200px 内可多行排布 THEN 返回 `{width, height}`(均为 px),其中 `height` 为段落 `GetHeight() + |baselineOffset|` 的结果 | 正常 |
| AC-2.2 | WHEN `constraintWidth` 已设 THEN 返回的 `width` **恒等于** `constraintWidth` 的 px 值(即返回约束宽度本身,而非文本实际宽度);WHEN 未设 `constraintWidth` THEN `width` 为 `ceil(min(maxWidth, max(actualWidth, maxIntrinsicWidth)))`(单行取 max 避免尾随空白被裁剪) | 正常 |
| AC-2.3 | WHEN 段落为单行且 `isReturnActualWidth=false`(公开 API 路径)THEN `width` 取 `max(actualWidth, maxIntrinsicWidth)` 后再 clamp 到 `GetMaxWidth()`;WHEN 多行 THEN `width = GetActualWidth()` | 正常 |
| AC-2.4 | WHEN `maxLines` 设为正整数 THEN 段落最多排布该行数,超出部分依 `overflow` 处理(`TextOverflow.ELLIPSIS` 时追加省略号 `…`);WHEN `maxLines=0` 或缺省 THEN 不设 maxLines,按无限行排布 | 正常 |
| AC-2.5 | WHEN `overflow !== TextOverflow.ELLIPSIS`(默认 CLIP)THEN 不向 TypographyStyle 设省略号;WHEN `overflow === ELLIPSIS` THEN 设 `style.ellipsis = u"\u2026"` | 正常 |
| AC-2.6 | WHEN `baselineOffset` 缺省 THEN `height = GetHeight()`;WHEN 设为正值或负值 THEN `height = GetHeight() + |baselineOffset|`(`fabs` 取绝对值,负偏移仍增大返回高度) | 边界 |
| AC-2.7 | WHEN `lineHeight` 为数值类型且与 `fontSize` 不等、大于 0、`fontSize` 非近零 THEN `heightScale = lineHeight.px / fontSize.px`;WHEN `lineHeight` 为百分数 THEN `heightScale = lineHeight.Value()`(直接作倍率,1.5=150%);WHEN `lineHeight ≈ fontSize` 或 ≤ 0 THEN 依 API 6 版本门控决定 `heightOnly` 是否生效 | 边界 |
| AC-2.8 | WHEN `textIndent` 为正值 THEN 仅首行缩进该 px;WHEN `textIndent ≤ 0` THEN 不生效;WHEN `textIndent` 为百分数且 `constraintWidth` 未设 THEN 不生效(返回 false) | 边界 |
| AC-2.9 | WHEN `wordBreak` 缺省 THEN 默认 `WordBreak.BREAK_WORD`;WHEN 传 `BREAK_ALL` + `overflow=ELLIPSIS` + `maxLines` THEN 可在字母间断行并显示省略号 | 正常 |
| AC-2.10 | WHEN `textCase` 设为非 `NORMAL` THEN 测量前对 `textContent` 调用 `StringUtils::TransformStrCase` 变换大小写后再排版,故返回宽高反映变换后文本 | 正常 |
| AC-2.11 | WHEN 入参非对象 THEN 返回 `null`,不抛异常 | 异常 |

### US-3: 从废弃 API 迁移到 UI 上下文绑定 API

**As a** 应用维护者
**I want** 将基于 `@ohos.measure.MeasureText.measureText/measureTextSize`(deprecated since 18)的存量代码迁移至 `UIContext.getMeasureUtils().measureText/measureTextSize`
**So that** 获得与 UI 上下文正确绑定的测量结果,避免模块级 API 在多窗口/多实例场景下的上下文错配

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 在 API ≥ 18 设备上调用模块级 `MeasureText.measureText` THEN 函数仍可正常返回结果(运行时未禁用),仅 IDE/类型层提示 deprecated | 正常 |
| AC-3.2 | WHEN 应用从模块级 API 迁移至 `UIContext.getMeasureUtils().measureText` THEN 返回值数值一致(同一 `MeasureUtil::MeasureText` 内核,同一共享 `Rosen::FontCollection`) | 正常 |
| AC-3.3 | WHEN 在 ArkTS 静态前端(since 23 static)调用 `MeasureText.measureText` THEN 该静态 API 未标 deprecated,无需迁移;返回类型为 `double` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1, R-5 | TASK-01 | 单测:固定文本+字号,断言返回值为预期 px 且布局参数不影响 | `measure_util.cpp:129-175` |
| AC-1.2 | R-1 | TASK-01 | 单测:`textContent` 含 `\n`,断言返回最长行宽 | `measure_util.cpp:168, 174` (`GetActualWidth` 取最长行) |
| AC-1.3 | R-3 | TASK-01 | 单测:空 `textContent`,断言返回 0 | `measure_util.cpp:168-174` |
| AC-1.4 | R-9 | TASK-01 | 单测:非对象入参,断言返回 null 无异常 | `js_measure.cpp:207` |
| AC-1.5 | R-4 | TASK-01 | 单测:缺省 fontSize + mock Pipeline,断言回退主题字号;mock null Pipeline 断言返回 0.0 | `measure_util.cpp:145-148` |
| AC-1.6 | R-7 | TASK-01 | 单测:目标 API 11 vs 12,同裸数字 fontSize 断言单位不同致结果不同 | `frontend_delegate_declarative_ng.cpp:676-683` |
| AC-1.7 | R-2 | TASK-01 | 单测:同 options 经 `getMeasureUtils().measureText` 与模块级 API 断言数值一致 | `frontend_delegate_declarative_ng.cpp:682` |
| AC-1.8 | R-2 | TASK-01 | 静态前端集成测:断言返回 `double` 且数值与动态版一致 | `global_scope_ohos_measure_utils_accessor.cpp:181-205` |
| AC-2.1 | R-6 | TASK-01 | 单测:`measureTextSize` 带 `constraintWidth`,断言 height 含 baselineOffset | `measure_util.cpp:219-229` |
| AC-2.2 | R-6 | TASK-01 | 单测:设/不设 `constraintWidth` 两组,断言 width 取约束本身 vs ceil 实际宽 | `measure_util.cpp:210-217` |
| AC-2.3 | R-6 | TASK-01 | 单测:单行 vs 多行,断言 width 取 max vs actualWidth | `measure_util.cpp:210-214` |
| AC-2.4 | R-6 | TASK-01 | 单测:不同 maxLines,断言行数与省略号 | `measure_util.cpp:188-193` |
| AC-2.5 | R-6 | TASK-01 | 单测:`overflow=ELLIPSIS` vs `CLIP`,断言省略号设置 | `measure_util.cpp:188-190` |
| AC-2.6 | R-6 | TASK-01 | 单测:正/负/缺省 baselineOffset,断言 height 公式 | `measure_util.cpp:219-223` |
| AC-2.7 | R-6 | TASK-01 | 单测:数值/百分数/≈fontSize/≤0 四组 lineHeight | `measure_util.cpp:36-51, 98-105` |
| AC-2.8 | R-6 | TASK-01 | 单测:正/负/百分数+有无 constraintWidth 的 textIndent | `measure_util.cpp:53-67, 109-127` |
| AC-2.9 | R-6 | TASK-01 | 单测:BREAK_WORD vs BREAK_ALL + ellipsis + maxLines | `measure_util.cpp:194` |
| AC-2.10 | R-6 | TASK-01 | 单测:UPPERCASE/LOWERCASE textCase 断言宽高变化 | `measure_util.cpp:200-202` |
| AC-2.11 | R-9 | TASK-01 | 单测:非对象入参,断言返回 null 无异常 | `js_measure.cpp:340` |
| AC-3.1 | R-10 | TASK-01 | 集成测:API 18 设备调用模块级 API 断言正常返回 | `@ohos.measure.d.ts:294-295`(仅类型层 deprecated) |
| AC-3.2 | R-2 | TASK-01 | 集成测:同 options 走两路径断言数值一致 | `frontend_delegate_declarative_ng.cpp:682` |
| AC-3.3 | R-10 | TASK-01 | 静态前端测:断言静态 API 未 deprecated 且返回 double | `@ohos.measure.static.d.ets:202-213` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `measureText(options)`,options 为对象,含 `textContent` 与可选样式参数 | NAPI 解析 6 个属性(textContent/fontSize/fontStyle/fontWeight/fontFamily/letterSpacing)→ `MeasureContext` → 委托 → `MeasureTextInner` 构建一次性 `Rosen::Typography`,以 `Size::INFINITE_SIZE` 调 `Layout`,返回 `ceil(GetActualWidth())` | 仅这 6 个属性被 NAPI 解析;`TypographyStyle` 仅设 `locale`;布局类参数(constraintWidth/maxLines/textAlign/overflow/lineHeight/baselineOffset/textCase/textIndent/wordBreak)被静默忽略 | AC-1.1, AC-1.2 |
| R-2 | 行为 | 调用 `UIContext.getMeasureUtils().measureText(options)` 或静态 `MeasureText.measureText(options)` | 动态 UIContext 路径经委托 `FrontendDelegateDeclarativeNG::MeasureText` → `MeasureUtil::MeasureText`;静态路径经 ANI 桥 `global_scope_ohos_measure_utils_accessor.cpp::MeasureTextImpl` → 同一 `MeasureUtil::MeasureText`。返回数值与模块级 API 一致 | 静态版返回 `double`,动态版返回 `number`;静态版未标 deprecated | AC-1.7, AC-1.8, AC-3.2 |
| R-3 | 边界 | `textContent` 为空字符串 | 构建空段落,`GetActualWidth()` 返回 0,`ceil(0)=0`;`measureText` 返回 0,无异常 | 不早退、不报错 | AC-1.3 |
| R-4 | 边界 | `fontSize` 缺省(undefined/nullopt) | `prepareTextStyleForMeasure`/`MeasureTextInner` 经 `PipelineContext::GetCurrentContextSafelyWithCheck` 取 `TextTheme::GetTextStyle().GetFontSize().ConvertToPx()`;Pipeline 不可得时 `MeasureTextInner` 返回 0.0,`prepareTextStyleForMeasure` 返回部分填充的 txtStyle | 主题字号缺省值 16fp(SDK 文档声明) | AC-1.5 |
| R-5 | 边界 | `measureText` 入参对象中同时传入 `constraintWidth`/`maxLines`/`textAlign`/`overflow`/`lineHeight`/`baselineOffset`/`textCase`/`textIndent`/`wordBreak` | 这些字段对 `measureText` 的返回值**无影响**(`JSMeasureText` 仅解析 6 属性,其余留在 `MeasureContext` 默认值;`MeasureTextInner` 不读取它们) | SDK JSDoc 明示:"measureText always measures single-line text width. Layout constraints in options do not affect results." | AC-1.1 |
| R-6 | 行为 | 调用 `measureTextSize(options)`,options 为对象,含任意 `MeasureOptions` 字段子集 | `JSMeasureTextSize` 解析全部 15 字段(wordBreak 经 `napi_has_named_property` 兼容性检查)→ `SetContextProperty` → `MeasureTextSizeInner`:构建 TypographyStyle(设 textAlign/ellipsis/maxLines/wordBreakType/locale)→ `prepareTextStyleForMeasure`(设 fontSize/fontStyle/fontWeight/letterSpacing/lineHeight)→ `TransformStrCase` 应用 textCase → `AppendText` → `CreateTypography` → `prepareParagraphForMeasure`(textIndent + Layout)→ 计算 width/height | 设 constraintWidth 时 width 恒等于其 px 值;baselineOffset 经 `fabs` 加入 height;lineHeight 百分比直作倍率;textIndent 需正值且(若百分数)需 constraintWidth | AC-2.1 至 AC-2.10 |
| R-7 | 边界 | 目标 API 版本 < 12 且 `fontSize` 以裸数字(number 无单位后缀)传入 | NAPI 层 `HandleDimensionType` 将裸数字按 FP 解析并置 `isFontSizeUseDefaultUnit=true`;委托层检测此 flag,将单位改写为 VP(`Dimension(value, DimensionUnit::VP)`),再调 `MeasureUtil::MeasureText` | `AceApplicationInfo::GreatOrEqualTargetAPIVersion(PlatformVersion::VERSION_TWELVE)` 为门控;API ≥ 12 保留 FP 不改写 | AC-1.6 |
| R-8 | 边界 | `MeasureUtil::MeasureText/MeasureTextSize` 调用时 `SystemProperties::GetRosenBackendEnabled()` 为 false,或编译期未定义 `ENABLE_ROSEN_BACKEND` | `MeasureText` 返回 `0.0`;`MeasureTextSize` 返回 `Size(0.0, 0.0)`;无日志告警 | 无 Rosen 后端时测量结果恒为 0 | (隐含约束,无独立 AC) |
| R-9 | 异常 | 入参为非对象类型(string/number/undefined/null/boolean/function) | `JSMeasureText`/`JSMeasureTextSize` 经 `napi_typeof` 判定非 `napi_object` 后 `return nullptr`,JS 侧收到 `null`/`undefined` | 不抛 BusinessError、无错误码、无日志 | AC-1.4, AC-2.11 |
| R-10 | 恢复 | API ≥ 18 调用模块级 `MeasureText.measureText/measureTextSize`(SDK 标 `@deprecated since 18`) | 运行时仍正常执行(类型层 deprecated 不影响运行时),返回值与 API < 18 一致;迁移至 `UIContext.getMeasureUtils().measureText/measureTextSize` 后数值不变 | 静态 `.d.ets`(since 23)未标 deprecated,无需迁移 | AC-3.1, AC-3.2, AC-3.3 |
| R-11 | 行为 | `RosenFontCollection::GetInstance().GetFontCollection()` 返回 null | `MeasureTextInner`/`MeasureTextSizeInner` 记 `LOGW`/`TAG_LOGW` 后返回 `0.0`/`Size(0.0, 0.0)` | 字体集合初始化失败时测量结果为 0 | (隐含约束) |
| R-12 | 边界 | 字体已注册但未加载完成时调用 `measureText` | standalone `MeasureUtil` **不注册**字体加载回调,不自动重跑;首次测量可能用回退字体;字体加载完成后的**后续调用**会读到已被变异的共享 `Rosen::FontCollection`(与 NG 组件共用同一实例),返回正确值 | NG 组件经 `RegisterCallbackNG` 触发 `MarkDirtyNode(MEASURE)` 自动重测;standalone API 无此机制 | (字体加载时序,跨 Feat-01 与 Feat-02 的共享约束) |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|---------|
| VM-1 | R-1, R-5(measureText 单行语义 + 忽略布局参数) | 单测 + SDK JSDoc 比对 | 6 属性解析集;布局参数注入后返回值不变 |
| VM-2 | R-2(三入口同内核) | 单测:模块级 vs UIContext vs 静态,同 options 断言一致 | 委托与 ANI 桥均落到 `MeasureUtil::MeasureText` |
| VM-3 | R-3, R-4(空文本/缺省 fontSize) | 单测 + mock Pipeline | 边界返回 0 与主题字号回退 |
| VM-4 | R-6(measureTextSize 全字段) | 参数化单测 | constraintWidth/maxLines/overflow/baselineOffset/lineHeight/textIndent/wordBreak/textCase 各组合 |
| VM-5 | R-7(API 12 单位修正) | 单测:API 11 vs 12 同裸数字 fontSize | 单位 VP→FP 切换导致结果差异 |
| VM-6 | R-9(非对象入参) | 单测:5 种非对象类型 | 返回 null 无异常无错误码 |
| VM-7 | R-10(deprecated 迁移) | 集成测:API 18 设备 + 静态前端 | 运行时未禁用;静态未 deprecated |
| VM-8 | R-11, R-12(字体集合 null / 未加载) | mock 测:fontCollection 返回 null;先测后加载字体再测 | 0.0 兜底;后续调用读到新字体 |

## API 变更分析

> 本特性为已实现能力补录,API 均为存量。下表为存量 API 清单与废弃迁移分析,供 SDD 后续变更参考。

### 新增 API

> N/A — 本特性不新增 API,仅补录存量 API 规格。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `@ohos.measure.MeasureText.measureText(options): number` | 废弃(deprecated since 18,动态版) | 单行文本宽度测量 | 改用 `UIContext.getMeasureUtils().measureText(options): number`(`@useinstead ohos.arkui.UIContext.MeasureUtils#measureText`) | AC-3.1, AC-3.2 |
| `@ohos.measure.MeasureText.measureTextSize(options): SizeOptions` | 废弃(deprecated since 18,动态版) | 受约束文本宽高测量 | 改用 `UIContext.getMeasureUtils().measureTextSize(options): SizeOptions` | AC-3.1, AC-3.2 |

> 静态版 `@ohos.measure.MeasureText.measureText/measureTextSize`(`@ohos.measure.static.d.ets`,since 23 static)**未**标 `@deprecated`,无需迁移。`UIContext.MeasureUtils.measureText/measureTextSize`(since 12)与模块级 API 数值完全一致(同一 `MeasureUtil` 内核),迁移零行为差异。

## 接口规格

### 接口定义

**MeasureText.measureText(动态)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static measureText(options: MeasureOptions): number` |
| 返回值 | `number` — 单行文本宽度(px,向上取整);多行文本取最长行宽;空文本返回 0 |
| 开放范围 | Public |
| 错误码 | N/A — 整个 measure 表面无 `@throws`/BusinessError;非对象入参返回 null |
| 关联 AC | AC-1.1 至 AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options | `MeasureOptions` | 是 | — | 非对象入参返回 null(R-9);对象内字段如下 |
| textContent | `string \| Resource` | 是 | — | 空字符串返回 0(R-3);Resource 需可解析 |
| fontSize | `number \| string \| Resource` | 否 | 主题字号(16fp 声明) | 裸数字:API<12 按 VP、API≥12 按 FP(R-7);不可为百分数;NaN/负值无守卫直接传播至 Rosen |
| fontStyle | `number \| FontStyle` | 否 | `FontStyle.Normal` | 数值型 [0,1] 步长 1 |
| fontWeight | `number \| string \| FontWeight` | 否 | `FontWeight.Normal`(400) | 数值型 [100,900] 步长 100 |
| fontFamily | `string \| Resource` | 否 | `'HarmonyOS Sans'` | 仅默认字体受支持(多字体仅逗号分隔列表传 Rosen) |
| letterSpacing | `number \| string` | 否 | 0 | 默认单位 VP |
| constraintWidth / maxLines / textAlign / overflow / lineHeight / baselineOffset / textCase / textIndent / wordBreak | 各类型 | 否 | 各默认 | **对 measureText 无影响**(R-5),仅 measureTextSize 生效 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 对象入参,文本含 `\n` 多行 | 返回最长行宽 px | AC-1.2 |
| 2 | 对象入参,空 textContent | 返回 0 | AC-1.3 |
| 3 | 非对象入参 | 返回 null,无异常 | AC-1.4 |
| 4 | API<12 + 裸数字 fontSize | 按 VP 单位测量 | AC-1.6 |
| 5 | API≥12 + 裸数字 fontSize | 按 FP 单位测量 | AC-1.6 |
| 6 | fontSize 缺省 + Pipeline 可得 | 回退主题字号 | AC-1.5 |

---

**MeasureText.measureTextSize(动态)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static measureTextSize(options: MeasureOptions): SizeOptions` |
| 返回值 | `SizeOptions`(`{width?: Length, height?: Length}`,均 px);width 设 constraintWidth 时恒为约束 px;否则 ceil(min(maxWidth, max(actualWidth, maxIntrinsicWidth))) |
| 开放范围 | Public(`@stagemodelonly`) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 至 AC-2.11 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| constraintWidth | `number \| string \| Resource` | 否 | 无穷大宽度 | 默认单位 VP;不可百分数;设则 width 恒返回其 px 值(R-6) |
| maxLines | `number` | 否 | 0(不设上限) | [0, INT32_MAX];0 表示不设 |
| textAlign | `number \| TextAlign` | 否 | `TextAlign.Start` | 数值 [0,3] 步长 1 |
| overflow | `number \| TextOverflow` | 否 | `TextOverflow.Clip`(1) | 数值 [0,3];ELLIPSIS 时设省略号 |
| lineHeight | `number \| string \| Resource` | 否 | 无 | 百分数直作倍率;数值=px/字号比 |
| baselineOffset | `number \| string` | 否 | 0 | 经 fabs 加入 height,负值仍增大 |
| textCase | `number \| TextCase` | 否 | `TextCase.Normal` | 数值 [0,2] 步长 1 |
| textIndent | `number \| string` | 否 | 0 | ≤0 不生效;百分数需 constraintWidth |
| wordBreak | `WordBreak` | 否 | `WordBreak.BREAK_WORD` | NAPI 经 has_named_property 兼容性检查 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设 constraintWidth | width=constraintWidth.px | AC-2.2 |
| 2 | 单行无 constraintWidth | width=ceil(min(maxWidth, max(actualWidth, maxIntrinsicWidth))) | AC-2.3 |
| 3 | maxLines 正整数 + overflow=ELLIPSIS | 限行+省略号 | AC-2.4, AC-2.5 |
| 4 | 负 baselineOffset | height=GetHeight()+|baselineOffset| | AC-2.6 |
| 5 | lineHeight 百分数 | heightScale=Value()(1.5=150%) | AC-2.7 |
| 6 | textIndent 百分数 + 无 constraintWidth | 不生效 | AC-2.8 |
| 7 | textCase=UPPERCASE | 测变换后文本 | AC-2.10 |
| 8 | 非对象入参 | 返回 null | AC-2.11 |

---

**UIContext.getMeasureUtils() + MeasureUtils.measureText/measureTextSize**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getMeasureUtils(): MeasureUtils`;`measureText(options): number`;`measureTextSize(options): SizeOptions` |
| 返回值 | 同上(`measureText` 返 `number`,`measureTextSize` 返 `SizeOptions`) |
| 开放范围 | Public(`@stagemodelonly`,`@crossplatform`,`@atomicservice`) |
| 错误码 | N/A |
| 关联 AC | AC-1.7, AC-3.2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 任意 options | 与模块级 API 数值一致(同一 MeasureUtil 内核) | AC-1.7 |
| 2 | API≥18 迁移 | 数值零差异 | AC-3.2 |

---

**静态 ArkTS MeasureText.measureText/measureTextSize**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static measureText(options: MeasureOptions): double`;`static measureTextSize(options: MeasureOptions): SizeOptions` |
| 返回值 | `measureText` 返 `double`(非 `number`);`measureTextSize` 返 `SizeOptions` |
| 开放范围 | Public(`@stagemodelonly`,since 23 static) |
| 错误码 | N/A |
| 关联 AC | AC-1.8, AC-3.3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 静态前端调用 | 经 ANI 桥 `global_scope_ohos_measure_utils_accessor.cpp` 落到同一 `MeasureUtil::MeasureText` | AC-1.8 |
| 2 | since 23 static | 未标 deprecated,无需迁移 | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 是。`fontSize` 裸数字单位在 API 12 边界发生 VP→FP 切换(`frontend_delegate_declarative_ng.cpp:676-692`),需在 API<12 与 API≥12 设备上分别验证。模块级 `MeasureText.measureText/measureTextSize` 自 API 18 起标 `@deprecated`(`@ohos.measure.d.ts:294-295,318-319`),运行时未禁用,但类型层提示迁移至 `UIContext.MeasureUtils`。静态版(since 23 static)未废弃。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9(模块级 `measureText` 动态版起);API 10(`measureTextSize` 动态版起);API 12(`UIContext.MeasureUtils` 起);API 23(静态版起)
- **API 版本号策略:** 动态版字段 since 9/10/11 渐进;`measureText` since 9 `dynamiconly`,`measureTextSize` since 10 `dynamiconly`;UIContext 路径 since 12;静态版 since 23 static;`getParagraphs` 不属本 Feat(Feat-02)

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 三入口同内核约束 | 模块级 / UIContext / 静态三入口必须落到同一 `OHOS::Ace::MeasureUtil::MeasureText/MeasureTextSize`,共享同一 `RosenFontCollection` 单例,数值一致 | AC-1.7, AC-1.8, AC-3.2 |
| 非对象入参零异常约束 | NAPI 层 `napi_typeof` 非 `napi_object` 时 `return nullptr`,禁止抛 BusinessError | AC-1.4, AC-2.11 |
| Rosen 后端可用性约束 | `SystemProperties::GetRosenBackendEnabled()` 为 false 或编译期无 `ENABLE_ROSEN_BACKEND` 时,返回值恒为 0 | (隐含,跨设备验证) |
| 字体集合共享约束 | standalone `MeasureUtil` 与 NG 组件文本渲染共用同一 `Rosen::FontCollection`(非 form 场景);form 渲染使用独立 per-env 集合 | (跨 Feat-01/02 共享) |
| standalone 不重跑约束 | standalone API 不注册字体加载回调,字体加载后需应用层重新调用才能拿到新值;NG 组件自动重测机制不在本 Feat | (隐含) |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 单次 `measureText` 调用 ≤ 5ms(典型短文本,参考阈值) | 单测+基准 | `measure_util.cpp:129-175`(构建一次性 Typography) |
| 可靠性 | 字体集合 null 时不崩溃,返回 0 | mock 测 | `measure_util.cpp:135-138, 181-184` |
| 可测试性 | 非对象入参零异常,便于模糊测试 | 模糊测 | `js_measure.cpp:207, 340` |
| 自动化维测 | 每 10 次调用上报一次 histogram 计数(`measureText`/`measureTextSize`) | hilog 指标 | `js_measure.cpp:36-38, 180-182, 345-347` |

> 功耗/内存/安全/定界定位 N/A(纯同步无 IO 计算函数,无独立功耗/内存指标)。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | 字号/密度由 Pipeline 决定,`ConvertToPx` 已处理 | 同手机 | `measure_util.cpp:143, 164` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | measure API 不涉及无障碍树 | — |
| 大字体 | 是 | `PipelineContext::GetFontWeightScale()` 参与 fontWeight 轴值计算 | `measure_util.cpp:154-158` |
| 深色模式 | 否 | 测量结果与颜色无关 | — |
| 多窗口/分屏 | 是 | 模块级 API 经 `EngineHelper::GetCurrentDelegateSafely()` 取当前上下文委托,多窗口场景下可能上下文错配 — 正是 API 18 废弃模块级、推荐 UIContext 绑定的根因 | `js_measure.cpp:226-228`;`@ohos.measure.d.ts:276-285` |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 12 单位修正、API 18 废弃迁移 | AC-1.6, AC-3.1 |
| 生态兼容 | 是 | 静态版(since 23 static)与动态版数值一致,返回类型不同(double vs number) | AC-1.8 |

## 行为场景（可选，Gherkin）

> 本特性为 L1 标准复杂度,使用"接口规格 → 行为场景"表即可,本节从略。

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式,可独立测试
- [x] 范围边界明确(本 Feat 仅覆盖 standalone 测量,不含 `getParagraphs`/`LayoutManager`)
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致(每个 AC 至少关联一条规则,每条规则至少关联一个 AC)
- [x] 规则表每条通过 5 项质量检查(可复现/可观测/边界值/关联AC/无冲突)

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "standalone 文本测量三入口(模块级/UIContext/静态)如何落到同一 MeasureUtil 内核,字体集合如何在 standalone 与 NG 组件间共享"
  - repo: "openharmony/ace_engine"
    query: "measureText 为何静默忽略布局约束类参数,NAPI 仅解析 6 个属性的设计动机"
  - repo: "openharmony/ace_engine"
    query: "API 12 fontSize 单位 VP→FP 修正的委托层实现与 GreatOrEqualTargetAPIVersion 门控"
```

**关键文档:** `interface/sdk-js/api/@ohos.measure.d.ts`、`interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`、`frameworks/base/utils/measure_util.cpp`、`frameworks/bridge/declarative_frontend/ng/frontend_delegate_declarative_ng.cpp`、`frameworks/core/interfaces/native/implementation/global_scope_ohos_measure_utils_accessor.cpp`
