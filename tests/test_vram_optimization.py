#!/usr/bin/env python3
"""
Test script to verify VRAM optimization and compare different configurations.

This script helps you:
1. Check current model configuration
2. Monitor VRAM usage
3. Compare different optimization settings
"""

import requests
import json
import time
import sys
from typing import Dict, Any


API_BASE_URL = "http://localhost:4123"
TEST_TEXT = "This is a test to measure VRAM usage with different configurations."


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def get_model_info() -> Dict[str, Any]:
    """Get current model configuration"""
    try:
        response = requests.get(f"{API_BASE_URL}/config")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting model info: {e}")
        sys.exit(1)


def get_memory_info() -> Dict[str, Any]:
    """Get current memory usage"""
    try:
        response = requests.get(f"{API_BASE_URL}/memory")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting memory info: {e}")
        sys.exit(1)


def test_tts_generation(text: str) -> bool:
    """Test TTS generation and return success status"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/audio/speech",
            json={"input": text},
            timeout=30
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ TTS generation failed: {e}")
        return False


def format_memory_mb(mb: float) -> str:
    """Format memory in MB with color coding"""
    if mb < 500:
        return f"🟢 {mb:.2f} MB"
    elif mb < 1000:
        return f"🟡 {mb:.2f} MB"
    else:
        return f"🔴 {mb:.2f} MB"


def main():
    print_section("VRAM Optimization Test Suite")
    
    # Check if API is running
    try:
        requests.get(f"{API_BASE_URL}/health")
        print("✅ API is running")
    except requests.exceptions.RequestException:
        print("❌ API is not running. Please start it first:")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 4123")
        sys.exit(1)
    
    # Get model configuration
    print_section("Current Model Configuration")
    config = get_model_info()
    
    print(f"📊 Model Type: {config.get('model_type', 'unknown')}")
    print(f"📊 Device: {config.get('device', 'unknown')}")
    print(f"📊 Quantization: {config.get('quantization', 'none')}")
    print(f"📊 Data Type: {config.get('dtype', 'unknown')}")
    print(f"📊 Multilingual: {config.get('USE_MULTILINGUAL_MODEL', False)}")
    
    # Get initial memory usage
    print_section("Initial Memory Usage")
    initial_memory = get_memory_info()
    
    if 'memory_info' in initial_memory:
        mem = initial_memory['memory_info']
        print(f"💾 CPU Memory: {format_memory_mb(mem.get('cpu_memory_mb', 0))}")
        
        if 'gpu_memory_allocated_mb' in mem:
            print(f"🎮 GPU Memory Allocated: {format_memory_mb(mem.get('gpu_memory_allocated_mb', 0))}")
            print(f"🎮 GPU Memory Reserved: {format_memory_mb(mem.get('gpu_memory_reserved_mb', 0))}")
            if 'gpu_memory_total_mb' in mem:
                total = mem.get('gpu_memory_total_mb', 0)
                allocated = mem.get('gpu_memory_allocated_mb', 0)
                percent = (allocated / total * 100) if total > 0 else 0
                print(f"🎮 GPU Memory Usage: {percent:.1f}% of {total:.0f} MB")
    
    # Test TTS generation
    print_section("Testing TTS Generation")
    print(f"📝 Generating speech for: '{TEST_TEXT[:50]}...'")
    
    success = test_tts_generation(TEST_TEXT)
    
    if not success:
        print("\n❌ TTS generation failed. Check the API logs for details.")
        sys.exit(1)
    
    print("✅ TTS generation successful!")
    
    # Get memory after generation
    print_section("Memory Usage After Generation")
    time.sleep(1)  # Wait for memory to settle
    final_memory = get_memory_info()
    
    if 'memory_info' in final_memory:
        mem = final_memory['memory_info']
        print(f"💾 CPU Memory: {format_memory_mb(mem.get('cpu_memory_mb', 0))}")
        
        if 'gpu_memory_allocated_mb' in mem:
            print(f"🎮 GPU Memory Allocated: {format_memory_mb(mem.get('gpu_memory_allocated_mb', 0))}")
            print(f"🎮 GPU Memory Reserved: {format_memory_mb(mem.get('gpu_memory_reserved_mb', 0))}")
            
            # Calculate change
            initial_gpu = initial_memory['memory_info'].get('gpu_memory_allocated_mb', 0)
            final_gpu = mem.get('gpu_memory_allocated_mb', 0)
            change = final_gpu - initial_gpu
            
            if change > 0:
                print(f"📈 GPU Memory Change: +{change:.2f} MB")
            elif change < 0:
                print(f"📉 GPU Memory Change: {change:.2f} MB")
            else:
                print(f"➡️  GPU Memory Change: {change:.2f} MB")
    
    # Optimization recommendations
    print_section("Optimization Recommendations")
    
    quantization = config.get('quantization', 'none')
    dtype = config.get('dtype', 'auto')
    device = config.get('device', 'unknown')
    
    if quantization == 'none':
        if device == 'cuda':
            print("💡 To reduce VRAM usage:")
            print("   1. Enable INT8 quantization (recommended):")
            print("      echo 'USE_INT8_QUANTIZATION=true' >> .env")
            print("   2. Or use float16 precision:")
            print("      echo 'MODEL_DTYPE=float16' >> .env")
            print("\n   Expected savings:")
            print("   - INT8: ~50% VRAM reduction (vs FP16)")
            print("   - Float16: ~50% VRAM reduction (vs FP32)")
        else:
            print("💡 INT8 quantization is recommended for CPU inference:")
            print("   echo 'USE_INT8_QUANTIZATION=true' >> .env")
    else:
        print("✅ INT8 quantization is already enabled!")
        print("   This provides maximum VRAM savings (~75% vs FP32)")
    
    print("\n📚 For more details, see: docs/VRAM_OPTIMIZATION.md")
    
    # Summary
    print_section("Test Summary")
    print("✅ All tests passed!")
    print(f"🔧 Current setup: {quantization} quantization, {dtype} dtype on {device}")
    
    if 'gpu_memory_allocated_mb' in final_memory.get('memory_info', {}):
        gpu_mem = final_memory['memory_info']['gpu_memory_allocated_mb']
        print(f"🎮 GPU VRAM Usage: {format_memory_mb(gpu_mem)}")
        
        # Provide context
        if quantization == 'int8':
            print("   (INT8 quantized - optimal for low VRAM)")
        elif dtype == 'float16':
            print("   (FP16 - balanced quality and VRAM)")
        else:
            print("   (FP32 - maximum quality, high VRAM)")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
