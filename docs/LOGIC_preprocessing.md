# LOGIC_preprocessing — Audio Signal Normalization & Augmentation

---

## 1. Preprocessing Pipeline (`src/preprocessing/audio_processor.py`)

### Step 1: Mono Conversion & Resampling
- Audio channels averaged to mono: $x_{mono}[n] = \frac{1}{C} \sum_{c=1}^C x_c[n]$.
- Sampling rate resampled to exactly **16,000 Hz** (standard for Wav2Vec 2.0 and AASIST).

### Step 2: Silence Trimming
- RMS energy calculated with `frame_length=512`, `hop_length=160`.
- Threshold set at the **20th percentile** of the frame energies:
  $$\text{threshold} = P_{20}(\text{RMS})$$
- Frames with $\text{RMS} > \text{threshold}$ are retained; leading and trailing silence frames are sliced off.
- Eliminates technical bias caused by silence artifacts in recording tools.

### Step 3: Fixed Duration (64,000 Samples = 4.0s)
- **If length < 64,000 samples**: Repeat padding is applied using `np.tile(wav, repeats)[:64000]`.
  > STUBBORN_FACT: Repeat padding is strictly preferred over zero-padding to maintain spectral-temporal continuity for convolutional and graph filters.
- **If length >= 64,000 samples**: Crop to the first 64,000 samples (or center crop during inference).

### Step 4: Amplitude Z-Score Normalization
- Signal normalized to zero-mean and unit-variance:
  $$x_{norm}[n] = \frac{x[n] - \mu}{\sigma + 10^{-8}}$$

---

## 2. Augmentation Algorithms

### RawBoost (Domain: Time-Domain Waveform)
- **Branch 1**: Signal-dependent additive noise (ISD).
- **Branch 2**: Signal-independent impulsive noise (SSI).
- **Branch 3**: Linear and non-linear convolutional filtering (LnL - Algo 3/5).
- Injected on-the-fly during training with 50% probability.

### Codec & Bandwidth Simulation
- **Opus**: Low-bitrate simulation (16–32 kbps, simulating Zalo / Telegram voice notes).
- **AMR / GSM**: Narrowband telephony codecs.
- **8kHz Downsampling & Filtering**: Resample to 8kHz and back to 16kHz with 300Hz–3400Hz bandpass filter (simulating PSTN / VoIP calls).

---

*v0.1.0 — 2026-10-16*
