/**
 * ViTrueVoice v0.9.4 — Main Forensic Editorial & Studio Application Controller
 * Connects:
 *   - Cinematic Preloader (00 -> 100 wipe)
 *   - Lenis Smooth Scroll + GSAP ScrollTrigger (Clip-Path Cinema Reveal + Sticky Cards)
 *   - Custom Desktop Cursor (#vtv-cursor with Vietnamese data-cursor pills)
 *   - WebGL 3D Obsidian Orb state color, audio reactivity & ON/OFF toggle
 *   - Feature 1 (Tab 01): POST /api/v1/predict (Upload, Live Mic, 5 Real Samples + 4 HD Charts)
 *   - Feature 2 (Tab 02): POST /api/v1/clone-and-audit (Upload/Mic/Preset + OmniVoice CFM Comparative Matrix)
 */
(function () {
  'use strict';

  const ENDPOINT_PREDICT = '/api/v1/predict';
  const ENDPOINT_CLONE = '/api/v1/clone-and-audit';
  const ENDPOINT_SAMPLES = '/api/v1/samples';
  const ENDPOINT_HEALTH = '/health';

  const COLORS = {
    bonafide: '#00e599',
    spoof: '#df0042',
    borderline: '#ffbd5d',
    idle: '#00e599',
  };

  const DEFAULT_SAMPLES = [
    {
      filename: 'sample_bonafide_spk0004.wav',
      url: '/static/samples/sample_bonafide_spk0004.wav',
      shortLabel: '01 // GIỌNG THẬT (SPK_0004)',
      category: 'BONA_FIDE',
      codec: '16KHZ WAV',
    },
    {
      filename: 'sample_spoof_f5tts.wav',
      url: '/static/samples/sample_spoof_f5tts.wav',
      shortLabel: '02 // F5-TTS (GIẢ)',
      category: 'SPOOF',
      codec: 'F5-TTS',
    },
    {
      filename: 'sample_spoof_voicestudio_cfm.wav',
      url: '/static/samples/sample_spoof_voicestudio_cfm.wav',
      shortLabel: '03 // OMNIVOICE CFM (GIẢ)',
      category: 'SPOOF',
      codec: 'OMNIVOICE CFM',
    },
    {
      filename: 'sample_spoof_zalo_opus.wav',
      url: '/static/samples/sample_spoof_zalo_opus.wav',
      shortLabel: '04 // ZALO OPUS 24K (GIẢ)',
      category: 'SPOOF',
      codec: 'OPUS 24KBPS',
    },
    {
      filename: 'sample_telephony_amrnb.wav',
      url: '/static/samples/sample_telephony_amrnb.wav',
      shortLabel: '05 // AMR-NB 8KHZ (GIẢ)',
      category: 'SPOOF',
      codec: 'AMR-NB 8KHZ',
    },
  ];

  // Application State
  const state = {
    lenis: null,
    overlayOpen: false,
    activeTab: 'predict', // 'predict' | 'clone'
    lastPredictPayload: null,
    lastPredictObjectUrl: null,
    lastClonePayload: null,
    cloneRefFile: null,
    cloneRefObjectUrl: null,
    cloneElapsedTimer: null,
    cloneStartedAt: 0,
    predictRecorder: null,
    cloneRecorder: null,
    previewAudio: null,
    previewBtn: null,
    previewAudioCtx: null,
    previewAnalyser: null,
    previewRaf: null,
    previewBuf: null,
    isBusyPredict: false,
    isBusyClone: false,
  };

  function $(id) {
    return document.getElementById(id);
  }

  function setOrbColor(hex) {
    if (!window.vieTrueVoice3D) return;
    if (typeof window.vieTrueVoice3D.setStateColor === 'function') {
      window.vieTrueVoice3D.setStateColor(hex);
    } else if (typeof window.vieTrueVoice3D.setRimColor === 'function') {
      window.vieTrueVoice3D.setRimColor(hex);
    }
  }

  function setOrbScan(val) {
    if (window.vieTrueVoice3D && typeof window.vieTrueVoice3D.setScanIntensity === 'function') {
      window.vieTrueVoice3D.setScanIntensity(val);
    }
  }

  function setOrbAudio(val) {
    if (window.vieTrueVoice3D && typeof window.vieTrueVoice3D.setAudioLevel === 'function') {
      window.vieTrueVoice3D.setAudioLevel(val);
    }
  }

  // =========================================================================
  // 1. Text Scramble Effect (Forensic Verdict Headline)
  // =========================================================================
  const SCRAMBLE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/_-#%§';

  function scrambleText(el, finalText, durationMs) {
    if (!el) return;
    const totalFrames = Math.max(12, Math.round((durationMs || 520) / 28));
    let frame = 0;
    if (el._vtvScrambleTimer) {
      window.clearInterval(el._vtvScrambleTimer);
    }
    el._vtvScrambleTimer = window.setInterval(function () {
      frame += 1;
      const progress = frame / totalFrames;
      const locked = Math.floor(progress * finalText.length);
      let out = '';
      for (let i = 0; i < finalText.length; i++) {
        if (i < locked || finalText[i] === ' ' || finalText[i] === '_') {
          out += finalText[i];
        } else {
          out += SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
        }
      }
      el.textContent = out;
      if (frame >= totalFrames) {
        window.clearInterval(el._vtvScrambleTimer);
        el._vtvScrambleTimer = null;
        el.textContent = finalText;
      }
    }, 28);
  }

  // =========================================================================
  // 2. Cinematic Preloader (00 -> 100 Wipe Reveal)
  // =========================================================================
  function runPreloader() {
    const preloader = $('vtv-preloader');
    const countEl = $('vtv-preloader-count');
    const barEl = $('vtv-preloader-bar');
    if (!preloader) return;

    const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion || typeof window.gsap === 'undefined') {
      if (countEl) countEl.textContent = '100';
      if (barEl) barEl.style.width = '100%';
      preloader.classList.add('vtv-preloader-done');
      return;
    }

    const counter = { val: 0 };
    const tl = window.gsap.timeline({
      onComplete: function () {
        preloader.classList.add('vtv-preloader-done');
      },
    });

    tl.to(counter, {
      val: 100,
      duration: 0.95,
      ease: 'power2.inOut',
      onUpdate: function () {
        const v = Math.round(counter.val);
        if (countEl) countEl.textContent = String(v).padStart(2, '0');
        if (barEl) barEl.style.width = v + '%';
      },
    })
      .to(preloader, {
        clipPath: 'inset(0% 0% 100% 0%)',
        duration: 0.65,
        ease: 'power4.inOut',
        delay: 0.08,
      })
      .from(
        '.vtv-hero-reveal',
        {
          y: 26,
          opacity: 0,
          duration: 0.7,
          stagger: 0.08,
          ease: 'power3.out',
          clearProps: 'transform,opacity',
        },
        '-=0.32'
      );
  }

  // =========================================================================
  // 3. Lenis Smooth Scroll & GSAP ScrollTrigger (Cinema Reveal + Sticky Cards)
  // =========================================================================
  function initMotionAndScroll() {
    const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!reducedMotion && typeof window.Lenis !== 'undefined') {
      state.lenis = new window.Lenis({
        duration: 1.08,
        easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); },
        orientation: 'vertical',
        smoothWheel: true,
        // Never intercept wheel/touch events while Forensic Studio Overlay is open
        prevent: function (node) {
          if (state.overlayOpen) return true;
          return Boolean(
            node &&
            typeof node.closest === 'function' &&
            node.closest('#forensic-overlay, [data-lenis-prevent]')
          );
        },
      });

      if (typeof window.gsap !== 'undefined' && typeof window.ScrollTrigger !== 'undefined') {
        window.gsap.registerPlugin(window.ScrollTrigger);
        state.lenis.on('scroll', window.ScrollTrigger.update);
        window.gsap.ticker.add(function (time) {
          if (state.lenis) state.lenis.raf(time * 1000);
        });
        window.gsap.ticker.lagSmoothing(0);
      } else {
        function rafLoop(time) {
          if (state.lenis) state.lenis.raf(time);
          window.requestAnimationFrame(rafLoop);
        }
        window.requestAnimationFrame(rafLoop);
      }
    }

    if (reducedMotion || typeof window.gsap === 'undefined' || typeof window.ScrollTrigger === 'undefined') {
      const cf = $('cinema-frame');
      const ci = $('cinema-inner');
      const ch = $('cinema-aperture-hint');
      if (cf) {
        cf.style.clipPath = 'inset(0% 0% 0% 0% round 0px)';
        cf.style.transform = 'none';
      }
      if (ci) ci.style.opacity = '1';
      if (ch) ch.style.display = 'none';
      return;
    }

    window.gsap.registerPlugin(window.ScrollTrigger);
    const mm = window.gsap.matchMedia();

    // Desktop Clip-Path Cinema Reveal: starts tightly shrunk over bold running marquee, expands on scroll
    mm.add('(min-width: 769px)', function () {
      const cinemaSection = $('cinema-section');
      const cinemaFrame = $('cinema-frame');
      const cinemaInner = $('cinema-inner');
      const cinemaHint = $('cinema-aperture-hint');
      const marqueeBand = cinemaSection ? cinemaSection.querySelector('.vtv-marquee-band') : null;

      if (cinemaSection && cinemaFrame) {
        const tl = window.gsap.timeline({
          scrollTrigger: {
            trigger: cinemaSection,
            start: 'top top',
            end: '+=165%',
            scrub: 0.75,
            pin: true,
            anticipatePin: 1,
          },
        });

        // Hold tiny shrunk aperture briefly (0 -> 0.14) so running marquee is clearly visible first
        tl.to({}, { duration: 0.14 })
          // Fade out centered aperture hint as expansion starts
          .to(
            cinemaHint,
            { opacity: 0, duration: 0.16, ease: 'power1.out' },
            0.12
          )
          // Expand clipped frame smoothly from tight center portal to full container
          .fromTo(
            cinemaFrame,
            { clipPath: 'inset(42% 39% 42% 39% round 12px)', scale: 0.72 },
            {
              clipPath: 'inset(0% 0% 0% 0% round 0px)',
              scale: 1,
              duration: 0.68,
              ease: 'power2.inOut',
            },
            0.14
          )
          // Reveal inner comparison content smoothly as frame opens up
          .fromTo(
            cinemaInner,
            { opacity: 0, y: 18 },
            { opacity: 1, y: 0, duration: 0.42, ease: 'power2.out' },
            0.34
          );

        if (marqueeBand) {
          tl.fromTo(
            marqueeBand,
            { opacity: 1 },
            { opacity: 0.22, duration: 0.62, ease: 'none' },
            0.22
          );
        }

        // Hold fully open briefly (0.82 -> 1.0) so reader views full metrics cleanly before unpinning
        tl.to({}, { duration: 0.18 });
      }

      // Subtle depth compression for Sticky Stacking Cards
      const cards = document.querySelectorAll('.vtv-stack-card');
      cards.forEach(function (card, idx) {
        if (idx === cards.length - 1) return;
        const nextCard = cards[idx + 1];
        window.gsap.to(card, {
          scale: 0.96,
          opacity: 0.72,
          ease: 'none',
          scrollTrigger: {
            trigger: nextCard,
            start: 'top 80%',
            end: 'top 20%',
            scrub: true,
          },
        });
      });
    });
  }

  // =========================================================================
  // 4. Custom Desktop Cursor (#vtv-cursor)
  // =========================================================================
  function initCustomCursor() {
    const cursorEl = $('vtv-cursor');
    const labelEl = $('vtv-cursor-label');
    if (!cursorEl || !labelEl) return;

    const isFinePointer = window.matchMedia && window.matchMedia('(pointer: fine) and (min-width: 1024px)').matches;
    if (!isFinePointer) return;

    let mouseX = -100;
    let mouseY = -100;
    let curX = -100;
    let curY = -100;

    window.addEventListener(
      'pointermove',
      function (ev) {
        mouseX = ev.clientX;
        mouseY = ev.clientY;
      },
      { passive: true }
    );

    function tick() {
      curX += (mouseX - curX) * 0.22;
      curY += (mouseY - curY) * 0.22;
      cursorEl.style.transform = 'translate3d(' + curX.toFixed(1) + 'px, ' + curY.toFixed(1) + 'px, 0) translate(-50%, -50%)';
      window.requestAnimationFrame(tick);
    }
    window.requestAnimationFrame(tick);

    document.addEventListener('mouseover', function (ev) {
      const target = ev.target && ev.target.closest ? ev.target.closest('[data-cursor]') : null;
      if (target) {
        const text = target.getAttribute('data-cursor') || '';
        const tone = target.getAttribute('data-cursor-tone') || '';
        labelEl.textContent = text;
        cursorEl.classList.add('is-labeled');
        cursorEl.classList.toggle('is-danger', tone === 'danger');
        cursorEl.classList.toggle('is-amber', tone === 'amber');
      } else {
        cursorEl.classList.remove('is-labeled', 'is-danger', 'is-amber');
      }
    });
  }

  // =========================================================================
  // 5. Global Sample Audio Previewer + Live 3D Orb Reactivity
  // =========================================================================
  function stopPreviewAudio() {
    if (state.previewRaf) {
      window.cancelAnimationFrame(state.previewRaf);
      state.previewRaf = null;
    }
    if (state.previewAudio) {
      try {
        state.previewAudio.pause();
        state.previewAudio.currentTime = 0;
      } catch (_e) { /* ignore */ }
    }
    if (state.previewBtn) {
      state.previewBtn.classList.remove('vtv-btn-playing');
      const orig = state.previewBtn.getAttribute('data-orig-label');
      if (orig) state.previewBtn.textContent = orig;
      state.previewBtn = null;
    }
    setOrbAudio(0);
  }

  function togglePlaySample(url, buttonEl, toneHex) {
    if (state.previewBtn === buttonEl && state.previewAudio && !state.previewAudio.paused) {
      stopPreviewAudio();
      return;
    }

    stopPreviewAudio();

    if (!state.previewAudio) {
      state.previewAudio = new Audio();
      state.previewAudio.crossOrigin = 'anonymous';
      state.previewAudio.addEventListener('ended', function () {
        stopPreviewAudio();
      });
      state.previewAudio.addEventListener('error', function () {
        stopPreviewAudio();
      });
    }

    if (buttonEl) {
      if (!buttonEl.getAttribute('data-orig-label')) {
        buttonEl.setAttribute('data-orig-label', buttonEl.textContent);
      }
      buttonEl.textContent = '■ DỪNG PHÁT';
      buttonEl.classList.add('vtv-btn-playing');
      state.previewBtn = buttonEl;
    }

    if (toneHex) {
      setOrbColor(toneHex);
    }

    // Attach Web Audio Analyser once to pulse the 3D WebGL orb with real playback amplitude
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx && !state.previewAudioCtx) {
        state.previewAudioCtx = new AudioCtx();
        const src = state.previewAudioCtx.createMediaElementSource(state.previewAudio);
        state.previewAnalyser = state.previewAudioCtx.createAnalyser();
        state.previewAnalyser.fftSize = 256;
        state.previewBuf = new Uint8Array(state.previewAnalyser.frequencyBinCount);
        src.connect(state.previewAnalyser);
        state.previewAnalyser.connect(state.previewAudioCtx.destination);
      }
      if (state.previewAudioCtx && state.previewAudioCtx.state === 'suspended') {
        state.previewAudioCtx.resume();
      }
    } catch (_err) {
      // Fallback gracefully if Web Audio graph is restricted
    }

    state.previewAudio.src = url;
    state.previewAudio.play().catch(function () {
      stopPreviewAudio();
    });

    function pumpPlayback() {
      if (!state.previewAudio || state.previewAudio.paused || state.previewAudio.ended) {
        state.previewRaf = null;
        return;
      }
      if (state.previewAnalyser && state.previewBuf) {
        state.previewAnalyser.getByteFrequencyData(state.previewBuf);
        let sum = 0;
        for (let i = 0; i < state.previewBuf.length; i++) sum += state.previewBuf[i];
        const avg = sum / (state.previewBuf.length * 255);
        setOrbAudio(Math.min(1.2, avg * 2.4));
      } else {
        setOrbAudio(0.35 + Math.sin(performance.now() * 0.015) * 0.2);
      }
      state.previewRaf = window.requestAnimationFrame(pumpPlayback);
    }
    state.previewRaf = window.requestAnimationFrame(pumpPlayback);
  }

  // =========================================================================
  // 6. Forensic Studio Overlay & Tab Switcher
  // =========================================================================
  function openOverlay(tabName) {
    const overlay = $('forensic-overlay');
    if (!overlay) return;

    stopPreviewAudio();
    state.overlayOpen = true;
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    document.documentElement.classList.add('vtv-overlay-open');
    document.body.classList.add('vtv-overlay-open');

    // Halt residual background momentum without invoking lenis.stop() (which swallows overlay wheel events)
    if (state.lenis && typeof state.lenis.scrollTo === 'function') {
      state.lenis.scrollTo(window.scrollY, { immediate: true, force: true });
    }

    switchTab(tabName || state.activeTab || 'predict');
    overlay.scrollTop = 0;
  }

  function closeOverlay() {
    const overlay = $('forensic-overlay');
    if (!overlay) return;

    if (state.predictRecorder && state.predictRecorder.isRecording) {
      state.predictRecorder.cancel();
    }
    if (state.cloneRecorder && state.cloneRecorder.isRecording) {
      state.cloneRecorder.cancel();
    }

    state.overlayOpen = false;
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    document.documentElement.classList.remove('vtv-overlay-open');
    document.body.classList.remove('vtv-overlay-open');

    if (state.lenis && typeof state.lenis.resize === 'function') {
      state.lenis.resize();
    }
  }

  function switchTab(tabName) {
    const target = tabName === 'clone' ? 'clone' : 'predict';
    state.activeTab = target;

    const btnPredict = $('tab-btn-predict');
    const btnClone = $('tab-btn-clone');
    const panelPredict = $('tab-panel-predict');
    const panelClone = $('tab-panel-clone');

    if (btnPredict) {
      btnPredict.classList.toggle('is-active', target === 'predict');
      btnPredict.setAttribute('aria-selected', String(target === 'predict'));
    }
    if (btnClone) {
      btnClone.classList.toggle('is-active-crimson', target === 'clone');
      btnClone.setAttribute('aria-selected', String(target === 'clone'));
    }
    if (panelPredict) panelPredict.classList.toggle('hidden', target !== 'predict');
    if (panelClone) panelClone.classList.toggle('hidden', target !== 'clone');

    // Re-render charts on tab switch so hidden canvases size cleanly to visible width
    window.requestAnimationFrame(function () {
      if (target === 'predict' && state.lastPredictPayload) {
        renderPredictCharts(state.lastPredictPayload);
      } else if (target === 'clone' && state.lastClonePayload) {
        renderCloneCharts(state.lastClonePayload);
      }
    });
  }

  // =========================================================================
  // 7. Utility Helpers (Probabilities, Formatting, Fetch Samples)
  // =========================================================================
  function computeProbabilities(item) {
    const rawScore = Number(item.raw_score) || 0;
    const threshold = Number(item.threshold) || 0;
    const pc = item.forensics && item.forensics.platt_curve ? item.forensics.platt_curve : null;

    let probBona = item.prob_bona_pct != null
      ? Number(item.prob_bona_pct)
      : (pc && pc.prob_bona_pct != null ? Number(pc.prob_bona_pct) : null);
    let probSpoof = item.prob_spoof_pct != null
      ? Number(item.prob_spoof_pct)
      : (pc && pc.prob_spoof_pct != null ? Number(pc.prob_spoof_pct) : null);

    if (probBona === null || !Number.isFinite(probBona)) {
      const p = 1 / (1 + Math.exp(-0.0625 * (rawScore - threshold)));
      probBona = Math.max(0.1, Math.min(99.9, p * 100));
    }
    if (probSpoof === null || !Number.isFinite(probSpoof)) {
      probSpoof = Math.max(0.1, Math.min(99.9, 100 - probBona));
    }
    return {
      bonaPct: Number(probBona.toFixed(1)),
      spoofPct: Number(probSpoof.toFixed(1)),
    };
  }

  function formatLatency(sec) {
    const s = Number(sec) || 0;
    if (s < 1) return Math.round(s * 1000) + ' ms';
    return s.toFixed(2) + ' s';
  }

  function shortHash(sha) {
    if (!sha || typeof sha !== 'string') return '—';
    return sha.length > 16 ? sha.slice(0, 10) + '…' + sha.slice(-6) : sha;
  }

  async function fetchSampleAsFile(url, fallbackName) {
    const resp = await fetch(url);
    if (!resp.ok) {
      throw new Error('Không tải được tệp mẫu (' + resp.status + '): ' + url);
    }
    const blob = await resp.blob();
    const fname = fallbackName || url.split('/').pop() || 'sample.wav';
    return new File([blob], fname, { type: blob.type || 'audio/wav' });
  }

  // =========================================================================
  // 8. FEATURE 1 (TAB 01): REAL POST /api/v1/predict + 4 HD CHARTS
  // =========================================================================
  function showPredictError(msg) {
    const box = $('predict-error');
    if (!box) return;
    if (!msg) {
      box.classList.add('hidden');
      box.textContent = '';
      return;
    }
    box.textContent = msg;
    box.classList.remove('hidden');
  }

  function setPredictLoading(isLoading, labelText) {
    state.isBusyPredict = isLoading;
    const loader = $('predict-loading');
    const txt = $('predict-loading-text');
    if (loader) loader.classList.toggle('hidden', !isLoading);
    if (txt && labelText) txt.textContent = labelText;
    setOrbScan(isLoading ? 1.0 : 0.0);
  }

  function renderPredictCharts(data) {
    if (!data || !window.ViTrueVoiceCharts) return;
    const f = data.forensics || {};
    const verdict = data.prediction || 'SPOOF';
    const isBorderline = Boolean(data.is_borderline);

    window.ViTrueVoiceCharts.renderMelSpectrogram(
      $('chart-predict-mel'),
      f.mel_spectrogram,
      { durationSec: f.duration_sec, compact: false }
    );
    window.ViTrueVoiceCharts.renderWaveform(
      $('chart-predict-wave'),
      f.waveform,
      {
        verdict: verdict,
        isBorderline: isBorderline,
        durationSec: f.duration_sec,
        peakDb: f.peak_db,
        compact: false,
      }
    );
    window.ViTrueVoiceCharts.renderWindowVetoChart(
      $('chart-predict-windows'),
      f.windows,
      f.pooling,
      data.threshold,
      { compact: false }
    );
    window.ViTrueVoiceCharts.renderPlattAndBands(
      $('chart-predict-platt'),
      data.raw_score,
      data.threshold,
      f.platt_curve,
      f.band_energy_pct,
      isBorderline
    );
  }

  function renderPredictResult(data, audioUrl, filename) {
    state.lastPredictPayload = data;

    const emptyHint = $('predict-empty-hint');
    const resultsWrap = $('predict-results');
    if (emptyHint) emptyHint.classList.add('hidden');
    if (resultsWrap) resultsWrap.classList.remove('hidden');

    const isBona = data.prediction === 'BONA_FIDE';
    const isBorderline = Boolean(data.is_borderline);
    const probs = computeProbabilities(data);
    const f = data.forensics || {};

    // Update WebGL 3D Orb color smoothly
    if (isBorderline) {
      setOrbColor(COLORS.borderline);
    } else if (isBona) {
      setOrbColor(COLORS.bonafide);
    } else {
      setOrbColor(COLORS.spoof);
    }

    // Verdict card styling
    const card = $('predict-verdict-card');
    if (card) {
      card.classList.remove('vtv-verdict-bonafide', 'vtv-verdict-spoof', 'vtv-verdict-borderline');
      if (isBorderline) card.classList.add('vtv-verdict-borderline');
      else if (isBona) card.classList.add('vtv-verdict-bonafide');
      else card.classList.add('vtv-verdict-spoof');
    }

    const badge = $('predict-verdict-badge');
    const title = $('predict-verdict-title');
    const sub = $('predict-verdict-sub');
    const borderBanner = $('predict-borderline-banner');

    if (badge) {
      if (isBorderline) {
        badge.textContent = 'CẢNH BÁO VÙNG RỦI RO // BORDERLINE (|s| ≤ 8.0)';
        badge.className = 'inline-flex items-center gap-2 px-3 py-1 text-[11px] font-mono-tech uppercase tracking-widest border border-[#ffbd5d]/60 bg-[#ffbd5d]/15 text-[#ffe0bc]';
      } else if (isBona) {
        badge.textContent = 'XÁC THỰC ĐẠT // GIỌNG NGƯỜI THẬT';
        badge.className = 'inline-flex items-center gap-2 px-3 py-1 text-[11px] font-mono-tech uppercase tracking-widest border border-[#6dffba]/50 bg-[#00e599]/15 text-[#6dffba]';
      } else {
        badge.textContent = 'PHÁT HIỆN GIẢ MẠO // SYNTHETIC SPOOF';
        badge.className = 'inline-flex items-center gap-2 px-3 py-1 text-[11px] font-mono-tech uppercase tracking-widest border border-[#df0042]/70 bg-[#df0042]/20 text-[#ffb3b6]';
      }
    }

    if (title) {
      title.className = 'text-4xl sm:text-5xl md:text-6xl font-black tracking-tighter font-display-vn mt-3 ' +
        (isBorderline ? 'text-[#ffbd5d]' : (isBona ? 'text-[#6dffba]' : 'text-[#df0042]'));
      scrambleText(title, isBona ? 'BONA_FIDE' : 'SPOOF', 540);
    }

    if (sub) {
      if (isBorderline) {
        sub.textContent = 'Logit nằm trong vùng tranh chấp [-8, +8] (s = ' + Number(data.raw_score).toFixed(2) + '). Khuyến nghị xác minh bổ sung hoặc đối chiếu giọng trực tiếp.';
      } else if (isBona) {
        sub.textContent = 'Tín hiệu mang cấu trúc hòa âm thanh đới hữu cơ ổn định qua Consensus Asymmetric Veto.';
      } else {
        sub.textContent = 'Phát hiện dấu vết tổng hợp AI / vocoder hoặc bất thường pha trên dải phổ kênh thoại.';
      }
    }

    if (borderBanner) {
      borderBanner.classList.toggle('hidden', !isBorderline);
    }

    // Calibrated Platt Probabilities
    const elBona = $('predict-prob-bona');
    const elSpoof = $('predict-prob-spoof');
    const elBar = $('predict-prob-bar-bona');
    if (elBona) elBona.textContent = probs.bonaPct.toFixed(1) + '%';
    if (elSpoof) elSpoof.textContent = probs.spoofPct.toFixed(1) + '%';
    if (elBar) elBar.style.width = probs.bonaPct + '%';

    // Telemetry grid
    const sVal = Number(data.raw_score) || 0;
    if ($('predict-raw-score')) {
      $('predict-raw-score').textContent = (sVal >= 0 ? '+' : '') + sVal.toFixed(2);
      $('predict-raw-score').className = 'text-xl font-bold font-mono-tech ' + (sVal >= (Number(data.threshold) || 0) ? 'text-[#6dffba]' : 'text-[#ffb3b6]');
    }
    if ($('predict-latency')) $('predict-latency').textContent = formatLatency(data.latency_sec);
    if ($('predict-sha256')) {
      $('predict-sha256').textContent = shortHash(data.audio_sha256);
      $('predict-sha256').title = data.audio_sha256 || '';
    }
    if ($('predict-bandwidth')) {
      const bw = f.bandwidth_profile || 'WIDEBAND_16KHZ';
      $('predict-bandwidth').textContent = bw === 'NARROWBAND_8KHZ' ? 'NARROWBAND 8KHZ (<3.4K)' : 'WIDEBAND 16KHZ';
    }
    if ($('predict-f0')) {
      const f0 = Number(f.estimated_f0_hz) || 0;
      $('predict-f0').textContent = f0 > 0 ? f0.toFixed(1) + ' Hz' : 'N/A';
    }
    if ($('predict-hf-ratio')) {
      const hf = f.hf_ratio_pct != null ? Number(f.hf_ratio_pct).toFixed(2) + '%' : '—';
      $('predict-hf-ratio').textContent = hf;
    }
    if ($('predict-n-windows')) {
      $('predict-n-windows').textContent = (data.n_windows || (f.windows ? f.windows.length : 1)) + ' WINDOWS';
    }

    // Playable audio element for submitted clip
    const audioEl = $('predict-audio-player');
    const fnEl = $('predict-source-filename');
    if (audioEl && audioUrl) {
      audioEl.src = audioUrl;
    }
    if (fnEl) {
      fnEl.textContent = filename || 'audio_input.wav';
    }

    // Pooling explanation
    const pooling = f.pooling || {};
    if ($('predict-pooling-branch')) {
      const br = (pooling.branch || 'max_default').toUpperCase();
      $('predict-pooling-branch').textContent = pooling.veto_triggered ? 'VETO TRIGGERED // ' + br : 'BRANCH // ' + br;
      $('predict-pooling-branch').className = 'text-[11px] font-mono-tech px-2 py-0.5 border ' +
        (pooling.veto_triggered
          ? 'border-[#df0042]/60 bg-[#df0042]/15 text-[#ffb3b6]'
          : 'border-[#6dffba]/40 bg-[#00e599]/10 text-[#6dffba]');
    }
    if ($('predict-pooling-explanation')) {
      $('predict-pooling-explanation').textContent =
        pooling.explanation || 'Tổng hợp đa cửa sổ 4.0s (hop 1.0s) bằng Consensus Asymmetric Veto.';
    }

    // Render all 4 real HD charts after container becomes visible
    window.requestAnimationFrame(function () {
      renderPredictCharts(data);
    });
  }

  async function submitPredictFile(file, existingObjectUrl) {
    if (!file || state.isBusyPredict) return;
    showPredictError('');
    setPredictLoading(true, 'ĐANG GIẢI MÃ IN-MEMORY & QUÉT ĐA CỬA SỔ SSL-AASIST v0.9.4...');

    if (state.lastPredictObjectUrl && state.lastPredictObjectUrl !== existingObjectUrl) {
      try { URL.revokeObjectURL(state.lastPredictObjectUrl); } catch (_e) { /* ignore */ }
    }
    const audioUrl = existingObjectUrl || URL.createObjectURL(file);
    state.lastPredictObjectUrl = audioUrl;

    try {
      const formData = new FormData();
      formData.append('file', file, file.name || 'input.wav');

      const resp = await fetch(ENDPOINT_PREDICT, {
        method: 'POST',
        body: formData,
      });

      if (!resp.ok) {
        let detail = 'Lỗi máy chủ (' + resp.status + ')';
        try {
          const errJson = await resp.json();
          if (errJson && errJson.detail) detail = errJson.detail;
        } catch (_e) { /* ignore */ }
        throw new Error(detail);
      }

      const data = await resp.json();
      renderPredictResult(data, audioUrl, file.name);
    } catch (err) {
      showPredictError('Thẩm định thất bại: ' + (err && err.message ? err.message : String(err)));
    } finally {
      setPredictLoading(false);
    }
  }

  async function runPredictOnSample(url, labelText, pillEl) {
    document.querySelectorAll('.vtv-sample-pill').forEach(function (el) {
      el.classList.remove('is-selected');
    });
    if (pillEl) pillEl.classList.add('is-selected');

    try {
      setPredictLoading(true, 'ĐANG NẠP MẪU THẬT ' + (labelText || url) + '...');
      const file = await fetchSampleAsFile(url, url.split('/').pop());
      setPredictLoading(false);
      await submitPredictFile(file);
    } catch (err) {
      setPredictLoading(false);
      showPredictError(err && err.message ? err.message : 'Không thể nạp tệp mẫu.');
    }
  }

  // =========================================================================
  // 9. FEATURE 2 (TAB 02): REAL POST /api/v1/clone-and-audit
  // =========================================================================
  function showCloneError(msg) {
    const box = $('clone-error');
    if (!box) return;
    if (!msg) {
      box.classList.add('hidden');
      box.textContent = '';
      return;
    }
    box.textContent = msg;
    box.classList.remove('hidden');
  }

  function setCloneLoading(isLoading) {
    state.isBusyClone = isLoading;
    const loader = $('clone-loading');
    const btn = $('btn-run-clone-audit');
    if (loader) loader.classList.add('hidden');
    if (btn) {
      btn.disabled = isLoading;
      btn.classList.toggle('opacity-60', isLoading);
    }
    setOrbScan(isLoading ? 1.0 : 0.0);
    if (isLoading) setOrbColor(COLORS.spoof);
  }

  function startCloneElapsedTimer() {
    stopCloneElapsedTimer();
    state.cloneStartedAt = performance.now();
    const timerEl = $('clone-elapsed-timer');
    if (timerEl) timerEl.textContent = '0.0 s';
    state.cloneElapsedTimer = window.setInterval(function () {
      const el = $('clone-elapsed-timer');
      if (!el) return;
      const elapsedSec = (performance.now() - state.cloneStartedAt) / 1000;
      el.textContent = elapsedSec.toFixed(1) + ' s';
    }, 100);
  }

  function stopCloneElapsedTimer() {
    if (state.cloneElapsedTimer) {
      window.clearInterval(state.cloneElapsedTimer);
      state.cloneElapsedTimer = null;
    }
  }

  function setCloneRightLoading(isRightLoading, stageLabel) {
    const loadingBox = $('clone-fake-loading');
    const contentBox = $('clone-fake-content');
    const fakeCard = $('clone-fake-card');
    const fakeBadge = $('clone-fake-badge');

    if (loadingBox) loadingBox.classList.toggle('hidden', !isRightLoading);
    if (contentBox) contentBox.classList.toggle('hidden', isRightLoading);

    if (isRightLoading) {
      if (fakeCard) {
        fakeCard.classList.remove('vtv-verdict-bonafide', 'vtv-verdict-spoof', 'vtv-verdict-borderline');
      }
      if (fakeBadge) {
        fakeBadge.textContent = stageLabel || 'CLONING...';
        fakeBadge.className = 'px-2.5 py-1 text-xs font-bold font-mono-tech border border-[#df0042]/70 bg-[#df0042]/15 text-[#ffb3b6] animate-pulse';
      }
    }
  }

  function setCloneStepStatus(step1Done) {
    const s1 = $('clone-step-1');
    const s2 = $('clone-step-2');
    if (s1) {
      if (step1Done) {
        s1.textContent = '✓ 01 // BẢN GỐC ĐÃ PHÂN TÍCH';
        s1.className = 'border border-[#6dffba]/50 bg-[#00e599]/10 px-3 py-2 text-[#6dffba]';
      } else {
        s1.textContent = '01 // ĐANG PHÂN TÍCH BẢN GỐC...';
        s1.className = 'border border-[#ffbd5d]/60 bg-[#ffbd5d]/10 px-3 py-2 text-[#ffe0bc]';
      }
    }
    if (s2) {
      if (step1Done) {
        s2.textContent = '02 // ĐANG NHÂN BẢN OMNIVOICE CFM...';
        s2.className = 'border border-[#df0042]/70 bg-[#df0042]/15 px-3 py-2 text-[#ffb3b6]';
      } else {
        s2.textContent = '02 // CHỜ NHÂN BẢN OMNIVOICE CFM';
        s2.className = 'border border-on-surface-variant/20 bg-surface-container-low/70 px-3 py-2 text-on-surface-variant';
      }
    }
  }

  function setCloneReferenceFile(file, existingObjectUrl) {
    if (!file) return;
    if (state.cloneRefObjectUrl && state.cloneRefObjectUrl !== existingObjectUrl) {
      try { URL.revokeObjectURL(state.cloneRefObjectUrl); } catch (_e) { /* ignore */ }
    }
    state.cloneRefFile = file;
    state.cloneRefObjectUrl = existingObjectUrl || URL.createObjectURL(file);

    const previewBox = $('clone-ref-preview-box');
    const fnEl = $('clone-ref-filename');
    const audioEl = $('clone-ref-audio');
    if (previewBox) previewBox.classList.remove('hidden');
    if (fnEl) fnEl.textContent = file.name + ' (' + Math.max(1, Math.round(file.size / 1024)) + ' KB)';
    if (audioEl) audioEl.src = state.cloneRefObjectUrl;
    showCloneError('');
  }

  async function loadSpk0004PresetForClone() {
    try {
      const file = await fetchSampleAsFile(
        '/static/samples/sample_bonafide_spk0004.wav',
        'sample_bonafide_spk0004.wav'
      );
      setCloneReferenceFile(file);
    } catch (err) {
      showCloneError(err && err.message ? err.message : 'Không tải được mẫu SPK_0004.');
    }
  }

  function renderCloneBonaCharts(bona) {
    if (!bona || !window.ViTrueVoiceCharts) return;
    const fb = bona.forensics || {};
    window.ViTrueVoiceCharts.renderWaveform($('chart-clone-bona-wave'), fb.waveform, {
      verdict: bona.prediction || 'BONA_FIDE',
      isBorderline: Boolean(bona.is_borderline),
      durationSec: fb.duration_sec || bona.duration_s,
      peakDb: fb.peak_db,
      compact: true,
    });
    window.ViTrueVoiceCharts.renderMelSpectrogram($('chart-clone-bona-mel'), fb.mel_spectrogram, {
      durationSec: fb.duration_sec || bona.duration_s,
      compact: true,
    });
    window.ViTrueVoiceCharts.renderWindowVetoChart($('chart-clone-bona-windows'), fb.windows, fb.pooling, bona.threshold, {
      compact: true,
    });
  }

  function renderCloneFakeCharts(fake) {
    if (!fake || !window.ViTrueVoiceCharts) return;
    const ff = fake.forensics || {};
    window.ViTrueVoiceCharts.renderWaveform($('chart-clone-fake-wave'), ff.waveform, {
      verdict: fake.prediction || 'SPOOF',
      isBorderline: Boolean(fake.is_borderline),
      durationSec: ff.duration_sec || fake.duration_s,
      peakDb: ff.peak_db,
      compact: true,
    });
    window.ViTrueVoiceCharts.renderMelSpectrogram($('chart-clone-fake-mel'), ff.mel_spectrogram, {
      durationSec: ff.duration_sec || fake.duration_s,
      compact: true,
    });
    window.ViTrueVoiceCharts.renderWindowVetoChart($('chart-clone-fake-windows'), ff.windows, ff.pooling, fake.threshold, {
      compact: true,
    });
  }

  function renderCloneCharts(data) {
    if (!data || !window.ViTrueVoiceCharts) return;
    if (data.bonafide) renderCloneBonaCharts(data.bonafide);
    if (data.clone) renderCloneFakeCharts(data.clone);
  }

  function renderCloneBonaCard(bona) {
    if (!bona) return;
    const bonaProbs = computeProbabilities(bona);
    const bonaIsReal = bona.prediction === 'BONA_FIDE';

    if ($('clone-bona-card')) {
      $('clone-bona-card').classList.remove('vtv-verdict-bonafide', 'vtv-verdict-spoof', 'vtv-verdict-borderline');
      $('clone-bona-card').classList.add(bona.is_borderline ? 'vtv-verdict-borderline' : (bonaIsReal ? 'vtv-verdict-bonafide' : 'vtv-verdict-spoof'));
    }
    if ($('clone-bona-badge')) {
      $('clone-bona-badge').textContent = bona.prediction || 'BONA_FIDE';
      $('clone-bona-badge').className = 'px-2.5 py-1 text-xs font-bold font-mono-tech border ' +
        (bonaIsReal ? 'border-[#6dffba]/60 bg-[#00e599]/15 text-[#6dffba]' : 'border-[#df0042]/60 bg-[#df0042]/20 text-[#ffb3b6]');
    }
    if ($('clone-bona-prob')) {
      $('clone-bona-prob').textContent = 'BONA ' + bonaProbs.bonaPct.toFixed(1) + '% • SPOOF ' + bonaProbs.spoofPct.toFixed(1) + '%';
    }
    if ($('clone-bona-score')) {
      const sb = Number(bona.raw_score) || 0;
      $('clone-bona-score').textContent = (sb >= 0 ? '+' : '') + sb.toFixed(2);
    }
    if ($('clone-bona-latency')) $('clone-bona-latency').textContent = formatLatency(bona.latency_sec);
    if ($('clone-bona-sha')) $('clone-bona-sha').textContent = shortHash(bona.audio_sha256);
    if ($('clone-bona-audio') && state.cloneRefObjectUrl) {
      $('clone-bona-audio').src = state.cloneRefObjectUrl;
    }
  }

  function renderCloneAuditResult(data) {
    state.lastClonePayload = data;
    const resultsWrap = $('clone-results');
    if (resultsWrap) resultsWrap.classList.remove('hidden');

    stopCloneElapsedTimer();
    setCloneRightLoading(false);

    const bona = data.bonafide || {};
    const fake = data.clone || {};
    const fakeProbs = computeProbabilities(fake);

    const delta = data.delta_margin != null
      ? Number(data.delta_margin)
      : (Number(bona.raw_score) || 0) - (Number(fake.raw_score) || 0);

    if ($('clone-delta-margin')) {
      $('clone-delta-margin').textContent = (delta >= 0 ? '+' : '') + delta.toFixed(2);
    }
    if ($('clone-transcript-used')) {
      $('clone-transcript-used').textContent = data.transcript_used || fake.transcript_used || 'Auto ASR Wav2Vec2';
    }
    if ($('clone-target-text-echo')) {
      $('clone-target-text-echo').textContent = data.target_text || '';
    }

    // Engine Status Badge (LIVE OMNIVOICE CFM vs CFM PRESET FALLBACK clearly labeled!)
    const statusBadge = $('clone-engine-status-badge');
    if (statusBadge) {
      if (fake.status === 'done') {
        statusBadge.textContent = 'LIVE OMNIVOICE CFM // ZERO-SHOT SYNTHESIS';
        statusBadge.className = 'inline-flex items-center gap-2 px-3 py-1 text-[11px] font-mono-tech uppercase tracking-widest border border-[#6dffba]/50 bg-[#00e599]/15 text-[#6dffba]';
      } else if (fake.status === 'synthetic_fallback') {
        statusBadge.textContent = 'SYNTHETIC FALLBACK // HEADLESS CI MODE';
        statusBadge.className = 'inline-flex items-center gap-2 px-3 py-1 text-[11px] font-mono-tech uppercase tracking-widest border border-[#ffbd5d]/60 bg-[#ffbd5d]/15 text-[#ffe0bc]';
      } else {
        statusBadge.textContent = 'CFM PRESET FALLBACK // VOICESTUDIO SAMPLE';
        statusBadge.className = 'inline-flex items-center gap-2 px-3 py-1 text-[11px] font-mono-tech uppercase tracking-widest border border-[#ffbd5d]/60 bg-[#ffbd5d]/15 text-[#ffe0bc]';
      }
    }

    // Left Card: Bona Fide (synced with final response so delta_margin matches exactly)
    renderCloneBonaCard(bona);

    // Right Card: OmniVoice CFM Clone
    const fakeIsSpoof = fake.prediction !== 'BONA_FIDE';
    if ($('clone-fake-card')) {
      $('clone-fake-card').classList.remove('vtv-verdict-bonafide', 'vtv-verdict-spoof', 'vtv-verdict-borderline');
      $('clone-fake-card').classList.add(fake.is_borderline ? 'vtv-verdict-borderline' : (fakeIsSpoof ? 'vtv-verdict-spoof' : 'vtv-verdict-bonafide'));
    }
    if ($('clone-fake-badge')) {
      $('clone-fake-badge').textContent = fake.prediction || 'SPOOF';
      $('clone-fake-badge').className = 'px-2.5 py-1 text-xs font-bold font-mono-tech border ' +
        (fakeIsSpoof ? 'border-[#df0042]/70 bg-[#df0042]/20 text-[#ffb3b6]' : 'border-[#6dffba]/60 bg-[#00e599]/15 text-[#6dffba]');
    }
    if ($('clone-fake-prob')) {
      $('clone-fake-prob').textContent = 'SPOOF ' + fakeProbs.spoofPct.toFixed(1) + '% • BONA ' + fakeProbs.bonaPct.toFixed(1) + '%';
    }
    if ($('clone-fake-score')) {
      const sf = Number(fake.raw_score) || 0;
      $('clone-fake-score').textContent = (sf >= 0 ? '+' : '') + sf.toFixed(2);
    }
    if ($('clone-fake-latency')) $('clone-fake-latency').textContent = formatLatency(fake.latency_sec);
    if ($('clone-fake-sha')) $('clone-fake-sha').textContent = shortHash(fake.audio_sha256);

    if ($('clone-fake-audio') && fake.audio_base64) {
      $('clone-fake-audio').src = fake.audio_base64;
    }

    // Orb reflects comparative threat catch
    setOrbColor(fakeIsSpoof ? COLORS.spoof : COLORS.borderline);

    window.requestAnimationFrame(function () {
      renderCloneCharts(data);
    });
  }

  async function submitCloneAndAudit() {
    if (state.isBusyClone) return;
    if (!state.cloneRefFile) {
      showCloneError('Vui lòng tải file giọng mẫu, thu âm trực tiếp hoặc chọn mẫu SPK_0004 trước khi nhân bản.');
      return;
    }

    const targetInput = $('clone-target-text');
    const customRefInput = $('clone-custom-ref-text');
    const targetText = (targetInput && targetInput.value ? targetInput.value.trim() : '') ||
      'Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ.';
    const customRefText = customRefInput && customRefInput.value ? customRefInput.value.trim() : '';

    showCloneError('');
    setCloneLoading(true);

    // Reveal comparison stage immediately: Left analyzes first, Right shows live cloning loader
    const resultsWrap = $('clone-results');
    if (resultsWrap) resultsWrap.classList.remove('hidden');

    const statusBadge = $('clone-engine-status-badge');
    if (statusBadge) {
      statusBadge.textContent = 'STAGE 1/2 // ĐANG PHÂN TÍCH BẢN GỐC (SSL-AASIST)...';
      statusBadge.className = 'inline-flex items-center gap-2 px-3 py-1 text-[11px] font-mono-tech uppercase tracking-widest border border-[#ffbd5d]/60 bg-[#ffbd5d]/15 text-[#ffe0bc]';
    }
    if ($('clone-transcript-used')) {
      $('clone-transcript-used').textContent = customRefText || 'Đang nhận diện ASR Wav2Vec2...';
    }
    if ($('clone-target-text-echo')) {
      $('clone-target-text-echo').textContent = targetText;
    }
    if ($('clone-delta-margin')) {
      $('clone-delta-margin').textContent = '...';
    }
    if ($('clone-bona-badge')) {
      $('clone-bona-badge').textContent = 'ĐANG QUÉT...';
      $('clone-bona-badge').className = 'px-2.5 py-1 text-xs font-bold font-mono-tech border border-[#ffbd5d]/60 bg-[#ffbd5d]/15 text-[#ffe0bc] animate-pulse';
    }

    setCloneStepStatus(false);
    setCloneRightLoading(true, 'CLONING...');
    startCloneElapsedTimer();

    let stage1Done = false;

    try {
      // STAGE 1 (~200-400ms): Fast SSL-AASIST audit on original audio so Left Card appears first
      const bonaForm = new FormData();
      bonaForm.append('file', state.cloneRefFile, state.cloneRefFile.name || 'ref.wav');

      const bonaResp = await fetch(ENDPOINT_PREDICT, {
        method: 'POST',
        body: bonaForm,
      });

      if (!bonaResp.ok) {
        let detail = 'Lỗi phân tích bản gốc (' + bonaResp.status + ')';
        try {
          const errJson = await bonaResp.json();
          if (errJson && errJson.detail) detail = errJson.detail;
        } catch (_e) { /* ignore */ }
        throw new Error(detail);
      }

      const bonaData = await bonaResp.json();
      stage1Done = true;
      state.lastClonePayload = { bonafide: bonaData, clone: null };

      renderCloneBonaCard(bonaData);
      window.requestAnimationFrame(function () {
        renderCloneBonaCharts(bonaData);
      });

      // Transition status to Stage 2 while Right Card continues its live cloning motion
      setCloneStepStatus(true);
      if (statusBadge) {
        statusBadge.textContent = 'STAGE 2/2 // BẢN GỐC ĐÃ XONG — ĐANG NHÂN BẢN OMNIVOICE CFM...';
        statusBadge.className = 'inline-flex items-center gap-2 px-3 py-1 text-[11px] font-mono-tech uppercase tracking-widest border border-[#df0042]/70 bg-[#df0042]/15 text-[#ffb3b6]';
      }

      // STAGE 2 (~4-11s): Zero-Shot OmniVoice CFM synthesis + symmetric audit
      const formData = new FormData();
      formData.append('file', state.cloneRefFile, state.cloneRefFile.name || 'ref.wav');
      formData.append('target_text', targetText);
      formData.append('custom_ref_text', customRefText);

      const resp = await fetch(ENDPOINT_CLONE, {
        method: 'POST',
        body: formData,
      });

      if (!resp.ok) {
        let detail = 'Lỗi máy chủ (' + resp.status + ')';
        try {
          const errJson = await resp.json();
          if (errJson && errJson.detail) detail = errJson.detail;
        } catch (_e) { /* ignore */ }
        throw new Error(detail);
      }

      const data = await resp.json();
      renderCloneAuditResult(data);
    } catch (err) {
      stopCloneElapsedTimer();
      setCloneRightLoading(false);
      if (!stage1Done && resultsWrap) {
        resultsWrap.classList.add('hidden');
      } else if ($('clone-fake-badge')) {
        $('clone-fake-badge').textContent = 'LỖI CLONE';
        $('clone-fake-badge').className = 'px-2.5 py-1 text-xs font-bold font-mono-tech border border-[#df0042]/70 bg-[#df0042]/20 text-[#ffb3b6]';
        if ($('clone-fake-content')) $('clone-fake-content').classList.add('hidden');
      }
      showCloneError('Nhân bản & thẩm định thất bại: ' + (err && err.message ? err.message : String(err)));
    } finally {
      stopCloneElapsedTimer();
      setCloneLoading(false);
    }
  }

  // =========================================================================
  // 10. Wire Mic Recorders (Tab 01 & Tab 02), Drag-Drop, Health & Events
  // =========================================================================
  function initRecorders() {
    if (typeof window.ViTrueVoiceRecorder === 'undefined') return;

    // Tab 01 Mic Recorder (auto-submits to POST /api/v1/predict when stopped!)
    const btnMic1 = $('btn-predict-mic');
    const timer1 = $('predict-mic-timer');
    const db1 = $('predict-mic-db');
    const meter1 = $('predict-mic-meter-fill');

    state.predictRecorder = new window.ViTrueVoiceRecorder({
      onStateChange: function (st) {
        if (!btnMic1) return;
        if (st === 'recording') {
          btnMic1.classList.add('vtv-recording-active');
          btnMic1.innerHTML = '<span class="material-symbols-outlined text-base">stop_circle</span> DỪNG &amp; QUÉT NGAY';
          setOrbColor(COLORS.spoof);
        } else {
          btnMic1.classList.remove('vtv-recording-active');
          btnMic1.innerHTML = '<span class="material-symbols-outlined text-base">mic</span> THU ÂM TRỰC TIẾP (16KHZ)';
          if (meter1) meter1.style.width = '0%';
        }
      },
      onTimer: function (_sec, mmss) {
        if (timer1) timer1.textContent = mmss;
      },
      onLevel: function (info) {
        if (db1) db1.textContent = info.db.toFixed(0) + ' dB';
        if (meter1) meter1.style.width = Math.round(info.normalized * 100) + '%';
      },
      onStop: function (result) {
        if (result && result.file) {
          submitPredictFile(result.file, result.url);
        }
      },
      onError: function (msg) {
        showPredictError(msg);
      },
    });

    if (btnMic1) {
      btnMic1.addEventListener('click', function () {
        if (state.cloneRecorder && state.cloneRecorder.isRecording) state.cloneRecorder.cancel();
        if (state.predictRecorder.isRecording) state.predictRecorder.stop();
        else state.predictRecorder.start();
      });
    }

    // Tab 02 Mic Recorder (sets reference voice + audio preview for OmniVoice CFM)
    const btnMic2 = $('btn-clone-mic');
    const timer2 = $('clone-mic-timer');
    const db2 = $('clone-mic-db');
    const meter2 = $('clone-mic-meter-fill');

    state.cloneRecorder = new window.ViTrueVoiceRecorder({
      onStateChange: function (st) {
        if (!btnMic2) return;
        if (st === 'recording') {
          btnMic2.classList.add('vtv-recording-active');
          btnMic2.innerHTML = '<span class="material-symbols-outlined text-base">stop_circle</span> DỪNG GHI MẪU GIỌNG';
          setOrbColor(COLORS.spoof);
        } else {
          btnMic2.classList.remove('vtv-recording-active');
          btnMic2.innerHTML = '<span class="material-symbols-outlined text-base">mic</span> THU GIỌNG MẪU (3–8S)';
          if (meter2) meter2.style.width = '0%';
        }
      },
      onTimer: function (_sec, mmss) {
        if (timer2) timer2.textContent = mmss;
      },
      onLevel: function (info) {
        if (db2) db2.textContent = info.db.toFixed(0) + ' dB';
        if (meter2) meter2.style.width = Math.round(info.normalized * 100) + '%';
      },
      onStop: function (result) {
        if (result && result.file) {
          setCloneReferenceFile(result.file, result.url);
        }
      },
      onError: function (msg) {
        showCloneError(msg);
      },
    });

    if (btnMic2) {
      btnMic2.addEventListener('click', function () {
        if (state.predictRecorder && state.predictRecorder.isRecording) state.predictRecorder.cancel();
        if (state.cloneRecorder.isRecording) state.cloneRecorder.stop();
        else state.cloneRecorder.start();
      });
    }
  }

  function wireDropzone(zoneEl, inputEl, onFileSelected) {
    if (!zoneEl || !inputEl) return;

    zoneEl.addEventListener('click', function () {
      inputEl.click();
    });

    zoneEl.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        inputEl.click();
      }
    });

    inputEl.addEventListener('change', function () {
      if (inputEl.files && inputEl.files[0]) {
        onFileSelected(inputEl.files[0]);
        inputEl.value = '';
      }
    });

    ['dragenter', 'dragover'].forEach(function (evName) {
      zoneEl.addEventListener(evName, function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        zoneEl.classList.add('is-dragover');
      });
    });

    ['dragleave', 'drop'].forEach(function (evName) {
      zoneEl.addEventListener(evName, function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        zoneEl.classList.remove('is-dragover');
      });
    });

    zoneEl.addEventListener('drop', function (ev) {
      const files = ev.dataTransfer && ev.dataTransfer.files;
      if (files && files[0]) {
        onFileSelected(files[0]);
      }
    });
  }

  async function hydrateBackendMetadata() {
    // 1. Live Health status pill
    try {
      const r = await fetch(ENDPOINT_HEALTH);
      if (r.ok) {
        const h = await r.json();
        const pill = $('vtv-health-pill');
        if (pill) {
          const ver = h.version || '0.9.4';
          const dev = (h.device || 'CPU').toUpperCase();
          pill.textContent = 'CORE_v' + ver + ' // ' + dev + ' • θ=' + Number(h.threshold || 0).toFixed(1);
        }
      }
    } catch (_e) { /* offline-safe */ }

    // 2. Check /api/v1/samples for any extra real WAVs on disk
    try {
      const r = await fetch(ENDPOINT_SAMPLES);
      if (!r.ok) return;
      const list = await r.json();
      if (!Array.isArray(list) || list.length === 0) return;

      const grid = $('predict-samples-grid');
      if (!grid) return;
      const existingUrls = new Set(DEFAULT_SAMPLES.map(function (s) { return s.url; }));
      list.forEach(function (item) {
        if (!item || !item.url || existingUrls.has(item.url) || item.exists === false) return;
        existingUrls.add(item.url);
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'vtv-sample-pill px-3 py-2 text-left text-[11px] font-mono-tech uppercase tracking-wider';
        btn.setAttribute('data-cursor', 'QUÉT');
        btn.setAttribute('data-predict-sample', item.url);
        btn.textContent = (item.label || item.filename).toUpperCase();
        btn.addEventListener('click', function () {
          runPredictOnSample(item.url, item.label || item.filename, btn);
        });
        grid.appendChild(btn);
      });
    } catch (_e) { /* silent fallback to 5 canonical buttons */ }
  }

  function initEvents() {
    // WebGL 3D Toggle Button
    const btnWebgl = $('btn-toggle-webgl');
    if (btnWebgl) {
      btnWebgl.addEventListener('click', function () {
        if (!window.vieTrueVoice3D || typeof window.vieTrueVoice3D.setEnabled !== 'function') return;
        const next = !window.vieTrueVoice3D.isEnabled();
        const active = window.vieTrueVoice3D.setEnabled(next);
        btnWebgl.textContent = active ? 'WEBGL 3D // BẬT' : 'WEBGL 3D // TẮT';
        btnWebgl.setAttribute('aria-pressed', String(active));
        btnWebgl.classList.toggle('border-[#6dffba]/40', active);
        btnWebgl.classList.toggle('text-[#6dffba]', active);
        btnWebgl.classList.toggle('text-[#bacbbe]', !active);
      });
    }

    // Hero & Nav CTA buttons
    const btnNavStudio = $('btn-nav-studio');
    if (btnNavStudio) btnNavStudio.addEventListener('click', function () { openOverlay('predict'); });

    const btnHeroPredict = $('btn-hero-predict');
    if (btnHeroPredict) btnHeroPredict.addEventListener('click', function () { openOverlay('predict'); });

    const btnHeroClone = $('btn-hero-clone');
    if (btnHeroClone) btnHeroClone.addEventListener('click', function () { openOverlay('clone'); });

    const btnHeroSample = $('btn-hero-sample');
    if (btnHeroSample) {
      btnHeroSample.addEventListener('click', function () {
        togglePlaySample('/static/samples/sample_spoof_voicestudio_cfm.wav', btnHeroSample, COLORS.spoof);
      });
    }

    const btnScrollDown = $('btn-scroll-down');
    if (btnScrollDown) {
      btnScrollDown.addEventListener('click', function () {
        const target = $('cinema-section');
        if (!target) return;
        if (state.lenis && typeof state.lenis.scrollTo === 'function') {
          state.lenis.scrollTo(target);
        } else {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
    }

    // Section 3 Sticky Cards: Play sample audio buttons
    document.querySelectorAll('[data-play-sample]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const url = btn.getAttribute('data-play-sample');
        const tone = btn.getAttribute('data-play-tone') === 'bonafide' ? COLORS.bonafide : COLORS.spoof;
        if (url) togglePlaySample(url, btn, tone);
      });
    });

    // Section 3 Sticky Cards: Scan sample immediately in Overlay Tab 01
    document.querySelectorAll('[data-scan-sample]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const url = btn.getAttribute('data-scan-sample');
        const label = btn.getAttribute('data-scan-label') || url;
        openOverlay('predict');
        if (url) runPredictOnSample(url, label, null);
      });
    });

    // Section 3 Card 03 & Footer: Open Overlay Tab 01 / Tab 02 pre-ready
    document.querySelectorAll('[data-open-predict]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        openOverlay('predict');
      });
    });

    document.querySelectorAll('[data-open-clone-preset]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        openOverlay('clone');
        if (!state.cloneRefFile) {
          loadSpk0004PresetForClone();
        }
      });
    });

    // Overlay Controls
    const btnClose = $('btn-close-overlay');
    if (btnClose) btnClose.addEventListener('click', closeOverlay);

    const tabBtnPredict = $('tab-btn-predict');
    if (tabBtnPredict) tabBtnPredict.addEventListener('click', function () { switchTab('predict'); });

    const tabBtnClone = $('tab-btn-clone');
    if (tabBtnClone) tabBtnClone.addEventListener('click', function () { switchTab('clone'); });

    // Tab 01 Dropzone + 5 Real Quick Samples
    wireDropzone($('predict-dropzone'), $('predict-file-input'), function (file) {
      submitPredictFile(file);
    });

    document.querySelectorAll('[data-predict-sample]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const url = btn.getAttribute('data-predict-sample');
        if (url) runPredictOnSample(url, btn.textContent.trim(), btn);
      });
    });

    // Tab 02 Dropzone, SPK_0004 Preset, Scam Script Pills, Run CTA & Download Clone WAV
    wireDropzone($('clone-dropzone'), $('clone-file-input'), function (file) {
      setCloneReferenceFile(file);
    });

    const btnLoadSpk = $('btn-clone-load-spk0004');
    if (btnLoadSpk) btnLoadSpk.addEventListener('click', loadSpk0004PresetForClone);

    document.querySelectorAll('[data-scam-script]').forEach(function (pill) {
      pill.addEventListener('click', function () {
        const ta = $('clone-target-text');
        if (ta) {
          ta.value = pill.getAttribute('data-scam-script') || '';
          ta.focus();
        }
      });
    });

    const btnRunClone = $('btn-run-clone-audit');
    if (btnRunClone) btnRunClone.addEventListener('click', submitCloneAndAudit);

    // Keyboard shortcuts (Escape closes overlay)
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && state.overlayOpen) {
        closeOverlay();
      }
    });

    // Responsive chart redraw on resize
    let resizeTimer = null;
    window.addEventListener('resize', function () {
      if (resizeTimer) window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(function () {
        if (!state.overlayOpen) return;
        if (state.activeTab === 'predict' && state.lastPredictPayload) {
          renderPredictCharts(state.lastPredictPayload);
        } else if (state.activeTab === 'clone' && state.lastClonePayload) {
          renderCloneCharts(state.lastClonePayload);
        }
      }, 160);
    });
  }

  function boot() {
    runPreloader();
    initMotionAndScroll();
    initCustomCursor();
    initRecorders();
    initEvents();
    hydrateBackendMetadata();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
