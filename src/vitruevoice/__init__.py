"""
ViTrueVoice Dual-Engine Speech Synthesis & Quality Gate Framework.
CMP436 - Synthetic Voice Detection in Compressed Telephony.
"""

from .base import SynthesisRequest, SynthesisResult, QualityMetrics, BaseTTSAdapter, ManifestRecord
from .evaluator import MultiGateEvaluator
from .speaker_profiler import SpeakerProfiler
from .pipeline import ViTrueVoiceDualPipeline, PipelineMode
from .batch_processor import DatasetPartitioner, TelephonyCompressor, BatchDatasetProcessor

__all__ = [
    "SynthesisRequest",
    "SynthesisResult",
    "QualityMetrics",
    "BaseTTSAdapter",
    "ManifestRecord",
    "MultiGateEvaluator",
    "SpeakerProfiler",
    "ViTrueVoiceDualPipeline",
    "PipelineMode",
    "DatasetPartitioner",
    "TelephonyCompressor",
    "BatchDatasetProcessor"
]
