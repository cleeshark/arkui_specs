# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RefPtr/WeakPtr/AceType引用计数智能指针 |
| 特性编号 | Func-03-08-02-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定 ArkUI ace_engine 侵入式引用计数智能指针体系：Referenced 基类持有 RefCounter、RefPtr 强引用智能指针、WeakPtr 弱引用智能指针与 Upgrade 原子提升、RefCounter 基于 std::atomic CAS 的线程安全计数器与自销毁机制、AceType + DECLARE_ACE_TYPE 自定义 RTTI（替代 -fno-rtti 下的 C++ dynamic_cast）、frameworks/base/memory/ 转发层重定向。不涉及 MemoryMonitor 调试分配监控（Feat-02）、NG MemoryManager 内存回收管线（Feat-03）、系统内存压力监听与全局 GC（Feat-04）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Referenced 基类与 RefCounter 生命周期规格 | referenced.h:38-177 定义 Referenced 持有 RefCounter* refCounter_ (line 172)，构造时 RefCounter::Create() (line 109)，析构时 DecWeakRef (line 121) |
| ADDED | RefPtr 强引用智能指针规格 | referenced.h:182-356 定义 RefPtr final 模板类，私有构造 IncRefCount (line 341-347)，析构 DecRefCount (line 206)，operator== 按 refCounter_ 指针比较 (line 287) |
| ADDED | WeakPtr 弱引用智能指针与 Upgrade 规格 | referenced.h:361-536 定义 WeakPtr final 模板类，私有构造 IncWeakRef (line 525)，Upgrade() 调用 TryIncStrongRef 原子提升 (line 412-416)，Invalid() 检查 (line 417-420) |
| ADDED | RefCounter 原子计数器与自销毁规格 | ref_counter.h:27-64 定义 ThreadSafeCounter 使用 std::atomic CAS；ref_counter.h:66-111 定义 RefCounter，strongRef_{0} + weakRef_{1} 初始值 (line 107-110)，DecWeakRef 归零时 delete this (line 97-99) |
| ADDED | AceType 自定义 RTTI 规格 | ace_type.h:38-39 定义 DECLARE_ACE_TYPE 宏；ace_type.h:50 定义 AceType 继承 virtual TypeInfoBase + virtual Referenced；ace_type.h:56-142 定义 DynamicCast/TypeId/TypeName/InstanceOf 模板 |
| ADDED | TypeInfoBase 自定义类型系统规格 | type_info_base.h:29-71 定义 DECLARE_CLASSTYPE_INFO / DECLARE_RELATIONSHIP_OF_CLASSES 宏；type_info_base.h:76-174 定义 TypeInfoBase 与 TypeInfoHelper，SafeCastById 哈希查找 |
| ADDED | 框架转发层重定向规格 | frameworks/base/memory/ 下 4 个头文件各 1 行 #include 重定向到 ui/base/ |

## 输入文档

- 关联设计：`specs/03-engine-framework/08-dfx-foundation/02-memory-management/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `interfaces/inner_api/ace_kit/include/ui/base/referenced.h`（540 行）—— Referenced 基类、RefPtr、WeakPtr 完整实现
  - `interfaces/inner_api/ace_kit/include/ui/base/ref_counter.h`（115 行）—— ThreadSafeCounter 与 RefCounter 原子计数器
  - `interfaces/inner_api/ace_kit/include/ui/base/ace_type.h`（150 行）—— AceType 基类与 DECLARE_ACE_TYPE 宏
  - `interfaces/inner_api/ace_kit/include/ui/base/type_info_base.h`（178 行）—— 自定义 RTTI 类型系统
  - `frameworks/base/memory/referenced.h`（21 行）—— 转发 shim
  - `frameworks/base/memory/ace_type.h`（21 行）—— 转发 shim
  - `frameworks/base/memory/ref_counter.h`（21 行）—— 转发 shim
  - `frameworks/base/memory/type_info_base.h`（21 行）—— 转发 shim

## 用户故事

### US-1: Referenced 基类与 RefCounter 初始状态

- As a 框架对象开发者
- I want 继承 Referenced 的对象在构造时自动创建 RefCounter，初始 strongRef=0、weakRef=1
- So that 对象可被 RefPtr/WeakPtr 安全管理，且 RefCounter 在对象自身生命周期内始终有效

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN Referenced 构造函数执行 THEN 调用 `RefCounter::Create()`（`ref_counter.h:68-71`）创建 RefCounter 对象并赋值给 `refCounter_` 成员（`referenced.h:109`）。来源：`referenced.h:108-110` | 正常 |
| AC-1.2 | WHEN RefCounter 被创建 THEN `strongRef_` 初始值为 0（`ref_counter.h:107`），`weakRef_` 初始值为 1（`ref_counter.h:110`），weakRef 额外 1 代表 Referenced 对象自身持有引用计数器。来源：`ref_counter.h:107-110` | 正常 |
| AC-1.3 | WHEN Referenced 析构函数执行 THEN 调用 `refCounter_->DecWeakRef()`（`referenced.h:121`）递减自身持有的 weak reference，随后将 `refCounter_` 置为 nullptr（`referenced.h:122`）。来源：`referenced.h:118-128` | 正常 |
| AC-1.4 | WHEN 对 Referenced 对象进行拷贝构造或移动构造 THEN 编译失败，因为 `ACE_DISALLOW_COPY_AND_MOVE(Referenced)`（`referenced.h:174`）将拷贝构造、拷贝赋值、移动构造、移动赋值声明为 delete。来源：`referenced.h:174` | 边界 |

### US-2: RefPtr 强引用管理

- As a 框架内存使用者
- I want RefPtr 在构造时递增 strongRef、析构时递减 strongRef，strongRef 归零且 MaybeRelease 返回 true 时自动销毁对象
- So that 强引用生命周期内对象不会被释放，引用计数归零后自动回收

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN RefPtr 私有构造函数 `RefPtr(T* rawPtr, bool forceIncRef = true)`（`referenced.h:341`）以 forceIncRef=true 调用 THEN 若 rawPtr != nullptr 则调用 `rawPtr_->IncRefCount()`（`referenced.h:345`），IncRefCount 内部调用 `refCounter_->IncStrongRef()`（`referenced.h:91`）。来源：`referenced.h:341-347` | 正常 |
| AC-2.2 | WHEN RefPtr 析构函数执行且 rawPtr_ != nullptr THEN 调用 `rawPtr_->DecRefCount()`（`referenced.h:206`），随后将 rawPtr_ 置为 nullptr（`referenced.h:207`）。来源：`referenced.h:202-209` | 正常 |
| AC-2.3 | WHEN DecRefCount 执行 THEN 调用 `refCounter_->DecStrongRef()` 获取返回值 refCount（`referenced.h:95`），若 refCount == 0 且 `MaybeRelease()` 返回 true（默认实现 `referenced.h:130-133` 返回 true） THEN 执行 `delete this`（`referenced.h:98`）。来源：`referenced.h:93-100` | 正常 |
| AC-2.4 | WHEN RefPtr 赋值操作符执行 THEN 通过 `Swap(RefPtr(other))` 实现：先构造临时 RefPtr 递增新对象 strongRef，swap 后旧 RefPtr 析构递减旧对象 strongRef。来源：`referenced.h:246-278` | 正常 |
| AC-2.5 | WHEN RefPtr::operator== 比较两个对象 THEN 当双方 rawPtr_ 均非空时比较 `rawPtr_->refCounter_ == rawPtr->refCounter_`（`referenced.h:287`），即按引用计数器指针判定同一性而非原始对象指针。来源：`referenced.h:282-288` | 正常 |

### US-3: WeakPtr 弱引用与 Upgrade 原子提升

- As a 框架开发者
- I want WeakPtr 仅持有弱引用不阻止对象释放，Upgrade 时通过 TryIncStrongRef 原子测试并递增避免竞争窗口
- So that 可安全观测对象生命周期且消除 check-then-act 竞争

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN WeakPtr 私有构造函数 `WeakPtr(O* rawPtr, RefCounter* aceRef)`（`referenced.h:522`）执行 THEN 仅在 refCounter_ != nullptr 时调用 `refCounter_->IncWeakRef()`（`referenced.h:525`），不调用 IncStrongRef，即不改变 strongRef 计数。来源：`referenced.h:521-527` | 正常 |
| AC-3.2 | WHEN WeakPtr::Upgrade()（`referenced.h:412`）执行 THEN 检查 `refCounter_ != nullptr && refCounter_->TryIncStrongRef()`（`referenced.h:415`），TryIncStrongRef 返回 true 时以 forceIncRef=false 构造 `RefPtr<T>(unsafeRawPtr_, false)`（`referenced.h:415`），不再额外递增 strongRef。来源：`referenced.h:412-416` | 正常 |
| AC-3.3 | WHEN WeakPtr::Upgrade() 执行且 TryIncStrongRef 返回 false（strongRef 已为 0） THEN 返回 `nullptr`（即空 RefPtr）（`referenced.h:415`）。来源：`referenced.h:412-416` | 异常 |
| AC-3.4 | WHEN WeakPtr::Invalid() 被调用 THEN 返回 `refCounter_ == nullptr || refCounter_->StrongRefCount() == 0`（`referenced.h:419`）。来源：`referenced.h:417-420` | 正常 |
| AC-3.5 | WHEN WeakPtr 析构且 refCounter_ != nullptr THEN 调用 `refCounter_->DecWeakRef()`（`referenced.h:392`），随后将 refCounter_ 和 unsafeRawPtr_ 置为 nullptr（`referenced.h:393-394`）。来源：`referenced.h:388-396` | 正常 |

### US-4: RefCounter 自销毁与 ThreadSafeCounter 原子操作

- As a 框架内存基础设施维护者
- I want RefCounter 使用 std::atomic CAS 保证线程安全，且在所有弱引用（含对象自身持有）归零时自动销毁自身
- So that 多线程下引用计数操作无数据竞争，RefCounter 生命周期无需外部管理

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN RefCounter::DecWeakRef() 执行（`ref_counter.h:94`） THEN 调用 `weakRef_.Decrease()`（`ref_counter.h:96`）获取返回值 refCount，若 refCount == 0 THEN 执行 `delete this`（`ref_counter.h:99`）。来源：`ref_counter.h:94-101` | 正常 |
| AC-4.2 | WHEN ThreadSafeCounter::Increase() 执行 THEN 调用 `count_.fetch_add(1, std::memory_order_relaxed)`（`ref_counter.h:34`）。来源：`ref_counter.h:32-35` | 正常 |
| AC-4.3 | WHEN ThreadSafeCounter::Decrease() 执行 THEN 调用 `count_.fetch_sub(1, std::memory_order_release)`（`ref_counter.h:38`）获取旧值 count，返回 `count - 1`（`ref_counter.h:40`），并通过 `ACE_DCHECK(count > 0)` 断言计数不会下溢。来源：`ref_counter.h:36-41` | 正常 |
| AC-4.4 | WHEN ThreadSafeCounter::TryIncrease() 执行（`ref_counter.h:48`） THEN 先读取 `CurrentCount()`（`ref_counter.h:50`），若 count == 0 返回 false（`ref_counter.h:52-53`），否则通过 `compare_exchange_weak(count, count + 1, std::memory_order_relaxed)` CAS 循环（`ref_counter.h:56`）原子递增，CAS 失败时重试。来源：`ref_counter.h:48-58` | 正常 |
| AC-4.5 | WHEN RefCounter 析构函数声明为 protected（`ref_counter.h:104`） THEN 仅 RefCounter 自身成员函数（DecWeakRef 中的 delete this）可触发析构，外部无法直接 delete RefCounter。来源：`ref_counter.h:103-104` | 边界 |

### US-5: MakeRefPtr / Claim / WeakClaim 工厂方法

- As a 框架对象创建者
- I want 通过 Referenced::MakeRefPtr 安全创建新对象并返回 RefPtr，通过 Claim 将已有裸指针包装为 RefPtr，通过 WeakClaim 包装为 WeakPtr
- So that 对象创建和指针包装均在统一入口完成，并附带安全检查

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `Referenced::MakeRefPtr<T, Args...>(args...)` 被调用 THEN 执行 `new T(std::forward<Args>(args)...)`（`referenced.h:76`）创建对象，随后调用 `Claim<T, true>(ptr)`（`referenced.h:76`），isNewOrRecycle=true 分支检查 `rawPtr->RefCount()`（`referenced.h:45`），若 RefCount > 0 则调用 `OnDetectedClaimDeathObj(true)`（`referenced.h:46`）。来源：`referenced.h:73-77,44-47` | 正常 |
| AC-5.2 | WHEN `Referenced::Claim<T>(rawPtr)` 以默认 isNewOrRecycle=false 调用且 rawPtr 的 RefCount() == 0 THEN 调用 `rawPtr->OnDetectedClaimDeathObj(false)`（`referenced.h:56`），检测到对已释放对象的 Claim 操作。来源：`referenced.h:54-57` | 异常 |
| AC-5.3 | WHEN `Referenced::WeakClaim<T>(rawPtr)` 被调用 THEN 直接返回 `WeakPtr<T>(rawPtr)`（`referenced.h:68`），WeakPtr 私有构造函数从中提取 `rawPtr->refCounter_`（`referenced.h:520`）并调用 IncWeakRef。来源：`referenced.h:65-69,518-527` | 正常 |

### US-6: AceType 自定义 RTTI

- As a 框架组件开发者
- I want 继承 AceType 并使用 DECLARE_ACE_TYPE 宏声明类型关系，通过 DynamicCast/InstanceOf/TypeId/TypeName 实现类型识别
- So that 在 -fno-rtti 编译环境下替代 C++ RTTI 进行安全的向下转型和类型检查

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `DECLARE_ACE_TYPE(classname, ...)` 宏在类内展开（`ace_type.h:38`） THEN 生成 `DECLARE_RELATIONSHIP_OF_CLASSES(__VA_ARGS__)`（`ace_type.h:38`）展开为 SafeCastById / GetTypeId / GetTypeName 虚方法覆盖及 TrySafeCastById 模板链，并添加 `friend class Referenced`（`ace_type.h:39`）。来源：`ace_type.h:38-39`, `type_info_base.h:44-71` | 正常 |
| AC-6.2 | WHEN `AceType::DynamicCast<T>(O* rawPtr)` 被调用 THEN 委托 `TypeInfoHelper::DynamicCast<T>(rawPtr)`（`ace_type.h:59`），后者在 rawPtr != nullptr 时返回 `reinterpret_cast<T*>(rawPtr->SafeCastById(T::TypeId()))`（`type_info_base.h:108`），SafeCastById 通过递归 TrySafeCastById 在继承链中匹配目标 TypeId，未匹配返回 0。来源：`type_info_base.h:104-109,44-62` | 正常 |
| AC-6.3 | WHEN `DECLARE_CLASSTYPE_INFO(classname)` 宏展开 THEN 生成静态方法 `TypeId()` 返回 `static IdType myTypeId = std::hash<std::string>{}(#classname)`（`type_info_base.h:38`），即类名字符串的哈希值作为类型 ID，IdType 为 `std::size_t`（`type_info_base.h:81`）。来源：`type_info_base.h:29-41,81` | 正常 |
| AC-6.4 | WHEN `AceType::InstanceOf<T>(O* rawPtr)` 被调用 THEN 委托 `TypeInfoHelper::InstanceOf<T>(rawPtr)`（`ace_type.h:131`），等价于 `DynamicCast<T>(rawPtr) != nullptr`（`type_info_base.h:167`）。来源：`ace_type.h:128-132`, `type_info_base.h:164-168` | 正常 |
| AC-6.5 | WHEN AceType 继承关系声明为 `public virtual TypeInfoBase, public virtual Referenced`（`ace_type.h:50`） THEN 通过 virtual 继承解决 TypeInfoBase 与 Referenced 的菱形继承问题，DECLARE_ACE_TYPE(AceType, TypeInfoBase)（`ace_type.h:51`）声明 AceType 的直接父类为 TypeInfoBase。来源：`ace_type.h:50-51` | 正常 |

### US-7: 框架转发层重定向

- As a 框架内部代码消费者
- I want 通过 `frameworks/base/memory/` 下的头文件引用智能指针，这些文件自动重定向到 ace_kit inner API 的规范实现
- So that 框架代码使用 `#include "base/memory/referenced.h"` 等路径即可获得完整智能指针能力，同时保持 ace_kit 为唯一定义源

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 框架代码 `#include "base/memory/referenced.h"` THEN 该文件（`frameworks/base/memory/referenced.h:19`）仅含一行 `#include "ui/base/referenced.h"` 重定向到 ace_kit 规范实现。同理 ace_type.h、ref_counter.h、type_info_base.h 各为 1 行重定向（`frameworks/base/memory/ace_type.h:19`、`frameworks/base/memory/ref_counter.h:19`、`frameworks/base/memory/type_info_base.h:19`）。来源：各转发 shim 文件 line 19 | 正常 |
| AC-7.2 | WHEN 框架代码引用 4 个智能指针头文件之一 THEN 实际编译入口为 `frameworks/base/memory/*.h`，最终 include 解析到 `interfaces/inner_api/ace_kit/include/ui/base/*.h`，保证 ace_kit 为唯一定义源（design.md ADR-1）。来源：`frameworks/base/memory/*.h:19` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-01 | 代码评审 | 代码审查 |
| AC-1.2 | R-1 | TASK-01 | 代码评审 | 代码审查 |
| AC-1.3 | R-9 | TASK-01 | 代码评审 | 代码审查 |
| AC-1.4 | R-14 | TASK-01 | 编译验证 | 代码审查 |
| AC-2.1 | R-2 | TASK-01 | 单元测试 | 代码审查 |
| AC-2.2 | R-3 | TASK-01 | 单元测试 | 代码审查 |
| AC-2.3 | R-3 / R-10 | TASK-01 | 单元测试 | 代码审查 |
| AC-2.4 | R-2 / R-3 | TASK-01 | 单元测试 | 代码审查 |
| AC-2.5 | R-11 | TASK-01 | 代码评审 | 代码审查 |
| AC-3.1 | R-4 | TASK-01 | 单元测试 | 代码审查 |
| AC-3.2 | R-7 | TASK-01 | 单元测试 | 代码审查 |
| AC-3.3 | R-7 / R-8 | TASK-01 | 单元测试 | 代码审查 |
| AC-3.4 | R-7 | TASK-01 | 单元测试 | 代码审查 |
| AC-3.5 | R-5 | TASK-01 | 单元测试 | 代码审查 |
| AC-4.1 | R-6 | TASK-01 | 单元测试 | 代码审查 |
| AC-4.2 | R-12 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.3 | R-12 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.4 | R-8 / R-12 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.5 | R-6 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.1 | R-1 / R-15 | TASK-01 | 单元测试 | 代码审查 |
| AC-5.2 | R-15 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.3 | R-4 | TASK-01 | 单元测试 | 代码审查 |
| AC-6.1 | R-13 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.2 | R-13 | TASK-01 | 单元测试 | 代码审查 |
| AC-6.3 | R-13 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.4 | R-13 | TASK-01 | 单元测试 | 代码审查 |
| AC-6.5 | R-16 | TASK-01 | 代码评审 | 代码审查 |
| AC-7.1 | R-17 | TASK-01 | 代码评审 | 代码审查 |
| AC-7.2 | R-17 | TASK-01 | 代码评审 | 代码审查 |

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Referenced 对象构造 | 构造函数调用 RefCounter::Create() 创建 RefCounter，初始 strongRef_=0、weakRef_=1。weakRef 初始值 1 代表 Referenced 对象自身持有引用计数器。 | RefCounter 通过 `new` 在堆上分配（`ref_counter.h:70`）。 | AC-1.1 / AC-1.2 / AC-5.1 |
| R-2 | 行为 | RefPtr 持有对象（forceIncRef=true） | 调用 IncStrongRef 原子递增 strongRef。赋值操作通过 Swap 模式先增新对象后减旧对象。 | RefPtr 私有构造函数 forceIncRef 默认 true（`referenced.h:341`）。 | AC-2.1 / AC-2.4 |
| R-3 | 行为 | RefPtr 释放对象（析构或赋值替换） | 调用 DecStrongRef 原子递减 strongRef，若结果为 0 且 MaybeRelease() 返回 true 则 `delete this` 销毁 Referenced 对象。 | MaybeRelease() 默认返回 true，子类可 override 否决释放（`referenced.h:130-133`）。 | AC-2.2 / AC-2.3 / AC-2.4 |
| R-4 | 行为 | WeakPtr 持有对象 | 私有构造函数仅调用 IncWeakRef 递增 weakRef，不调用 IncStrongRef，即不改变 strongRef 计数。 | WeakPtr 保存 unsafeRawPtr_ 但不得直接使用（`referenced.h:533` 注释警告）。 | AC-3.1 / AC-5.3 |
| R-5 | 行为 | WeakPtr 释放对象（析构） | 调用 DecWeakRef 递减 weakRef。 | 若 weakRef 归零则触发 R-6 自销毁。 | AC-3.5 |
| R-6 | 行为 | RefCounter::DecWeakRef 返回值为 0 | RefCounter 执行 `delete this` 自销毁（`ref_counter.h:99`）。这发生在最后一个 WeakPtr 析构且 Referenced 对象已析构（自身持有的 weakRef 已递减）之后。 | RefCounter 析构函数为 protected，仅 DecWeakRef 可触发自销毁。 | AC-4.1 / AC-4.5 |
| R-7 | 行为 | WeakPtr::Upgrade() 调用 | 通过 refCounter_->TryIncStrongRef() 原子测试并递增 strongRef。成功时以 forceIncRef=false 构造 RefPtr（不重复递增），失败（strongRef==0）返回空 RefPtr。Invalid() 返回 refCounter_==nullptr 或 StrongRefCount()==0。 | 消除 check-then-act 竞争窗口（design.md ADR-4）。 | AC-3.2 / AC-3.3 / AC-3.4 |
| R-8 | 边界 | ThreadSafeCounter::TryIncrease 当 count==0 | 返回 false，不递增。compare_exchange_weak CAS 循环保证原子性。 | CAS 使用 std::memory_order_relaxed（`ref_counter.h:56`）。 | AC-3.3 / AC-4.4 |
| R-9 | 行为 | Referenced 析构 | 调用 refCounter_->DecWeakRef() 递减自身持有的 weak reference（初始值 1 中的那个），然后将 refCounter_ 置 nullptr。 | 此后 refCounter_ 不再可用，但 RefCounter 对象可能仍存活（若有 WeakPtr 持有 weakRef）。 | AC-1.3 |
| R-10 | 行为 | strongRef 归零时 MaybeRelease 检查 | DecRefCount 在 strongRef==0 后调用虚方法 MaybeRelease()，默认返回 true 触发 delete this，子类可 override 返回 false 否决释放（用于回收复用场景）。 | MaybeRelease 为虚方法（`referenced.h:130`）。 | AC-2.3 |
| R-11 | 行为 | RefPtr operator== 比较 | 当双方 rawPtr 均非空时比较 `rawPtr_->refCounter_ == rawPtr->refCounter_`（refCounter 指针同一性），而非原始对象指针。operator< 同理按 refCounter_ 指针比较，支持 std::map/std::set。 | nullptr == nullptr 返回 true。 | AC-2.5 |
| R-12 | 行为 | ThreadSafeCounter 原子操作 | Increase 使用 fetch_add(1, relaxed)，Decrease 使用 fetch_sub(1, release) 返回旧值-1，CurrentCount 使用 load(relaxed)，TryIncrease 使用 compare_exchange_weak CAS 循环。底层为 std::atomic<int32_t>。 | ACE_DCHECK(count > 0) 在 Decrease 中断言计数不下溢（`ref_counter.h:39`）。 | AC-4.2 / AC-4.3 / AC-4.4 |
| R-13 | 行为 | DECLARE_ACE_TYPE + DynamicCast | DECLARE_ACE_TYPE 展开为 DECLARE_RELATIONSHIP_OF_CLASSES（生成 SafeCastById 虚方法 + TrySafeCastById 继承链查找）+ friend Referenced。DynamicCast 通过 `rawPtr->SafeCastById(T::TypeId())` 在继承链中哈希匹配目标 TypeId。TypeId 为类名字符串的 `std::hash<std::string>` 值。InstanceOf 等价于 DynamicCast != nullptr。 | 编译环境为 -fno-rtti，标准 dynamic_cast 不可用（design.md ADR-3）。 | AC-6.1 / AC-6.2 / AC-6.3 / AC-6.4 |
| R-14 | 边界 | Referenced 拷贝/移动 | ACE_DISALLOW_COPY_AND_MOVE(Referenced) 禁止拷贝构造、拷贝赋值、移动构造、移动赋值，编译期拒绝。 | 引用计数对象语义上不可复制（`referenced.h:174`）。 | AC-1.4 |
| R-15 | 异常 | Claim 检测到已释放对象 | Claim(rawPtr) 默认分支检查 `!rawPtr->RefCount()`（strongRef==0），若为 true 调用 OnDetectedClaimDeathObj(false)。MakeRefPtr 使用 isNewOrRecycle=true 检查 `rawPtr->RefCount() > 0` 时同样调用 OnDetectedClaimDeathObj(true)。 | OnDetectedClaimDeathObj 声明在 `referenced.h:171`。 | AC-5.1 / AC-5.2 |
| R-16 | 行为 | AceType 菱形继承 | AceType 通过 `public virtual TypeInfoBase, public virtual Referenced` 解决菱形继承，两个 virtual 基类共享同一实例。DECLARE_ACE_TYPE(AceType, TypeInfoBase) 声明继承链根为 TypeInfoBase。 | AceType 构造函数为 protected（`ace_type.h:145`），不可直接实例化。 | AC-6.5 |
| R-17 | 行为 | 框架代码 include 智能指针头文件 | frameworks/base/memory/ 下 4 个头文件各仅含 1 行 #include 重定向到 ui/base/ 对应文件，ace_kit 为唯一定义源。 | 转发层不得添加任何额外定义（design.md ADR-1）。 | AC-7.1 / AC-7.2 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1 / AC-1.2 / R-1 | 代码评审 | referenced.h:108-110 构造函数对照; ref_counter.h:107-110 初始值对照 |
| VM-2 | AC-1.3 / R-9 | 代码评审 | referenced.h:118-128 析构函数对照 |
| VM-3 | AC-1.4 / R-14 | 编译验证 | 对 Referenced 子类尝试拷贝构造，确认编译失败 |
| VM-4 | AC-2.1..2.5 / R-2 / R-3 / R-10 / R-11 | 单元测试 | test/unittest/core/base/ 下 RefPtr 引用计数增减、对象释放、operator== 行为验证 |
| VM-5 | AC-3.1..3.5 / R-4 / R-5 / R-7 / R-8 | 单元测试 | test/unittest/core/base/ 下 WeakPtr 构造/析构/Upgrade/Invalid 行为验证 |
| VM-6 | AC-4.1..4.5 / R-6 / R-8 / R-12 | 单元测试 + 代码评审 | ref_counter.h:27-111 ThreadSafeCounter CAS 操作与 RefCounter 自销毁对照 |
| VM-7 | AC-5.1..5.3 / R-1 / R-15 | 单元测试 | MakeRefPtr/Claim/WeakClaim 工厂方法验证 |
| VM-8 | AC-6.1..6.5 / R-13 / R-16 | 单元测试 + 代码评审 | test/unittest/core/base/ 下 AceType DynamicCast/InstanceOf/TypeId 行为验证; type_info_base.h:29-71 宏展开对照 |
| VM-9 | AC-7.1..7.2 / R-17 | 代码评审 | frameworks/base/memory/*.h:19 重定向对照 |

## API 变更分析

### 新增 API

N/A，无新增 Public/System/InnerApi。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

无新增接口规格。

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 无 @since 标注（框架内部能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 双层架构单向依赖 | 规范实现在 interfaces/inner_api/ace_kit/include/ui/base/，框架通过 frameworks/base/memory/ 1 行 #include 转发引用，不允许反向依赖（ADR-1） | AC-1.1 |
| ArkUI 托管对象继承 AceType | 所有托管对象应继承 AceType（而非直接继承 Referenced 或 TypeInfoBase），以同时获得引用计数和自定义 RTTI 能力 | AC-2.1 |
| RefPtr/WeakPtr 不可继承 | RefPtr/WeakPtr 为 final class（referenced.h:182,361），不可被继承 | AC-2.2 |
| Referenced virtual 继承 | AceType 通过 virtual 继承 Referenced 和 TypeInfoBase 解决菱形继承 | AC-2.3 |
| 指针比较基于 refCounter_ | 智能指针比较一律基于 refCounter_ 指针，不基于原始对象指针（R-11） | AC-5.1 |
| WeakPtr unsafeRawPtr_ 禁止直接解引用 | 必须通过 Upgrade() 提升为 RefPtr 后访问（referenced.h:533 注释警告） | AC-6.1 |
| -fno-rtti 禁止 dynamic_cast | 禁止使用 dynamic_cast / typeid / std::dynamic_pointer_cast，必须使用 AceType::DynamicCast / InstanceOf / TypeId 替代（ADR-3） | AC-4.1 |

## 非功能性需求

- 性能：引用计数增减为 std::atomic 单次原子操作（fetch_add/fetch_sub/CAS），无锁无自旋，开销为单条 CPU 原子指令。DynamicCast 通过 SafeCastById 在继承链上线性查找，深度为继承层级。
- 线程安全：ThreadSafeCounter 的所有操作（Increase/Decrease/TryIncrease/CurrentCount）均为 std::atomic 原子操作，RefPtr/WeakPtr 的引用计数操作在多线程并发持有同一对象时无数据竞争。单个 RefPtr/WeakPtr 实例的非原子操作（如 Swap、operator=）非线程安全，需调用方同步。
- 内存安全：RefCounter 在 weakRef 归零时自销毁（R-6），保证 RefCounter 不会泄漏；Referenced 对象在 strongRef 归零且 MaybeRelease 通过时自动 delete（R-3），保证对象不会泄漏。WeakPtr::Upgrade 通过 TryIncStrongRef 原子提升消除竞争窗口（R-7）。
- 可调试：ACE_DEBUG 编译条件下 Referenced 构造/析构与 Claim 路径集成 MemoryMonitor（`referenced.h:58-62,111-115,123-127`），支持按类型聚合分配跟踪（Feat-02 范围）。

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | N/A | 智能指针不影响无障碍语义 | — |
| 大字体 | N/A | 引用计数与字体缩放无关 | — |
| 深色模式 | N/A | 智能指针与颜色无关 | — |
| 多窗口/分屏 | N/A | 每个窗口的 PipelineContext 独立持有 AceType 对象 | — |
| 多用户 | N/A | 引用计数无用户态差异 | — |
| 版本升级 | N/A | 本 Feat 自 API 9 起存在，无版本守护分支 | — |
| 生态兼容 | 是 | 所有继承 AceType 的对象隐式依赖本 Feat；新增类须使用 DECLARE_ACE_TYPE 声明父类（R-13）；新增智能指针头文件须在转发层添加 shim（R-17） | AC-7.1, AC-7.2 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "Referenced RefCounter RefPtr WeakPtr AceType DECLARE_ACE_TYPE ThreadSafeCounter implementation"
  - repo: "openharmony/ace_engine"
    query: "RefPtr WeakPtr Upgrade TryIncStrongRef IncRefCount DecRefCount operator== Swap Reset"
  - repo: "openharmony/ace_engine"
    query: "AceType DynamicCast InstanceOf TypeId TypeName TypeInfoBase SafeCastById TrySafeCastById"
  - repo: "openharmony/ace_engine"
    query: "RefCounter DecWeakRef IncStrongRef DecStrongRef TryIncStrongRef self-delete protected destructor"
  - repo: "openharmony/ace_engine"
    query: "MakeRefPtr Claim WeakClaim OnDetectedClaimDeathObj RefCount MaybeRelease"
```

**关键文档：**
- `interfaces/inner_api/ace_kit/include/ui/base/ref_counter.h:27-64` — ThreadSafeCounter CAS 原子计数器
- `interfaces/inner_api/ace_kit/include/ui/base/ref_counter.h:66-111` — RefCounter 自销毁机制
- `interfaces/inner_api/ace_kit/include/ui/base/referenced.h:38-177` — Referenced 基类
- `interfaces/inner_api/ace_kit/include/ui/base/referenced.h:182-356` — RefPtr 强引用智能指针
- `interfaces/inner_api/ace_kit/include/ui/base/referenced.h:361-536` — WeakPtr 弱引用智能指针
- `interfaces/inner_api/ace_kit/include/ui/base/ace_type.h:38-146` — AceType 自定义 RTTI
- `interfaces/inner_api/ace_kit/include/ui/base/type_info_base.h:29-174` — TypeInfoBase 类型系统
- `frameworks/base/memory/*.h:19` — 转发 shim 层
