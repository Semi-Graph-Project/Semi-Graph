"""Process-wide runtime for the local ONNX cross-encoder."""

from __future__ import annotations

import os
from threading import Lock
from typing import Any

from huggingface_hub import snapshot_download
from sentence_transformers import CrossEncoder


MODEL_ID = "jinaai/jina-reranker-v1-tiny-en"

_model: CrossEncoder | None = None
_model_load_lock = Lock()
_inference_lock = Lock()


def _enable_offline_mode() -> None:
    """Keep Hugging Face lookups local without overriding caller settings."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")


def get_cross_encoder_model() -> CrossEncoder:
    """Load the local ONNX model once and reuse it for this process."""
    global _model
    if _model is None:
        with _model_load_lock:
            if _model is None:
                _enable_offline_mode()
                model_path = snapshot_download(
                    MODEL_ID,
                    local_files_only=True,
                )
                _model = CrossEncoder(
                    model_path,
                    backend="onnx",
                    max_length=2048,
                    local_files_only=True,
                    model_kwargs={
                        "file_name": "onnx/model_quantized.onnx",
                        "provider": "CPUExecutionProvider",
                    },
                )
    return _model


def predict_cross_encoder_scores(
    pairs: list[tuple[str, str]],
) -> Any:
    """Run one CPU inference at a time using the shared ONNX model."""
    model = get_cross_encoder_model()
    with _inference_lock:
        return model.predict(
            pairs,
            batch_size=2,
            show_progress_bar=False,
        )
