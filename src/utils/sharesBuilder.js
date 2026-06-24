// sharesBuilder.js — pure lookup into shares_agg.json.
// Multi-select blending: when multiple selection keys are provided,
// blend by total weight: Σ(tw_k × share_k) / Σ(tw_k)  (weighted mode)
//                        Σ(n_k  × share_k) / Σ(n_k)   (unweighted mode)

// Returns { series, lots, data: {drug: [v1L,v2L,v3L]}, n: {lot} }  (values in %)
export function buildShares(agg, selectionKeys, indication, stratum, timeframe, weightMode) {
  const M = agg.meta;
  const series = M.series[indication];
  const lots = M.lots;

  // Gather per-lot cells for each selection key
  const lotData = {};
  lots.forEach(lot => {
    let sumW = 0;
    const drugAccum = {};
    series.forEach(s => { drugAccum[s] = 0; });

    selectionKeys.forEach(key => {
      const selData = agg.data[key];
      if (!selData) return;
      const cell = selData?.[indication]?.[timeframe]?.[stratum]?.[lot];
      if (!cell) return;

      const w = weightMode === 'weighted' ? (cell.tw || 0) : (cell.n || 0);
      if (w <= 0) return;
      const src = weightMode === 'weighted' ? cell.weighted : cell.unweighted;
      if (!src) return;

      sumW += w;
      series.forEach(s => {
        drugAccum[s] += (src[s] || 0) * w;
      });
    });

    lotData[lot] = { drugAccum, sumW };
  });

  // Build output data arrays per series
  const data = {};
  series.forEach(s => { data[s] = []; });
  lots.forEach(lot => {
    const { drugAccum, sumW } = lotData[lot];
    series.forEach(s => {
      data[s].push(sumW > 0 ? drugAccum[s] / sumW : 0);
    });
  });

  // n = max n across selection keys for display (not used in blend math)
  const n = {};
  lots.forEach((lot, i) => {
    let total = 0;
    selectionKeys.forEach(key => {
      const cell = agg.data[key]?.[indication]?.[timeframe]?.[stratum]?.[lot];
      total += (cell?.n || 0);
    });
    n[lot] = total;
  });

  return { series, lots, data, n };
}

export function topSeries(sharesObj, lotIdx, k = 3) {
  return sharesObj.series
    .map(s => ({ series: s, val: sharesObj.data[s][lotIdx] }))
    .filter(x => x.val > 0.05)
    .sort((a, b) => b.val - a.val)
    .slice(0, k);
}
