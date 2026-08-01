import React, {useEffect, useMemo, useState} from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import summaryData from '../data/spec-evaluation-summary.json';

const GATES = ['all', 'pass', 'warn', 'fail', 'error'];
const SEVERITIES = ['Critical', 'Major', 'Minor', 'Info'];

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

      {item.error && <div className="evalErrorBox">扫描异常：{item.error}</div>}

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
  const [loadError, setLoadError] = useState(null);
  const reportUrl = useBaseUrl('/data/spec-evaluation.json');
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
  const allFunctions = evaluation?.functions || [];
  const functions = useMemo(() => allFunctions.filter((item) => {
    if (gate !== 'all' && item.gate !== gate) return false;
    if (!normalizedQuery) return true;
    const rules = Object.keys(item.ruleCounts).join(' ');
    return `${item.funcId} ${item.title} ${item.path} ${rules}`.toLowerCase().includes(normalizedQuery);
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
                <div className="evalControls">
                  <input aria-label="Search Functions" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索 FuncID、名称、路径或 Rule ID" />
                  <select aria-label="Filter by gate" value={gate} onChange={(event) => setGate(event.target.value)}>
                    {GATES.map((value) => <option value={value} key={value}>{value === 'all' ? 'All gates' : value.toUpperCase()}</option>)}
                  </select>
                </div>
                <div className="tableScroll">
                  <table className="portalTable evalTable">
                    <thead><tr><th>FuncID</th><th>Function</th><th>Gate</th><th>Features</th><th>Findings</th><th>Evidence</th><th></th></tr></thead>
                    <tbody>
                      {functions.map((item) => (
                        <tr key={item.funcId} className={selectedId === item.funcId ? 'selectedRow' : ''}>
                          <td className="monoCell">{item.funcId}</td>
                          <td><div className="functionTitle">{item.title || '-'}</div><div className="functionPath">{item.path}</div></td>
                          <td><GateBadge gate={item.gate} /></td>
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
