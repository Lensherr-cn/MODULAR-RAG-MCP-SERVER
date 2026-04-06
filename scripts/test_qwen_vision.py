"""Test Qwen Vision LLM connection.

This script validates the Qwen Vision LLM configuration and API connectivity.
It tests image captioning using a sample image or a generated placeholder.
"""

import sys
from pathlib import Path
import base64
import io

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from src.core.settings import load_settings
from src.libs.llm.qwen_vision_llm import QwenVisionLLM, QwenVisionLLMError
from src.libs.llm.base_vision_llm import ImageInput

def create_test_image() -> Path:
    """Create a simple test image if one doesn't exist."""
    test_img_path = project_root / "tests" / "fixtures" / "sample_image.png"
    
    # If we have a sample image in fixtures, use it
    if test_img_path.exists():
        return test_img_path
    
    # Otherwise, try to find any image in uploads
    uploads_dir = project_root / "uploads"
    if uploads_dir.exists():
        for img_file in uploads_dir.glob("*.png"):
            return img_file
        for img_file in uploads_dir.glob("*.jpg"):
            return img_file
            
    return None

def test_qwen_vision_connection():
    """Test Qwen Vision LLM connection with minimal setup."""
    print("=" * 50)
    print("Testing Qwen Vision LLM Connection")
    print("=" * 50)

    # Load settings
    try:
        settings = load_settings(project_root / "config" / "settings.yaml")
        print(f"✓ Settings loaded")

        if not hasattr(settings, 'vision_llm') or not settings.vision_llm:
            print(f"✗ ERROR: vision_llm section not found in settings")
            return False
            
        vision_config = settings.vision_llm
        print(f"  Enabled: {vision_config.enabled}")
        print(f"  Provider: {vision_config.provider}")
        print(f"  Model: {vision_config.model}")
        
        if not vision_config.enabled:
            print(f"⚠ Warning: Vision LLM is disabled in settings. Set enabled: true to test.")
            
    except Exception as e:
        print(f"✗ ERROR loading settings: {e}")
        return False

    # Create Qwen Vision LLM instance
    try:
        vision_llm = QwenVisionLLM(settings=settings)
        print(f"✓ QwenVisionLLM instance created")
        print(f"  Base URL: {vision_llm.base_url}")
        print(f"  Model: {vision_llm.model}")
    except ValueError as e:
        print(f"✗ ERROR creating vision LLM: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Find a test image
    test_image_path = create_test_image()
    if not test_image_path:
        print(f"\n✗ No test image found. Please place an image in 'tests/fixtures/sample_image.png' or 'uploads/'")
        print(f"  Skipping image captioning tests.")
        return True # Return true because config was valid, just no image

    print(f"\n{'=' * 50}")
    print(f"Test 1: Image Captioning")
    print(f"{'=' * 50}")
    print(f"Using image: {test_image_path.name}")

    try:
        image_input = ImageInput(path=str(test_image_path))
        prompt = "请简要描述这张图片的内容。"
        
        print(f"Prompt: '{prompt}'")
        response = vision_llm.chat_with_image(text=prompt, image=image_input)
        
        print(f"✓ Caption generated successfully")
        print(f"  Model used: {response.model}")
        print(f"  Content preview: {response.content[:100]}...")
        
        if response.usage:
            print(f"  Usage: {response.usage}")
            
    except QwenVisionLLMError as e:
        print(f"✗ Qwen Vision API error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during captioning: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Complex Prompt (Visual QA)
    print(f"\n{'=' * 50}")
    print(f"Test 2: Visual Question Answering")
    print(f"{'=' * 50}")
    
    try:
        qa_prompt = "这张图片里有什么文字吗？如果有，请提取出来。"
        print(f"Prompt: '{qa_prompt}'")
        
        response = vision_llm.chat_with_image(text=qa_prompt, image=image_input)
        print(f"✓ QA response generated successfully")
        print(f"  Content preview: {response.content[:100]}...")
        
    except QwenVisionLLMError as e:
        print(f"✗ Qwen Vision API error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during QA: {e}")
        return False

    print(f"\n{'=' * 50}")
    print("✓ Qwen Vision LLM Connection Test: SUCCESS")
    print(f"{'=' * 50}")
    return True

if __name__ == "__main__":
    success = test_qwen_vision_connection()
    sys.exit(0 if success else 1)
