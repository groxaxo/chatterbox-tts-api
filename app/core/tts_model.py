"""
TTS model initialization and management
"""

import os
import asyncio
import torch
from enum import Enum
from typing import Optional, Dict, Any
from chatterbox.tts import ChatterboxTTS
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from app.core.mtl import SUPPORTED_LANGUAGES
from app.config import Config, detect_device

# Global model instance
_model = None
_device = None
_initialization_state = "not_started"
_initialization_error = None
_initialization_progress = ""
_is_multilingual = None
_supported_languages = {}


class InitializationState(Enum):
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"


def get_optimal_dtype(device: str):
    """Determine the optimal data type for the given device"""
    dtype_setting = Config.MODEL_DTYPE.lower()
    
    # If user specified a dtype, use it
    if dtype_setting == 'float32':
        return torch.float32
    elif dtype_setting == 'float16':
        return torch.float16
    elif dtype_setting == 'bfloat16':
        return torch.bfloat16
    
    # Auto-detect optimal dtype based on device
    if dtype_setting == 'auto':
        if device == 'cuda':
            # Use float16 for CUDA if available
            return torch.float16
        elif device == 'mps':
            # MPS works best with float32
            return torch.float32
        else:
            # CPU defaults to float32
            return torch.float32
    
    return torch.float32


def quantize_model_int8(model):
    """Apply INT8 dynamic quantization to the model"""
    print("🔧 Applying INT8 quantization to reduce VRAM usage...")
    
    # Get model size before quantization
    param_size_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 ** 2)
    print(f"   Original model size: {param_size_mb:.2f} MB")
    
    # Apply dynamic quantization to Linear and LSTM layers
    # This reduces memory usage and can improve inference speed
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear, torch.nn.LSTM, torch.nn.GRU},  # Layers to quantize
        dtype=torch.qint8
    )
    
    # Get model size after quantization
    param_size_mb_after = sum(p.numel() * p.element_size() for p in quantized_model.parameters() if hasattr(p, 'numel')) / (1024 ** 2)
    print(f"   Quantized model size: {param_size_mb_after:.2f} MB")
    print(f"   VRAM savings: {param_size_mb - param_size_mb_after:.2f} MB ({((param_size_mb - param_size_mb_after) / param_size_mb * 100):.1f}%)")
    
    return quantized_model


async def initialize_model():
    """Initialize the Chatterbox TTS model"""
    global _model, _device, _initialization_state, _initialization_error, _initialization_progress, _is_multilingual, _supported_languages
    
    try:
        _initialization_state = InitializationState.INITIALIZING.value
        _initialization_progress = "Validating configuration..."
        
        Config.validate()
        _device = detect_device()
        
        print(f"Initializing Chatterbox TTS model...")
        print(f"Device: {_device}")
        print(f"Voice sample: {Config.VOICE_SAMPLE_PATH}")
        print(f"Model cache: {Config.MODEL_CACHE_DIR}")
        
        _initialization_progress = "Creating model cache directory..."
        # Ensure model cache directory exists
        os.makedirs(Config.MODEL_CACHE_DIR, exist_ok=True)
        
        # Check voice sample exists
        if not os.path.exists(Config.VOICE_SAMPLE_PATH):
            raise FileNotFoundError(f"Voice sample not found: {Config.VOICE_SAMPLE_PATH}")
        
        _initialization_progress = "Configuring device compatibility..."
        # Patch torch.load for CPU compatibility if needed
        if _device == 'cpu':
            import torch
            original_load = torch.load
            original_load_file = None
            
            # Try to patch safetensors if available
            try:
                import safetensors.torch
                original_load_file = safetensors.torch.load_file
            except ImportError:
                pass
            
            def force_cpu_torch_load(f, map_location=None, **kwargs):
                # Always force CPU mapping if we're on a CPU device
                return original_load(f, map_location='cpu', **kwargs)
            
            def force_cpu_load_file(filename, device=None):
                # Force CPU for safetensors loading too
                return original_load_file(filename, device='cpu')
            
            torch.load = force_cpu_torch_load
            if original_load_file:
                safetensors.torch.load_file = force_cpu_load_file
        
        # Determine if we should use multilingual model
        use_multilingual = Config.USE_MULTILINGUAL_MODEL
        
        _initialization_progress = "Loading TTS model (this may take a while)..."
        # Initialize model with run_in_executor for non-blocking
        loop = asyncio.get_event_loop()
        
        if use_multilingual:
            print(f"Loading Chatterbox Multilingual TTS model...")
            _model = await loop.run_in_executor(
                None, 
                lambda: ChatterboxMultilingualTTS.from_pretrained(device=_device)
            )
            _is_multilingual = True
            _supported_languages = SUPPORTED_LANGUAGES.copy()
            print(f"✓ Multilingual model initialized with {len(_supported_languages)} languages")
        else:
            print(f"Loading standard Chatterbox TTS model...")
            _model = await loop.run_in_executor(
                None, 
                lambda: ChatterboxTTS.from_pretrained(device=_device)
            )
            _is_multilingual = False
            _supported_languages = {"en": "English"}  # Standard model only supports English
            print(f"✓ Standard model initialized (English only)")
        
        # Apply INT8 quantization if enabled
        if Config.USE_INT8_QUANTIZATION:
            _initialization_progress = "Applying INT8 quantization..."
            _model = await loop.run_in_executor(
                None,
                lambda: quantize_model_int8(_model)
            )
            print(f"✓ INT8 quantization applied successfully")
        
        # Apply dtype conversion if specified and not using quantization
        elif Config.MODEL_DTYPE.lower() != 'auto' and not Config.USE_INT8_QUANTIZATION:
            optimal_dtype = get_optimal_dtype(_device)
            if optimal_dtype != torch.float32:
                _initialization_progress = f"Converting model to {optimal_dtype}..."
                print(f"🔧 Converting model to {optimal_dtype}...")
                _model = _model.to(dtype=optimal_dtype)
                print(f"✓ Model converted to {optimal_dtype}")
        
        _initialization_state = InitializationState.READY.value
        _initialization_progress = "Model ready"
        _initialization_error = None
        print(f"✓ Model initialized successfully on {_device}")
        return _model
        
    except Exception as e:
        _initialization_state = InitializationState.ERROR.value
        _initialization_error = str(e)
        _initialization_progress = f"Failed: {str(e)}"
        print(f"✗ Failed to initialize model: {e}")
        raise e


def get_model():
    """Get the current model instance"""
    return _model


def get_device():
    """Get the current device"""
    return _device


def get_initialization_state():
    """Get the current initialization state"""
    return _initialization_state


def get_initialization_progress():
    """Get the current initialization progress message"""
    return _initialization_progress


def get_initialization_error():
    """Get the initialization error if any"""
    return _initialization_error


def is_ready():
    """Check if the model is ready for use"""
    return _initialization_state == InitializationState.READY.value and _model is not None


def is_initializing():
    """Check if the model is currently initializing"""
    return _initialization_state == InitializationState.INITIALIZING.value 


def is_multilingual():
    """Check if the loaded model supports multilingual generation"""
    return _is_multilingual


def get_supported_languages():
    """Get the dictionary of supported languages"""
    return _supported_languages.copy()


def supports_language(language_id: str):
    """Check if the model supports a specific language"""
    return language_id in _supported_languages


def get_model_info() -> Dict[str, Any]:
    """Get comprehensive model information"""
    return {
        "model_type": "multilingual" if _is_multilingual else "standard",
        "is_multilingual": _is_multilingual,
        "supported_languages": _supported_languages,
        "language_count": len(_supported_languages),
        "device": _device,
        "is_ready": is_ready(),
        "initialization_state": _initialization_state,
        "quantization": "int8" if Config.USE_INT8_QUANTIZATION else "none",
        "dtype": Config.MODEL_DTYPE
    }