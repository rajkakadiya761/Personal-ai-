"""
Pollinations.AI API Test Script
Tests all available endpoints for image, text, and audio generation.
"""

import requests
import json

BASE_IMAGE_URL = "https://image.pollinations.ai"
BASE_TEXT_URL = "https://text.pollinations.ai"


def test_image_models():
    """List available image models."""
    print("\n=== Image Models ===")
    response = requests.get(f"{BASE_IMAGE_URL}/models")
    if response.ok:
        models = response.json()
        print(f"Available models: {json.dumps(models, indent=2)}")
    else:
        print(f"Error: {response.status_code}")
    return response.ok


def test_text_models():
    """List available text models."""
    print("\n=== Text Models ===")
    response = requests.get(f"{BASE_TEXT_URL}/models")
    if response.ok:
        models = response.json()
        print(f"Available models: {json.dumps(models, indent=2)}")
    else:
        print(f"Error: {response.status_code}")
    return response.ok


def test_image_generation(prompt="a beautiful sunset over mountains"):
    """Generate an image from a text prompt."""
    print(f"\n=== Image Generation ===")
    print(f"Prompt: {prompt}")
    url = f"{BASE_IMAGE_URL}/prompt/{requests.utils.quote(prompt)}"
    print(f"URL: {url}")
    response = requests.get(url, stream=True)
    if response.ok:
        filename = "generated_image.png"
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Image saved to: {filename}")
    else:
        print(f"Error: {response.status_code}")
    return response.ok


def test_text_generation_get(prompt="Hello, tell me a short joke"):
    """Generate text using GET request."""
    print(f"\n=== Text Generation (GET) ===")
    print(f"Prompt: {prompt}")
    url = f"{BASE_TEXT_URL}/{requests.utils.quote(prompt)}"
    response = requests.get(url)
    if response.ok:
        print(f"Response: {response.text[:500]}")
    else:
        print(f"Error: {response.status_code}")
    return response.ok


def test_text_generation_post(prompt="Write a haiku about coding"):
    """Generate text using POST request (advanced)."""
    print(f"\n=== Text Generation (POST) ===")
    print(f"Prompt: {prompt}")
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "openai"
    }
    response = requests.post(BASE_TEXT_URL, json=payload)
    if response.ok:
        print(f"Response: {response.text[:500]}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return response.ok


def test_audio_generation(prompt="Say hello world", voice="alloy"):
    """Generate audio from text."""
    print(f"\n=== Audio Generation ===")
    print(f"Prompt: {prompt}, Voice: {voice}")
    url = f"{BASE_TEXT_URL}/{requests.utils.quote(prompt)}?model=openai-audio&voice={voice}"
    response = requests.get(url)
    if response.ok:
        filename = "generated_audio.mp3"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Audio saved to: {filename}")
    else:
        print(f"Error: {response.status_code}")
    return response.ok


def test_openai_compatible():
    """Test OpenAI compatible endpoint."""
    print(f"\n=== OpenAI Compatible Endpoint ===")
    payload = {
        "model": "openai",
        "messages": [{"role": "user", "content": "What is 2+2?"}]
    }
    response = requests.post(f"{BASE_TEXT_URL}/openai", json=payload)
    if response.ok:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)[:500]}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return response.ok


if __name__ == "__main__":
    print("=" * 50)
    print("Pollinations.AI API Test")
    print("=" * 50)
    
    results = {
        "Image Models": test_image_models(),
        "Text Models": test_text_models(),
        "Text Generation (GET)": test_text_generation_get(),
        "Text Generation (POST)": test_text_generation_post(),
        "Image Generation": test_image_generation(),
        "Audio Generation": test_audio_generation(),
        "OpenAI Compatible": test_openai_compatible(),
    }
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test}: {status}")
