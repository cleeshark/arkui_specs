# 特性规格

> `componentUtils.getItemsInShapePath` 的 API 23 System API 契约、默认 NAPI 占位行为、前端覆盖和 vendor 可替换构建边界。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 形状区域图像项筛选 |
| 特性编号 | Func-04-11-01-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `getItemsInShapePath(value: GetItemsInShapePathParams): Array<ImageItem>` System API 契约 | 补录 API 23 dynamic/static 声明、Stage 模型限制、参数模型和 `ratio` 默认值 `0.15` |
| ADDED | 仓内默认 NAPI 实现的可观测行为 | 明确默认实现不执行形状、像素、矩形、旋转或阈值筛选，而是直接透传 `images` 属性 |
| ADDED | vendor 编译期替换边界 | 明确产品配置可替换默认实现并引入 OpenCV 与 image_framework 依赖，但当前检出代码不包含 vendor 算法和对应测试 |
| ADDED | 动态/静态声明与实现通道差异 | canonical SDK 同时声明 dynamic/static，当前 ace_engine 仅检出动态 NAPI 导出，未检出 ANI、CJ、UIContext、NDK 或 ArkUI-X 等价实现 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/11-component-info/01-component-utils/design.md` | Baselined |
| Canonical SDK（dynamic） | `interface_sdk-js/api/@ohos.arkui.componentUtils.d.ts:446-598` | 已核对 |
| Canonical SDK（static） | `interface_sdk-js/api/@ohos.arkui.componentUtils.static.d.ets:386-537` | 已核对 |
| 默认 NAPI 实现 | `interfaces/napi/kits/componentutils/js_mistouch_prevention.cpp:25-46` | 已实现，占位透传 |
| NAPI 导出 | `interfaces/napi/kits/componentutils/js_component_utils.cpp:227-237` | 已实现 |
| 构建选择 | `interfaces/napi/kits/componentutils/BUILD.gn:19-46` | 已实现 |
| vendor 配置装载 | `build/ace_ext.gni:16-41` | 已实现 |
| bundle 依赖 | `bundle.json:95,120` | 已声明 |

## 用户故事

### US-1: 通过形状区域筛选图像项

**作为** 使用 ArkUI System API 的系统应用开发者，  
**我想要** 提交图像项、选择区域路径和可选阈值，  
**以便** 按 API 契约取得位于选择区域内的图像项。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN API 23 Stage 模型代码使用 dynamic 或 static 声明调用 `getItemsInShapePath(value)` THEN 编译期接口返回类型为 `Array<ImageItem>`，开放范围为 System API | 正常 |
| AC-1.2 | WHEN `value.images` 中的元素参与契约校验 THEN 每个元素包含 `PixelMap image`、`common2D.Rect rect` 和 `int zIndex`，并可选包含 `Rotation2D rotation` | 正常 |
| AC-1.3 | WHEN `rotation` 存在 THEN 其 `angle`、`centerX`、`centerY` 均按 `double` 字段解释 | 正常 |
| AC-1.4 | WHEN 调用方省略 `ratio` THEN SDK 契约使用默认值 `0.15` 表示选区内非透明空白像素相对图像总像素的比例阈值 | 边界 |
| AC-1.5 | WHEN 按 canonical SDK 契约执行筛选 THEN 返回位于 `shapePath` 选择区域内的 `ImageItem` 数组 | 正常 |

### US-2: 识别仓内默认实现的占位行为

**作为** API、运行时和测试维护者，  
**我想要** 精确识别未启用 vendor 替换时的返回语义，  
**以便** 不把透传占位实现误判为已经完成图像筛选。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 默认 NAPI 实现收到一个包含 `images` 属性的参数对象 THEN 返回该 `images` 属性的原始值并保持对象标识，不读取 `shapePath`、`ratio`、像素、矩形、旋转或 `zIndex` | 正常 |
| AC-2.2 | WHEN 默认 NAPI 实现未收到参数 THEN 返回新建空数组 `[]` | 异常 |
| AC-2.3 | WHEN 默认 NAPI 实现收到 `{}` 或其他不存在 `images` 属性的对象 THEN 返回 JavaScript `undefined`，与 SDK 声明的数组返回类型不一致 | 异常 |
| AC-2.4 | WHEN 默认 NAPI 实现收到的 `images` 属性不是数组 THEN 原样返回该属性值，不执行类型校验或转换 | 异常 |
| AC-2.5 | WHEN 调用方传入一个以上实参 THEN 默认 NAPI 只请求并处理第一个实参，其余实参不影响返回值 | 边界 |

### US-3: 区分实现通道与产品替换边界

**作为** 产品集成、ArkTS 静态和跨语言前端维护者，  
**我想要** 明确当前实现覆盖与编译期替换机制，  
**以便** 正确安排集成验证并暴露缺失通道。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 构建未定义 `vendor_configs.ace_engine_mistouch_prevention` THEN `napi_componentutils_static` 编译仓内 `js_mistouch_prevention.cpp` 默认实现 | 正常 |
| AC-3.2 | WHEN 构建定义 `vendor_configs.ace_engine_mistouch_prevention` THEN source list 改由 `ace_engine_mistouch_prevention_mode` 提供，并加入 OpenCV、image_framework 与 PixelMap 相关依赖 | 正常 |
| AC-3.3 | WHEN 评审 vendor 路径的筛选算法、阈值边界和异常行为 THEN 当前检出代码只证明替换接口与依赖，不能推导未检出的 vendor 实现行为 | 边界 |
| AC-3.4 | WHEN 核对 API 23 前端覆盖 THEN canonical SDK 同时声明 dynamic/static，但当前 ace_engine 仅检出动态 NAPI 导出，未检出 ANI、CJ、UIContext、NDK 或 ArkUI-X 等价实现 | 异常 |
| AC-3.5 | WHEN 评估现有验证证据 THEN 当前仓未检出该 API 的专用 UT、XTS 或示例，默认实现和 vendor 替换均需要独立验证资产 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.3 | R-1~R-2 | 已有 SDK 声明 | dynamic/static SDK 静态扫描 | `@ohos.arkui.componentUtils.d.ts:446-598`; `@ohos.arkui.componentUtils.static.d.ets:386-537` |
| AC-1.4~AC-1.5 | R-3~R-4 | 已有 SDK 声明 | SDK 文档与类型检查 | `@ohos.arkui.componentUtils.d.ts:543-598`; `@ohos.arkui.componentUtils.static.d.ets:482-537` |
| AC-2.1 | R-5 | 已有默认实现 | NAPI 单测、对象标识断言 | `js_mistouch_prevention.cpp:25-46` |
| AC-2.2~AC-2.4 | R-6~R-8 | 已有默认实现 | NAPI 缺参/缺属性/错误类型测试 | `js_mistouch_prevention.cpp:28-46` |
| AC-2.5 | R-9 | 已有默认实现 | 多实参 NAPI 测试 | `js_mistouch_prevention.cpp:28-35` |
| AC-3.1~AC-3.3 | R-10~R-11 | 已有构建边界 | GN 配置矩阵审查、产品构建验证 | `BUILD.gn:19-46`; `ace_ext.gni:16-41`; `bundle.json:95,120` |
| AC-3.4 | R-12 | 通道缺口 | SDK/实现符号扫描、static 调用验证 | `js_component_utils.cpp:227-237`; canonical SDK dynamic/static 声明 |
| AC-3.5 | R-13 | 验证缺口 | 测试目录与符号扫描 | 当前检出仓库搜索结果 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | API 23 Stage 模型 dynamic/static 编译环境解析模块声明 | 暴露 `getItemsInShapePath(GetItemsInShapePathParams): Array<ImageItem>` System API | API 22 及以下无该声明；无 crossplatform、atomicservice 或 permission 标签 | AC-1.1 |
| R-2 | 行为 | 类型系统检查 `ImageItem` 和 `Rotation2D` | `image`/`rect`/`zIndex` 必填，`rotation` 可选；旋转包含 3 个 `double` 字段 | `zIndex` 为 `int`；SDK 未声明额外字段约束 | AC-1.2、AC-1.3 |
| R-3 | 边界 | `GetItemsInShapePathParams.ratio` 被省略 | 契约默认阈值为 `0.15` | SDK 未声明最小值、最大值、NaN 或无穷值的处理 | AC-1.4 |
| R-4 | 行为 | 合法 `images`、`shapePath` 和可选 `ratio` 交给符合 SDK 契约的实现 | 返回位于选择区域内的 `ImageItem` 数组 | vendor 算法未检出，不规定点边界、旋转矩形或阈值相等时的内部算法 | AC-1.5 |
| R-5 | 行为 | 默认 NAPI 的第一个实参具有 `images` 属性 | 直接返回属性值并保持引用标识 | 不读取或验证 `shapePath`、`ratio` 及 ImageItem 字段 | AC-2.1 |
| R-6 | 异常 | 默认 NAPI 实参个数为 0 | 创建并返回新的空数组 | 每次无参调用创建独立数组；不抛 SDK 错误码 | AC-2.2 |
| R-7 | 异常 | 默认 NAPI 第一个实参对象不存在 `images` 属性 | 返回 `undefined` | 与声明返回类型 `Array<ImageItem>` 不一致 | AC-2.3 |
| R-8 | 异常 | 默认 NAPI 的 `images` 属性值为非数组值，包括 `null`、number、string 或普通对象 | 原样返回该值 | 不执行数组检查、复制或元素验证 | AC-2.4 |
| R-9 | 边界 | 默认 NAPI 调用实参个数大于 1 | 仅读取第一个实参 | `argc` 请求上限为 1，后续实参被忽略 | AC-2.5 |
| R-10 | 行为 | 未定义 mistouch prevention vendor 配置 | 编译 `js_mistouch_prevention.cpp` | 该路径是仓内默认占位实现 | AC-3.1 |
| R-11 | 行为 | 定义 mistouch prevention vendor 配置 | 使用外部 source list，并链接 OpenCV 与 image/PixelMap 依赖 | vendor 源码不在当前检出范围，不规定其算法结果 | AC-3.2、AC-3.3 |
| R-12 | 异常 | 对照 dynamic/static SDK 与当前 ace_engine 导出 | 动态 NAPI 有 `getItemsInShapePath` 导出；其他等价运行时入口未检出 | static 声明存在不等同于 ANI 后端已实现 | AC-3.4 |
| R-13 | 异常 | 搜索当前仓库的 API 专用验证资产 | 记录专用 UT、XTS、示例均未检出 | 不以 Feat-01 的 ComponentUtils 测试替代本 API 验证 | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1、AC-1.2、AC-1.3、AC-1.4 | canonical SDK dynamic/static 声明扫描 | since、systemapi、stagemodelonly、字段类型和 `ratio=0.15` |
| VM-2 | AC-1.5 | vendor 产品集成测试 | 真实筛选结果与选择区域契约；算法细节以实际 vendor 实现为准 |
| VM-3 | AC-2.1 | NAPI 单测 | 返回值与输入 `images` 严格相等，修改返回数组可观察到同一引用 |
| VM-4 | AC-2.2、AC-2.3、AC-2.4 | NAPI 参数矩阵单测 | 无参为 `[]`、缺 `images` 为 `undefined`、非数组原样返回 |
| VM-5 | AC-2.5 | NAPI 多实参单测 | 第二个及后续实参不影响结果 |
| VM-6 | AC-3.1、AC-3.2、AC-3.3 | GN 双配置构建与依赖审查 | 默认 source 与 vendor source list 互斥、外部依赖完整、算法不可由构建文件推断 |
| VM-7 | AC-3.4 | dynamic NAPI/ANI/CJ/NDK/UIContext/ArkUI-X 符号扫描和调用测试 | 声明与运行时通道覆盖差异 |
| VM-8 | AC-3.5 | 测试资产清单检查 | 为默认实现和 vendor 产品分别建立可追溯验证证据 |

## API 变更分析

### 新增 API

> 下表为 API 23 已有声明的规格补录。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `componentUtils.getItemsInShapePath` | System | `images: Array<ImageItem>`、`shapePath: Array<common2D.Point>`、可选 `ratio: double` | `Array<ImageItem>` | N/A，SDK 未声明 throws | 返回位于选择区域内的图像项 | AC-1.1~AC-1.5 |

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**componentUtils.getItemsInShapePath**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getItemsInShapePath(value: GetItemsInShapePathParams): Array<ImageItem>` |
| 返回值 | `Array<ImageItem>` — SDK 契约为位于选择区域内的图像项；仓内默认 NAPI 实际透传 `images` |
| 开放范围 | System API，Stage 模型限定 |
| 错误码 | N/A，SDK 未声明 throws |
| 关联 AC | AC-1.1~AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| `value` | `GetItemsInShapePathParams` | 是 | 无 | SDK 要求对象包含 `images` 和 `shapePath`；默认 NAPI 未执行对象类型校验 |
| `value.images` | `Array<ImageItem>` | 是 | 无 | 每项含 `PixelMap image`、`Rect rect`、`int zIndex`，`rotation` 可选；默认 NAPI 仅取属性值 |
| `value.shapePath` | `Array<common2D.Point>` | 是 | 无 | SDK 表示选择区域路径点；默认 NAPI 不读取该字段 |
| `value.ratio` | `double` | 否 | `0.15` | SDK 未声明数值范围；默认 NAPI 不读取该字段 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 符合 SDK 契约的产品实现 | 见 Gherkin 场景“按选择区域筛选” | AC-1.1~AC-1.5 |
| 2 | 仓内默认 NAPI 实现 | 见 Gherkin 场景“默认实现透传 images”和异常参数矩阵 | AC-2.1~AC-2.5 |
| 3 | 默认/vendor 构建切换 | 见 Gherkin 场景“编译期选择实现” | AC-3.1~AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；本规格补录 API 23 已有声明和当前实现。SDK 筛选契约与仓内默认透传实现存在重大偏差。
- **配置文件格式变更:** 否；沿用既有 `vendor_configs.ace_engine_mistouch_prevention` 配置入口。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 23。
- **API 版本号策略:** dynamic/static 均标注 `@since 23`，同时标注 `@systemapi` 与 `@stagemodelonly`；未标注 crossplatform、atomicservice、permission、throws、callback、Promise、deprecated 或 useinstead。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 契约优先 | 外部 API 签名、开放范围和类型以 canonical dynamic/static 声明为准，源码偏差必须显式记录 | AC-1.1~AC-1.5、AC-2.1~AC-2.4 |
| 默认/vendor 二选一 | GN 配置必须只选择仓内默认实现或 vendor source list，不能同时编译两套实现 | AC-3.1~AC-3.3 |
| 不推导未检出算法 | 构建依赖和接口名称不能作为筛选算法、阈值边界或正确性的证据 | AC-1.5、AC-3.3 |
| 通道能力不互相代替 | dynamic NAPI 导出不能证明 static ANI、CJ、NDK、UIContext 或 ArkUI-X 已实现 | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | canonical SDK 和默认实现未声明时延、吞吐或图像数量阈值 | 产品 vendor 按真实算法建立图像数量与像素规模分档基线 | vendor 集成测试报告 |
| 功耗 | 无独立功耗指标 | 产品场景功耗回归 | 产品验证报告 |
| 内存 | 默认实现不复制 `images`；vendor 实现的 PixelMap/OpenCV 内存峰值需按实际源码验证 | 引用标识测试、产品内存采样 | NAPI UT、vendor 集成测试 |
| 安全 | System API、Stage 模型限定；不新增权限声明 | SDK 标签检查、调用范围验证 | canonical SDK |
| 可靠性 | 默认实现异常参数返回类型必须保持本规格记录的可观测结果 | 参数矩阵单测 | NAPI UT |
| 可测试性 | 每个 AC 至少映射一个 VM；默认和 vendor 路径分开取证 | 追溯表检查 | VM-1~VM-8 |
| 自动化维测 | 当前实现仅有入口日志，无专用统计指标 | 日志检查 | `js_mistouch_prevention.cpp:27,37,43` |
| 定界定位 | 构建产物需能区分默认 source 与 vendor source list | GN args/source 清单审查 | `BUILD.gn:33-46` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | SDK 未声明设备差异 | 由产品实际选择的默认或 vendor 实现决定 | 产品集成测试 | 构建 source 清单 |
| 平板 | 无声明差异 | 同手机 | 产品集成测试 | 构建 source 清单 |
| 折叠屏 | 无声明差异 | 展开/折叠不改变 API 类型契约 | 展开态/折叠态产品测试 | 产品验证报告 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 处理 PixelMap 和几何数据，不直接改变语义树 | 无 |
| 大字体 | 否 | 无文字布局接口 | 无 |
| 深色模式 | 否 | 不改变 PixelMap 内容或主题资源 | 无 |
| 多窗口/分屏 | 是 | 输入坐标由调用方提供，SDK 未声明窗口坐标系转换 | AC-1.5 |
| 多用户 | 否 | 不访问用户数据服务 | 无 |
| 版本升级 | 是 | API 23 起可见；API 22 及以下无声明 | AC-1.1 |
| 生态兼容 | 是 | System API 且 Stage-only；dynamic/static 声明与实现覆盖不一致 | AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 形状区域图像项筛选
  作为 ArkUI System API 的使用者和维护者
  我想要区分 SDK 筛选契约、默认占位实现和 vendor 产品实现
  以便正确验证返回结果与通道覆盖

  Scenario: 按选择区域筛选
    Given API 23 Stage 模型环境提供符合 SDK 契约的实现
    And value 包含合法 images 和 shapePath
    When 调用 getItemsInShapePath(value)
    Then 返回值类型为 Array<ImageItem>
    And 返回项位于 shapePath 表示的选择区域内

  Scenario: 默认实现透传 images
    Given 构建未启用 vendor mistouch prevention 配置
    And value.images 引用数组 imagesRef
    When 调用 getItemsInShapePath(value)
    Then 返回值严格等于 imagesRef
    And shapePath 与 ratio 的取值不影响返回值

  Scenario Outline: 默认实现异常参数矩阵
    Given 构建使用仓内默认实现
    When 以 <输入> 调用 getItemsInShapePath
    Then 返回 <结果>

    Examples:
      | 输入 | 结果 |
      | 无实参 | 新建空数组 |
      | 空对象 | undefined |
      | images 为 null | null |
      | images 为数字 1 | 数字 1 |

  Scenario: 编译期选择实现
    Given 产品配置定义 vendor_configs.ace_engine_mistouch_prevention
    When 生成 napi_componentutils_static 的 source list
    Then 使用 ace_engine_mistouch_prevention_mode 提供的外部源文件
    And 链接 OpenCV 与 image_framework 相关依赖
    And 不编译仓内 js_mistouch_prevention.cpp
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/interface_sdk-js"
    query: "componentUtils getItemsInShapePath API 23 dynamic/static System API contract and ImageItem data model"
  - repo: "openharmony/arkui_ace_engine"
    query: "getItemsInShapePath default NAPI passthrough behavior, export registration, vendor source replacement and test coverage"
```

**关键文档：** canonical SDK dynamic/static 声明、`js_mistouch_prevention.cpp`、ComponentUtils `BUILD.gn`、`build/ace_ext.gni`。
