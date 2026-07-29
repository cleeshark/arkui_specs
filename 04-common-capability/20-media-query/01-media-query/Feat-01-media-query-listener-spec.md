# 特性规格

> Func-04-20-01-Feat-01 MediaQuery 媒体条件匹配与监听生命周期存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | MediaQuery 媒体条件匹配与监听生命周期 |
| 特性编号 | Func-04-20-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 7+；Static API 23+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 查询结果 | 补录 `matches`、`media` 与 `matchMediaSync` |
| ADDED | 监听生命周期 | 补录 Dynamic on/off 与 Static onChange/offChange |
| ADDED | 条件边界 | 补录比较、方向和设备媒体特征 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/20-media-query/01-media-query/design.md` | 已核对 |
| Dynamic SDK | `interface_sdk-js/api/@ohos.mediaquery.d.ts` | 已核对 |
| Static SDK | `interface_sdk-js/api/@ohos.mediaquery.static.d.ets` | 已核对 |
| NAPI | `interfaces/napi/kits/mediaquery/js_media_query.cpp` | 已核对 |
| Query engine | `frameworks/bridge/common/media_query/media_queryer.cpp` | 已核对 |

## 用户故事

### US-1: 查询当前媒体条件

**作为** ArkUI 应用开发者
**我想要** 用条件字符串同步得到当前媒体匹配结果
**以便** 按当前设备、方向、尺寸或颜色状态选择界面行为

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `matchMediaSync` 且条件可解析 THEN 返回 Listener，其 `matches` 为当前匹配结果且 `media` 保留查询字符串 | 正常 |
| AC-1.2 | WHEN 条件使用实现支持的数值比较、orientation、device-type、round-screen 或 dark-mode THEN Queryer 按当前 MediaFeature 求值 | 正常 |
| AC-1.3 | WHEN 参数不是单个字符串或字符串超出 NAPI 缓冲区 THEN NAPI 参数校验拒绝创建有效 Listener | 异常 |

### US-2: 订阅并释放媒体变化回调

**作为** ArkUI 应用开发者
**我想要** 注册并按需注销媒体变化回调
**以便** 避免页面销毁后仍持有回调引用

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Dynamic `on('change', callback)` 或 Static `onChange(callback)` 注册成功 THEN 前端媒体更新时回调接收 MediaQueryResult | 正常 |
| AC-2.2 | WHEN 同一 Listener 重复注册同一 callback THEN 不保存第二个引用 | 边界 |
| AC-2.3 | WHEN Dynamic `off`/Static `offChange` 传入 callback THEN 仅注销该 callback；WHEN 不传 callback THEN 清理该 Listener 的全部回调 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1~AC-1.3 | R-1~R-3 | 已有实现 | Query/NAPI UT | `js_media_query.cpp:415-448`; `media_queryer.cpp:90-250` |
| AC-2.1~AC-2.3 | R-4~R-6 | 已有实现 | Listener 生命周期 UT | `js_media_query.cpp:180-255` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 单个可解析 condition 字符串 | 创建 Listener 并写入当前 matches/media | 结果为查询时快照 | AC-1.1 |
| R-2 | 行为 | 使用已实现媒体特征 | 用当前 MediaFeature 计算比较或枚举条件 | 不承诺未实现 CSS 语法 | AC-1.2 |
| R-3 | 异常 | 非字符串、参数数不为 1 或过长字符串 | NAPI 断言，不产生有效 Listener | 缓冲区上限由实现控制 | AC-1.3 |
| R-4 | 行为 | 注册 change callback | 前端更新时分发结果 | Dynamic/Static 方法名不同 | AC-2.1 |
| R-5 | 边界 | callback 已注册 | 不重复插入 callback 引用 | 同一 Listener 内去重 | AC-2.2 |
| R-6 | 恢复 | 传 callback 或省略 callback 调用 off | 删除一个或全部 callback 引用 | 页面退出应显式调用注销 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | media_query 单元测试 | 规则、结果和非法参数 |
| VM-2 | AC-2.1~AC-2.3 | NAPI/ANI mock callback | 更新、去重和全量注销 |
| VM-3 | Dynamic/Static/UIContext | SDK/绑定对照 | 版本和入口差异 |

## API 变更分析

### 新增 API

N/A；本次仅登记已有 Public API。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**`matchMediaSync` 与 Listener**

| 属性 | 值 |
|------|-----|
| 函数签名 | `matchMediaSync(condition: string): MediaQueryListener` |
| 返回值 | Listener，提供只读 `matches`、`media` 与监听方法 |
| 开放范围 | Public |
| 错误码 | N/A；Dynamic NAPI 以参数断言处理非法输入 |
| 关联 AC | AC-1.1~AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| condition | string | 是 | 无 | 必须为查询核心可解析的条件字符串 |
| callback | Callback<MediaQueryResult> | on 时是 | 无 | Dynamic 使用 `on/off('change', callback?)`；Static 使用 `onChange/offChange(callback?)` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|----------|
| 1 | 有效 width 或 orientation 条件 | 返回当前结果 | AC-1.1, AC-1.2 |
| 2 | 媒体信息更新且已注册回调 | 回调获得更新结果 | AC-2.1 |
| 3 | listener 销毁前调用无参 off | 清理全部回调引用 | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic API 7；Static API 23。
- **API 版本号策略:** Dynamic、Static 和 UIContext 按各自 SDK `@since` 记录，不统一方法名。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| SDK 权威 | 对外签名以 Dynamic/Static SDK 为准 | AC-1.1, AC-2.1 |
| 实例作用域 | UIContext 入口绑定当前 UI 实例 | AC-2.1 |
| 生命周期 | Listener 回调必须可按单个或全部注销 | AC-2.2, AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 媒体更新只分发已注册 Listener | UT/Trace | `js_media_query.cpp:180-255` |
| 内存 | off 后不保留被注销 callback 引用 | UT | 同上 |
| 可靠性 | 非法输入不创建有效 Listener | NAPI UT | `js_media_query.cpp:415-448` |
| 可测试性 | 条件核心可独立构造 MediaFeature 验证 | 单元测试 | `test/unittest/bridge/common/media_query` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 按当前特征查询 | 方向/尺寸可变化 | UT | Queryer |
| 平板 | 同一条件语法 | device-type 参与匹配 | UT | Queryer |
| 圆形设备 | round-screen 可参与匹配 | 仅实现支持的取值 | UT | Queryer |

## 全局特性影响

| 特性 | 是否适用 | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无专属语义 | VM-1 |
| 深色模式 | 是 | dark-mode 为媒体特征 | AC-1.2 |
| 多窗口/分屏 | 是 | 当前实例的媒体信息变化可回调 | AC-2.1 |
| 版本升级 | 是 | Dynamic/Static 入口版本不同 | VM-3 |
| 生态兼容 | 是 | 保留 System 模块兼容声明，不扩展语法 | AC-1.2 |

## 行为场景（可选，Gherkin）

接口规格中的行为场景已覆盖标准复杂度的调用路径。

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 查询语法、入口与监听释放边界明确
- [x] 未将实现支持范围扩展为浏览器 CSS 全量能力
- [x] AC、规则与 VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "MediaQueryer MediaQueryListener matchMediaSync NAPI ANI"
```

**关键文档：** `docs/kb/api/mediaquery.md`
