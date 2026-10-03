# app.py
"""
NGEIS — Chinese to English Translator (Web App)
Runs on Hugging Face Spaces (Gradio SDK) and locally.
"""

import os
import gradio as gr
from translate_text import translate_text
from translate_audio import translate_audio

def translate_chinese_text(text):
    if not text or not text.strip():
        return "Please enter some Chinese text."
    try:
        return translate_text(text)
    except Exception as exc:
        return f"Error: {exc}"

def translate_chinese_audio(audio_path):
    if not audio_path:
        return "Please record or upload an audio file first.", ""
    try:
        result = translate_audio(audio_path)
        if isinstance(result, dict):
            return result.get("translation", ""), result.get("original", "")
        return str(result), ""
    except Exception as exc:
        return f"Error: {exc}", ""

with gr.Blocks(title="NGEIS — Chinese to English Translator") as demo:
    gr.Markdown(
        """
        # 🀄 NGEIS — Chinese → English Translator
        Translate Chinese text or spoken audio to English in one click.
        """
    )
    
    with gr.Tabs():
        with gr.Tab("📝 Text Translation"):
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(
                        label="Chinese Text",
                        placeholder="在这里输入中文… (Enter Chinese text here)",
                        lines=5,
                    )
                    text_btn = gr.Button("Translate Text", variant="primary")
                with gr.Column():
                    text_output = gr.Textbox(
                        label="English Translation",
                        lines=5,
                    )
            text_btn.click(fn=translate_chinese_text, inputs=text_input, outputs=text_output)
            
        with gr.Tab("🎙️ Audio & Speech Translation"):
            with gr.Row():
                with gr.Column():
                    audio_input = gr.Audio(
                        label="Record from Microphone or Upload Audio",
                        type="filepath",
                        sources=["microphone", "upload"],
                    )
                    audio_btn = gr.Button("Translate Audio", variant="primary")
                with gr.Column():
                    orig_output = gr.Textbox(
                        label="🎙️ Detected Chinese Speech",
                        lines=2,
                    )
                    trans_output = gr.Textbox(
                        label="🇬🇧 English Translation",
                        lines=3,
                    )
            audio_btn.click(fn=translate_chinese_audio, inputs=audio_input, outputs=[trans_output, orig_output])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860 if os.environ.get("SPACE_ID") else 5000))
    demo.launch(server_name="0.0.0.0", server_port=port)
