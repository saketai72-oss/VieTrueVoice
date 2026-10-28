"""
ViTrueVoice Dual-Engine Speech Synthesis & Quality Gate Framework.
CMP436 - Synthetic Voice Detection in Compressed Telephony.
"""

from .base import SynthesisRequest, SynthesisResult, QualityMetrics, BaseTTSAdapter, ManifestRecord
from .text_utils import normalize_for_eval, fix_tone_token, has_digits
from .dialect_evaluator import (
    compute_pitch_dynamics,
    evaluate_prosodic_consistency,
    evaluate_dialect_consistency,
)

try:
    from .evaluator import MultiGateEvaluator
except Exception:
    MultiGateEvaluator = None

try:
    from .speaker_profiler import SpeakerProfiler
except Exception:
    SpeakerProfiler = None

try:
    from .pipeline import ViTrueVoiceDualPipeline, PipelineMode
except Exception:
    ViTrueVoiceDualPipeline = None
    PipelineMode = None

try:
    from .batch_processor import DatasetPartitioner, TelephonyCompressor, BatchDatasetProcessor
except Exception:
    DatasetPartitioner = None
    TelephonyCompressor = None
    BatchDatasetProcessor = None

__all__ = [
    "SynthesisRequest",
    "SynthesisResult",
    "QualityMetrics",
    "BaseTTSAdapter",
    "ManifestRecord",
    "normalize_for_eval",
    "fix_tone_token",
    "has_digits",
    "compute_pitch_dynamics",
    "evaluate_prosodic_consistency",
    "evaluate_dialect_consistency",
    "MultiGateEvaluator",
    "SpeakerProfiler",
    "ViTrueVoiceDualPipeline",
    "PipelineMode",
    "DatasetPartitioner",
    "TelephonyCompressor",
    "BatchDatasetProcessor"
]
