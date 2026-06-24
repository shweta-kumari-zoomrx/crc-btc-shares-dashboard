import React, { useMemo, useRef } from 'react';
import Plot from 'react-plotly.js';
import Plotly from 'plotly.js-dist-min';

const DRUG_COLORS = {
  'enhertu': '#EE7623',
  'product y + trastuzumab': '#C55A11',
  'pembrolizumab': '#71BF88',
  'pembrolizumab + cisplatin + gemcitabine': '#AED578',
  'nivolumab + ipilimumab': '#002060',
  'durvalumab + cisplatin + gemcitabine': '#0070C0',
  'encorafenib + cetuximab': '#9B59B6',
  'cetuximab + folfox / folfiri': '#F39C12',
  'cetuximab ± folfiri': '#E67E22',
  'panitumumab + folfox/folfiri': '#27AE60',
  'panitumumab + folfiri': '#2ECC71',
  'panitumumab': '#1ABC9C',
  'ramucirumab + folfiri': '#3498DB',
  'aflibercept + folfiri': '#2980B9',
  'bevacizumab + fluoropyrimidine-based chemotherapy': '#548235',
  'regorafenib': '#BF9000',
  'fruquintinib': '#FFC000',
  'trifluridine-tipiracil ± bevacizumab': '#D4B89A',
  'zanidatamab': '#7FB7DF',
  'pemigatinib': '#5B9BD5',
  'futibatinib': '#4472C4',
  'ivosidenib': '#A9C5E8',
  'cisplatin + gemcitabine': '#70AD47',
  'ntrk inhibitors': '#A9D18E',
  'clinical trial': '#7F7F7F',
};
const OTHER_COLOR = '#D9D9D9';
const CHEMO_COLOR = '#FFBFFF';

function colorFor(label) {
  const key = String(label).replace(/\s+/g, ' ').trim().toLowerCase();
  if (DRUG_COLORS[key]) return DRUG_COLORS[key];
  if (key.startsWith('chemotherapy')) return CHEMO_COLOR;
  if (key === 'other') return OTHER_COLOR;
  return '#B0B0B0';
}

export default function SharesChart({ shares, title, subtitle, accentColor = '#E8512A', height = 460 }) {
  const ref = useRef(null);

  const { traces, layout } = useMemo(() => {
    const xLabels = shares.lots.map(lot => `${lot}  (n=${shares.n[lot] ?? 0})`);
    const traces = shares.series
      .filter(s => shares.data[s] && shares.data[s].some(v => v > 0.05))
      .map(s => ({
        type: 'bar',
        name: s,
        x: xLabels,
        y: shares.data[s],
        marker: { color: colorFor(s), line: { width: 0.5, color: '#fff' } },
        text: shares.data[s].map(v => (v >= 4 ? `${v.toFixed(0)}%` : '')),
        textposition: 'inside',
        insidetextanchor: 'middle',
        textfont: { size: 11, color: '#fff' },
        hovertemplate: `<b>${s}</b><br>%{x}<br>%{y:.1f}%<extra></extra>`,
      }));
    const layout = {
      barmode: 'stack',
      barnorm: 'percent',
      height,
      margin: { l: 40, r: 16, t: 16, b: 40 },
      yaxis: { range: [0, 100], ticksuffix: '%', gridcolor: '#eef0f4', zeroline: false },
      xaxis: { tickfont: { size: 12, color: '#333' } },
      legend: { orientation: 'h', y: -0.18, font: { size: 10 } },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      bargap: 0.45,
    };
    return { traces, layout };
  }, [shares, height]);

  const copyChart = async () => {
    try {
      const gd = ref.current?.el;
      if (!gd) return;
      const dataUrl = await Plotly.toImage(gd, { format: 'png', scale: 2, width: 900, height });
      const blob = await (await fetch(dataUrl)).blob();
      await navigator.clipboard.write([new window.ClipboardItem({ 'image/png': blob })]);
      alert('Chart copied — paste into your slide.');
    } catch (e) {
      alert('Copy failed: ' + e.message);
    }
  };

  return (
    <div style={{ padding: 18 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#1a1a2e' }}>{title}</div>
          {subtitle && <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>{subtitle}</div>}
        </div>
        <button onClick={copyChart} style={{
          padding: '6px 14px', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer',
          border: `1.5px solid ${accentColor}`, background: accentColor + '14', color: accentColor,
        }}>Copy Chart</button>
      </div>
      <Plot ref={ref} data={traces} layout={layout} useResizeHandler
        style={{ width: '100%' }} config={{ displayModeBar: false, responsive: true }} />
    </div>
  );
}
