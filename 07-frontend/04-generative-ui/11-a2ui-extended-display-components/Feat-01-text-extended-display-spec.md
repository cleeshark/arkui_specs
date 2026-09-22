# 特性规格

> Func-07-04-11-Feat-01 Text 扩展组件：固化 A2UI 扩展展示组件 Text 的契约——文本内容属性 `content`（必填，ExtendedDynamicString，`text` 为旧别名）与 `styles` 字体族样式（fontSize/fontWeight/fontColor/textAlign/maxLines/textOverflow/wordBreak/decoration/minFontSize/maxFontSize/fontScaleMode/minFontScale/maxFontScale）。基准实现：`@arkui-genius/genui`（A2UIRender，native C++ `ExtendedTextComponent`/`ExtendedTextTheme`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Text 扩展组件 |
| 特性编号 | Func-07-04-11-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 扩展协议 catalog `ohos.a2ui.extended.catalog` + 起始 API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-11 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/11-a2ui-extended-display-components/design.md` | Baselined |
| 组件实现（C++） | `genui/src/main/cpp/components/extended/ExtendedTextComponent.cpp` | — |
| 主题映射（C++） | `genui/src/main/cpp/components/extended/ExtendedTextTheme.cpp` | — |
| 目录声明（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 协议 Schema | `genui/src/main/resources/rawfile/schema/Extended/components/ExtendedText.json` | — |
| 文档参考 | `render_docs/reference/extended-components/text.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 文本内容显示（content / text 别名）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `content` 属性声明 Text 扩展组件的显示内容（兼容旧 DSL 的 `text` 键）,
**以便** 渲染引擎正确显示文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `content` 为合法字符串（如 `"Hello"`） THEN 渲染节点文本内容为该字符串（`ExtendedTextComponent.cpp:271-280`） | 正常 |
| AC-1.2 | WHEN `content` 为 DynamicString（DataBinding/FunctionCall/Expression 返回 string） THEN 引擎按动态值解析后显示（`allowDynamic=true,allowExpression=true`，`ExtendedTextComponent.cpp:299-300`） | 正常 |
| AC-1.3 | WHEN `content` 为 bool 或 number 标量（如 `true`/`42`） THEN 引擎接受并强转为字符串显示（`ExtendedTextComponent.cpp:273-274`） | 边界 |
| AC-1.4 | WHEN descriptor 同时缺省 `content` 与 `text` THEN 上报 `SCHEMA_ERROR_CODE_INVALID_VALUE` 并回落空串（`ExtendedTextComponent.cpp:262-268`） | 异常 |
| AC-1.5 | WHEN 仅提供 `text`（无 `content`） THEN 引擎按旧别名映射到 `content` 显示（`ExtendedTextComponent.cpp:263,271-279`） | 边界 |
| AC-1.6 | WHEN `content` 为非 string/bool/number/绑定的对象（如数组/嵌套对象） THEN 上报 `SCHEMA_ERROR_CODE_TYPE_MISMATCH` 并 `RemoveBindingsForProperty` + 回落空串（`ExtendedTextComponent.cpp:283-288`） | 异常 |

### US-2: 字体样式（fontSize / fontWeight / fontColor）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles` 声明字号、字重与颜色,
**以便** 精确控制文本外观。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `styles.fontSize` 为正有限数（如 `18`） THEN 节点字号为该值（`ExtendedTextComponent.cpp:419-421`） | 正常 |
| AC-2.2 | WHEN `styles.fontSize` 缺省或非法 THEN 回落默认 `16`（`DEFAULT_TEXT_FONT_SIZE`，`ExtendedTextComponent.cpp:34,431-433`） | 边界 |
| AC-2.3 | WHEN `styles.fontWeight` 为 `100~900` 步长 100 的数或关键字 THEN 映射到对应字重（`TryParseTextFontWeight`，`ExtendedTextComponent.cpp:151-160,305-324`） | 正常 |
| AC-2.4 | WHEN `styles.fontWeight` 非法或类型错误 THEN 回落默认 `W400` 并告警（`ExtendedTextComponent.cpp:311-320`） | 边界 |
| AC-2.5 | WHEN `styles.fontColor` 为合法十六进制颜色（如 `"#333333"`） THEN 节点字体色为该值且 `useDefaultFontColor_=false`（`ExtendedTextComponent.cpp:325-329`） | 正常 |
| AC-2.6 | WHEN `styles.fontColor` 非法或缺省 THEN 回落主题默认字体色（浅色 `0xE5000000`/深色 `0x99FFFFFF`）（`ExtendedTextComponent.cpp:330-344`、`ExtendedTextTheme.cpp:48-52`） | 边界 |

### US-3: 文本对齐与换行（textAlign / maxLines / textOverflow / wordBreak）

**作为** 生成式 UI 宿主开发者,
**我想要** 声明对齐、行数与溢出策略,
**以便** 文本按预期对齐并处理超长内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `styles.textAlign` 为 `start/center/end/justify` 之一 THEN 映射到对应对齐值（`StyleApplyUtilsText.cpp:157-166`） | 正常 |
| AC-3.2 | WHEN `styles.textAlign` 非法或缺省 THEN 回落默认 `start`（`DEFAULT_TEXT_ALIGN=0`，`ExtendedTextComponent.cpp:36,494`） | 边界 |
| AC-3.3 | WHEN `styles.maxLines` 为合法非负整数（如 `2`） THEN 节点最大行数为该值（`ExtendedTextComponent.cpp:439-454`） | 正常 |
| AC-3.4 | WHEN `styles.maxLines` 非法/负数 THEN 回落不限制（`DEFAULT_TEXT_MAX_LINES=INT_MAX`，`ExtendedTextComponent.cpp:39,452`） | 边界 |
| AC-3.5 | WHEN `styles.textOverflow` 为 `none/clip/ellipsis/marquee` 之一 THEN 映射对应溢出值（`StyleApplyUtilsText.cpp:146-155`） | 正常 |
| AC-3.6 | WHEN `styles.textOverflow` 非法 THEN 回落默认 `clip`（`DEFAULT_TEXT_OVERFLOW=1`，`ExtendedTextComponent.cpp:37,468`） | 边界 |
| AC-3.7 | WHEN `styles.textOverflow` 非默认且未配置 `maxLines` THEN 上报 warning 提示溢出不可见（`ShouldWarnTextOverflowWithoutMaxLines`，`ExtendedTextComponent.cpp:175-183,471-476`） | 异常 |
| AC-3.8 | WHEN `styles.wordBreak` 为 `normal/breakAll/breakWord/hyphenation` 之一 THEN 映射对应策略（`StyleApplyUtilsText.cpp:47-51,168-174`） | 正常 |

### US-4: 装饰线（decoration）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.decoration` 声明文本装饰线,
**以便** 显示下划线/上划线/删除线等效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `styles.decoration.type` 为 `underline/overline/lineThrough` 之一 THEN 应用对应装饰线（`ParseDecorationTypeToken`，`ExtendedTextComponent.cpp:90-101`） | 正常 |
| AC-4.2 | WHEN `styles.decoration.color` 合法 THEN 应用该装饰线颜色（`ResolveDecorationWithFallback`，`ExtendedTextComponent.cpp:692-703`） | 正常 |
| AC-4.3 | WHEN `styles.decoration.color` 非法或缺省 THEN 回落主题默认装饰色（浅色 `0xFF000000`/深色 `0x99FFFFFF`）（`ExtendedTextTheme.cpp:54-58`） | 边界 |
| AC-4.4 | WHEN `styles.decoration.style` 为 `solid/double/dotted/dashed/wavy` 之一 THEN 映射对应样式（`ParseDecorationStyleToken`，`ExtendedTextComponent.cpp:103-114`） | 正常 |
| AC-4.5 | WHEN `styles.decoration.thicknessScale` 为有限数 THEN 应用该倍率，否则回落 `1.0`（`ExtendedTextComponent.cpp:714-721`） | 边界 |
| AC-4.6 | WHEN `styles.decoration` 非对象或非法 THEN 回落默认装饰态（`BuildDefaultDecorationState`，`ExtendedTextComponent.cpp:776-786`） | 异常 |

### US-5: 字体缩放与自适应字号（fontScaleMode / minFontScale / maxFontScale / minFontSize / maxFontSize）

**作为** 生成式 UI 宿主开发者,
**我想要** 控制字体是否跟随系统缩放并限制缩放范围,
**以便** 适配大字体与自定义缩放场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `styles.fontScaleMode` 为 `followSystem`/`custom` THEN 应用对应模式（`ExtendedTextComponent.cpp:397-417`） | 正常 |
| AC-5.2 | WHEN `styles.fontScaleMode` 非法或缺省 THEN 回落 `followSystem`（`DEFAULT_FONT_SCALE_MODE`，`ExtendedTextComponent.cpp:40,408`） | 边界 |
| AC-5.3 | WHEN `styles.minFontScale` 超出 `[0,1]`（如 `-1`/`2`） THEN 钳制到 `0`/`1` 并告警（`TryParseValidMinFontScale`，`ExtendedTextComponent.cpp:192-217,354-357`） | 边界 |
| AC-5.4 | WHEN `styles.maxFontScale` 小于 `1` THEN 钳制到 `1`（`TryParseValidMaxFontScale`，`ExtendedTextComponent.cpp:219-239,377-380`） | 边界 |
| AC-5.5 | WHEN `styles.minFontSize`/`maxFontSize` 为合法正数 THEN 启用自适应字号（`ApplyMinFontSizeStyle`/`ApplyMaxFontSizeStyle`，`ExtendedTextComponent.cpp:515-576`） | 正常 |
| AC-5.6 | WHEN `styles.minFontSize >= maxFontSize`（两者均合法正数） THEN 上报 warning 并忽略自适应字号（`HasConflictingAdaptiveFontSizes`，`ExtendedTextComponent.cpp:185-190,570-575`） | 异常 |

### US-6: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Text 扩展组件以 `component:"Text"` 注册到扩展目录,
**以便** DSL 中的扩展 Text 组件被正确路由到 native 渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 组件类型查询 THEN `ExtendedTextComponent::GetType()` 返回 `"Text"`（`ExtendedTextComponent.cpp:249-252`） | 正常 |
| AC-6.2 | WHEN 工厂注册 THEN `ExtendedComponentFactory::RegisterBuiltInComponents` 注册 `"Text"` → `ExtendedTextComponent`（`ExtendedComponentFactory.cpp:109`） | 正常 |
| AC-6.3 | WHEN 目录声明 THEN `A2UIExtendedComponents` 以 `Text` 加入 `EXTENDED_NATIVE_COMPONENT_NAMES` 并加载 `ExtendedText.json`（`A2UIExtendedComponents.ets:28-45,47-64`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2,R-3 | T-1 | C++ UT（`#ifdef TDD_BUILD`） | `ExtendedTextComponent.cpp:260-303` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 | R-4,R-5,R-6 | T-1 | C++ UT + 静态映射比对 | `ExtendedTextComponent.cpp:305-345`、`ExtendedTextTheme.cpp:48-58` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7,AC-3.8 | R-7,R-8,R-9 | T-1 | C++ UT + 静态映射比对 | `StyleApplyUtilsText.cpp:47-51,146-174` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 | R-10,R-11 | T-1 | C++ UT | `ExtendedTextComponent.cpp:90-114,671-813` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 | R-12,R-13 | T-1 | C++ UT | `ExtendedTextComponent.cpp:192-239,347-576` |
| AC-6.1,AC-6.2,AC-6.3 | R-14 | T-1 | 静态比对 | `ExtendedComponentFactory.cpp:109`、`A2UIExtendedComponents.ets:28-64` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `content`（或 `text` 别名）为 string/bool/number/绑定 | 设置节点文本内容 | 内容键 `content` 优先，`text` 为旧别名 | AC-1.1,AC-1.2,AC-1.3,AC-1.5 |
| R-2 | 异常 | `content` 与 `text` 均缺省 | 上报 `INVALID_VALUE` 并回落空串 | 必填属性 | AC-1.4 |
| R-3 | 异常 | `content` 为非标量对象 | 上报 `TYPE_MISMATCH` 并移除绑定回落空串 | 仅接受 string/bool/number/绑定 | AC-1.6 |
| R-4 | 边界 | `styles.fontSize` 非法/缺省 | 回落默认 `16`（fp） | 正有限数才生效 | AC-2.1,AC-2.2 |
| R-5 | 行为 | `styles.fontWeight` 合法（数/关键字/数字串） | 映射到对应字重 | 100~900 步长 100 | AC-2.3,AC-2.4 |
| R-6 | 行为 | `styles.fontColor` 非法/缺省 | 回落主题默认字体色（随 ThemeMode） | 浅色 0xE5000000，深色 0x99FFFFFF | AC-2.5,AC-2.6 |
| R-7 | 行为 | `styles.textAlign` 合法枚举 | 映射对齐值 0/1/2/3 | {start,center,end,justify} | AC-3.1,AC-3.2 |
| R-8 | 边界 | `styles.maxLines` 非法/负 | 回落不限制 | [0, INT_MAX] | AC-3.3,AC-3.4 |
| R-9 | 行为 | `styles.textOverflow` 合法枚举 | 映射溢出值 0/1/2/3 | 默认 clip（=1）；缺 maxLines 时告警 | AC-3.5,AC-3.6,AC-3.7 |
| R-10 | 行为 | `styles.decoration.type/style/color/thicknessScale` 合法 | 应用装饰线状态 | type 含 `lineThrough`（大写 T） | AC-4.1,AC-4.2,AC-4.4,AC-4.5 |
| R-11 | 异常 | `styles.decoration` 非法/非对象/颜色非法 | 回落默认装饰态或主题默认装饰色 | 浅色 0xFF000000，深色 0x99FFFFFF | AC-4.3,AC-4.6 |
| R-12 | 行为 | `styles.fontScaleMode`/`minFontScale`/`maxFontScale` 合法 | 应用缩放模式并钳制比例 | minFontScale∈[0,1]、maxFontScale≥1 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| R-13 | 异常 | `styles.minFontSize ≥ maxFontSize` | 忽略自适应字号并告警 | 两者均正数才冲突 | AC-5.5,AC-5.6 |
| R-14 | 行为 | 组件类型/目录 | 类型 `"Text"`，native 工厂 + 扩展目录注册 | — | AC-6.1,AC-6.2,AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 content/text | C++ UT | 字符串/别名/标量强转/缺省与类型警告 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 字体样式 | C++ UT + 静态映射比对 | fontSize/fontWeight/fontColor 与回落 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7,AC-3.8 对齐换行 | C++ UT | 枚举映射、maxLines、溢出告警 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 decoration | C++ UT | type/style/color/thicknessScale 与回落 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 缩放自适应 | C++ UT | fontScaleMode 分支、scale 钳制、自适应冲突 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3 类型/目录 | 静态比对 | GetType 与工厂/目录注册 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `CatalogItem`（`A2UIExtendedComponents.allA2UIExtendedComponents()` 内 `Text` 项） | 既有 | 扩展目录注册 | 不直接暴露给宿主 | AC-6.3 |
| `ExtendedComponentFactory::RegisterBuiltInComponents()`（`"Text"`） | 既有 | native 工厂路由 | 不直接暴露给宿主 | AC-6.2 |

> d.ts 位置：`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**Text 扩展组件特有属性/样式（descriptor 属性契约，非函数 API）**

| 属性 | 值 |
|------|-----|
| 属性声明 | `ExtendedTextComponent::GetPrivatePropertyDeclaration`（`ExtendedTextComponent.cpp:291-303`） |
| 必填属性 | `content`（schema `ExtendedText.json:18-21`；源码兼容 `text` 别名） |
| 开放范围 | 协议 DSL（无 Public/System API） |
| 错误码 | schema warning `SCHEMA_ERROR_CODE_INVALID_VALUE`/`SCHEMA_ERROR_CODE_TYPE_MISMATCH` |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7,AC-3.8,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content | ExtendedDynamicString | 是 | `""` | 任意字符串；缺省/非法回落空串；`text` 为旧别名 |
| styles.fontSize | ExtendedDynamicNumber | 否 | `16` | 正有限数，单位 fp |
| styles.fontWeight | number\|string | 否 | `400`（W400） | 100~900 步长 100 或关键字/数字串 |
| styles.fontColor | ExtendedDynamicString | 否 | 主题默认 | 十六进制；随 ThemeMode 刷新 |
| styles.textAlign | enum | 否 | `"start"` | {start,center,end,justify} |
| styles.maxLines | number | 否 | 无限制 | [0, INT_MAX] |
| styles.textOverflow | enum | 否 | `"clip"` | {none,clip,ellipsis,marquee} |
| styles.wordBreak | enum | 否 | `"breakWord"` | {normal,breakAll,breakWord,hyphenation} |
| styles.decoration.type | enum | 否 | `"none"` | {none,underline,overline,lineThrough} |
| styles.decoration.color | ExtendedDynamicString | 否 | 主题默认 | 十六进制 |
| styles.decoration.style | enum | 否 | `"solid"` | {solid,double,dotted,dashed,wavy} |
| styles.decoration.thicknessScale | number | 否 | `1.0` | 有限数 |
| styles.minFontSize | ExtendedDynamicNumber | 否 | 未设置 | 正数生效 |
| styles.maxFontSize | ExtendedDynamicNumber | 否 | 未设置 | 正数生效，需 ≥ minFontSize |
| styles.fontScaleMode | enum | 否 | `"followSystem"` | {followSystem,custom} |
| styles.minFontScale | number | 否 | 跟随系统 | [0,1]，越界钳制 |
| styles.maxFontScale | number | 否 | 跟随系统 | [1,∞)，越界钳制 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `content:"Hello"` | 节点文本 "Hello" | AC-1.1 |
| 2 | `content` 缺省 | INVALID_VALUE 告警 + 空串 | AC-1.4 |
| 3 | 仅 `text:"Hi"` | 映射到 content 显示 "Hi" | AC-1.5 |
| 4 | `styles.fontSize:18` | 字号 18 | AC-2.1 |
| 5 | `styles.fontSize` 缺省 | 字号 16 | AC-2.2 |
| 6 | `styles.fontColor:"#333333"` | 字体色 0x333333（useDefault=false） | AC-2.5 |
| 7 | `styles.textOverflow:"ellipsis"` 且无 maxLines | 溢出 ellipsis + 告警 | AC-3.5,AC-3.7 |
| 8 | `styles.decoration:{type:"underline"}` | 下划线 | AC-4.1 |
| 9 | `styles.fontScaleMode:"custom"`, `minFontScale:0.5` | custom 缩放 + 下界钳制 | AC-5.1,AC-5.3 |
| 10 | `styles.minFontSize:20, maxFontSize:12` | 忽略自适应 + 告警 | AC-5.6 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 catalog `ohos.a2ui.extended.catalog`，起始 API Version 20。
- **API 版本号策略:** 协议 schema 版本由 `SchemaResourceLoader.loadSchema('schema/Extended/components/ExtendedText.json')` 声明（`A2UIExtendedComponents.ets:150-157`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 必填属性 content | 缺省上报警告并回落默认；`text` 仅作别名兼容 | AC-1.4,AC-1.5 |
| styles 统一承载 | 特有样式统一经 `styles.*`，非法一律回落默认 + schema warning | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7,AC-3.8,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 |
| native 组件路径 | Text 走 C++ 属性/样式管线（`ExtendedComponent`），非 Custom 组件 | AC-6.1,AC-6.2 |
| 主题刷新 | 默认字体色/装饰色随 `ThemeMode` 在 `OnConfigChange` 刷新 | AC-2.6,AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法/缺省属性不抛异常，统一回落默认 + schema warning | C++ UT | `ExtendedTextComponent.cpp:260-626` |
| 性能 | 属性/样式应用为单次节点 API 调用 | C++ UT | `ExtendedTextComponent.cpp:628-921` |
| 可测试性 | `#ifdef TDD_BUILD` 暴露 `ApplyTextStyleStateForTest` 供状态断言 | C++ UT | `ExtendedTextComponent.cpp:923-1098` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 固定字号/默认色与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 走通用 `accessibility` 属性（归通用样式域），本域不扩展 | — |
| 大字体 | 是 | `fontScaleMode`/`minFontScale`/`maxFontScale`/自适应字号控制缩放 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 |
| 深色模式 | 是 | 默认字体色/装饰色随 `ThemeMode` 分流（`ExtendedTextTheme`） | AC-2.6,AC-4.3 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 catalog 绑定（`ohos.a2ui.extended.catalog`） | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 扩展协议 Text 语义对齐 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Text 扩展组件
  作为 生成式 UI 宿主开发者
  我想要 通过 content 与 styles 字体族声明文本
  以便 渲染引擎正确显示并样式化文本

  Scenario: 文本内容显示
    Given DSL 组件为 {"component":"Text","id":"t1","content":"Hello"}
    When 应用 descriptor
    Then 节点文本内容为 "Hello"

  Scenario: 内容缺省回落
    Given DSL 组件为 {"component":"Text","id":"t1"}
    When 应用 descriptor
    Then 上报 INVALID_VALUE 警告且文本内容为空串

  Scenario Outline: 字体样式回落
    Given DSL 组件为 {"component":"Text","id":"t1","content":"X","styles":<styles>}
    When 应用 styles
    Then 字号为 <size> 且字重为 <weight>

    Examples:
      | styles                        | size | weight |
      | {"fontSize":18}               | 18.0 | 400    |
      | {"fontSize":0}                | 16.0 | 400    |
      | {"fontWeight":"bold"}         | 16.0 | 700    |
      | {"fontWeight":"invalid"}      | 16.0 | 400    |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Text 扩展特有属性 content 与 `styles` 字体族；通用属性归通用样式域）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTextComponent ApplyPrivateAttributes content text alias GetPrivatePropertyDeclaration"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTextComponent ApplyComponentSpecificStyles fontSize fontWeight fontColor textAlign maxLines textOverflow wordBreak"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTextComponent ApplyDecorationStyleWithFallback ParseDecorationTypeToken lineThrough"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTextTheme GetDefaultFontColor GetDefaultDecorationColor ThemeMode"
```

**关键文档：** `genui/src/main/cpp/components/extended/ExtendedTextComponent.cpp`、`genui/src/main/cpp/components/extended/ExtendedTextTheme.cpp`、`genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets`、`genui/src/main/resources/rawfile/schema/Extended/components/ExtendedText.json`