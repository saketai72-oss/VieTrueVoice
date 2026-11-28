/**
 * VieTrueVoice v0.9.4 — Live Browser Microphone Recorder (16kHz Mono PCM WAV)
 * Requests raw un-gated microphone audio (echoCancellation/noiseSuppression/AGC OFF)
 * to preserve genuine acoustic room floor & harmonics for SSL-AASIST forensics.
 * Feeds real-time volume level into window.vieTrueVoice3D.setAudioLevel().
 */
(function () {
  'use strict';

  const TARGET_SR = 16000;
  const MAX_RECORD_SECONDS = 30;

  function formatMMSS(totalSeconds) {
    const sec = Math.max(0, Math.floor(totalSeconds));
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    return m + ':' + s;
  }

  function mergeFloat32Chunks(chunks) {
    let totalLen = 0;
    for (let i = 0; i < chunks.length; i++) {
      totalLen += chunks[i].length;
    }
    const merged = new Float32Array(totalLen);
    let offset = 0;
    for (let i = 0; i < chunks.length; i++) {
      merged.set(chunks[i], offset);
      offset += chunks[i].length;
    }
    return merged;
  }

  function resampleLinear(samples, srcRate, dstRate) {
    if (!samples || samples.length === 0) return new Float32Array(0);
    if (srcRate === dstRate) return samples;
    const ratio = srcRate / dstRate;
    const outLen = Math.max(1, Math.round(samples.length / ratio));
    const output = new Float32Array(outLen);
    for (let i = 0; i < outLen; i++) {
      const pos = i * ratio;
      const idx = Math.floor(pos);
      const frac = pos - idx;
      const s0 = samples[idx] || 0;
      const s1 = idx + 1 < samples.length ? samples[idx + 1] : s0;
      output[i] = s0 + (s1 - s0) * frac;
    }
    return output;
  }

  function writeAscii(view, offset, str) {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  }

  function encodeWav16kMono(samplesFloat32, sampleRate) {
    const numSamples = samplesFloat32.length;
    const dataBytes = numSamples * 2;
    const buffer = new ArrayBuffer(44 + dataBytes);
    const view = new DataView(buffer);

    writeAscii(view, 0, 'RIFF');
    view.setUint32(4, 36 + dataBytes, true);
    writeAscii(view, 8, 'WAVE');
    writeAscii(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // PCM subchunk size
    view.setUint16(20, 1, true);  // AudioFormat = PCM
    view.setUint16(22, 1, true);  // NumChannels = 1 (mono)
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true); // ByteRate
    view.setUint16(32, 2, true);  // BlockAlign
    view.setUint16(34, 16, true); // BitsPerSample
    writeAscii(view, 36, 'data');
    view.setUint32(40, dataBytes, true);

    let offset = 44;
    for (let i = 0; i < numSamples; i++) {
      const clamped = Math.max(-1, Math.min(1, samplesFloat32[i]));
      const int16 = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
      view.setInt16(offset, int16, true);
      offset += 2;
    }

    return new Blob([buffer], { type: 'audio/wav' });
  }

  class VieTrueVoiceRecorder {
    constructor(callbacks) {
      this.cb = callbacks || {};
      this.isRecording = false;
      this.stream = null;
      this.audioCtx = null;
      this.sourceNode = null;
      this.analyserNode = null;
      this.processorNode = null;
      this.muteGain = null;
      this.mediaRecorder = null;
      this.webmChunks = [];
      this.pcmChunks = [];
      this.inputSampleRate = 48000;
      this.startTime = 0;
      this.timerInterval = null;
      this.meterRaf = null;
      this.timeDomainBuf = null;
    }

    async start() {
      if (this.isRecording) return;
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        this._emitError('Trình duyệt không hỗ trợ ghi âm micro (yêu cầu HTTPS hoặc localhost).');
        return;
      }

      try {
        this.stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: false,
            channelCount: 1,
          },
        });
      } catch (err) {
        this._emitError('Không thể truy cập micro: ' + (err && err.message ? err.message : 'Quyền bị từ chối'));
        return;
      }

      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.pcmChunks = [];
      this.webmChunks = [];

      try {
        this.audioCtx = new AudioCtx();
        if (this.audioCtx.state === 'suspended') {
          await this.audioCtx.resume();
        }
        this.inputSampleRate = this.audioCtx.sampleRate || 48000;
        this.sourceNode = this.audioCtx.createMediaStreamSource(this.stream);

        this.analyserNode = this.audioCtx.createAnalyser();
        this.analyserNode.fftSize = 512;
        this.analyserNode.smoothingTimeConstant = 0.72;
        this.timeDomainBuf = new Float32Array(this.analyserNode.fftSize);

        // ScriptProcessorNode captures clean raw PCM without WebRTC codec loss
        if (typeof this.audioCtx.createScriptProcessor === 'function') {
          this.processorNode = this.audioCtx.createScriptProcessor(4096, 1, 1);
          this.muteGain = this.audioCtx.createGain();
          this.muteGain.gain.value = 0;

          this.processorNode.onaudioprocess = (ev) => {
            if (!this.isRecording) return;
            const ch0 = ev.inputBuffer.getChannelData(0);
            this.pcmChunks.push(new Float32Array(ch0));
          };

          this.sourceNode.connect(this.analyserNode);
          this.analyserNode.connect(this.processorNode);
          this.processorNode.connect(this.muteGain);
          this.muteGain.connect(this.audioCtx.destination);
        } else {
          this.sourceNode.connect(this.analyserNode);
        }
      } catch (_ctxErr) {
        // Fallback solely to MediaRecorder if AudioContext fails
        this.audioCtx = null;
      }

      // Secondary MediaRecorder fallback (WebM/Opus) in case PCM capture returns empty
      if (typeof window.MediaRecorder !== 'undefined') {
        try {
          const preferred = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
            ? 'audio/webm;codecs=opus'
            : (MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '');
          this.mediaRecorder = preferred
            ? new MediaRecorder(this.stream, { mimeType: preferred })
            : new MediaRecorder(this.stream);
          this.mediaRecorder.ondataavailable = (ev) => {
            if (ev.data && ev.data.size > 0) {
              this.webmChunks.push(ev.data);
            }
          };
          this.mediaRecorder.start(250);
        } catch (_mrErr) {
          this.mediaRecorder = null;
        }
      }

      this.isRecording = true;
      this.startTime = performance.now();
      if (this.cb.onStateChange) this.cb.onStateChange('recording');
      if (this.cb.onTimer) this.cb.onTimer(0, '00:00');

      this.timerInterval = window.setInterval(() => {
        const elapsed = (performance.now() - this.startTime) / 1000;
        if (this.cb.onTimer) this.cb.onTimer(elapsed, formatMMSS(elapsed));
        if (elapsed >= MAX_RECORD_SECONDS) {
          this.stop();
        }
      }, 200);

      this._pumpMeter();
    }

    _pumpMeter() {
      if (!this.isRecording) return;
      this.meterRaf = window.requestAnimationFrame(() => this._pumpMeter());
      if (!this.analyserNode || !this.timeDomainBuf) return;

      this.analyserNode.getFloatTimeDomainData(this.timeDomainBuf);
      let sumSq = 0;
      for (let i = 0; i < this.timeDomainBuf.length; i++) {
        const v = this.timeDomainBuf[i];
        sumSq += v * v;
      }
      const rms = Math.sqrt(sumSq / this.timeDomainBuf.length);
      const db = rms > 1e-6 ? 20 * Math.log10(rms) : -60;
      const normalized = Math.max(0, Math.min(1, rms * 5.2));

      if (window.vieTrueVoice3D && typeof window.vieTrueVoice3D.setAudioLevel === 'function') {
        window.vieTrueVoice3D.setAudioLevel(normalized);
      }
      if (this.cb.onLevel) {
        this.cb.onLevel({
          rms: rms,
          db: Math.max(-60, Math.min(0, db)),
          normalized: normalized,
        });
      }
    }

    async stop() {
      if (!this.isRecording) return null;
      this.isRecording = false;
      const durationSec = Math.max(0.1, (performance.now() - this.startTime) / 1000);

      if (this.timerInterval) {
        window.clearInterval(this.timerInterval);
        this.timerInterval = null;
      }
      if (this.meterRaf) {
        window.cancelAnimationFrame(this.meterRaf);
        this.meterRaf = null;
      }

      if (window.vieTrueVoice3D && typeof window.vieTrueVoice3D.setAudioLevel === 'function') {
        window.vieTrueVoice3D.setAudioLevel(0);
      }

      // Stop MediaRecorder cleanly if active
      const mediaRecorderPromise = new Promise((resolve) => {
        if (!this.mediaRecorder || this.mediaRecorder.state === 'inactive') {
          resolve();
          return;
        }
        this.mediaRecorder.onstop = () => resolve();
        try {
          this.mediaRecorder.stop();
        } catch (_err) {
          resolve();
        }
      });

      this._teardownAudioGraph();
      await mediaRecorderPromise;
      this._releaseStream();

      let blob = null;
      let filename = 'mic_live_' + Date.now() + '.wav';
      let mimeType = 'audio/wav';

      if (this.pcmChunks.length > 0) {
        const merged = mergeFloat32Chunks(this.pcmChunks);
        const resampled = resampleLinear(merged, this.inputSampleRate, TARGET_SR);
        blob = encodeWav16kMono(resampled, TARGET_SR);
      } else if (this.webmChunks.length > 0) {
        mimeType = this.webmChunks[0].type || 'audio/webm';
        blob = new Blob(this.webmChunks, { type: mimeType });
        filename = 'mic_live_' + Date.now() + '.webm';
      }

      this.pcmChunks = [];
      this.webmChunks = [];

      if (!blob || blob.size < 128) {
        if (this.cb.onStateChange) this.cb.onStateChange('idle');
        this._emitError('Đoạn ghi âm quá ngắn hoặc không thu được tín hiệu.');
        return null;
      }

      const file = new File([blob], filename, { type: mimeType });
      const url = URL.createObjectURL(blob);
      const result = {
        blob: blob,
        file: file,
        url: url,
        durationSec: Number(durationSec.toFixed(2)),
        mimeType: mimeType,
      };

      if (this.cb.onStateChange) this.cb.onStateChange('idle');
      if (this.cb.onStop) this.cb.onStop(result);
      return result;
    }

    cancel() {
      if (!this.isRecording) return;
      this.isRecording = false;
      if (this.timerInterval) {
        window.clearInterval(this.timerInterval);
        this.timerInterval = null;
      }
      if (this.meterRaf) {
        window.cancelAnimationFrame(this.meterRaf);
        this.meterRaf = null;
      }
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        try { this.mediaRecorder.stop(); } catch (_err) { /* ignore */ }
      }
      this._teardownAudioGraph();
      this._releaseStream();
      this.pcmChunks = [];
      this.webmChunks = [];
      if (window.vieTrueVoice3D) window.vieTrueVoice3D.setAudioLevel(0);
      if (this.cb.onStateChange) this.cb.onStateChange('idle');
    }

    _teardownAudioGraph() {
      try { if (this.processorNode) this.processorNode.disconnect(); } catch (_e) { /* ignore */ }
      try { if (this.analyserNode) this.analyserNode.disconnect(); } catch (_e) { /* ignore */ }
      try { if (this.sourceNode) this.sourceNode.disconnect(); } catch (_e) { /* ignore */ }
      try { if (this.muteGain) this.muteGain.disconnect(); } catch (_e) { /* ignore */ }
      if (this.audioCtx) {
        try { this.audioCtx.close(); } catch (_e) { /* ignore */ }
      }
      this.processorNode = null;
      this.analyserNode = null;
      this.sourceNode = null;
      this.muteGain = null;
      this.audioCtx = null;
    }

    _releaseStream() {
      if (this.stream) {
        this.stream.getTracks().forEach((track) => {
          try { track.stop(); } catch (_e) { /* ignore */ }
        });
        this.stream = null;
      }
    }

    _emitError(msg) {
      if (this.cb.onError) this.cb.onError(msg);
    }
  }

  window.VieTrueVoiceRecorder = VieTrueVoiceRecorder;
})();
