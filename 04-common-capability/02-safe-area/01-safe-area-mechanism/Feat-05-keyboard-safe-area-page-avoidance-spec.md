# 特性规格

> Func-04-02-01-Feat-05 键盘安全区联动与页面避让存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 键盘安全区联动与页面避让 |
| 特性编号 | Func-04-02-01-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性定义键盘可见高度如何生成 KEYBOARD inset，以及 NONE、RESIZE、RESIZE_WITH_CARET、OFFSET 等模式如何影响 combined safe area、页面 offset/resize、焦点 caret、旋转、Web 镜像与 Page。`UIContext.setKeyboardAvoidMode` 只控制 Page；OverlayManager 管理的 Dialog、Popup、Menu 等具有独立避让路径。键盘模式 API 自身归键盘控制域，本 Feat 只记录安全区侧消费。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | KEYBOARD inset | 补录根高度/系统 bottom 到键盘安全区的转换 |
| ADDED | 模式分流 | 补录 NONE/RESIZE/OFFSET/caret 行为 |
| ADDED | 页面联动 | 补录焦点、旋转、Web、Page/Overlay 与 expandSafeArea(KEYBOARD) |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md` | 并行补录 |
| SafeAreaManager | `frameworks/core/components_ng/manager/safe_area/safe_area_manager.cpp` | 已核对 |
| Pipeline | `frameworks/core/pipeline_ng/pipeline_context.cpp` | 已核对 |
| LayoutWrapper | `frameworks/core/components_ng/layout/layout_wrapper.cpp` | 已核对 |
| Keyboard API | `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts` | 外部输入已核对 |

## 用户故事

### US-1: 将键盘高度转换为安全区

**作为** ArkUI Pipeline  
**我想要** 在键盘显示、隐藏或尺寸变化时更新 KEYBOARD inset  
**以便** 页面布局与渲染使用当前键盘边界

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 键盘可见高度有效 THEN bottom keyboard inset 由系统 bottom 或根高度与键盘 top 的关系生成 | 正常 |
| AC-1.2 | WHEN 键盘隐藏、高度为 0 或模式 NONE 清除避让 THEN 可见 keyboard inset 清空 | 边界 |
| AC-1.3 | WHEN 根高度、屏幕方向或 viewport 变化 THEN 使用新几何重新计算 keyboard inset 和页面偏移 | 正常 |
| AC-1.4 | WHEN 高度、焦点或 Pipeline 上下文失效 THEN 安全退出或保持合法既有几何，不访问失效节点 | 异常 |

### US-2: 按键盘避让模式选择路径

**作为** 应用开发者  
**我想要** 当前键盘模式具有明确的安全区效果  
**以便** 输入控件和页面内容不发生不可预测跳动

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 模式为 RESIZE 或 RESIZE_WITH_CARET THEN keyboard inset 进入 combined safe area 并压缩/调整页面可用区域 | 正常 |
| AC-2.2 | WHEN 模式为 OFFSET THEN keyboard 不并入 resize combined inset，页面使用独立 keyboard offset 路径 | 边界 |
| AC-2.3 | WHEN 模式切换为 NONE THEN 清理可见 inset 和既有 offset，后续页面不避让键盘 | 边界 |
| AC-2.4 | WHEN模式从 NONE/其他模式切换 THEN 只按新模式建立 resize 或 offset 状态，不叠加旧模式结果 | 正常 |

### US-3: 联动焦点、Web 与渲染扩展

**作为** ArkUI 应用开发者
**我想要** 在焦点、Web 和渲染扩展场景中沿用统一的键盘避让状态
**以便** 页面与叠加层在各自职责边界内保持可预期的避让行为

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN caret 模式启用且焦点位置变化 THEN 结合 caret/焦点矩形重新计算所需页面偏移 | 正常 |
| AC-3.2 | WHEN Web 或动态内容镜像键盘状态 THEN 通过既有 Pipeline 输入更新，不创建第二套安全区真值 | 正常 |
| AC-3.3 | WHEN Page 计算最终 paint rect THEN 使用 top safe area 和当前 Page keyboard offset；WHEN Dialog/Popup/Menu 等 Overlay 避让键盘 THEN 由 OverlayManager 的独立策略计算，不由 UIContext 的 Page 模式统一控制 | 边界 |
| AC-3.4 | WHEN Page 为 RESIZE 且组件设置 expandSafeArea([KEYBOARD], [BOTTOM]) THEN Page 仍执行 RESIZE，KEYBOARD 扩展设置不生效；WHEN Page 为 OFFSET THEN 仍由页面 offset 独立处理 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Keyboard inset UT | `frameworks/core/components_ng/manager/safe_area/safe_area_manager.cpp:119-155`; `frameworks/core/pipeline_ng/pipeline_context.cpp:3274-3415` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | Mode matrix UT | `frameworks/core/components_ng/manager/safe_area/safe_area_manager.cpp:157-176,250-263` |
| AC-3.1~AC-3.4 | R-9~R-12 | 已有实现 | caret/Web/Page/Overlay 边界测试 | `frameworks/core/pipeline_ng/pipeline_context.cpp:3436-3509`; `frameworks/core/components_ng/layout/layout_wrapper.cpp:139-188,732-759`; `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts:5437-5447` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 可见键盘高度>0 | 生成 bottom inset | 基于当前根高度/系统 bottom | AC-1.1 |
| R-2 | 恢复 | 隐藏/0/NONE | 清空 keyboard inset | 不保留可见状态 | AC-1.2 |
| R-3 | 行为 | 根尺寸/旋转变化 | 重算 inset/offset | 使用最新几何 | AC-1.3 |
| R-4 | 异常 | 节点/上下文失效 | 安全退出 | 不访问悬空引用 | AC-1.4 |
| R-5 | 行为 | RESIZE/RESIZE_WITH_CARET | 并入 combined safe area | 开启压缩 | AC-2.1 |
| R-6 | 边界 | OFFSET | 使用页面 offset | 不并入 resize inset | AC-2.2 |
| R-7 | 恢复 | 切到 NONE | 清理 inset 和 offset | 页面不避让 | AC-2.3 |
| R-8 | 行为 | 模式切换 | 仅建立新模式状态 | 旧结果不叠加 | AC-2.4 |
| R-9 | 行为 | caret/焦点变化 | 重算所需偏移 | 仅有效焦点 | AC-3.1 |
| R-10 | 行为 | Web/动态输入 | 复用 Pipeline 真值 | 不建独立 Manager | AC-3.2 |
| R-11 | 边界 | Page 或 Overlay paint | Page 使用 UIContext 模式；OverlayManager 对 Dialog/Popup/Menu 等独立计算 | UIContext.setKeyboardAvoidMode 不统一控制 Overlay | AC-3.3 |
| R-12 | 边界 | expand KEYBOARD+BOTTOM | RESIZE 下 expansion 不生效且 Page 继续 resize；OFFSET 仍走页面 offset | 不据此推导 RESIZE_WITH_CARET | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | SafeAreaManager/Pipeline UT | 高度、隐藏、旋转、失效 |
| VM-2 | AC-2.1~AC-2.4 | 模式转换矩阵 | NONE/RESIZE/OFFSET/caret |
| VM-3 | AC-3.1~AC-3.2 | 焦点/Web 集成 UT | 单一真值与偏移 |
| VM-4 | AC-3.3~AC-3.4 | Page/Overlay/expand 边界测试 | Page 与 Overlay 控制边界、RESIZE+KEYBOARD/BOTTOM 无扩展及 OFFSET 分流 |

## API 变更分析

### 新增 API

N/A，本 Feat 不新增键盘控制 API；`SafeAreaType.KEYBOARD` 为 API 10 已有类型。

### 变更/废弃 API

N/A；`UIContext.setKeyboardAvoidMode` 属键盘控制域，仅作为输入引用。

## 接口规格

### 接口定义

**键盘安全区消费（内部）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SafeAreaManager::UpdateKeyboardSafeArea / SetKeyBoardAvoidMode` |
| 返回值 | void — 更新 inset、combined safe area 或 offset 状态 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| keyboardHeight | float | 是 | 0 | 非负；结合根高度解释 |
| mode | KeyboardAvoidMode | 是 | 当前 Pipeline 默认 | NONE/RESIZE/RESIZE_WITH_CARET/OFFSET 等既有枚举 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | RESIZE + 键盘显示 | inset 进入 combined safe area | AC-2.1 |
| 2 | OFFSET + 键盘显示 | 页面使用独立 offset | AC-2.2 |
| 3 | RESIZE + expandSafeArea(KEYBOARD, BOTTOM) | Page 继续 RESIZE，扩展设置不生效 | AC-3.4 |
| 4 | UIContext 模式变化 + Overlay 显示 | Page 使用新模式；Overlay 按 OverlayManager 策略避让 | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 是；键盘模式和 caret 路径按各自 API 版本及当前实现分支记录，并保留 RESIZE 下 KEYBOARD/BOTTOM expansion 无效及 Page/Overlay 分治行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** SafeAreaType.KEYBOARD API 10。
- **API 版本号策略:** 键盘控制 API 归外部域，本 Feat 记录安全区消费行为至 API 26。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 单一数据源 | keyboard inset 由 SafeAreaManager 集中维护 | AC-3.2 |
| 模式互斥 | RESIZE combined inset 与 OFFSET 页面偏移不叠加 | AC-2.1, AC-2.2 |
| 跨域边界 | 模式设置 API 属键盘控制，安全区仅消费 | AC-2.4 |
| 容器边界 | UIContext 键盘模式只控制 Page，OverlayManager 保持独立策略 | AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每次键盘/焦点变化按固定 Pipeline 路径重算 | Trace | `frameworks/core/pipeline_ng/pipeline_context.cpp:3274-3509` |
| 功耗 | 仅响应键盘、焦点、旋转事件 | 审查 | VM-1 |
| 内存 | 保存固定 inset、mode、offset 与弱引用 | 生命周期 UT | VM-1 |
| 安全 | 不记录输入内容，仅几何 | API 审查 | VM-3 |
| 可靠性 | 模式切换清理旧状态；RESIZE expansion 例外不改变页面 resize | 转换/边界测试 | VM-2, VM-4 |
| 可测试性 | 高度/模式/焦点可注入 | UT | VM-1~VM-4 |
| 自动化维测 | mode/inset/offset 可通过 Dump/Trace 定位 | Trace | AC-2.4 |
| 定界定位 | keyboard input→Pipeline→Manager→Page 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 软键盘和单页输入常见 | 全模式矩阵 | 真机测试 | AC-2.1 |
| 平板 | 浮动键盘/多窗口常见 | 使用当前窗口几何 | 多窗口测试 | AC-1.3 |
| 折叠屏 | 旋转/展开期间键盘几何变化 | 重算且不叠加旧 offset | 折叠态测试 | AC-1.3, AC-2.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 焦点可见性受键盘避让影响 | AC-3.1 |
| 大字体 | 是 | caret/焦点位置可能改变偏移 | AC-3.1 |
| 深色模式 | 否 | 不涉及颜色 | VM-1 |
| 多窗口/分屏 | 是 | 每窗口根高度与键盘状态独立 | AC-1.3 |
| 多用户 | 否 | 不存输入内容 | VM-3 |
| 版本升级 | 是 | 模式和 caret 分支需回归 | AC-2.4 |
| 生态兼容 | 是 | RESIZE/OFFSET/NONE、Page/Overlay 边界和 KEYBOARD expansion 例外保持 | AC-2.1~AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 键盘安全区模式
  Scenario Outline: 键盘模式选择页面路径
    Given 键盘可见且高度有效
    When KeyboardAvoidMode 为 <mode>
    Then 页面使用 <result>

    Examples:
      | mode | result |
      | RESIZE | combined safe area |
      | OFFSET | keyboard offset |
      | NONE | 无避让 |

  Scenario: RESIZE 下 KEYBOARD 底边扩展不覆盖页面避让
    Given Page 使用 RESIZE 且组件设置 expandSafeArea KEYBOARD BOTTOM
    When 键盘显示
    Then Page 继续 RESIZE 且该 KEYBOARD 扩展设置不生效
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 高度、模式、焦点、Web、Page/Overlay 控制边界与 expand 例外明确
- [x] 键盘控制跨域边界明确
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "keyboard safe area resize offset caret page overlay"
  - repo: "openharmony/interface_sdk-js"
    query: "SafeAreaType KEYBOARD KeyboardAvoidMode UIContext"
```

**关键文档：** `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md`
