from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np

@dataclass
class SynthesisRequest:
    text: str
    speaker_id: str
    ref_audio: str
    seed: int = 100
    engine_preset: Optional[str] = None  # e.g., 'VieNeu-A', 'VieNeu-F', 'F5'
    extra_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SynthesisResult:
    audio: np.ndarray
    sample_rate: int
    engine_name: str
    latency_s: float
    duration_s: float = 0.0
    channels: int = 1
    dtype: str = "float32"
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.duration_s == 0.0 and len(self.audio) > 0 and self.sample_rate > 0:
            self.duration_s = round(len(self.audio) / self.sample_rate, 3)

@dataclass
class QualityMetrics:
    clean_wer: float
    clean_cer: float
    speaker_sim: float
    band_2_4k_pct: float
    band_4_8k_pct: float
    is_catastrophic: bool
    gate1_pass: bool
    gate2_pass: bool
    gate3_pass: bool
    overall_pass: bool
    composite_score: float
    is_valid: bool = True
    error_message: Optional[str] = None
    dialect_score: float = 1.0
    dialect_match: bool = True
    gate4_pass: bool = True
    dialect_drift: bool = False

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        aliases = {
            "wer": "clean_wer", "raw_wer": "clean_wer",
            "cer": "clean_cer", "raw_cer": "clean_cer",
            "ecapa_sim": "speaker_sim", "sim": "speaker_sim",
            "gate4": "gate4_pass", "drift": "dialect_drift",
            "dialect": "dialect_score"
        }
        if item in aliases and hasattr(self, aliases[item]):
            return getattr(self, aliases[item])
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except (KeyError, AttributeError):
            return default

@dataclass
class ManifestRecord:
    audio_path: str
    speaker_id: str
    is_bonafide: bool
    ecapa_sim: float
    raw_wer: float
    raw_cer: float
    codec: str = "studio"  # "studio", "g711_alaw", "amr_nb"
    engine_name: Optional[str] = None
    ref_audio_path: Optional[str] = None
    seed: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def derive_attack_tier(
        self,
        t_strong: float = 0.5068,
        t_medium: float = 0.4633,
        max_wer_strong: float = 0.15,
        max_wer_medium: float = 0.20
    ) -> str:
        """Suy ra tầng tấn công hậu nghiệm (post-hoc) - tách riêng danh tính & độ rõ, không đưa vào feature mô hình."""
        if self.is_bonafide:
            return "BonaFide"
        if self.ecapa_sim >= t_strong and self.raw_wer <= max_wer_strong:
            return "Tier 1 (Strong)"
        elif self.ecapa_sim >= t_medium and self.raw_wer <= max_wer_medium:
            return "Tier 2 (Medium)"
        return "Tier 3 (Weak)"

class BaseTTSAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Tên định danh engine."""
        pass

    @abstractmethod
    def synthesize(self, req: SynthesisRequest) -> SynthesisResult:
        """Thực thi tổng hợp âm thanh chuẩn hóa."""
        pass
