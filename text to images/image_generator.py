"""
Simple Text-to-Image Generator using Pollinations.AI
"""

import requests
import os
from datetime import datetime


def generate_image(prompt, model="flux", width=1024, height=1024, seed=None):
    """Generate an image from a text prompt."""
    base_url = "https://image.pollinations.ai/prompt"
    encoded_prompt = requests.utils.quote(prompt)
    
    url = f"{base_url}/{encoded_prompt}?model={model}&width={width}&height={height}"
    if seed:
        url += f"&seed={seed}"
    
    print(f"\n🎨 Generating image...")
    print(f"Prompt: {prompt}")
    print(f"Model: {model} | Size: {width}x{height}")
    
    response = requests.get(url, stream=True)
    
    if response.ok:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.png"
        
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        full_path = os.path.abspath(filename)
        print(f"✅ Image saved: {full_path}")
        return filename
    else:
        print(f"❌ Error: {response.status_code}")
        return None


def main():
    print("=" * 50)
    print("🖼️  Pollinations.AI Image Generator")
    print("=" * 50)
    print("\nAvailable models: flux, turbo, gptimage")
    print("Type 'quit' to exit\n")
    
    while True:
        prompt = input("\nEnter your prompt: ").strip()
        
        if prompt.lower() == 'quit':
            print("Goodbye!")
            break
        
        if not prompt:
            print("Please enter a prompt!")
            continue
        
        model = input("Model (flux/turbo/gptimage) [flux]: ").strip() or "flux"
        
        generate_image(prompt, model=model)


if __name__ == "__main__":
    main()
