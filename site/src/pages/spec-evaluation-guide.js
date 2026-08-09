import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';

const DIMENSIONS = [
  {
    name: '事实正确性与证据',
    id: 'correctness',
    weight: '30',
    focus: '源码事实、SDK 契约、边界/状态/异常，以及 Spec、Design、Registry 的一致性。',
  },
  {
    name: 'Spec 可执行性',
    id: 'spec_executability',
    weight: '25',
    focus: 'AC 是否可测试、可观测，规则是否覆盖边界，AC、Rule、VM 与证据是否闭环。',
  },
  {
    name: 'Design 设计质量',
    id: 'design_quality',
    weight: '25',
    focus: '调用链、状态流、模块职责、异常处理和设计决策是否足以指导实现。',
  },
  {
    name: '兼容性与系统影响',
    id: 'compatibility_system_impact',
    weight: '10',
    focus: '版本兼容、跨端差异、权限/线程/性能等系统影响是否被识别和处理。',
  },
  {
    name: 'Function 功能建模质量',
    id: 'function_modeling',
    weight: '10',
    focus: 'Function 与 Feature 边界、范围、复用关系和 Registry 建模是否合理。',
  },
];

const CONCLUSIONS = [
  ['SUPPORTED', '证据充分，结论与源码、SDK 或测试事实一致，不产生扣分。'],
  ['PARTIALLY_SUPPORTED', '部分支持或证据不完整；应阅读该 Criterion 下的 Finding、证据路径和建议。'],
  ['CONTRADICTED', '与已验证事实冲突；通常是最高优先级的修复入口。'],
  ['MISSING', '缺少要求的规则、行为或关键文档内容，按 Criterion 规则扣分。'],
  ['NOT_APPLICABLE', '有理由和证据说明该 Criterion 不适用，从该维度分母排除。'],
  ['NOT_VERIFIABLE', '当前证据不足以判断，不直接扣分，但会降低 confidence。'],
];

const CAPS = [
  ['Critical', '39', '存在未豁免 Critical Finding'],
  ['Major', '59', '不存在 Critical，但存在未豁免 Major Finding'],
  ['Minor', '79', '最高严重度为 Minor'],
  ['None', '100', '没有活跃 Finding'],
];

function GuideCard({title, children, tone}) {
  return <article className={`guideCard ${tone ? `guideCard-${tone}` : ''}`}><h3>{title}</h3>{children}</article>;
}

export default function SpecEvaluationGuidePage() {
  return (
    <Layout title="Spec Eval Scoring Guide" description="ArkUI spec_eval 评价体系、评分规则和优化方法">
      <main className="guidePage">
        <section className="guideHero">
          <div className="contentWrap">
            <p className="eyebrow">spec_eval / Rubric 0.3.0 / frozen</p>
            <h1>理解 Spec Eval 评价体系</h1>
            <p className="heroCopy">
              这套评价以 Function 为最小单元，用可复核证据识别 Spec 和 Design 的真实风险。它评价的是
              “能否正确、完整、可执行地指导实现”，不是文档的篇幅或排版。
            </p>
            <div className="heroActions">
              <Link className="button button--primary" to="/spec-evaluation">查看评价报告</Link>
              <Link className="button button--secondary" to="/docs">浏览 Spec 文档</Link>
            </div>
          </div>
        </section>

        <section className="pageBand">
          <div className="contentWrap">
            <div className="guideCallout">
              <strong>一句话理解：</strong>
              <span>从 100 分开始，只因证据支持的缺陷扣分；静态 Finding 仍然权威，语义评价不能删除或降低它。</span>
            </div>
            <div className="sectionHeader"><h2>五个评分维度</h2><p>权重是维度满分，不是可以通过增加文档形式要素获得的“奖励分”。</p></div>
            <div className="tableScroll">
              <table className="portalTable guideDimensionTable">
                <thead><tr><th>维度</th><th>满分</th><th>主要检查什么</th></tr></thead>
                <tbody>{DIMENSIONS.map((dimension) => <tr key={dimension.id}><td><strong>{dimension.name}</strong><br /><code>{dimension.id}</code></td><td className="guideWeight">{dimension.weight}</td><td>{dimension.focus}</td></tr>)}</tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="pageBand mutedBand">
          <div className="contentWrap">
            <div className="sectionHeader"><h2>分数是怎样产生的</h2><p>每一步都有独立含义，不能用一个指标替代另一个指标。</p></div>
            <div className="guideFlow" aria-label="评分流程">
              {['Static findings + Evidence', 'Criterion 扣分', '维度归一化', 'Raw score', 'Severity cap', 'Published score', 'Gate / Confidence / Admission'].map((step, index) => <div className="guideFlowStep" key={step}><span>{index + 1}</span><strong>{step}</strong></div>)}
            </div>
            <div className="guideCardGrid guideMetricGrid">
              <GuideCard title="Published score"><p>原始分经过活跃最高严重度封顶后的发布分。它代表当前质量结果，范围为 0–100。</p></GuideCard>
              <GuideCard title="Gate"><p>门禁状态来自静态与语义结果的合并：<code>effective_gate = max(static_gate, semantic_gate)</code>。语义结果不能放宽静态门禁。</p></GuideCard>
              <GuideCard title="Confidence"><p>证据核验、人工确认、源码 revision 可复现性和工具阶段完整性的加权值。它表示“结论有多可复核”，不是质量分。</p></GuideCard>
              <GuideCard title="Admission"><p><code>BASELINED</code> 要求 Gate 全通过、Published ≥ 80、Confidence ≥ 0.8；<code>HIGH_QUALITY</code> 提高到 90 和 0.85，否则为 <code>NOT_READY</code>。</p></GuideCard>
            </div>
          </div>
        </section>

        <section className="pageBand">
          <div className="contentWrap">
            <div className="sectionHeader"><h2>严重度如何影响发布分</h2><p>封顶只限制发布分，不会抹掉 Finding 或改变原始扣分。</p></div>
            <div className="tableScroll">
              <table className="portalTable"><thead><tr><th>活跃最高严重度</th><th>发布分上限</th><th>含义</th></tr></thead><tbody>{CAPS.map(([severity, cap, meaning]) => <tr key={severity}><td><span className={`severityBadge severity-${severity.toLowerCase()}`}>{severity}</span></td><td><strong>{cap}</strong></td><td>{meaning}</td></tr>)}</tbody></table>
            </div>
          </div>
        </section>

        <section className="pageBand mutedBand">
          <div className="contentWrap">
            <div className="sectionHeader"><h2>Criterion 结论怎么读</h2><p>详情页只把需要行动的结论展开为 Finding、证据路径和 recommendation。</p></div>
            <div className="guideConclusionGrid">{CONCLUSIONS.map(([conclusion, explanation]) => <GuideCard key={conclusion} title={conclusion} tone={conclusion === 'CONTRADICTED' || conclusion === 'PARTIALLY_SUPPORTED' ? 'actionable' : ''}><p>{explanation}</p></GuideCard>)}</div>
          </div>
        </section>

        <section className="pageBand">
          <div className="contentWrap guideTwoColumn">
            <div>
              <div className="sectionHeader"><h2>使用评价结果的顺序</h2></div>
              <ol className="guidePriorityList">
                <li><strong>先看 Gate、Published score、Admission。</strong>先判断是否能进入基线，再判断分数和准入等级。</li>
                <li><strong>再看五维雷达图。</strong>找出最薄弱的维度，不要只盯总分。</li>
                <li><strong>下钻 actionable Criterion。</strong>优先处理 <code>CONTRADICTED</code> 和 <code>PARTIALLY_SUPPORTED</code>，阅读同一块中的 Finding、证据路径和建议。</li>
                <li><strong>核对证据。</strong>检查路径、行号、source revision 和 content hash 是否足以复现结论。</li>
                <li><strong>下载 Function JSON。</strong>把它交给负责人作为后续 Spec/Design 优化的结构化输入。</li>
              </ol>
            </div>
            <GuideCard title="自动评价与正式 Review">
              <p><code>status: confirmed</code> 的人工确认 Review 才是站点正式语义质量依据。draft、自动盲评和多 run 稳定性结果用于诊断，不会自动改写正式 Review 或历史基线。</p>
              <p>修改后应重新执行静态检查、证据构建和语义评价，并确认评价使用同一源码 revision。</p>
            </GuideCard>
          </div>
        </section>

        <section className="pageBand mutedBand">
          <div className="contentWrap">
            <div className="sectionHeader"><h2>Spec 优化目标</h2><p>优化目标是降低真实实现风险，而不是追求表面分数。</p></div>
            <div className="guideCardGrid">
              <GuideCard title="事实正确"><p>每个关键结论都能回到源码、SDK、测试或 Registry 证据。</p></GuideCard>
              <GuideCard title="契约精确"><p>参数、返回值、默认值、错误码、生命周期和兼容范围与实际 API 一致。</p></GuideCard>
              <GuideCard title="边界可执行"><p>状态转换、异常分支、设备差异和可观测结果能被实现和测试。</p></GuideCard>
              <GuideCard title="文档闭环"><p>Spec、Design、Registry、Task、VM、AC 和证据之间可以互相追溯。</p></GuideCard>
              <GuideCard title="实现可落地"><p>调用链、模块职责、构建/注册/部署影响和验证路径足够具体。</p></GuideCard>
              <GuideCard title="模型合理"><p>Function/Feature 边界清楚，复用关系稳定，避免把无关能力塞进同一功能域。</p></GuideCard>
            </div>
            <div className="guideCallout guideCallout-warning"><strong>不要这样优化：</strong><span>增加篇幅、表格、图、引用数量或自审勾选不会带来正向加分；如果问题没有被证据和可执行规则解决，分数不会真正改善。</span></div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
