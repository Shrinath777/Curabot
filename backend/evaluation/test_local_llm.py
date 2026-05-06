"""Quick test of GPT4All local LLM integration."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gpt4all import GPT4All

print("Downloading & loading Llama 3 8B model (one-time, ~4GB)...")
print("This will take a few minutes on first run.\n")

model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf", allow_download=True)
print("Model loaded! Testing medical query...\n")

with model.chat_session():
    response = model.generate(
        'Extract symptoms from: "I have severe chest pain radiating to my left arm, sweating, and nausea." '
        'Respond in JSON: {"symptoms": [{"name": "...", "system": "..."}]}',
        max_tokens=512,
        temp=0.3
    )
    print("Response:", response)
    print("\nLocal LLM is working!")
