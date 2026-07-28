# 特性规格

> Func-05-15-01-Feat-01 WithTheme 组件：固化主题作用域语法节点的创建、theme/colorMode 选项、幂等 SetThemeScopeId、嵌套构建栈、销毁回调、逐节点主题更新传播的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | WithTheme 组件 (WithTheme Component) |
| 特性编号 | Func-05-15-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 API 12 起，静态 API 23 起，API 26 新增 Builder 重载 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | WithTheme 语法节点完整行为规格 | 补录 WithThemeNode 创建、作用域管理、构建栈、主题传播、销毁回调全部行为 |
| ADDED | 动态 vs 静态 API 差异说明 | 补录 with_theme.d.ts @since 12 与 withTheme.d.ets @since 23 的签名差异 |
| ADDED | C-API Modifier 表说明 | 补录 getWithThemeModifier() 与 getThemeModifier() 两张表的职责划分 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/15-theme-components/01-with-theme/design.md` | Baselined |
| SDK 动态 | `interface/sdk-js/api/@internal/component/ets/with_theme.d.ts` | — |
| SDK 静态 | `interface/sdk-js/api/arkui/component/withTheme.d.ets` | — |

---

## 用户故事

### US-1: 创建 WithTheme 主题作用域

**作为** 应用开发者,
**我想要** 使用 `WithTheme(options)` 创建一个主题作用域容器,
**以便** 在该作用域内为子组件提供局部主题覆盖。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `WithTheme({ theme?: CustomTheme, colorMode?: ThemeColorMode })` THEN 创建一个 WithThemeNode 语法节点（tag=V2::JS_WITH_THEME_ETS_TAG），IsSyntaxNode()=true，IsAtomicNode()=false | 正常 |
| AC-1.2 | WHEN options.theme 为 undefined THEN 作用域内组件使用默认 token 样式 | 边界 |
| AC-1.3 | WHEN options.colorMode 未设置 THEN 默认为 ThemeColorMode.SYSTEM | 边界 |

### US-2: 设置 theme 和 colorMode 选项

**作为** 应用开发者,
**我想要** 通过 options 传入自定义主题和颜色模式,
**以便** 控制作用域内组件的主题和深浅色模式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN options.theme 为 CustomTheme THEN 颜色数组通过 SendThemeToNative/ThemeBridge::Create 解析并存入 TokenThemeStorage | 正常 |
| AC-2.2 | WHEN options.colorMode 为 LIGHT 或 DARK THEN 作用域内组件使用指定颜色模式 | 正常 |
| AC-2.3 | WHEN darkColors 未设置（darkSetStatus=false）THEN 暗色使用亮色副本，并调用 InitDarkThemeMapWithoutUserSet | 异常 |

### US-3: 作用域根与幂等 SetThemeScopeId

**作为** 框架开发者,
**我想要** WithThemeNode 在构造时设置 ThemeScopeId 且幂等,
**以便** 保证主题作用域标识在生命周期内稳定不变。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN WithThemeNode 构造 THEN 调用 SetThemeScopeId(nodeId)，themeScopeId_ 被设置为 nodeId | 正常 |
| AC-3.2 | WHEN themeScopeId_==0 时调用 SetThemeScopeId(id) THEN 设置成功；WHEN themeScopeId_!=0 时调用 THEN 静默忽略 | 边界 |
| AC-3.3 | WHEN UpdateThemeScopeId/UpdateThemeScopeUpdate 被调用 THEN 执行 NO-OP（作用域根不向上传播） | 边界 |

### US-4: 嵌套 WithTheme 与构建栈

**作为** 应用开发者,
**我想要** 嵌套使用多个 WithTheme 且子组件能获取最内层作用域,
**以便** 实现多层主题覆盖的精确解析。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN WithThemeNode::Build 执行 THEN GetId() 被 push 到 thread_local g_withThemeBuildNodeIdStack | 正常 |
| AC-4.2 | WHEN Build 完成（guard 析构）THEN 栈顶被 pop，GetCurrentBuildingNodeId 返回上层或 nullopt | 正常 |
| AC-4.3 | WHEN 嵌套 WithTheme 构建 THEN 最内层 WithTheme 的子节点通过 GetCurrentBuildingNodeId 获取内层 nodeId | 边界 |

### US-5: onThemeScopeDestroy 销毁回调

**作为** 应用开发者,
**我想要** WithTheme 作用域销毁时触发回调,
**以便** 执行主题资源清理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN ~WithThemeNode 析构 THEN 触发 themeScopeDestroyCallback_（若已设置） | 正常 |
| AC-5.2 | WHEN ~WithThemeNode 析构 THEN 调用 TokenThemeStorage::RemoveThemeScope(GetId()) 清理存储 | 正常 |

### US-6: 逐节点 onThemeScopeUpdate 传播

**作为** 框架开发者,
**我想要** 主题更新时递归传播并逐节点回调,
**以便** 作用域内所有注册节点都能响应主题变更。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN NotifyThemeScopeUpdate 被调用 THEN 先执行 UINode::UpdateThemeScopeUpdate(GetThemeScopeId()) 递归更新子树 | 正常 |
| AC-6.2 | WHEN NotifyThemeScopeUpdate 被调用 THEN 遍历 themeScopeUpdateCallbacksMap_，逐个触发已注册回调 | 正常 |
| AC-6.3 | WHEN PushOnThemeScopeUpdateWithId(callback, nodeId) 注册 THEN 回调存入 themeScopeUpdateCallbacksMap_[nodeId]；RemoveOnThemeScopeUpdateWithId(nodeId) 移除 | 边界 |

### US-7: colorMode 与默认主题回退

**作为** 应用开发者,
**我想要** 指定 colorMode 或不指定 theme 时有合理默认行为,
**以便** 适配不同深浅色场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN colorMode 为 SYSTEM THEN 作用域内组件跟随系统深浅色设置 | 正常 |
| AC-7.2 | WHEN theme 未设置（undefined）THEN 作用域内组件使用默认 token 样式（TokenThemeStorage 默认/系统主题） | 边界 |

### US-8: WithThemeAttribute 空属性与动态/静态 API 差异

**作为** 应用开发者,
**我想要** 了解 WithThemeAttribute 不支持通用属性/事件及动态/静态 API 差异,
**以便** 正确使用 WithTheme 组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 动态 API（with_theme.d.ts）THEN WithThemeAttribute 为空 class，通用属性/事件不被支持 | 边界 |
| AC-8.2 | WHEN 静态 API（withTheme.d.ets）THEN WithThemeAttribute 含 debugLine/setWithThemeOptions/applyAttributesFinish（@since 26），但 C++ 实现当前为 NO-OP | 边界 |
| AC-8.3 | WHEN C-API getWithThemeModifier() THEN ConstructImpl 有效；SetWithThemeOptionsImpl 和 SetDebugLineImpl 为 NO-OP（仅校验非空） | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 with_theme_node.h:29,37,42,47 |
| AC-1.2 | US-1 | R-2 | 代码审查 with_theme.d.ts:51 |
| AC-1.3 | US-1 | R-3 | 代码审查 with_theme.d.ts:63 |
| AC-2.1 | US-2 | R-4 | 代码审查 js_with_theme.cpp:71-116 + arkts_native_theme_bridge.cpp:26-89 |
| AC-2.2 | US-2 | R-5 | 代码审查 arkts_native_theme_bridge.cpp:65 |
| AC-2.3 | US-2 | R-6 | 代码审查 arkts_native_theme_bridge.cpp:55-58 |
| AC-3.1 | US-3 | R-7 | 代码审查 with_theme_node.h:37-39 |
| AC-3.2 | US-3 | R-8 | 单元测试 WithThemeNodeTest001 |
| AC-3.3 | US-3 | R-9 | 代码审查 with_theme_node.cpp:91-99 |
| AC-4.1 | US-4 | R-10 | 单元测试 WithThemeNodeBuildStackTest002 |
| AC-4.2 | US-4 | R-11 | 单元测试 WithThemeNodeBuildStackTest001/002 |
| AC-4.3 | US-4 | R-12 | 单元测试 WithThemeNodeBuildStackTest003 |
| AC-5.1 | US-5 | R-13 | 代码审查 with_theme_node.cpp:42-46 |
| AC-5.2 | US-5 | R-14 | 代码审查 with_theme_node.cpp:47 |
| AC-6.1 | US-6 | R-15 | 代码审查 with_theme_node.cpp:83 |
| AC-6.2 | US-6 | R-16 | 代码审查 with_theme_node.cpp:84-88 |
| AC-6.3 | US-6 | R-17 | 代码审查 with_theme_node.cpp:71-79 |
| AC-7.1 | US-7 | R-3 | 代码审查 with_theme.d.ts:63 |
| AC-7.2 | US-7 | R-2 | 代码审查 with_theme.d.ts:51 |
| AC-8.1 | US-8 | R-18 | 代码审查 with_theme.d.ts:78-89 |
| AC-8.2 | US-8 | R-19 | 代码审查 withTheme.d.ets:62-95 + with_theme_modifier.cpp:34-52 |
| AC-8.3 | US-8 | R-20 | 代码审查 with_theme_modifier.cpp:24-31,34-52 |

---

## 规则定义

> **统一规则表。** 类型标签：**行为**（正常路径）、**边界**（输入/状态临界点）、**异常**（非法输入或异常状态）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `with_theme_node.h:29,37,42,47` | WithThemeNode 继承 UINode，tag=JS_WITH_THEME_ETS_TAG，IsAtomicNode()=false，IsSyntaxNode()=true | 语法节点，非 Pattern/Model | AC-1.1 |
| R-2 | 行为 | `with_theme.d.ts:51` | theme 为 undefined 时，作用域内组件使用默认 token 样式 | — | AC-1.2, AC-7.2 |
| R-3 | 行为 | `with_theme.d.ts:63` | colorMode 默认为 ThemeColorMode.SYSTEM | — | AC-1.3, AC-7.1 |
| R-4 | 行为 | `js_with_theme.cpp:71-116`, `arkts_native_theme_bridge.cpp:26-89` | 颜色数组通过 SendThemeToNative/ThemeBridge::Create 解析，存入 JSThemeScope::jsThemes/TokenThemeStorage | — | AC-2.1 |
| R-5 | 行为 | `arkts_native_theme_bridge.cpp:65` | colorMode 传递给 createTheme | — | AC-2.2 |
| R-6 | 异常 | `arkts_native_theme_bridge.cpp:55-58` | darkSetStatus=false 时暗色使用亮色副本，调用 InitDarkThemeMapWithoutUserSet | — | AC-2.3 |
| R-7 | 行为 | `with_theme_node.h:37-39` | 构造时 SetThemeScopeId(nodeId) | — | AC-3.1 |
| R-8 | 边界 | `with_theme_node.cpp:106-111` | SetThemeScopeId 幂等：仅当 themeScopeId_==0 时设置 | — | AC-3.2 |
| R-9 | 边界 | `with_theme_node.cpp:91-99` | UpdateThemeScopeId/UpdateThemeScopeUpdate 为 NO-OP | scope root 不向上传播 | AC-3.3 |
| R-10 | 行为 | `with_theme_node.cpp:113-117` | Build 时 WithThemeBuildStackGuard push GetId() | thread_local 栈 | AC-4.1 |
| R-11 | 行为 | `with_theme_node.cpp:26-39,119-125` | guard 析构 pop 栈顶；GetCurrentBuildingNodeId 返回栈顶或 nullopt | — | AC-4.2 |
| R-12 | 边界 | `with_theme_node.cpp:119-125` | 嵌套时 GetCurrentBuildingNodeId 返回最内层 WithTheme nodeId | thread_local | AC-4.3 |
| R-13 | 行为 | `with_theme_node.cpp:42-46` | ~WithThemeNode 触发 themeScopeDestroyCallback_ | — | AC-5.1 |
| R-14 | 行为 | `with_theme_node.cpp:47` | ~WithThemeNode 调用 TokenThemeStorage::RemoveThemeScope(GetId()) | — | AC-5.2 |
| R-15 | 行为 | `with_theme_node.cpp:83` | NotifyThemeScopeUpdate 先调 UINode::UpdateThemeScopeUpdate(GetThemeScopeId()) 递归子树 | — | AC-6.1 |
| R-16 | 行为 | `with_theme_node.cpp:84-88` | NotifyThemeScopeUpdate 遍历 themeScopeUpdateCallbacksMap_ 逐个触发回调 | — | AC-6.2 |
| R-17 | 边界 | `with_theme_node.cpp:71-79` | PushOnThemeScopeUpdateWithId 存入 map；RemoveOnThemeScopeUpdateWithId 移除 | — | AC-6.3 |
| R-18 | 边界 | `with_theme.d.ts:78-89` | 动态 WithThemeAttribute 为空 class，通用属性/事件不支持 | — | AC-8.1 |
| R-19 | 边界 | `withTheme.d.ets:62-95`, `with_theme_modifier.cpp:34-52` | 静态 WithThemeAttribute 含 debugLine/setWithThemeOptions/applyAttributesFinish @since 26，C++ 为 NO-OP | — | AC-8.2 |
| R-20 | 边界 | `with_theme_modifier.cpp:24-31,34-52` | ConstructImpl 有效；SetWithThemeOptionsImpl/SetDebugLineImpl 为 NO-OP（仅校验非空） | — | AC-8.3 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 创建 WithTheme 作用域 (AC-1.1~1.3) | 代码审查 | 语法节点属性；theme/colorMode 默认值 |
| VM-2 | US-2 theme/colorMode 选项 (AC-2.1~2.3) | 代码审查 | 颜色解析路径；darkColors 回退 |
| VM-3 | US-3 作用域根幂等 (AC-3.1~3.3) | 单元测试 + 代码审查 | SetThemeScopeId 幂等；NO-OP 传播 |
| VM-4 | US-4 嵌套构建栈 (AC-4.1~4.3) | 单元测试 | push/pop 栈；嵌套最内层暴露 |
| VM-5 | US-5 销毁回调 (AC-5.1~5.2) | 代码审查 | 析构触发回调 + 存储清理 |
| VM-6 | US-6 主题更新传播 (AC-6.1~6.3) | 代码审查 | 递归 + 逐节点回调 |
| VM-7 | US-7 colorMode 与默认回退 (AC-7.1~7.2) | 代码审查 | SYSTEM 默认；undefined 默认 token |
| VM-8 | US-8 属性与桥接差异 (AC-8.1~8.3) | 代码审查 | 空 Attribute；NO-OP 方法 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/core/components_ng/syntax/with_theme_node.h:29,37,42,47` |
| AC-1.2 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/with_theme.d.ts:51` |
| AC-1.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/with_theme.d.ts:63` |
| AC-2.1 | 代码审查 | `frameworks/bridge/declarative_frontend/ark_theme/theme_apply/js_with_theme.cpp:71-116` + `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_theme_bridge.cpp:26-89` |
| AC-2.2 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_theme_bridge.cpp:65` |
| AC-2.3 | 代码审查 | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_theme_bridge.cpp:55-58` |
| AC-3.1 | 代码审查 | `frameworks/core/components_ng/syntax/with_theme_node.h:37-39` |
| AC-3.2 | 单元测试 | `test/unittest/core/pattern/withtheme/withtheme_test_ng.cpp` WithThemeNodeTest001 |
| AC-3.3 | 代码审查 | `frameworks/core/components_ng/syntax/with_theme_node.cpp:91-99` |
| AC-4.1 | 单元测试 | `test/unittest/core/pattern/withtheme/withtheme_test_ng.cpp` WithThemeNodeBuildStackTest002 |
| AC-4.2 | 单元测试 | `test/unittest/core/pattern/withtheme/withtheme_test_ng.cpp` WithThemeNodeBuildStackTest001/002 |
| AC-4.3 | 单元测试 | `test/unittest/core/pattern/withtheme/withtheme_test_ng.cpp` WithThemeNodeBuildStackTest003 |
| AC-5.1 | 代码审查 | `frameworks/core/components_ng/syntax/with_theme_node.cpp:42-46` |
| AC-5.2 | 代码审查 | `frameworks/core/components_ng/syntax/with_theme_node.cpp:47` |
| AC-6.1 | 代码审查 | `frameworks/core/components_ng/syntax/with_theme_node.cpp:83` |
| AC-6.2 | 代码审查 | `frameworks/core/components_ng/syntax/with_theme_node.cpp:84-88` |
| AC-6.3 | 代码审查 | `frameworks/core/components_ng/syntax/with_theme_node.cpp:71-79` |
| AC-7.1 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/with_theme.d.ts:63` |
| AC-7.2 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/with_theme.d.ts:51` |
| AC-8.1 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/with_theme.d.ts:78-89` |
| AC-8.2 | 代码审查 | `interface/sdk-js/api/arkui/component/withTheme.d.ets:62-95` + `frameworks/core/interfaces/native/implementation/with_theme_modifier.cpp:34-52` |
| AC-8.3 | 代码审查 | `frameworks/core/interfaces/native/implementation/with_theme_modifier.cpp:24-31,34-52` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/with_theme.d.ts` (动态) / `interface/sdk-js/api/arkui/component/withTheme.d.ets` (静态)

#### WithThemeOptions

```typescript
// with_theme.d.ts:38-64
interface WithThemeOptions {
  theme?: CustomTheme;        // 默认 undefined → 默认 token 样式
  colorMode?: ThemeColorMode; // 默认 SYSTEM
}
```

#### WithThemeInterface (动态)

```typescript
// with_theme.d.ts:76
type WithThemeInterface = (options: WithThemeOptions) => WithThemeAttribute;
// with_theme.d.ts:99
declare const WithTheme: WithThemeInterface;
```

#### WithThemeAttribute (动态)

```typescript
// with_theme.d.ts:88-89
declare class WithThemeAttribute {}  // 空，不支持通用属性/事件
```

#### WithTheme (静态)

```typescript
// withTheme.d.ets:108-112 @since 23
@ComponentBuilder
declare function WithTheme(options: WithThemeOptions | undefined, content_?: CustomBuilder): WithThemeAttribute;

// withTheme.d.ets:125-129 @since 26
@Builder
declare function WithTheme(style_: CustomBuilderT<WithThemeAttribute>, content_?: CustomBuilder): WithThemeAttribute;
```

#### WithThemeAttribute (静态)

```typescript
// withTheme.d.ets:62-95
interface WithThemeAttribute {
  debugLine(sourceLine: string, moduleName?: string): this;              // @since 26
  setWithThemeOptions(options: WithThemeOptions | undefined): this;     // @since 26
  applyAttributesFinish(): void;                                        // @since 26
}
```

| 方法签名 | 返回类型 | 说明 | @since | C++ 实现 |
|----------|----------|------|--------|----------|
| `debugLine(sourceLine, moduleName?)` | this | 设置源码行重定向信息 | 26 | NO-OP |
| `setWithThemeOptions(options \| undefined)` | this | 设置 WithTheme 选项 | 26 | NO-OP |
| `applyAttributesFinish()` | void | 通知属性设置完成 | 26 | — |

> **重要偏差**: 静态 API 26 新增的 debugLine/setWithThemeOptions/applyAttributesFinish 在 C++ with_theme_modifier.cpp 中为 NO-OP（SetWithThemeOptionsImpl 仅校验 frameNode+options 非空，SetDebugLineImpl 注释掉了实际逻辑）。主题作用域通过 ThemeBridge::Create 路径建立，不经过 SetWithThemeOptions。

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
| 动态 API 12 | WithTheme(options) 返回 WithThemeAttribute（空 class） | 通用属性/事件不支持 | 不可在 WithTheme 上链式调用 padding/margin/onClick 等 |
| 静态 API 23 | WithTheme(options, content_) 为 @ComponentBuilder，@noninterop | 静态前端专用 | 动态前端不可使用静态重载 |
| 静态 API 26 | 新增 @Builder 重载 WithTheme(style_, content_) 和 debugLine/setWithThemeOptions/applyAttributesFinish | C++ 端为 NO-OP | 调用这些方法不会产生效果，主题作用域仍通过 ThemeBridge::Create 建立 |
| 动态 vs 静态 | 动态 WithThemeAttribute 为空 class；静态含 debugLine/setWithThemeOptions/applyAttributesFinish | API 表面不同 | 按前端类型使用对应重载 |
| C-API | getWithThemeModifier() 的 SetWithThemeOptionsImpl/SetDebugLineImpl 为 NO-OP | 静态前端通过 Modifier 调用无效 | 主题作用域通过 getThemeModifier() 的 createTheme/createThemeScope 建立 |
| WithThemeOptions | 仅 theme + colorMode，无 onAppearing/onDisappearing | 无生命周期回调 | 仅有 onThemeScopeDestroy（C++ 端）+ onThemeScopeUpdate（逐节点注册） |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 语法节点架构 | WithThemeNode : UINode，IsSyntaxNode()=true，非 Pattern/Model 组件，无 LayoutProperty/PaintProperty |
| 作用域根幂等 | SetThemeScopeId 仅当 themeScopeId_==0 时设置，重复调用静默忽略 |
| 不向上传播 | UpdateThemeScopeId/UpdateThemeScopeUpdate 在 WithThemeNode 中为 NO-OP（scope root 不向父传播） |
| thread_local 构建栈 | g_withThemeBuildNodeIdStack 为 thread_local，嵌套时暴露最内层，线程安全但跨线程不共享 |
| 主题更新双层传播 | NotifyThemeScopeUpdate 先递归子树（UINode::UpdateThemeScopeUpdate），再逐节点回调（themeScopeUpdateCallbacksMap_） |
| WithThemeAttribute 空 | 通用属性/事件不被支持；静态 API 26 新增方法 C++ 为 NO-OP |
| 无 onAppearing/onDisappearing | WithThemeOptions 仅 theme + colorMode；生命周期通过 onThemeScopeDestroy + onThemeScopeUpdate 管理 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | WithTheme 为语法节点，无渲染开销；构建栈为 thread_local vector，push/pop 为 O(1) |
| 线程安全 | thread_local 构建栈天然线程安全 |
| 可调试性 | TokenThemeStorage 单例支持主题映射查询和 Inspector 诊断 |

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
| 无障碍 | 否 — WithTheme 为语法节点，不涉及无障碍属性 |
| 大字体 | 否 — WithTheme 不涉及大字体适配 |
| 深色模式 | 是 — WithTheme 通过 colorMode 选项覆盖作用域内组件的深浅色模式，darkColors 独立配置 |
| 多窗口分屏 | 否 — WithTheme 不涉及多窗口行为 |
| 多用户 | 否 — WithTheme 不涉及多用户隔离 |
| 版本升级 | 否 — 动态 API 12 起、静态 API 23 起已有，API 26 新增方法为 NO-OP |
| 生态兼容 | 否 — WithTheme 不涉及生态兼容性 |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 规则编号连续且可追溯到源码（file:line）
- [x] API 变更分析基于真实 SDK 定义文件（with_theme.d.ts / withTheme.d.ets）
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更
- [x] 明确标注 WithTheme 为语法节点（非 Pattern/Model）
- [x] 明确标注 WithThemeOptions 无 onAppearing/onDisappearing
- [x] 明确标注 setWithThemeOptions/debugLine 为 NO-OP

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/syntax/with_theme_node.h` | WithThemeNode 语法节点定义（71 行） |
| `frameworks/core/components_ng/syntax/with_theme_node.cpp` | WithThemeNode 实现：构建栈、销毁回调、主题传播（127 行） |
| `frameworks/bridge/declarative_frontend/ark_theme/theme_apply/js_with_theme.h` | JS 桥接层声明（36 行） |
| `frameworks/bridge/declarative_frontend/ark_theme/theme_apply/js_with_theme.cpp` | JS 桥接层实现：颜色解析、主题交换（142 行） |
| `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_theme_bridge.cpp` | ArkTS 桥接层：C-API 调用、回调封装（203 行） |
| `frameworks/core/interfaces/native/implementation/with_theme_modifier.cpp` | C-API Modifier 表：ConstructImpl / SetWithThemeOptionsImpl(NO-OP) / SetDebugLineImpl(NO-OP)（64 行） |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/withtheme/withtheme_test_ng.cpp` | NG 单元测试：SetThemeScopeId 幂等、构建栈 push/pop、嵌套最内层暴露（850 行） |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `interface/sdk-js/api/@internal/component/ets/with_theme.d.ts` | 动态 SDK API 定义 @since 12（109 行） |
| `interface/sdk-js/api/arkui/component/withTheme.d.ets` | 静态 SDK API 定义 @since 23/26（129 行） |
