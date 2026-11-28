/**
 * VieTrueVoice v0.9.4 — Real HD Canvas Forensic Charts Renderer
 * Renders 4 scientific visualizations directly from backend `response.forensics`
 * (ZERO mock data):
 *   1. Mel-Spectrogram Heatmap (Magma/Thermal LUT + Slaney 3.4kHz & 4.0kHz cutoffs)
 *   2. Waveform Oscilloscope (colored by BONA_FIDE / SPOOF / BORDERLINE verdict)
 *   3. Multi-Window Consensus Asymmetric Veto Bar Chart + Anomaly Risk Heatbar
 *   4. Platt Calibration Curve (T=16.0, [-8,+8] Borderline Zone) & 3-Band Energy Bars
 */
(function () {
  'use strict';

  const COLORS = {
    bg: '#0e0e10',
    surface: '#1c1b1e',
    grid: 'rgba(186, 203, 190, 0.11)',
    gridStrong: 'rgba(186, 203, 190, 0.24)',
    text: '#e5e1e5',
    muted: '#bacbbe',
    emerald: '#6dffba',
    emeraldStrong: '#00e599',
    crimson: '#df0042',
    crimsonSoft: '#ffb3b6',
    amber: '#ffbd5d',
    amberSoft: '#ffe0bc',
  };

  // Precompute 256-entry Magma / Thermal Forensic LUT (obsidian floor -> violet -> crimson -> amber -> cream)
  const MAGMA_STOPS = [
    [0.00, 14, 14, 16],     // #0e0e10 obsidian floor
    [0.16, 28, 16, 68],     // deep indigo
    [0.34, 81, 18, 124],    // forensic violet
    [0.54, 182, 54, 121],   // magenta
    [0.74, 232, 72, 92],    // thermal crimson
    [0.89, 254, 169, 108],  // warm amber
    [1.00, 252, 253, 191],  // peak cream
  ];

  const MAGMA_LUT = (function buildLut() {
    const lut = new Uint8Array(256 * 3);
    for (let i = 0; i < 256; i++) {
      const t = i / 255;
      let s0 = MAGMA_STOPS[0];
      let s1 = MAGMA_STOPS[MAGMA_STOPS.length - 1];
      for (let k = 0; k < MAGMA_STOPS.length - 1; k++) {
        if (t >= MAGMA_STOPS[k][0] && t <= MAGMA_STOPS[k + 1][0]) {
          s0 = MAGMA_STOPS[k];
          s1 = MAGMA_STOPS[k + 1];
          break;
        }
      }
      const span = Math.max(1e-6, s1[0] - s0[0]);
      const f = (t - s0[0]) / span;
      lut[i * 3] = Math.round(s0[1] + (s1[1] - s0[1]) * f);
      lut[i * 3 + 1] = Math.round(s0[2] + (s1[2] - s0[2]) * f);
      lut[i * 3 + 2] = Math.round(s0[3] + (s1[3] - s0[3]) * f);
    }
    return lut;
  })();

  // Exact Slaney Mel scale (matches librosa.feature.melspectrogram default htk=False)
  function hzToMelSlaney(hz) {
    const fMin = 0.0;
    const fSp = 200.0 / 3.0;
    const minLogHz = 1000.0;
    const minLogMel = (minLogHz - fMin) / fSp;
    const logStep = Math.log(6.4) / 27.0;
    if (hz >= minLogHz) {
      return minLogMel + Math.log(hz / minLogHz) / logStep;
    }
    return (hz - fMin) / fSp;
  }

  function setupHiDPICanvas(canvas, defaultHeight) {
    if (!canvas) return null;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const cssWidth = Math.max(
      240,
      Math.floor(canvas.clientWidth || canvas.parentElement?.clientWidth || 640)
    );
    const cssHeight = Math.max(
      110,
      Math.floor(Number(canvas.getAttribute('data-height')) || defaultHeight || 220)
    );
    canvas.width = Math.round(cssWidth * dpr);
    canvas.height = Math.round(cssHeight * dpr);
    canvas.style.height = cssHeight + 'px';

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = COLORS.bg;
    ctx.fillRect(0, 0, cssWidth, cssHeight);
    return { ctx: ctx, w: cssWidth, h: cssHeight };
  }

  function drawEmptyState(ctx, w, h, message) {
    ctx.fillStyle = COLORS.bg;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = COLORS.grid;
    ctx.strokeRect(0.5, 0.5, w - 1, h - 1);
    ctx.fillStyle = COLORS.muted;
    ctx.font = '11px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(message || 'CHƯA CÓ DỮ LIỆU PHÂN TÍCH', w / 2, h / 2);
  }

  function getVerdictColor(verdict, isBorderline) {
    if (isBorderline) return COLORS.amber;
    if (verdict === 'BONA_FIDE') return COLORS.emerald;
    return COLORS.crimson;
  }

  /**
   * 1. Mel-Spectrogram Heatmap Canvas
   * Renders forensics.mel_spectrogram ({ n_mels, n_frames, fmax, values })
   * with dashed cutoff markers at 3.4 kHz (AMR-NB) and 4.0 kHz (Vocoder/CFM).
   */
  function renderMelSpectrogram(canvas, melSpec, options) {
    const opts = options || {};
    const compact = Boolean(opts.compact);
    const setup = setupHiDPICanvas(canvas, compact ? 150 : 230);
    if (!setup) return;
    const { ctx, w, h } = setup;

    if (!melSpec || !Array.isArray(melSpec.values) || melSpec.values.length === 0) {
      drawEmptyState(ctx, w, h, 'KHÔNG CÓ DỮ LIỆU MEL-SPECTROGRAM');
      return;
    }

    const values = melSpec.values;
    const nMels = values.length;
    const nFrames = Array.isArray(values[0]) ? values[0].length : 0;
    const fmax = Number(melSpec.fmax) || 8000;
    const duration = Number(opts.durationSec) || 0;

    if (nFrames === 0) {
      drawEmptyState(ctx, w, h, 'SPECTROGRAM RỖNG');
      return;
    }

    const pad = compact
      ? { top: 14, right: 10, bottom: 20, left: 42 }
      : { top: 20, right: 14, bottom: 28, left: 52 };
    const plotW = Math.max(40, w - pad.left - pad.right);
    const plotH = Math.max(40, h - pad.top - pad.bottom);

    // Build pixel-accurate offscreen bitmap [nFrames x nMels] and draw smoothly scaled
    const off = document.createElement('canvas');
    off.width = nFrames;
    off.height = nMels;
    const offCtx = off.getContext('2d');
    const imgData = offCtx.createImageData(nFrames, nMels);
    const buf = imgData.data;

    for (let m = 0; m < nMels; m++) {
      const row = values[m];
      const yImg = nMels - 1 - m; // Low freq at bottom, high freq at top
      for (let t = 0; t < nFrames; t++) {
        const rawVal = row && row[t] != null ? row[t] : 0;
        const idx = Math.max(0, Math.min(255, Math.round(rawVal)));
        const p = (yImg * nFrames + t) * 4;
        buf[p] = MAGMA_LUT[idx * 3];
        buf[p + 1] = MAGMA_LUT[idx * 3 + 1];
        buf[p + 2] = MAGMA_LUT[idx * 3 + 2];
        buf[p + 3] = 255;
      }
    }
    offCtx.putImageData(imgData, 0, 0);

    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(off, pad.left, pad.top, plotW, plotH);
    ctx.restore();

    // Border frame
    ctx.strokeStyle = COLORS.gridStrong;
    ctx.lineWidth = 1;
    ctx.strokeRect(pad.left + 0.5, pad.top + 0.5, plotW - 1, plotH - 1);

    const maxMel = hzToMelSlaney(fmax);
    function freqToY(hz) {
      const ratio = Math.max(0, Math.min(1, hzToMelSlaney(hz) / maxMel));
      return pad.top + plotH * (1 - ratio);
    }

    // Dashed Forensic Cutoffs: 3.4 kHz (AMR-NB PSTN) & 4.0 kHz (Vocoder / CFM phase boundary)
    const cutoffs = [
      { hz: 3400, color: COLORS.amber, label: compact ? '3.4k' : '3.4 kHz AMR-NB', yOffset: 10 },
      { hz: 4000, color: COLORS.crimsonSoft, label: compact ? '4.0k' : '4.0 kHz VOCODER', yOffset: -5 },
    ];

    cutoffs.forEach(function (c) {
      if (c.hz > fmax) return;
      const y = Math.round(freqToY(c.hz)) + 0.5;
      ctx.save();
      ctx.strokeStyle = c.color;
      ctx.lineWidth = 1.25;
      ctx.setLineDash([5, 4]);
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + plotW, y);
      ctx.stroke();
      ctx.setLineDash([]);

      // Inline badge on right edge
      ctx.font = '600 ' + (compact ? 9 : 10) + 'px "JetBrains Mono", monospace';
      const tw = ctx.measureText(c.label).width;
      const bx = pad.left + plotW - tw - 10;
      const by = c.yOffset < 0 ? y - 14 : y + 3;
      ctx.fillStyle = 'rgba(14, 14, 16, 0.82)';
      ctx.fillRect(bx - 4, by - 1, tw + 8, 13);
      ctx.fillStyle = c.color;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      ctx.fillText(c.label, bx, by + 1);
      ctx.restore();
    });

    // Y-axis frequency ticks
    const yTicks = compact ? [0, 1000, 3400, 8000] : [0, 500, 1000, 2000, 3400, 4000, 8000];
    ctx.fillStyle = COLORS.muted;
    ctx.font = (compact ? 9 : 10) + 'px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    yTicks.forEach(function (hz) {
      if (hz > fmax) return;
      const y = freqToY(hz);
      const label = hz >= 1000 ? (hz / 1000).toFixed(hz % 1000 === 0 ? 0 : 1) + 'k' : String(hz);
      ctx.fillText(label, pad.left - 6, y);
      ctx.strokeStyle = 'rgba(186, 203, 190, 0.25)';
      ctx.beginPath();
      ctx.moveTo(pad.left - 3, y);
      ctx.lineTo(pad.left, y);
      ctx.stroke();
    });

    // X-axis time ticks
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    const xSteps = compact ? 3 : 4;
    for (let i = 0; i <= xSteps; i++) {
      const frac = i / xSteps;
      const x = pad.left + plotW * frac;
      const tLabel = duration > 0 ? (duration * frac).toFixed(1) + 's' : Math.round(nFrames * frac) + 'f';
      ctx.fillStyle = COLORS.muted;
      ctx.fillText(tLabel, x, pad.top + plotH + 6);
    }
  }

  /**
   * 2. Waveform Oscilloscope Canvas
   * Renders forensics.waveform (array of up to 240 floats in [-1, 1]).
   */
  function renderWaveform(canvas, waveform, options) {
    const opts = options || {};
    const compact = Boolean(opts.compact);
    const setup = setupHiDPICanvas(canvas, compact ? 110 : 165);
    if (!setup) return;
    const { ctx, w, h } = setup;

    if (!Array.isArray(waveform) || waveform.length === 0) {
      drawEmptyState(ctx, w, h, 'KHÔNG CÓ DỮ LIỆU DẠNG SÓNG');
      return;
    }

    const pad = compact
      ? { top: 12, right: 10, bottom: 16, left: 36 }
      : { top: 18, right: 14, bottom: 22, left: 44 };
    const plotW = Math.max(40, w - pad.left - pad.right);
    const plotH = Math.max(36, h - pad.top - pad.bottom);
    const midY = pad.top + plotH / 2;
    const accent = getVerdictColor(opts.verdict, opts.isBorderline);

    // Subtle forensic grid
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    [0.25, 0.5, 0.75].forEach(function (frac) {
      const y = Math.round(pad.top + plotH * frac) + 0.5;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + plotW, y);
      ctx.stroke();
    });
    for (let g = 1; g < 4; g++) {
      const x = Math.round(pad.left + (plotW * g) / 4) + 0.5;
      ctx.beginPath();
      ctx.moveTo(x, pad.top);
      ctx.lineTo(x, pad.top + plotH);
      ctx.stroke();
    }

    // Center 0.0 axis
    ctx.strokeStyle = COLORS.gridStrong;
    ctx.beginPath();
    ctx.moveTo(pad.left, Math.round(midY) + 0.5);
    ctx.lineTo(pad.left + plotW, Math.round(midY) + 0.5);
    ctx.stroke();

    // Waveform area fill
    const n = waveform.length;
    const ampScale = plotH * 0.45;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(pad.left, midY);
    for (let i = 0; i < n; i++) {
      const x = pad.left + (i / Math.max(1, n - 1)) * plotW;
      const v = Math.max(-1, Math.min(1, Number(waveform[i]) || 0));
      ctx.lineTo(x, midY - v * ampScale);
    }
    ctx.lineTo(pad.left + plotW, midY);
    ctx.closePath();
    ctx.fillStyle = opts.isBorderline
      ? 'rgba(255, 189, 93, 0.16)'
      : (opts.verdict === 'BONA_FIDE' ? 'rgba(109, 255, 186, 0.15)' : 'rgba(223, 0, 66, 0.18)');
    ctx.fill();

    // Oscilloscope stroke
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const x = pad.left + (i / Math.max(1, n - 1)) * plotW;
      const v = Math.max(-1, Math.min(1, Number(waveform[i]) || 0));
      const y = midY - v * ampScale;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = accent;
    ctx.lineWidth = compact ? 1.35 : 1.7;
    ctx.stroke();
    ctx.restore();

    // Frame + Y ticks (+1, 0, -1)
    ctx.strokeStyle = COLORS.gridStrong;
    ctx.strokeRect(pad.left + 0.5, pad.top + 0.5, plotW - 1, plotH - 1);

    ctx.fillStyle = COLORS.muted;
    ctx.font = '9px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText('+1.0', pad.left - 5, pad.top + 5);
    ctx.fillText('0.0', pad.left - 5, midY);
    ctx.fillText('-1.0', pad.left - 5, pad.top + plotH - 5);

    // Inline acoustic metadata stamp
    const metaParts = [];
    if (opts.durationSec != null) metaParts.push(Number(opts.durationSec).toFixed(2) + 's');
    if (opts.peakDb != null) metaParts.push('PEAK ' + Number(opts.peakDb).toFixed(1) + ' dB');
    if (metaParts.length > 0) {
      ctx.fillStyle = COLORS.muted;
      ctx.textAlign = 'right';
      ctx.textBaseline = 'top';
      ctx.fillText(metaParts.join(' • '), pad.left + plotW - 6, pad.top + 5);
    }
  }

  /**
   * 3. Multi-Window Consensus Asymmetric Veto Chart + Anomaly Risk Heatbar
   * Renders forensics.windows ([{index, start_sec, end_sec, score, risk_weight}])
   * with θ=0.0, +6.0 Rescue, -12.0 Veto dashed lines.
   */
  function renderWindowVetoChart(canvas, windows, pooling, threshold, options) {
    const opts = options || {};
    const compact = Boolean(opts.compact);
    const setup = setupHiDPICanvas(canvas, compact ? 150 : 230);
    if (!setup) return;
    const { ctx, w, h } = setup;

    if (!Array.isArray(windows) || windows.length === 0) {
      drawEmptyState(ctx, w, h, 'CHƯA CÓ ĐIỂM ĐA CỬA SỔ');
      return;
    }

    const theta = Number.isFinite(Number(threshold)) ? Number(threshold) : 0.0;
    const scores = windows.map(function (win) { return Number(win.score) || 0; });
    const absMax = Math.max(
      24,
      Math.ceil(
        Math.max.apply(null, scores.map(function (s) { return Math.abs(s); }).concat([16])) / 10
      ) * 10
    );
    const yMin = -absMax;
    const yMax = absMax;

    const heatbarH = compact ? 14 : 20;
    const pad = compact
      ? { top: 18, right: 12, bottom: 26 + heatbarH, left: 40 }
      : { top: 24, right: 16, bottom: 36 + heatbarH, left: 48 };
    const plotW = Math.max(60, w - pad.left - pad.right);
    const plotH = Math.max(50, h - pad.top - pad.bottom);

    function scoreToY(val) {
      const clamped = Math.max(yMin, Math.min(yMax, val));
      const frac = (clamped - yMin) / (yMax - yMin);
      return pad.top + plotH * (1 - frac);
    }

    // Background shaded veto zone (< -12) and rescue zone (>= +6)
    const yVeto = scoreToY(-12.0);
    const yRescue = scoreToY(6.0);
    const yTheta = scoreToY(theta);

    ctx.fillStyle = 'rgba(223, 0, 66, 0.08)';
    ctx.fillRect(pad.left, yVeto, plotW, pad.top + plotH - yVeto);

    ctx.fillStyle = 'rgba(109, 255, 186, 0.05)';
    ctx.fillRect(pad.left, pad.top, plotW, yRescue - pad.top);

    // Horizontal threshold lines
    const refs = [
      { val: 6.0, color: COLORS.emerald, dash: [4, 4], label: '+6 RESCUE' },
      { val: theta, color: 'rgba(229, 225, 229, 0.65)', dash: [], label: 'θ=' + theta.toFixed(1) },
      { val: -12.0, color: COLORS.crimson, dash: [4, 4], label: '-12 VETO' },
    ];

    refs.forEach(function (r) {
      const y = Math.round(scoreToY(r.val)) + 0.5;
      ctx.save();
      ctx.strokeStyle = r.color;
      ctx.lineWidth = r.dash.length === 0 ? 1.2 : 1;
      ctx.setLineDash(r.dash);
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + plotW, y);
      ctx.stroke();
      ctx.setLineDash([]);
      if (!compact) {
        ctx.fillStyle = r.color;
        ctx.font = '600 9px "JetBrains Mono", monospace';
        ctx.textAlign = 'right';
        ctx.textBaseline = r.val >= 0 ? 'bottom' : 'top';
        ctx.fillText(r.label, pad.left + plotW - 4, r.val >= 0 ? y - 2 : y + 3);
      }
      ctx.restore();
    });

    // Bars per sliding window
    const count = windows.length;
    const slotW = plotW / count;
    const barW = Math.min(compact ? 36 : 56, slotW * 0.56);

    windows.forEach(function (win, idx) {
      const s = Number(win.score) || 0;
      const risk = Math.max(0, Math.min(1, Number(win.risk_weight) || 0));
      const cx = pad.left + slotW * idx + slotW / 2;
      const x = cx - barW / 2;
      const yVal = scoreToY(s);
      const topY = Math.min(yVal, yTheta);
      const barH = Math.max(2, Math.abs(yVal - yTheta));

      let fill = COLORS.emerald;
      if (s < -12.0) fill = COLORS.crimson;
      else if (s < theta) fill = '#f43f5e';
      else if (s < 6.0) fill = COLORS.amber;
      else fill = COLORS.emeraldStrong;

      ctx.fillStyle = fill;
      ctx.fillRect(x, topY, barW, barH);

      // Subtle top/bottom crisp highlight edge
      ctx.fillStyle = 'rgba(255,255,255,0.22)';
      ctx.fillRect(x, s >= theta ? topY : topY + barH - 2, barW, 2);

      // Score value label
      ctx.fillStyle = COLORS.text;
      ctx.font = '700 ' + (compact ? 9 : 10) + 'px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = s >= theta ? 'bottom' : 'top';
      const labelY = s >= theta ? Math.max(pad.top + 11, topY - 4) : Math.min(pad.top + plotH - 12, topY + barH + 4);
      ctx.fillText((s >= 0 ? '+' : '') + s.toFixed(1), cx, labelY);

      // Window index + time label
      ctx.fillStyle = COLORS.muted;
      ctx.font = (compact ? 9 : 10) + 'px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      const wLabel = 'W' + (win.index != null ? win.index : idx + 1);
      ctx.fillText(wLabel, cx, pad.top + plotH + 5);

      // Anomaly Risk Heatbar cell below each window
      const hbY = pad.top + plotH + (compact ? 17 : 22);
      const hbW = Math.max(barW, slotW - 8);
      const hbX = cx - hbW / 2;
      const rCol = Math.round(16 + risk * 207);
      const gCol = Math.round(205 * (1 - risk) + 18 * risk);
      const bCol = Math.round(138 * (1 - risk) + 66 * risk);
      ctx.fillStyle = 'rgba(' + rCol + ',' + gCol + ',' + bCol + ', 0.28)';
      ctx.fillRect(hbX, hbY, hbW, heatbarH - 4);
      ctx.fillStyle = 'rgb(' + rCol + ',' + gCol + ',' + bCol + ')';
      ctx.fillRect(hbX, hbY, hbW * risk, heatbarH - 4);

      if (!compact) {
        ctx.fillStyle = COLORS.text;
        ctx.font = '600 9px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('RISK ' + Math.round(risk * 100) + '%', cx, hbY + (heatbarH - 4) / 2 + 0.5);
      }
    });

    // Frame & Y-axis ticks
    ctx.strokeStyle = COLORS.gridStrong;
    ctx.strokeRect(pad.left + 0.5, pad.top + 0.5, plotW - 1, plotH - 1);

    ctx.fillStyle = COLORS.muted;
    ctx.font = '9px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    [yMax, 6, 0, -12, yMin].forEach(function (tick) {
      ctx.fillText((tick > 0 ? '+' : '') + tick, pad.left - 6, scoreToY(tick));
    });

    // Pooling branch pill at top-left inside plot
    if (pooling && pooling.branch && !compact) {
      const tag = pooling.veto_triggered
        ? 'VETO TRIGGERED // ' + pooling.branch.toUpperCase()
        : 'POOLING // ' + pooling.branch.toUpperCase();
      ctx.font = '600 9px "JetBrains Mono", monospace';
      const tw = ctx.measureText(tag).width;
      ctx.fillStyle = 'rgba(14, 14, 16, 0.85)';
      ctx.fillRect(pad.left + 6, pad.top + 5, tw + 10, 14);
      ctx.fillStyle = pooling.veto_triggered ? COLORS.crimsonSoft : COLORS.emerald;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      ctx.fillText(tag, pad.left + 11, pad.top + 7);
    }
  }

  /**
   * 4. Platt Calibration Curve (T=16.0) & 3-Band Frequency Energy Bars
   */
  function renderPlattAndBands(canvas, rawScore, threshold, plattCurve, bandEnergy, isBorderline) {
    const setup = setupHiDPICanvas(canvas, 230);
    if (!setup) return;
    const { ctx, w, h } = setup;

    const theta = Number.isFinite(Number(threshold)) ? Number(threshold) : 0.0;
    const score = Number.isFinite(Number(rawScore)) ? Number(rawScore) : 0.0;
    const scaleK = (plattCurve && Number(plattCurve.scale_k)) || 0.0625;
    const tempT = (plattCurve && Number(plattCurve.temperature)) || 16.0;
    const borderMargin = (plattCurve && Number(plattCurve.borderline_margin)) || 8.0;

    const splitHorizontal = w >= 480;
    const curveBox = splitHorizontal
      ? { x: 42, y: 24, w: Math.floor(w * 0.57) - 52, h: h - 52 }
      : { x: 40, y: 20, w: w - 54, h: Math.floor(h * 0.48) - 24 };
    const bandBox = splitHorizontal
      ? { x: Math.floor(w * 0.57) + 14, y: 24, w: w - Math.floor(w * 0.57) - 26, h: h - 52 }
      : { x: 40, y: Math.floor(h * 0.54) + 12, w: w - 54, h: Math.floor(h * 0.44) - 18 };

    // --- PART A: PLATT CALIBRATION LOGISTIC CURVE ---
    const sMin = -45;
    const sMax = 45;
    function sToX(s) {
      const clamped = Math.max(sMin, Math.min(sMax, s));
      return curveBox.x + ((clamped - sMin) / (sMax - sMin)) * curveBox.w;
    }
    function pToY(p) {
      return curveBox.y + curveBox.h * (1 - Math.max(0, Math.min(1, p)));
    }

    // Borderline shaded zone [-8, +8] around threshold
    const bx0 = sToX(theta - borderMargin);
    const bx1 = sToX(theta + borderMargin);
    ctx.fillStyle = 'rgba(255, 189, 93, 0.13)';
    ctx.fillRect(bx0, curveBox.y, bx1 - bx0, curveBox.h);

    // Subtle probability gridlines (25%, 50%, 75%)
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 1;
    [0.25, 0.5, 0.75].forEach(function (p) {
      const y = Math.round(pToY(p)) + 0.5;
      ctx.beginPath();
      ctx.moveTo(curveBox.x, y);
      ctx.lineTo(curveBox.x + curveBox.w, y);
      ctx.stroke();
    });

    // Vertical threshold θ line
    const xTheta = Math.round(sToX(theta)) + 0.5;
    ctx.save();
    ctx.strokeStyle = 'rgba(229, 225, 229, 0.45)';
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(xTheta, curveBox.y);
    ctx.lineTo(xTheta, curveBox.y + curveBox.h);
    ctx.stroke();
    ctx.restore();

    // Draw smooth logistic curve colored crimson (< theta) -> emerald (>= theta)
    const steps = 120;
    for (let i = 0; i < steps; i++) {
      const s0 = sMin + (i / steps) * (sMax - sMin);
      const s1 = sMin + ((i + 1) / steps) * (sMax - sMin);
      const p0 = 1 / (1 + Math.exp(-scaleK * (s0 - theta)));
      const p1 = 1 / (1 + Math.exp(-scaleK * (s1 - theta)));
      ctx.strokeStyle = Math.abs(s0 - theta) <= borderMargin
        ? COLORS.amber
        : (s0 >= theta ? COLORS.emerald : COLORS.crimson);
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(sToX(s0), pToY(p0));
      ctx.lineTo(sToX(s1), pToY(p1));
      ctx.stroke();
    }

    // Plot exact current score dot & reticle
    const probBona = 1 / (1 + Math.exp(-scaleK * (score - theta)));
    const dotX = sToX(score);
    const dotY = pToY(probBona);
    const dotColor = isBorderline ? COLORS.amber : (score >= theta ? COLORS.emerald : COLORS.crimson);

    ctx.save();
    ctx.strokeStyle = dotColor;
    ctx.globalAlpha = 0.45;
    ctx.setLineDash([2, 3]);
    ctx.beginPath();
    ctx.moveTo(dotX, curveBox.y + curveBox.h);
    ctx.lineTo(dotX, dotY);
    ctx.lineTo(curveBox.x, dotY);
    ctx.stroke();
    ctx.restore();

    ctx.beginPath();
    ctx.arc(dotX, dotY, 7, 0, Math.PI * 2);
    ctx.fillStyle = dotColor;
    ctx.globalAlpha = 0.25;
    ctx.fill();
    ctx.globalAlpha = 1;

    ctx.beginPath();
    ctx.arc(dotX, dotY, 4, 0, Math.PI * 2);
    ctx.fillStyle = dotColor;
    ctx.fill();
    ctx.strokeStyle = '#0e0e10';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Frame & labels for Platt curve
    ctx.strokeStyle = COLORS.gridStrong;
    ctx.lineWidth = 1;
    ctx.strokeRect(curveBox.x + 0.5, curveBox.y + 0.5, curveBox.w - 1, curveBox.h - 1);

    ctx.fillStyle = COLORS.muted;
    ctx.font = '600 9px "JetBrains Mono", monospace';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.fillText('PLATT CURVE (T=' + tempT.toFixed(1) + ')', curveBox.x, curveBox.y - 6);

    ctx.fillStyle = COLORS.amber;
    ctx.textAlign = 'right';
    ctx.fillText('ZONE [-' + borderMargin + ', +' + borderMargin + ']', curveBox.x + curveBox.w, curveBox.y - 6);

    ctx.fillStyle = COLORS.muted;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText('100%', curveBox.x - 5, curveBox.y + 4);
    ctx.fillText('50%', curveBox.x - 5, pToY(0.5));
    ctx.fillText('0%', curveBox.x - 5, curveBox.y + curveBox.h - 4);

    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    [-40, -8, 0, 8, 40].forEach(function (tick) {
      ctx.fillText(tick > 0 ? '+' + tick : String(tick), sToX(tick), curveBox.y + curveBox.h + 6);
    });

    // Current dot tooltip inside curve box
    const readout = 's=' + (score >= 0 ? '+' : '') + score.toFixed(2) + ' → ' + (probBona * 100).toFixed(1) + '%';
    ctx.font = '700 9px "JetBrains Mono", monospace';
    const rW = ctx.measureText(readout).width;
    const tipX = Math.max(curveBox.x + 4, Math.min(curveBox.x + curveBox.w - rW - 12, dotX - rW / 2));
    const tipY = dotY > curveBox.y + 28 ? dotY - 22 : dotY + 10;
    ctx.fillStyle = 'rgba(14, 14, 16, 0.88)';
    ctx.fillRect(tipX - 3, tipY - 2, rW + 8, 14);
    ctx.fillStyle = dotColor;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(readout, tipX + 1, tipY);

    // --- PART B: 3-BAND FREQUENCY ENERGY BARS ---
    const be = bandEnergy || {};
    const bands = [
      { label: '< 300 Hz (F0 / Trầm)', pct: Number(be.low_0_300hz) || 0, color: '#6dffba' },
      { label: '300 – 3.4 kHz (Thoại)', pct: Number(be.mid_300_3400hz) || 0, color: '#ffbd5d' },
      { label: '3.4 – 8.0 kHz (HF / AI)', pct: Number(be.high_3400_8000hz) || 0, color: '#df0042' },
    ];

    ctx.fillStyle = COLORS.muted;
    ctx.font = '600 9px "JetBrains Mono", monospace';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.fillText('NĂNG LƯỢNG 3 DẢI TẦN (%)', bandBox.x, bandBox.y - 6);

    const rowGap = bandBox.h / bands.length;
    bands.forEach(function (b, idx) {
      const yBase = bandBox.y + idx * rowGap + 4;
      const pctClamped = Math.max(0, Math.min(100, b.pct));

      ctx.fillStyle = COLORS.text;
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      ctx.fillText(b.label, bandBox.x, yBase);

      ctx.fillStyle = b.color;
      ctx.font = '700 10px "JetBrains Mono", monospace';
      ctx.textAlign = 'right';
      ctx.fillText(pctClamped.toFixed(1) + '%', bandBox.x + bandBox.w, yBase);

      const trackY = yBase + 16;
      const trackH = Math.max(8, Math.min(14, rowGap - 26));
      ctx.fillStyle = 'rgba(186, 203, 190, 0.1)';
      ctx.fillRect(bandBox.x, trackY, bandBox.w, trackH);

      ctx.fillStyle = b.color;
      ctx.fillRect(bandBox.x, trackY, (bandBox.w * pctClamped) / 100, trackH);
    });
  }

  window.VieTrueVoiceCharts = {
    renderMelSpectrogram: renderMelSpectrogram,
    renderWaveform: renderWaveform,
    renderWindowVetoChart: renderWindowVetoChart,
    renderPlattAndBands: renderPlattAndBands,
  };
})();
