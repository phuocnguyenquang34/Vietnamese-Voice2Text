# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from faster_whisper import WhisperModel
import yt_dlp as youtube_dl
from pydub import AudioSegment
from io import BytesIO
import os

app = Flask(_name_)

model_size = "small"
model = None
hallucinating_sen = ['Hãy subscribe cho kênh La La School Để không bỏ lỡ những video hấp dẫn', 'Hãy subscribe cho kênh Ghiền Mì Gõ Để không bỏ lỡ những video hấp dẫn', 'Hẹn Gặp Lại Các Bạn Trên Kênh Youtube Ngoại Truyện Với Nhạc', 'Các bạn hãy đăng kí cho kênh lalaschool Để không bỏ lỡ những video hấp dẫn','Đừng quên Like, Share và Đăng ký kênh để ủng hộ kênh của mình nhé!','Hẹn gặp lại các bạn trong những video tiếp theo.','Ghiền Mì Gõ Để không bỏ lỡ những video hấp dẫn']

@app.before_first_request
def load_model():
    global model
    model = WhisperModel(model_size, device="cuda", compute_type="float32")

@app.route('/')
def index():
    with open('index.html', 'r') as file:
        html_content = file.read()
    return html_content

@app.route('/transcribe-youtube', methods=['POST'])
def transcribe_youtube():
    yt_url = request.form['youtube_link']
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'yt',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([yt_url])
        except Exception as e:
            print(e)

    # Convert the audio data to 16kHz and 1 channel using Pydub
    sound = AudioSegment.from_file('yt.mp3')
    sound = sound.set_frame_rate(16000).set_channels(1)
    os.remove('yt.mp3')

    audio_path = './voice.wav'
    sound.export(audio_path, format='wav')
    segments, info = model.transcribe(audio_path, beam_size=5, language='vi')

    transcriptions = []
    for segment in segments:
        if segment.text.strip() in hallucinating_sen:
            continue
        transcription = '[' + '{:.2f}'.format(segment.start) + '] ' + segment.text
        transcriptions.append(transcription)

    formatted_transcriptions = "\n".join(transcriptions)
    formatted_transcriptions = formatted_transcriptions.encode().decode('utf-8')

    return formatted_transcriptions


@app.route('/transcribe-file', methods=['POST'])
def transcribe_file():
    # Get the uploaded audio file from the request
    audio_file = request.files['audio']

    # Convert the audio to 16kHz and 1 channel using Pydub
    sound = AudioSegment.from_file(audio_file)
    sound = sound.set_frame_rate(16000).set_channels(1)

    # Save the converted audio to a temporary file
    audio_path = './temp.wav'
    sound.export(audio_path, format='wav')

    segments, info = model.transcribe(audio_path, beam_size=5)

    transcriptions = []
    for segment in segments:
        transcription = segment.text

        transcriptions.append(transcription)

    return jsonify(transcriptions)

@app.route('/transcribe-audio', methods=['POST'])
def transcribe_audio():
    # Get the recorded audio file from the request
    audio_file = request.files['audio']

    # Convert the audio to 16kHz and 1 channel using Pydub
    sound = AudioSegment.from_file(audio_file)
    sound = sound.set_frame_rate(16000).set_channels(1)

    # Save the converted audio to a temporary file
    audio_path = './temp.wav'
    sound.export(audio_path, format='wav')

    segments, info = model.transcribe(audio_path, beam_size=5)

    transcriptions = []
    for segment in segments:
        transcription = segment.text

        transcriptions.append(transcription)

    return jsonify(transcriptions)

if _name_ == '_main_':
    app.run(host="127.0.0.1", port=5500, debug=True)
