import React, { useState, useEffect, useMemo } from 'react';
import { loadData } from './utils/dataLoader';
import { buildShares } from './utils/sharesBuilder';
import SharesChart from './components/SharesChart';
import './App.css';

const ACCENT = '#E8512A';

// Stratum options depend on indication
function strataFor(ind, M) {
  if (ind === 'CRC') {
    return [
      ...M.crcStrata.map(k => ({ key: k, label: M.crcStrataLabels[k] })),
      ...Object.entries(M.crcOverallMethods).map(([k, v]) => ({ key: k, label: v })),
    ];
  }
  return M.btcStrata.map(k => ({ key: k, label: M.btcStrataLabels[k] }));
}

// Group selections by segment type
function groupSelections(selections) {
  const groups = {};
  selections.forEach(s => {
    if (s.key === 'All') return;
    const eq = s.key.indexOf('=');
    if (eq === -1) return;
    const seg = s.key.slice(0, eq);
    if (!groups[seg]) groups[seg] = [];
    groups[seg].push(s);
  });
  return groups;
}

function MethodologyTab({ meta: M }) {
  return (
    <div style={{ padding: 28, maxWidth: 760 }}>
      <h2 style={{ fontSize: 17, fontWeight: 700, color: '#1a1a2e', marginTop: 0 }}>Methodology</h2>

      <h3 style={{ fontSize: 13, color: '#555', marginBottom: 6 }}>Data Source</h3>
      <p style={{ fontSize: 13, color: '#444', lineHeight: 1.7 }}>
        AP Portal survey 492204 (EU) + 648396 (DE, stitched). Global OL respondents excluded.
        Local outlier fencing applied per indication (CRC: Q3.10Z volume; BTC: eligible patient volume).
        n={M.nTotal} enrolled → {M.nGlobalOL} Global OL removed → {M.nActive} active.
      </p>

      <h3 style={{ fontSize: 13, color: '#555', marginBottom: 6 }}>Weighted Share</h3>
      <p style={{ fontSize: 13, color: '#444', lineHeight: 1.7 }}>
        Per respondent: weight = IHC-stratum patient volume (CRC: Q3.10Z; BTC: eligible × LoT %).
        Only respondents with weight &gt; 0 in that cell are included.
        Weighted share = Σ(weight_i × share_i) / Σ(weight_i).
      </p>

      <h3 style={{ fontSize: 13, color: '#555', marginBottom: 6 }}>CRC Overall Methods</h3>
      <ul style={{ fontSize: 13, color: '#444', lineHeight: 1.9, paddingLeft: 18 }}>
        <li><b>all3</b>: blend IHC3+ / IHC2+ / IHC-Unknown by total patient weight from each stratum</li>
        <li><b>ihc_pos</b>: blend IHC3+ + IHC2+ only (exclude Unknown)</li>
        <li><b>median_replace</b>: replace zero weights within each stratum with that stratum's median weight, then blend by IHC proportion</li>
      </ul>

      <h3 style={{ fontSize: 13, color: '#555', marginBottom: 6 }}>Multi-Segment Blending</h3>
      <p style={{ fontSize: 13, color: '#444', lineHeight: 1.7 }}>
        When multiple segment values are selected (e.g. two practice settings), shares are blended:
        blended share = Σ(tw_k × share_k) / Σ(tw_k) for weighted;
        Σ(n_k × share_k) / Σ(n_k) for unweighted.
        Cross-segment combinations (e.g. specialty × region) are not available — single segment type only.
      </p>

      <h3 style={{ fontSize: 13, color: '#555', marginBottom: 6 }}>Unweighted Share</h3>
      <p style={{ fontSize: 13, color: '#444', lineHeight: 1.7 }}>
        Simple mean of each respondent's share across all answering respondents (n-blended for multi-segment).
      </p>

      <h3 style={{ fontSize: 13, color: '#555', marginBottom: 6 }}>Product Labels</h3>
      <p style={{ fontSize: 13, color: '#444', lineHeight: 1.7 }}>
        "ENHERTU" = trastuzumab deruxtecan (T-DXd) — labeled as Product A / Product X in survey.
        "PRODUCT Y + trastuzumab" = second pipeline agent.
      </p>
    </div>
  );
}

export default function App() {
  const [agg, setAgg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [indication, setIndication] = useState('CRC');
  const [timeframe, setTimeframe] = useState('future');
  const [stratum, setStratum] = useState('IHC3');
  const [weightMode, setWeightMode] = useState('weighted');
  const [activeTab, setActiveTab] = useState('chart');

  // Multi-select: { segmentType: Set<value> }  e.g. { 'Practice Setting': Set(['Cancer / Specialized']) }
  // null/empty = "All"
  const [segmentSelections, setSegmentSelections] = useState({});

  useEffect(() => {
    loadData()
      .then(({ agg }) => { setAgg(agg); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, []);

  // When indication changes, reset stratum to IHC3
  useEffect(() => { setStratum('IHC3'); }, [indication]);

  const M = agg?.meta;

  // Determine active selection keys from multi-select state
  const activeSelectionKeys = useMemo(() => {
    if (!M) return ['All'];
    const activeSeg = Object.entries(segmentSelections).find(([, vals]) => vals && vals.size > 0);
    if (!activeSeg) return ['All'];
    const [segType, vals] = activeSeg;
    const keys = [...vals].map(v => `${segType}=${v}`).filter(k => agg.data[k]);
    return keys.length > 0 ? keys : ['All'];
  }, [segmentSelections, M, agg]);

  const shares = useMemo(() => {
    if (!agg) return null;
    return buildShares(agg, activeSelectionKeys, indication, stratum, timeframe, weightMode);
  }, [agg, activeSelectionKeys, indication, stratum, timeframe, weightMode]);

  if (loading) return <div className="center-screen">Loading data…</div>;
  if (error) return <div className="center-screen" style={{ color: '#ef4444' }}>Error: {error}</div>;

  const stratumOptions = strataFor(indication, M);
  const selectionGroups = groupSelections(M.selections);

  // Label for current segment selection
  const activeSeg = Object.entries(segmentSelections).find(([, v]) => v && v.size > 0);
  const selLabel = activeSeg
    ? `${activeSeg[0]}: ${[...activeSeg[1]].join(', ')}`
    : 'All respondents';
  const selN = activeSelectionKeys === 'All' || activeSelectionKeys[0] === 'All'
    ? M.nActive
    : activeSelectionKeys.reduce((s, k) => s + (M.selections.find(x => x.key === k)?.nActive || 0), 0);

  const strLabel = indication === 'CRC'
    ? (M.crcStrataLabels[stratum] || M.crcOverallMethods[stratum] || stratum)
    : (M.btcStrataLabels[stratum] || stratum);

  const chartTitle = `${M.indications[indication]} — ${strLabel}`;
  const chartSub = `${M.timeframes[timeframe]} · ${weightMode} · ${selLabel} · n=${selN}`;

  const toggleSegVal = (segType, val) => {
    setSegmentSelections(prev => {
      const cur = new Set(prev[segType] || []);
      // Clear other segment types
      const next = {};
      if (cur.has(val)) {
        cur.delete(val);
      } else {
        cur.add(val);
      }
      next[segType] = cur;
      return next;
    });
  };

  const clearSegments = () => setSegmentSelections({});

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <div className="controls-sidebar">
        <div className="brand">
          <span className="brand-dot" style={{ background: ACCENT }} />
          <span className="brand-name">ZoomRx</span>
        </div>
        <div className="brand-sub">CRC / BTC EU Wave 1 · Shares</div>

        <hr className="divider" />

        {/* View tabs */}
        <div className="section">
          <div className="section-label">View</div>
          {[['chart', 'Shares Chart'], ['methodology', 'Methodology']].map(([t, lbl]) => (
            <button key={t} className={`pill-btn ${activeTab === t ? 'active' : ''}`}
              style={activeTab === t ? { background: ACCENT + '22', borderColor: ACCENT, color: ACCENT } : {}}
              onClick={() => setActiveTab(t)}>{lbl}</button>
          ))}
        </div>

        <hr className="divider" />

        {/* Indication */}
        <div className="section">
          <div className="section-label">Indication</div>
          {Object.entries(M.indications).map(([k, v]) => (
            <label key={k} className="radio-row">
              <input type="radio" checked={indication === k} onChange={() => setIndication(k)} style={{ accentColor: ACCENT }} />
              <span>{v}</span>
              <span className="chip" style={{ background: ACCENT + '22', color: ACCENT }}>{k}</span>
            </label>
          ))}
        </div>

        <hr className="divider" />

        {/* Timeframe */}
        <div className="section">
          <div className="section-label">Timeframe</div>
          {Object.entries(M.timeframes).map(([k, v]) => (
            <label key={k} className="radio-row">
              <input type="radio" checked={timeframe === k} onChange={() => setTimeframe(k)} style={{ accentColor: ACCENT }} />
              <span>{v}</span>
            </label>
          ))}
        </div>

        <hr className="divider" />

        {/* IHC Stratum */}
        <div className="section">
          <div className="section-label">IHC Stratum</div>
          {stratumOptions.map(({ key, label }) => (
            <label key={key} className="radio-row">
              <input type="radio" checked={stratum === key} onChange={() => setStratum(key)} style={{ accentColor: ACCENT }} />
              <span style={{ fontSize: 12 }}>{label}</span>
            </label>
          ))}
        </div>

        <hr className="divider" />

        {/* Weighting */}
        <div className="section">
          <div className="section-label">Weighting</div>
          {[['weighted', 'Weighted'], ['unweighted', 'Unweighted']].map(([k, v]) => (
            <label key={k} className="radio-row">
              <input type="radio" checked={weightMode === k} onChange={() => setWeightMode(k)} style={{ accentColor: ACCENT }} />
              <span>{v}</span>
            </label>
          ))}
        </div>

        <hr className="divider" />

        {/* Segment multi-select */}
        <div className="section">
          <div className="section-label">Segment Filter</div>
          <div style={{ marginBottom: 6 }}>
            <label className="radio-row">
              <input type="radio" checked={!activeSeg} onChange={clearSegments} style={{ accentColor: ACCENT }} />
              <span>All respondents (n={M.nActive})</span>
            </label>
          </div>

          {Object.entries(selectionGroups).map(([segType, items]) => {
            const curSet = segmentSelections[segType] || new Set();
            const isActiveType = activeSeg && activeSeg[0] === segType;
            return (
              <div key={segType} className="segment-group" style={{ marginTop: 8 }}>
                <div className="segment-group-label">{segType}</div>
                {items.map(({ key, label, nActive }) => {
                  const val = key.slice(key.indexOf('=') + 1);
                  const checked = curSet.has(val);
                  return (
                    <label key={key} className="check-row">
                      <input type="checkbox"
                        checked={checked && isActiveType}
                        onChange={() => toggleSegVal(segType, val)}
                        style={{ accentColor: ACCENT }} />
                      <span style={{ fontSize: 12 }}>{label.replace(/^[^:]+:\s*/, '')}
                        <span style={{ color: '#aaa', fontSize: 10.5 }}> (n={nActive})</span>
                      </span>
                    </label>
                  );
                })}
              </div>
            );
          })}
          {activeSeg && (
            <div className="select-all-row" onClick={clearSegments}>Clear filter</div>
          )}
        </div>

        <hr className="divider" />
        <div style={{ fontSize: 10.5, color: '#bbb', lineHeight: 1.5, paddingBottom: 12 }}>
          n={M.nTotal} enrolled · {M.nGlobalOL} Global OL removed · {M.nActive} active
        </div>
      </div>

      {/* ── Main content ── */}
      <div className="main-content">
        <div className="main-header" style={{ borderLeft: `4px solid ${ACCENT}` }}>
          <div>
            <div className="main-title">{chartTitle}</div>
            <div className="main-sub">{chartSub}</div>
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            {Object.keys(M.indications).map(k => (
              <button key={k} onClick={() => setIndication(k)} style={{
                padding: '5px 16px', borderRadius: 20, fontSize: 12.5, fontWeight: 700,
                border: `1.5px solid ${indication === k ? ACCENT : '#ddd'}`,
                background: indication === k ? ACCENT : '#fff',
                color: indication === k ? '#fff' : '#555', cursor: 'pointer',
              }}>{k}</button>
            ))}
          </div>
        </div>

        <div className="content-card">
          {activeTab === 'chart' && shares && (
            <SharesChart shares={shares} title={chartTitle} subtitle={chartSub} accentColor={ACCENT} />
          )}
          {activeTab === 'methodology' && <MethodologyTab meta={M} />}
        </div>
      </div>
    </div>
  );
}
