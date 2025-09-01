"""
Dora PrimeSpeech - Standalone GPT-SoVITS Text-to-Speech Node

A self-contained TTS node using GPT-SoVITS technology without external dependencies.
"""

__version__ = "0.2.0"
__author__ = "Dora PrimeSpeech Contributors"

from .config import PrimeSpeechConfig

# Always use the main implementation with MoYoYo TTS
# No fallback - we want real TTS, not placeholder audio
from .main import main
print("[PrimeSpeech] Using MoYoYo TTS implementation")
GPTSoVITSEngine = None

__all__ = ["PrimeSpeechConfig", "main", "GPTSoVITSEngine"]