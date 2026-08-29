import React, {useEffect, useMemo, useState} from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import bundledSummaryData from '../data/spec-evaluation-summary.json';
import bundledSemanticSummaryData from '../data/semantic-evaluation-summary.json';
import bundledHistoryData from '../data/spec-evaluation-history.json';

const GATES = ['all', 'pass', 'warn', 'fail', 'error'];
const SEVERITIES = ['Critical', 'Major', 'Minor', 'Info'];
const DIMENSIONS = [
  {id: 'correctness', label: 'Correctness', max: 30},
  {id: 'spec_executability', label: 'Spec', max: 25},
  {id: 'design_quality', label: 'Design', max: 25},
  {id: 'compatibility_system_impact', label: 'Impact', max: 10},
  {id: 'function_modeling', label: 'Modeling', max: 10},
];

// Dynamic (B-lite) mode re-polls the data files so a per-archive data-only
// refresh appears on the served site without a full rebuild. Static mode fetches
// once. The interval is deliberately gentle; the payloads are small and cached.
const DYNAMIC_POLL_MS = 30000;

// Fetch a runtime JSON file, seeding state with the value bundled at build time
// so the first paint never blocks. When ``pollMs`` is set the file is re-fetched
// on that interval (dynamic mode). ``fallback`` is returned on fetch failure so
// a missing/served-late file degrades to the build-time snapshot.
function useRuntimeJson(url, fallback, pollMs) {
  const [value, setValue] = useState(fallback);
  useEffect(() => {
    let active = true;
    const load = () => {
      fetch(url)
        .then((response) => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        })
        .then((next) => {
          if (active) setValue(next);
        })
        .catch(() => {
          /* keep the previous value (bundled fallback on first load) */
        });
    };
    load();
    if (!pollMs) return () => { active = false; };
    const timer = setInterval(load, pollMs);
    return () => { active = false; clearInterval(timer); };
  }, [url, pollMs]);
  return value;
}

function GateBadge({gate}) {
  return <span className={`evalGate evalGate-${gate}`}>{String(gate).toUpperCase()}</span>;
}

function Percent({value}) {
  return <>{`${Math.round((Number(value) || 0) * 100)}%`}</>;
}

function SummaryCard({label, value, tone}) {
  return (
    <div className={`evalSummaryCard ${tone ? `evalSummary-${tone}` : ''}`}>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function TrendChart({snapshots}) {
  const width = 560;
  const height = 180;
  const left = 42;
  const right = 16;
  const top = 18;
  const bottom = 38;
  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;
  const values = snapshots.map((item) => Number(item.publishedScoreAverage) || 0);
  const point = (value, index) => {
    const x = snapshots.length === 1 ? left + chartWidth / 2 : left + (index * chartWidth) / (snapshots.length - 1);
    const y = top + chartHeight - (Math.max(0, Math.min(100, value)) / 100) * chartHeight;
    return {x, y};
  };
  const points = values.map(point);
  return (
    <svg className="governanceTrendChart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Published score average history">
      {[0, 25, 50, 75, 100].map((value) => {
        const y = point(value, 0).y;
        return <g key={value}><line x1={left} y1={y} x2={width - right} y2={y} className="trendGrid" /><text x={left - 8} y={y + 4} textAnchor="end" className="trendAxisLabel">{value}</text></g>;
      })}
      {points.length > 1 && <polyline points={points.map(({x, y}) => `${x},${y}`).join(' ')} className="trendLine" />}
      {points.map(({x, y}, index) => {
        const snap = snapshots[index];
        const day = snap.snapshotDay || (snap.snapshotAt ? String(snap.snapshotAt).slice(0, 10) : '');
        const dayLabel = day ? day.slice(5) : (snap.sourceRevision || '').slice(0, 7);
        const rev = (snap.sourceRevision || '').slice(0, 7);
        return (
          <g key={day || snap.sourceRevision || index}>
            <title>{`${day || '—'} · ${rev}`}</title>
            <circle cx={x} cy={y} r="5" className="trendPoint" />
            <text x={x} y={y - 11} textAnchor="middle" className="trendValueLabel">{values[index]}</text>
            <text x={x} y={height - 12} textAnchor="middle" className="trendRevisionLabel">{dayLabel}</text>
          </g>
        );
      })}
    </svg>
  );
}

function GovernanceOverview({historyData}) {
  if (!historyData.available || historyData.snapshots.length === 0) return null;
  const summary = historyData.summary;
  const current = historyData.snapshots[historyData.snapshots.length - 1];
  const delta = historyData.recentDelta || {functions: []};
  return (
    <section className="pageBand governanceBand">
      <div className="contentWrap">
        <div className="sectionHeader">
          <h2>Quality Governance</h2>
          <p>轻量历史快照与稳定 Finding ID 差异；不会把完整历史报告打入站点。</p>
        </div>
        <div className="evalSummaryGrid governanceSummaryGrid">
          <SummaryCard label="Snapshots" value={summary.snapshotCount} />
          <SummaryCard label="Confirmed Findings" value={summary.currentFindingCount} />
          <SummaryCard label="Added" value={summary.addedFindingCount} tone={summary.addedFindingCount ? 'fail' : 'pass'} />
          <SummaryCard label="Resolved" value={summary.resolvedFindingCount} tone="pass" />
          <SummaryCard label="Reclassified" value={summary.reclassifiedFindingCount} tone={summary.reclassifiedFindingCount ? 'warn' : 'pass'} />
        </div>
        {summary.comparisonStatus === 'INITIAL' && <div className="governanceNotice">当前是首个历史快照。后续归档新的源码 revision 后，这里会显示新增、已解决和持续存在的 Finding。</div>}
        <div className="governanceGrid">
          <article className="governancePanel">
            <div className="governancePanelHeader"><h3>Published score trend</h3><span>平均 {current.publishedScoreAverage}</span></div>
            <TrendChart snapshots={historyData.snapshots} />
          </article>
          <article className="governancePanel">
            <div className="governancePanelHeader"><h3>Dimension averages</h3><span>{current.functionCount} confirmed Functions</span></div>
            <div className="dimensionBars">
              {DIMENSIONS.map((dimension) => {
                const value = Number(current.dimensionAverages?.[dimension.id] || 0);
                return <div className="dimensionBar" key={dimension.id}><div><span>{dimension.label}</span><strong>{value}/{dimension.max}</strong></div><div className="dimensionBarTrack"><span style={{width: `${Math.min(100, (value / dimension.max) * 100)}%`}} /></div></div>;
              })}
            </div>
          </article>
        </div>
        <div className="governanceGrid governanceTables">
          <article className="governancePanel">
            <div className="governancePanelHeader"><h3>Top risk Functions</h3><span>按 Finding 数</span></div>
            <div className="governanceList">{(current.topFunctions || []).slice(0, 6).map((item) => <div key={item.funcId}><code>{item.funcId}</code><span>{item.title}</span><strong>{item.findingCount}</strong></div>)}</div>
          </article>
          <article className="governancePanel">
            <div className="governancePanelHeader"><h3>Top static rules</h3><span>当前快照</span></div>
            <div className="governanceList">{(current.topRules || []).slice(0, 6).map((item) => <div key={item.ruleId}><code>{item.ruleId}</code><span></span><strong>{item.count}</strong></div>)}</div>
          </article>
        </div>
        {(delta.functions || []).length > 0 && <div className="tableScroll governanceDeltaTable"><table className="portalTable"><thead><tr><th>Function</th><th>Added</th><th>Resolved</th><th>Reclassified</th></tr></thead><tbody>{delta.functions.map((item) => <tr key={item.funcId}><td><code>{item.funcId}</code> {item.title}</td><td>{item.added}</td><td>{item.resolved}</td><td>{item.reclassified}</td></tr>)}</tbody></table></div>}
      </div>
    </section>
  );
}

function Finding({item}) {
  const location = item.path ? `${item.path}${item.line ? `:${item.line}` : ''}` : '-';
  return (
    <article className="findingCard">
      <div className="findingHeader">
        <span className={`severityBadge severity-${String(item.severity).toLowerCase()}`}>{item.severity}</span>
        <code>{item.rule_id}</code>
        {item.feat_id && <span>{item.feat_id}</span>}
      </div>
      <p>{item.message}</p>
      <div className="findingLocation">{location}</div>
      {item.recommendation && <div className="findingRecommendation">建议：{item.recommendation}</div>}
    </article>
  );
}

function RadarChart({scores, rawScore, publishedScore}) {
  const size = 280;
  const center = size / 2;
  const radius = 92;
  const angle = (index) => -Math.PI / 2 + (index * Math.PI * 2) / DIMENSIONS.length;
  const point = (index, ratio, extraRadius = radius) => {
    const currentAngle = angle(index);
    const currentRadius = extraRadius * ratio;
    return `${center + Math.cos(currentAngle) * currentRadius},${center + Math.sin(currentAngle) * currentRadius}`;
  };
  const polygon = (ratio) => DIMENSIONS.map((_, index) => point(index, ratio)).join(' ');
  const values = DIMENSIONS.map((dimension) => {
    const value = Number(scores?.[dimension.id] || 0);
    return Math.max(0, Math.min(1, value / dimension.max));
  });
  return (
    <div className="radarWrap">
      <div className="radarScore">
        <strong>{publishedScore ?? '-'}</strong>
        <span>Published / 100</span>
        <small>Raw {rawScore ?? '-'}</small>
      </div>
      <svg className="radarChart" viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Five-dimension score radar chart">
        {[0.25, 0.5, 0.75, 1].map((ratio) => <polygon key={ratio} points={polygon(ratio)} className="radarGrid" />)}
        {DIMENSIONS.map((dimension, index) => <line key={dimension.id} x1={center} y1={center} x2={point(index, 1).split(',')[0]} y2={point(index, 1).split(',')[1]} className="radarAxis" />)}
        <polygon points={values.map((value, index) => point(index, value)).join(' ')} className="radarValue" />
        {DIMENSIONS.map((dimension, index) => {
          const [x, y] = point(index, 1, radius + 18).split(',');
          return <text key={dimension.id} x={x} y={y} className="radarLabel" textAnchor="middle">{dimension.label}</text>;
        })}
      </svg>
      <div className="radarLegend">
        {DIMENSIONS.map((dimension) => <span key={dimension.id}><code>{dimension.id}</code> {scores?.[dimension.id] ?? 0}/{dimension.max}</span>)}
      </div>
    </div>
  );
}

function CriterionReview({criterion}) {
  const actionable = ['CONTRADICTED', 'PARTIALLY_SUPPORTED'].includes(criterion.conclusion);
  return (
    <div className={`criterionBlock ${actionable ? 'criterionActionable' : ''}`}>
      <div className="criterionHeading">
        <code>{criterion.criterion_id}</code>
        <span>{criterion.conclusion}</span>
        {criterion.deduction > 0 && (
          <span className="criterionDeduction" title={`该 Criterion 扣 ${criterion.deduction} 分（得分 ${criterion.criterion_score ?? '-'} / ${criterion.max_score ?? '-'}）`}>-{criterion.deduction}</span>
        )}
      </div>
      {actionable && (
        <div className="criterionEvidence">
          <p>{criterion.reason || '该 Criterion 存在需要处理的支持缺口。'}</p>
          {(criterion.findings || []).map((finding, index) => (
            <article className="criterionFinding" key={finding.finding_id || `${criterion.criterion_id}-${index}`}>
              <div className="findingHeader">
                <span className={`severityBadge severity-${String(finding.severity).toLowerCase()}`}>{finding.severity}</span>
                <code>{finding.finding_id || 'finding'}</code>
                {finding.claim_id && (
                  <code className="findingClaim" title="关联的 Spec Claim">{finding.claim_id}</code>
                )}
              </div>
              <p>{finding.message}</p>
              {finding.recommendation && <p className="findingRecommendation">建议：{finding.recommendation}</p>}
              {(criterion.evidence || []).length > 0 && (
                <div className="criterionEvidencePaths">
                  {(criterion.evidence || []).map((evidence) => (
                    <code key={evidence.evidence_id || evidence.path}>{evidence.path || evidence.evidence_id}</code>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

function downloadFunctionJson(item) {
  const {semanticReview, ...staticFunction} = item;
  const payload = {
    schema_version: 1,
    report_type: 'function-evaluation-input',
    func_id: item.funcId,
    source_revision: semanticReview?.source_revision || null,
    static: staticFunction,
    semantic: semanticReview,
    optimization_hint: 'Use actionable Criterion findings, evidence paths, and recommendations as the optimization input; do not treat confidence as a quality score.',
  };
  const blob = new Blob([JSON.stringify(payload, null, 2) + '\n'], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `${item.funcId}-evaluation-report.json`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function KernelViolations({kernel}) {
  const groups = [
    {key: 'hard_errors', label: 'HARD（阻断）', items: kernel.hard_errors || []},
    {key: 'major_violations', label: 'MAJOR（核心不变量）', items: kernel.major_violations || []},
    {key: 'minor_violations', label: 'MINOR（完整性/一致性）', items: kernel.minor_violations || []},
  ].filter((group) => group.items.length > 0);
  if (groups.length === 0) return <p className="evalMuted">无校验违反，报告可靠性未被扣分。</p>;
  return (
    <div className="kernelViolationGroups">
      {groups.map((group) => (
        <div className="kernelViolationGroup" key={group.key}>
          <h5>{group.label}</h5>
          {group.items.map((item, index) => (
            <div className="kernelViolation" key={`${group.key}-${index}`}>
              <div className="kernelViolationHead">
                <code>{item.code}</code>
                {item.deduction > 0 && <span className="kernelDeduction">-{item.deduction}</span>}
                {item.criterion_id && <code className="kernelCriterion">{item.criterion_id}</code>}
              </div>
              {item.message && <p>{item.message}</p>}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function SemanticReview({review}) {
  if (!review) return <p className="evalMuted">当前 revision 没有 confirmed semantic Review。</p>;
  const score = review.scores || {};
  const kernel = score.kernel_confidence || null;
  return (
    <section className="semanticReview">
      {review.status === 'EXPIRED' && (
        <div className="evalErrorBox">该报告已过期：评价于 {review.staleness?.evaluated_at || review.evaluated_at || '-'}，已超过新鲜度期限（{review.expires_at || review.staleness?.expires_at || '-'}）。</div>
      )}
      {review.status !== 'EXPIRED' && review.revision_current === false && (
        <div className="evalNoticeBox">该报告评价于 <code>{String(review.source_revision || '').slice(0, 7)}</code>，当前主流 revision 为 <code>{String(review.observed_revision || '').slice(0, 7)}</code>；分数仍基于其评价时的源码有效，可能未覆盖之后的改动。</div>
      )}
      <div className="detailMetrics">
        <span>状态 <b>{review.status}</b></span>
        <span>新鲜度 <b>{review.freshness || '-'}</b></span>
        <span>发布分 <b>{score.published_score ?? '-'}</b></span>
        <span>可靠性置信度 <b>{kernel ? `${kernel.score ?? '-'} / 100` : '-'}</b>{kernel?.level && <em className={`confidenceLevel level-${String(kernel.level).toLowerCase()}`}>{kernel.level}</em>}</span>
        <span>证据置信度 <b>{score.confidence ?? '-'}</b>{typeof score.confidence_publishable === 'boolean' && <em className={`confidencePublishable ${score.confidence_publishable ? 'is-yes' : 'is-no'}`}>{score.confidence_publishable ? '可发布' : '不可发布'}</em>}</span>
        <span>准入 <b>{score.admission ?? '-'}</b></span>
      </div>
      <p className="evalMuted">评价时间：{review.evaluated_at || review.confirmation?.confirmed_at || '-'}</p>
      <p className="evalMuted">可靠性置信度：基于校验违反（HARD/MAJOR/MINOR）扣分，反映这份报告结论有多可靠。证据置信度：证据核验覆盖率/人工确认/可复现性——两者语义不同，均非质量得分。</p>
      {kernel && (
        <div className="deductionTips">
          <div className="deductionTipGroup">
            <h5>报告缺陷（可靠性降级扣分，共 -{kernel.deduction_total ?? 0}）</h5>
            <KernelViolations kernel={kernel} />
          </div>
        </div>
      )}
      {(score.admission_reasons || []).length > 0 && (
        <div className="deductionTips">
          <div className="deductionTipGroup">
            <h5>准入未达标原因</h5>
            <ul>{score.admission_reasons.map((reason, index) => <li key={`adm-${index}`}>{reason}</li>)}</ul>
          </div>
        </div>
      )}
      <RadarChart scores={score.dimensions} rawScore={score.raw_score} publishedScore={score.published_score} />
      <h4>Actionable Criterion details</h4>
      <div className="criterionList">
        {(review.criterion_summaries || []).map((criterion) => <CriterionReview criterion={criterion} key={criterion.criterion_id} />)}
      </div>
    </section>
  );
}

function FunctionDetailModal({item, onClose}) {
  if (!item) return null;
  return (
    <div className="evalModalBackdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
    <div className="evalModalPanel" role="dialog" aria-modal="true" aria-labelledby="function-detail-title">
      <button className="detailCloseButton" type="button" aria-label="关闭详情" onClick={onClose}>×</button>
      <section className="functionDetail">
      <div className="detailTitleRow">
        <div>
          <div className="detailEyebrow">{item.l1.title} / {item.l2.title}</div>
          <h2 id="function-detail-title">{item.funcId} {item.title}</h2>
          <div className="functionPath">{item.path}</div>
        </div>
        <GateBadge gate={item.gate} />
      </div>

      <div className="detailDownloadBar">
        <div>
          <strong>下载负责人优化输入</strong>
          <span>包含五维评分、Criterion、Finding、证据路径和优化建议</span>
        </div>
        <button className="button button--primary detailDownloadButton" type="button" onClick={() => downloadFunctionJson(item)}>
          <span aria-hidden="true">↓</span>
          下载 Function JSON 报告
        </button>
      </div>

      {item.error && <div className="evalErrorBox">扫描异常：{item.error}</div>}

      <h3>Confirmed semantic review</h3>
      <SemanticReview review={item.semanticReview} />

      <div className="detailMetrics">
        <span>{item.featureCount} Features</span>
        <span>{item.documentCount} Documents</span>
        <span>{item.findingCount} Findings</span>
        <span>Evidence <Percent value={item.evidence.coverage} /></span>
      </div>

      {item.docs.length > 0 && (
        <div className="detailDocs">
          <strong>规格文档</strong>
          {item.docs.map((doc) => <Link key={doc.docId} to={`/docs/${doc.docId}`}>{doc.label}</Link>)}
        </div>
      )}

      <div className="severityStrip">
        {SEVERITIES.map((severity) => (
          <span key={severity}><b>{item.severityCounts[severity] || 0}</b> {severity}</span>
        ))}
      </div>

      <h3>Findings</h3>
      {item.findings.length > 0
        ? <div className="findingList">{item.findings.map((finding, index) => <Finding item={finding} key={`${finding.rule_id}-${finding.path}-${finding.line || 0}-${index}`} />)}</div>
        : <p className="evalMuted">该 Function 没有检查发现。</p>}
      </section>
    </div>
    </div>
  );
}

export default function SpecEvaluationPage() {
  const [query, setQuery] = useState('');
  const [gate, setGate] = useState('all');
  const [selectedId, setSelectedId] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [semanticEvaluation, setSemanticEvaluation] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [semanticLoadError, setSemanticLoadError] = useState(null);
  const runtimeUrl = useBaseUrl('/data/site-runtime.json');
  const summaryUrl = useBaseUrl('/data/spec-evaluation-summary.json');
  const semanticSummaryUrl = useBaseUrl('/data/semantic-evaluation-summary.json');
  const historyUrl = useBaseUrl('/data/spec-evaluation-history.json');
  const reportUrl = useBaseUrl('/data/spec-evaluation.json');
  const semanticReportUrl = useBaseUrl('/data/semantic-evaluation.json');
  const normalizedQuery = query.trim().toLowerCase();

  // The runtime descriptor decides whether to poll for a live (dynamic-mode)
  // refresh. It is absent on older builds, so default to static (fetch once).
  const runtime = useRuntimeJson(runtimeUrl, {mode: 'static'});
  const pollMs = runtime.mode === 'dynamic' ? DYNAMIC_POLL_MS : 0;

  // Summary/history are runtime-fetched (not just build-time imports) so a
  // data-only refresh is reflected on reload; the bundled JSON is the fallback.
  const summaryData = useRuntimeJson(summaryUrl, bundledSummaryData, pollMs);
  const semanticSummaryData = useRuntimeJson(semanticSummaryUrl, bundledSemanticSummaryData, pollMs);
  const historyData = useRuntimeJson(historyUrl, bundledHistoryData, pollMs);

  useEffect(() => {
    if (!summaryData.available) return undefined;
    let active = true;
    const load = () => {
      fetch(reportUrl)
        .then((response) => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        })
        .then((value) => {
          if (active) { setEvaluation(value); setLoadError(null); }
        })
        .catch((error) => {
          if (active) setLoadError(String(error));
        });
    };
    load();
    if (!pollMs) return () => { active = false; };
    const timer = setInterval(load, pollMs);
    return () => { active = false; clearInterval(timer); };
  }, [reportUrl, summaryData.available, pollMs]);
  useEffect(() => {
    if (!semanticSummaryData.available) return undefined;
    let active = true;
    const load = () => {
      fetch(semanticReportUrl)
        .then((response) => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        })
        .then((value) => {
          if (active) { setSemanticEvaluation(value); setSemanticLoadError(null); }
        })
        .catch((error) => {
          if (active) setSemanticLoadError(String(error));
        });
    };
    load();
    if (!pollMs) return () => { active = false; };
    const timer = setInterval(load, pollMs);
    return () => { active = false; clearInterval(timer); };
  }, [semanticReportUrl, semanticSummaryData.available, pollMs]);
  const allFunctions = useMemo(() => {
    const semanticById = new Map((semanticEvaluation?.functions || []).map((item) => [item.func_id, item]));
    return (evaluation?.functions || []).map((item) => ({...item, semanticReview: semanticById.get(item.funcId) || null}));
  }, [evaluation, semanticEvaluation]);
  const functions = useMemo(() => allFunctions.filter((item) => {
    if (gate !== 'all' && item.gate !== gate) return false;
    if (!normalizedQuery) return true;
    const rules = Object.keys(item.ruleCounts).join(' ');
    return `${item.funcId} ${item.title} ${item.path} ${rules} ${item.semanticReview?.status || ''}`.toLowerCase().includes(normalizedQuery);
  }), [allFunctions, gate, normalizedQuery]);
  const selected = allFunctions.find((item) => item.funcId === selectedId) || null;
  const summary = summaryData.summary;
  const topRules = Object.entries(summary?.ruleCounts || {}).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 12);
  useEffect(() => {
    if (!selectedId) return undefined;
    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setSelectedId(null);
    };
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedId]);

  return (
    <Layout title="Spec Evaluation" description="Function-level ArkUI spec evaluation report">
      <main className="evalPage">
        <section className="evalHero">
          <div className="contentWrap">
            <p className="eyebrow">spec_eval / Function-level</p>
            <h1>Spec Evaluation Report</h1>
            <p className="heroCopy">所有注册功能域的结构、追溯、引用、SDK 合约和证据覆盖扫描结果。</p>
            <div className="heroActions">
              <Link className="button button--primary" to="/spec-evaluation-guide">
                了解评分规则
              </Link>
            </div>
            {summaryData.available && (
              <div className="evalMeta">
                <span>Source <code>{summaryData.sourceRevision?.slice(0, 12)}</code></span>
                <span>Tool {summaryData.toolVersion}</span>
                <span>Rules {summaryData.ruleVersion}</span>
                <span>{new Date(summaryData.generatedAt).toLocaleString('zh-CN')}</span>
              </div>
            )}
          </div>
        </section>

        {!summaryData.available ? (
          <section className="pageBand"><div className="contentWrap evalEmptyState">
            <h2>尚无全量扫描数据</h2>
            <p>先执行 `spec_eval scan --all --report-only` 生成并归档全量报告，再运行站点生成器。</p>
          </div></section>
        ) : (
          <>
            <section className="pageBand">
              <div className="contentWrap">
                <div className="evalSummaryGrid">
                  <SummaryCard label="Registered" value={summary.registeredFunctionCount} />
                  <SummaryCard label="Completed" value={summary.completedFunctionCount} tone="pass" />
                  <SummaryCard label="Gate Pass" value={summary.gateCounts.pass} tone="pass" />
                  <SummaryCard label="Gate Warn" value={summary.gateCounts.warn} tone="warn" />
                  <SummaryCard label="Gate Fail" value={summary.gateCounts.fail} tone="fail" />
                  <SummaryCard label="Scan Error" value={summary.gateCounts.error} tone="error" />
                  <SummaryCard label="Findings" value={summary.findingCount} />
                  <SummaryCard label="Evidence" value={<Percent value={summary.evidenceCoverage} />} />
                  <SummaryCard label="Confirmed semantic" value={semanticSummaryData.available ? semanticSummaryData.summary.confirmedFunctionCount : 0} tone="pass" />
                </div>
              </div>
            </section>

            <GovernanceOverview historyData={historyData} />

            <section className="pageBand mutedBand">
              <div className="contentWrap evalOverviewGrid">
                <div>
                  <div className="sectionHeader"><h2>Severity</h2></div>
                  <div className="severityOverview">
                    {SEVERITIES.map((severity) => (
                      <div key={severity}><span className={`severityBadge severity-${severity.toLowerCase()}`}>{severity}</span><strong>{summary.severityCounts[severity]}</strong></div>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="sectionHeader"><h2>Top Rules</h2></div>
                  <div className="ruleCloud">
                    {topRules.map(([rule, count]) => <span key={rule}><code>{rule}</code><b>{count}</b></span>)}
                  </div>
                </div>
              </div>
            </section>

            <section className="pageBand">
              <div className="contentWrap">
                <div className="sectionHeader"><h2>Functions</h2><p>{functions.length} / {summary.registeredFunctionCount}</p></div>
                {!evaluation && !loadError && <p className="evalMuted">正在加载归档报告…</p>}
                {loadError && <div className="evalErrorBox">归档报告加载失败：{loadError}</div>}
                {semanticLoadError && <div className="evalErrorBox">语义归档加载失败：{semanticLoadError}</div>}
                <div className="evalControls">
                  <input aria-label="Search Functions" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索 FuncID、名称、路径或 Rule ID" />
                  <select aria-label="Filter by gate" value={gate} onChange={(event) => setGate(event.target.value)}>
                    {GATES.map((value) => <option value={value} key={value}>{value === 'all' ? 'All gates' : value.toUpperCase()}</option>)}
                  </select>
                </div>
                <div className="tableScroll">
                  <table className="portalTable evalTable">
                    <thead><tr><th>FuncID</th><th>Function</th><th>Gate</th><th>Published</th><th>Confidence</th><th>Admission</th><th>Features</th><th>Findings</th><th>Evidence</th><th></th></tr></thead>
                    <tbody>
                      {functions.map((item) => (
                        <tr key={item.funcId} className={selectedId === item.funcId ? 'selectedRow' : ''}>
                          <td className="monoCell">{item.funcId}</td>
                          <td><div className="functionTitle">{item.title || '-'}</div><div className="functionPath">{item.path}</div></td>
                          <td><GateBadge gate={item.gate} /></td>
                          <td>
                            {item.semanticReview?.status === 'CONFIRMED' ? item.semanticReview.scores?.published_score ?? '-' : item.semanticReview?.status || '-'}
                            {item.semanticReview?.status === 'CONFIRMED' && item.semanticReview?.revision_current === false && (
                              <span className="revisionDriftMark" title={`评价于 ${String(item.semanticReview.source_revision || '').slice(0, 7)}，当前 ${String(item.semanticReview.observed_revision || '').slice(0, 7)}`}>*</span>
                            )}
                          </td>
                          <td>
                            {item.semanticReview?.status === 'CONFIRMED' ? (
                              (() => {
                                const kernel = item.semanticReview.scores?.kernel_confidence;
                                if (!kernel) return '-';
                                const violations = [...(kernel.major_violations || []), ...(kernel.minor_violations || []), ...(kernel.hard_errors || [])];
                                const tip = violations.length > 0
                                  ? `报告缺陷（可靠性降级 -${kernel.deduction_total ?? 0}）：\n- ${violations.map((v) => `${v.code}${v.message ? ` ${v.message}` : ''}`).join('\n- ')}`
                                  : '可靠性置信度：基于校验违反扣分，无违反';
                                return (
                                  <span className="confidenceCell" title={tip}>
                                    {kernel.score ?? '-'}
                                    {kernel.level && <sup className={`confidenceLevelMark level-${String(kernel.level).toLowerCase()}`}>{kernel.level.charAt(0)}</sup>}
                                  </span>
                                );
                              })()
                            ) : '-'}
                          </td>
                          <td>{item.semanticReview?.status === 'CONFIRMED' ? item.semanticReview.scores?.admission ?? '-' : '-'}</td>
                          <td>{item.featureCount}</td>
                          <td>{item.findingCount}</td>
                          <td><Percent value={item.evidence.coverage} /></td>
                          <td><button className="button button--sm button--secondary" onClick={() => setSelectedId(item.funcId)}>详情</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          </>
        )}
        <FunctionDetailModal item={selected} onClose={() => setSelectedId(null)} />
      </main>
    </Layout>
  );
}
