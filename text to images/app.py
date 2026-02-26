"""
Pollinations AI - Gemini-style Web Interface (FAST VERSION)
Flask app with streaming, voice input/output
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import requests
import os
import base64
from datetime import datetime
import json
import pyttsx3
import speech_recognition as sr
import threading
import queue

app = Flask(__name__)

# Text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 180)  # Speed
tts_queue = queue.Queue()

def tts_worker():
    """Background worker for text-to-speech."""
    while True:
        text = tts_queue.get()
        if text is None:
            break
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except:
            pass
        tts_queue.task_done()

# Start TTS worker thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

# Speech recognizer
recognizer = sr.Recognizer()

# API endpoints
IMAGE_API = "https://image.pollinations.ai"
TEXT_API = "https://text.pollinations.ai"

# Store chat history
chat_history = []

# Session for connection pooling (faster!)
session = requests.Session()
session.headers.update({'Connection': 'keep-alive'})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/models/text', methods=['GET'])
def get_text_models():
    """Get available text models."""
    try:
        response = session.get(f"{TEXT_API}/models", timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/models/image', methods=['GET'])
def get_image_models():
    """Get available image models."""
    try:
        response = session.get(f"{IMAGE_API}/models", timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Generate text response with streaming."""
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'openai-fast')  # Fast model by default
    
    try:
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": model,
            "stream": False  # Non-streaming for simplicity
        }
        
        # Add limited chat history for context
        if chat_history:
            payload["messages"] = chat_history[-6:] + payload["messages"]
        
        response = session.post(TEXT_API, json=payload, timeout=60)
        
        if response.ok:
            text = response.text
            # Store in history
            chat_history.append({"role": "user", "content": prompt})
            chat_history.append({"role": "assistant", "content": text})
            return jsonify({"response": text, "model": model})
        else:
            return jsonify({"error": f"API Error: {response.status_code}"}), 500
    except requests.Timeout:
        return jsonify({"error": "Request timed out. Try a faster model."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Generate text response with real streaming."""
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'openai-fast')
    
    def generate():
        try:
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "model": model,
                "stream": True
            }
            
            if chat_history:
                payload["messages"] = chat_history[-6:] + payload["messages"]
            
            with session.post(TEXT_API, json=payload, stream=True, timeout=60) as response:
                full_response = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        if line.startswith('data: '):
                            data_str = line[6:].strip()
                            if data_str == '[DONE]':
                                continue
                            try:
                                chunk_data = json.loads(data_str)
                                # Extract content from choices[0].delta.content
                                if chunk_data.get('choices') and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        full_response += content
                                        yield f"data: {json.dumps({'chunk': content})}\n\n"
                            except json.JSONDecodeError:
                                pass
                
                # Store in history after complete
                chat_history.append({"role": "user", "content": prompt})
                chat_history.append({"role": "assistant", "content": full_response})
                yield f"data: {json.dumps({'done': True})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    """Generate image from prompt (optimized)."""
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'turbo')  # Turbo is faster!
    width = data.get('width', 512)  # Smaller = faster
    height = data.get('height', 512)
    
    try:
        encoded_prompt = requests.utils.quote(prompt)
        # Add nologo and seed for consistency
        url = f"{IMAGE_API}/prompt/{encoded_prompt}?model={model}&width={width}&height={height}&nologo=true"
        
        response = session.get(url, timeout=120)
        
        if response.ok:
            # Convert to base64 for display
            img_base64 = base64.b64encode(response.content).decode('utf-8')
            
            # Save locally
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.png"
            filepath = os.path.join("static", "generated", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            return jsonify({
                "image": f"data:image/png;base64,{img_base64}",
                "filename": filename,
                "prompt": prompt,
                "model": model
            })
        else:
            return jsonify({"error": f"API Error: {response.status_code}"}), 500
    except requests.Timeout:
        return jsonify({"error": "Image generation timed out. Try smaller size or turbo model."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-audio', methods=['POST'])
def generate_audio():
    """Generate audio from text."""
    data = request.json
    prompt = data.get('prompt', '')
    voice = data.get('voice', 'alloy')
    
    try:
        encoded_prompt = requests.utils.quote(prompt)
        url = f"{TEXT_API}/{encoded_prompt}?model=openai-audio&voice={voice}"
        
        response = session.get(url, timeout=60)
        
        if response.ok:
            audio_base64 = base64.b64encode(response.content).decode('utf-8')
            return jsonify({
                "audio": f"data:audio/mp3;base64,{audio_base64}",
                "prompt": prompt,
                "voice": voice
            })
        else:
            return jsonify({"error": f"API Error: {response.status_code} - Audio requires seed tier"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear chat history."""
    global chat_history
    chat_history = []
    return jsonify({"status": "cleared"})


@app.route('/api/speak', methods=['POST'])
def speak_text():
    """Convert text to speech using pyttsx3."""
    data = request.json
    text = data.get('text', '')
    
    if text:
        tts_queue.put(text)
        return jsonify({"status": "speaking"})
    return jsonify({"error": "No text provided"}), 400


@app.route('/api/listen', methods=['POST'])
def listen_speech():
    """Convert speech to text using microphone."""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("🎤 Listening...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        
        text = recognizer.recognize_google(audio)
        print(f"📝 Recognized: {text}")
        return jsonify({"text": text})
    except sr.WaitTimeoutError:
        return jsonify({"error": "No speech detected. Try again."}), 400
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand audio. Try again."}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Speech service error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/voices', methods=['GET'])
def get_voices():
    """Get available TTS voices."""
    voices = tts_engine.getProperty('voices')
    voice_list = [{"id": v.id, "name": v.name} for v in voices]
    return jsonify(voice_list)


@app.route('/api/set-voice', methods=['POST'])
def set_voice():
    """Set TTS voice."""
    data = request.json
    voice_id = data.get('voice_id', '')
    if voice_id:
        tts_engine.setProperty('voice', voice_id)
        return jsonify({"status": "voice changed"})
    return jsonify({"error": "No voice_id provided"}), 400


if __name__ == '__main__':
    os.makedirs("static/generated", exist_ok=True)
    print("\n" + "="*50)
    print("🚀 POLLINATIONS AI - FAST VERSION")
    print("="*50)
    print("📍 Open http://localhost:5000")
    print("⚡ Using optimized settings for speed")
    print("="*50 + "\n")
    app.run(debug=True, port=5000, threaded=True)
