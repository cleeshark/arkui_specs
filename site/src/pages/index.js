import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import registry from '../data/registry.json';

function Stat({label, value}) {
  return (
    <div className="statBox">
      <div className="statValue">{value}</div>
      <div className="statLabel">{label}</div>
    </div>
  );
}

function StatusBadge({status}) {
  const normalized = String(status).toLowerCase();
  return <span className={`statusBadge status-${normalized}`}>{status}</span>;
}

function TopLevelCard({item}) {
  return (
    <section className="domainCard">
      <div className="domainHeader">
        <span className="domainId">{item.id}</span>
        <h3>{item.title}</h3>
      </div>
      <p>{item.description}</p>
      <div className="domainMeta">
        <span>{item.functionCount} domains</span>
        <span>{item.documentedFunctionCount} documented</span>
      </div>
    </section>
  );
}

function FunctionRow({item}) {
  const primary = item.designDocId || item.features.find((feature) => feature.docId)?.docId;
  return (
    <tr>
      <td className="monoCell">{item.id}</td>
      <td>
        <div className="functionTitle">{item.l3.title}</div>
        <div className="functionPath">{item.path}</div>
      </td>
      <td>{item.featureCount}</td>
      <td>{item.documentedFeatureCount}</td>
      <td>
        <div className="statusList">
          {Object.entries(item.statusCounts).map(([status, count]) => (
            <span key={status} className="statusCount">
              <StatusBadge status={status} /> {count}
            </span>
          ))}
        </div>
      </td>
      <td>{primary ? <Link to={`/docs/${primary}`}>Open</Link> : '-'}</td>
    </tr>
  );
}

export default function Home() {
  const documentedFunctions = registry.functions.filter((item) => item.hasDocs);
  const statusEntries = Object.entries(registry.summary.featureStatusCounts);

  return (
    <Layout title="ArkUI Specs" description="Registry-driven ArkUI feature specifications">
      <main>
        <section className="portalHero">
          <div className="portalHeroInner">
            <div>
              <p className="eyebrow">ArkUI ace_engine</p>
              <h1>Feature Specification Portal</h1>
              <p className="heroCopy">
                Browse ArkUI functional domains, design documents, feature specs, and implementation status from a
                registry-backed documentation index.
              </p>
              <div className="heroActions">
                <Link className="button button--primary" to="/docs">
                  Open Spec Index
                </Link>
                <Link className="button button--secondary" to="/docs/registry">
                  Registry Rules
                </Link>
              </div>
            </div>
            <div className="heroStats" aria-label="Repository summary">
              <Stat label="Functional domains" value={registry.summary.functionCount} />
              <Stat label="Documented domains" value={registry.summary.documentedFunctionCount} />
              <Stat label="Registered features" value={registry.summary.featureCount} />
              <Stat label="Spec files" value={registry.summary.documentedFeatureCount} />
            </div>
          </div>
        </section>

        <section className="pageBand">
          <div className="contentWrap">
            <div className="sectionHeader">
              <h2>Feature Status</h2>
              <p>Registry status counts are generated from `registry/features.yaml` at build time.</p>
            </div>
            <div className="statusGrid">
              {statusEntries.map(([status, count]) => (
                <div className="statusPanel" key={status}>
                  <StatusBadge status={status} />
                  <strong>{count}</strong>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="pageBand mutedBand">
          <div className="contentWrap">
            <div className="sectionHeader">
              <h2>Domain Map</h2>
              <p>Top-level ArkUI areas and how many functional domains already have visible documentation.</p>
            </div>
            <div className="domainGrid">
              {registry.topLevels.map((item) => (
                <TopLevelCard item={item} key={item.id} />
              ))}
            </div>
          </div>
        </section>

        <section className="pageBand">
          <div className="contentWrap">
            <div className="sectionHeader">
              <h2>Documented Functional Domains</h2>
              <p>Only domains with a design document or at least one spec file are listed here.</p>
            </div>
            <div className="tableScroll">
              <table className="portalTable">
                <thead>
                  <tr>
                    <th>FuncID</th>
                    <th>Domain</th>
                    <th>Features</th>
                    <th>Specs</th>
                    <th>Status</th>
                    <th>Docs</th>
                  </tr>
                </thead>
                <tbody>
                  {documentedFunctions.map((item) => (
                    <FunctionRow item={item} key={item.id} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
