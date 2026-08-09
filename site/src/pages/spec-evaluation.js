import React, {useEffect, useMemo, useState} from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import summaryData from '../data/spec-evaluation-summary.json';
import semanticSummaryData from '../data/semantic-evaluation-summary.json';

const GATES = ['all', 'pass', 'warn', 'fail', 'error'];
const SEVERITIES = ['Critical', 'Major', 'Minor', 'Info'];
const DIMENSIONS = [
  {id: 'correctness', label: 'Correctness', max: 30},
  {id: 'spec_executability', label: 'Spec', max: 25},
  {id: 'design_quality', label: 'Design', max: 25},
  {id: 'compatibility_system_impact', label: 'Impact', max: 10},
  {id: 'function_modeling', label: 'Modeling', max: 10},
];

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
      </div>
      {actionable && (
        <div className="criterionEvidence">
          <p>{criterion.reason || '该 Criterion 存在需要处理的支持缺口。'}</p>
          {(criterion.findings || []).map((finding, index) => (
            <article className="criterionFinding" key={finding.finding_id || `${criterion.criterion_id}-${index}`}>
              <div className="findingHeader">
                <span className={`severityBadge severity-${String(finding.severity).toLowerCase()}`}>{finding.severity}</span>
                <code>{finding.finding_id || 'finding'}</code>
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

function SemanticReview({review}) {
  if (!review) return <p className="evalMuted">当前 revision 没有 confirmed semantic Review。</p>;
  const score = review.scores || {};
  return (
    <section className="semanticReview">
      {review.status === 'EXPIRED' && (
        <div className="evalErrorBox">该 Review 已过期：Review revision {review.staleness?.review_source_revision}，当前静态 revision {review.staleness?.static_source_revision}。</div>
      )}
      <div className="detailMetrics">
        <span>状态 <b>{review.status}</b></span>
        <span>发布分 <b>{score.published_score ?? '-'}</b></span>
        <span>置信度 <b>{score.confidence ?? '-'}</b></span>
        <span>准入 <b>{score.admission ?? '-'}</b></span>
      </div>
      <p className="evalMuted">人工确认：{review.confirmation?.confirmed_by || '-'} · {review.confirmation?.confirmed_at || '-'}</p>
      <p className="evalMuted">置信度表示证据与评价流程的完整性，不是质量得分。</p>
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
              <button className="button button--sm button--secondary detailDownloadButton" type="button" onClick={() => downloadFunctionJson(item)}>
                下载 Function JSON
              </button>
        </div>
        <GateBadge gate={item.gate} />
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
  const reportUrl = useBaseUrl('/data/spec-evaluation.json');
  const semanticReportUrl = useBaseUrl('/data/semantic-evaluation.json');
  const normalizedQuery = query.trim().toLowerCase();
  useEffect(() => {
    if (!summaryData.available) return undefined;
    let active = true;
    fetch(reportUrl)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((value) => {
        if (active) setEvaluation(value);
      })
      .catch((error) => {
        if (active) setLoadError(String(error));
      });
    return () => { active = false; };
  }, [reportUrl]);
  useEffect(() => {
    if (!semanticSummaryData.available) return undefined;
    let active = true;
    fetch(semanticReportUrl)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((value) => {
        if (active) setSemanticEvaluation(value);
      })
      .catch((error) => {
        if (active) setSemanticLoadError(String(error));
      });
    return () => { active = false; };
  }, [semanticReportUrl]);
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
  const topRules = Object.entries(summary.ruleCounts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 12);
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
                    <thead><tr><th>FuncID</th><th>Function</th><th>Gate</th><th>Published</th><th>Admission</th><th>Features</th><th>Findings</th><th>Evidence</th><th></th></tr></thead>
                    <tbody>
                      {functions.map((item) => (
                        <tr key={item.funcId} className={selectedId === item.funcId ? 'selectedRow' : ''}>
                          <td className="monoCell">{item.funcId}</td>
                          <td><div className="functionTitle">{item.title || '-'}</div><div className="functionPath">{item.path}</div></td>
                          <td><GateBadge gate={item.gate} /></td>
                          <td>{item.semanticReview?.status === 'CONFIRMED' ? item.semanticReview.scores?.published_score ?? '-' : item.semanticReview?.status || '-'}</td>
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
