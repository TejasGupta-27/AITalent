import streamlit as st
import requests
from groq import Groq
import json
from datetime import datetime
import os
from io import BytesIO
import tempfile
from dotenv import load_dotenv

load_dotenv()


# Page configuration
st.set_page_config(
    page_title="Weather Activity Advisor | 天気アクティビティアドバイザー",
    page_icon="🌤️",
    layout="wide"
)


# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")


# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)


# Initialize session state
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_weather' not in st.session_state:
    st.session_state.current_weather = None


# Translations
translations = {
    'en': {
        'title': '🌤️ Weather Activity Advisor',
        'subtitle': 'Get personalized activity suggestions based on real-time weather',
        'location_input': 'Enter your location (city name)',
        'location_placeholder': 'e.g., Tokyo, New York, London',
        'get_weather': 'Get Weather & Suggestions',
        'voice_input': '🎤 Voice Input',
        'chat_input': 'Ask me anything about activities, fashion, or plans...',
        'example_prompts': 'Example Prompts:',
        'weather_info': 'Current Weather Information',
        'suggestions': 'AI Suggestions',
        'chat_history': 'Chat History',
        'clear_chat': 'Clear Chat',
        'error': 'Error',
        'weather_fetch_error': 'Could not fetch weather data. Please check the location.',
        'language': 'Language',
    },
    'ja': {
        'title': '🌤️ 天気アクティビティアドバイザー',
        'subtitle': 'リアルタイムの天気に基づいてパーソナライズされたアクティビティ提案を取得',
        'location_input': '場所を入力してください（都市名）',
        'location_placeholder': '例：東京、大阪、札幌',
        'get_weather': '天気と提案を取得',
        'voice_input': '🎤 音声入力',
        'chat_input': 'アクティビティ、ファッション、プランについて何でも聞いてください...',
        'example_prompts': '例のプロンプト：',
        'weather_info': '現在の気象情報',
        'suggestions': 'AI提案',
        'chat_history': 'チャット履歴',
        'clear_chat': 'チャットをクリア',
        'error': 'エラー',
        'weather_fetch_error': '天気データを取得できませんでした。場所を確認してください。',
        'language': '言語',
    }
}


def t(key):
    """Get translation for current language"""
    return translations[st.session_state.language].get(key, key)


def fetch_weather(location):
    """Fetch weather data from WeatherAPI.com"""
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={location}&aqi=yes"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"{t('error')}: {str(e)}")
        return None


def format_weather_data(weather_data):
    """Format weather data for display"""
    if not weather_data:
        return None
    
    location = weather_data['location']
    current = weather_data['current']
    
    formatted = {
        'location': f"{location['name']}, {location['country']}",
        'temperature': f"{current['temp_c']}°C / {current['temp_f']}°F",
        'condition': current['condition']['text'],
        'icon': current['condition']['icon'],
        'feels_like': f"{current['feelslike_c']}°C",
        'humidity': f"{current['humidity']}%",
        'wind': f"{current['wind_kph']} km/h {current['wind_dir']}",
        'precipitation': f"{current['precip_mm']} mm",
        'uv_index': current['uv'],
        'visibility': f"{current['vis_km']} km",
        'local_time': location['localtime']
    }
    return formatted


def transcribe_audio_deepgram(audio_bytes, audio_format=None):
    """
    Transcribe audio using Deepgram API
    Supports 100+ audio formats: MP3, WAV, FLAC, M4A, OGG, OPUS, WEBM, etc.
    
    Args:
        audio_bytes: Raw audio bytes
        audio_format: Optional format like 'mp3', 'wav', 'flac', 'm4a', etc.
    
    Returns:
        str: Transcribed text or error message
    """
    try:
        url = "https://api.deepgram.com/v1/listen"
        
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
        }
        
        # Content type mapping for different audio formats
        content_type_map = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'flac': 'audio/flac',
            'm4a': 'audio/mp4',
            'ogg': 'audio/ogg',
            'opus': 'audio/opus',
            'webm': 'audio/webm',
        }
        
        # Set content type based on format
        if audio_format:
            headers["Content-Type"] = content_type_map.get(audio_format.lower(), 'audio/wav')
        else:
            headers["Content-Type"] = "audio/wav"
        
        # Set language based on session state
        language = "ja" if st.session_state.language == 'ja' else "en"
        
        # Deepgram API parameters
        params = {
            "model": "nova-2",
            "language": language,
            "smart_format": "true",
            "punctuate": "true"
        }
        
        # Make the API request
        response = requests.post(url, headers=headers, params=params, data=audio_bytes)
        
        if response.status_code == 200:
            result = response.json()
            transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
            return transcript if transcript else None
        else:
            st.error(f"Deepgram API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return None


def get_ai_suggestions(weather_data, user_query=None):
    """Get AI-powered suggestions based on weather"""
    if not weather_data:
        return "Weather data not available."
    
    location = weather_data['location']
    current = weather_data['current']
    
    # Create context for AI
    weather_context = f"""
Current weather in {location['name']}, {location['country']}:
- Temperature: {current['temp_c']}°C (feels like {current['feelslike_c']}°C)
- Condition: {current['condition']['text']}
- Humidity: {current['humidity']}%
- Wind: {current['wind_kph']} km/h
- UV Index: {current['uv']}
- Precipitation: {current['precip_mm']} mm
- Local time: {location['localtime']}
"""
    
    # Build prompt based on language
    if st.session_state.language == 'ja':
        system_prompt = """あなたは親切な天気アドバイザーです。現在の天気に基づいて、アクティビティ、外出、ファッション、音楽、スポーツなどの提案を提供します。
提案は具体的で、実用的で、天気条件に適切なものにしてください。"""
        
        if user_query:
            prompt = f"{weather_context}\n\nユーザーの質問: {user_query}\n\n上記の天気を考慮して、詳細な提案を提供してください。"
        else:
            prompt = f"{weather_context}\n\nこの天気に基づいて、今日のアクティビティ、服装、外出のアイデアを提案してください。"
    else:
        system_prompt = """You are a helpful weather advisor. Based on current weather conditions, you provide suggestions for activities, outings, fashion, music, sports, and more.
Make your suggestions specific, practical, and appropriate for the weather conditions."""
        
        if user_query:
            prompt = f"{weather_context}\n\nUser query: {user_query}\n\nProvide detailed suggestions considering the weather above."
        else:
            prompt = f"{weather_context}\n\nBased on this weather, suggest activities, outfit ideas, and outing recommendations for today."
    
    try:
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting AI suggestions: {str(e)}"


# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }

    /* Weather card */
    .weather-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }

    /* Suggestion card background */
    .suggestion-card {
        background: #eef2ff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        color: #000;
    }

    /* Chat messages */
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    /* User message (light blue) */
    .user-message {
        background: #e3f2fd;
        margin-left: 2rem;
        color: #000;
    }

    /* Assistant message (light gray) */
    .assistant-message {
        background: #f0f0f5;
        margin-right: 2rem;
        color: #000;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# Header
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f"""
    <div class="main-header">
        <h1>{t('title')}</h1>
        <p>{t('subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    language = st.selectbox(
        t('language'),
        options=['en', 'ja'],
        format_func=lambda x: '🇬🇧 English' if x == 'en' else '🇯🇵 日本語',
        key='language_selector'
    )
    if language != st.session_state.language:
        st.session_state.language = language
        st.rerun()


# Sidebar for weather input
with st.sidebar:
    st.header("⚙️ " + t('weather_info'))
    
    location = st.text_input(
        t('location_input'),
        placeholder=t('location_placeholder'),
        value="Tokyo" if st.session_state.language == 'ja' else "New York"
    )
    
    if st.button(t('get_weather'), type="primary"):
        with st.spinner('🌍 Fetching weather data...'):
            weather_data = fetch_weather(location)
            if weather_data:
                st.session_state.current_weather = weather_data
                st.success("✅ Weather data loaded!")
                st.rerun()
    
    st.markdown("---")
    
    # Voice input section
    st.subheader(t('voice_input'))
    st.markdown("""
    <div style="background: #f0f2f6; padding: 1rem; border-radius: 8px;">
        <p style="margin: 0; font-size: 0.9em;">
            🎤 Record audio and it will be transcribed using Deepgram AI.
        </p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.8em; color: #666;">
            音声を録音するとDeepgram AIで自動的に文字起こしされます
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Option 1: Using Streamlit's built-in audio input (NO FFmpeg needed)
    st.markdown("**Option 1: Built-in Recorder (Recommended)**")
    audio_bytes = st.audio_input(
        label="🎤 Click to record / クリックして録音",
        label_visibility="collapsed"
    )
    
    if audio_bytes is not None:
        st.audio(audio_bytes, format="audio/wav")
        
        if st.button("🔄 Transcribe Recorded Audio / 録音を文字起こし", key="transcribe_builtin"):
            with st.spinner("🎯 Transcribing with Deepgram... / Deepgramで文字起こし中..."):
                text = transcribe_audio_deepgram(audio_bytes)
                
                if text:
                    st.session_state.voice_transcription = text
                    st.success(f"✅ Transcribed: {text}")
                else:
                    st.warning("⚠️ No speech detected in the audio.")
    
    st.markdown("---")
    
    # Option 2: Upload audio file (supports MP3, WAV, FLAC, M4A, OGG, etc.)
    st.markdown("**Option 2: Upload Audio File**")
    st.text("Supports: MP3, WAV, FLAC, M4A, OGG, OPUS, WEBM, and 100+ more formats")
    
    uploaded_file = st.file_uploader(
        label="Upload audio file / オーディオファイルをアップロード",
        type=['mp3', 'wav', 'flac', 'm4a', 'ogg', 'opus', 'webm', 'aac', 'pcm'],
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # Display audio player
        st.audio(uploaded_file)
        
        # Get file format from extension
        file_format = uploaded_file.name.split('.')[-1].lower()
        
        if st.button("🔄 Transcribe Uploaded File / ファイルを文字起こし", key="transcribe_upload"):
            with st.spinner(f"🎯 Transcribing {file_format.upper()} with Deepgram... / Deepgramで文字起こし中..."):
                audio_bytes = uploaded_file.read()
                text = transcribe_audio_deepgram(audio_bytes, audio_format=file_format)
                
                if text:
                    st.session_state.voice_transcription = text
                    st.success(f"✅ Transcribed: {text}")
                else:
                    st.warning("⚠️ No speech detected in the audio.")
    
    st.markdown("---")
    
    # Display transcribed text
    if 'voice_transcription' in st.session_state and st.session_state.voice_transcription:
        st.info(f"📝 Transcribed text: {st.session_state.voice_transcription}")
        if st.button("✅ Use this query / このクエリを使用"):
            st.session_state.pending_query = st.session_state.voice_transcription
            st.session_state.voice_transcription = ""
            st.rerun()
    
    st.markdown("---")
    
    # Example prompts
    st.subheader(t('example_prompts'))
    if st.session_state.language == 'ja':
        examples = [
            "今日は何を着ればいいですか？",
            "外出するのに良い時間は？",
            "雨が降るので、室内でできることは？",
            "この天気でおすすめのスポーツは？"
        ]
    else:
        examples = [
            "What should I wear today?",
            "Best time to go outside?",
            "Indoor activities for this weather?",
            "Recommended sports for this weather?"
        ]
    
    for example in examples:
        if st.button(example, key=f"example_{example}"):
            st.session_state.example_query = example


# Main content area
if st.session_state.current_weather:
    weather_formatted = format_weather_data(st.session_state.current_weather)
    
    # Display weather information
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🌡️ " + weather_formatted['location'])
        st.markdown(f"**{weather_formatted['condition']}**")
        st.image(f"https:{weather_formatted['icon']}", width=100)
        st.markdown(f"**Temperature:** {weather_formatted['temperature']}")
        st.markdown(f"**Feels like:** {weather_formatted['feels_like']}")
        st.markdown(f"**Humidity:** {weather_formatted['humidity']}")
        st.markdown(f"**Wind:** {weather_formatted['wind']}")
        st.markdown(f"**UV Index:** {weather_formatted['uv_index']}")
    
    with col2:
        st.markdown("### " + t('suggestions'))
        
        # Get initial suggestions if not already done
        if 'initial_suggestion' not in st.session_state or st.session_state.get('weather_changed'):
            with st.spinner('🤖 Generating AI suggestions...'):
                suggestion = get_ai_suggestions(st.session_state.current_weather)
                st.session_state.initial_suggestion = suggestion
                st.session_state.weather_changed = False
        
        st.markdown(f"""
        <div class="suggestion-card">
            {st.session_state.initial_suggestion}
        </div>
        """, unsafe_allow_html=True)

    # Chat interface
    st.markdown("---")
    st.markdown("### 💬 " + t('chat_history'))
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong> {message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant:</strong> {message['content']}
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input(t('chat_input'))
    
    # Handle pending query from voice input
    if 'pending_query' in st.session_state and st.session_state.pending_query:
        user_input = st.session_state.pending_query
        st.session_state.pending_query = None
    
    # Handle example query
    if 'example_query' in st.session_state:
        user_input = st.session_state.example_query
        del st.session_state.example_query
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get AI response
        with st.spinner('🤖 Thinking...'):
            response = get_ai_suggestions(st.session_state.current_weather, user_input)
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
        
        st.rerun()
    
    # Clear chat button
    if st.button(t('clear_chat')):
        st.session_state.chat_history = []
        st.rerun()

else:
    # Welcome screen
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <h2>👋 Welcome! / ようこそ！</h2>
        <p style="font-size: 1.2em;">
            Enter a location in the sidebar to get started<br>
            サイドバーに場所を入力して開始してください
        </p>
        <p style="margin-top: 2rem; color: #666;">
            🎤 Use Deepgram-powered voice input for hands-free interaction<br>
            🌤️ Get real-time weather information<br>
            🤖 Receive AI-powered activity suggestions<br>
            🌏 Support for English and Japanese
        </p>
    </div>
    """, unsafe_allow_html=True)


# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🌤️ Powered by WeatherAPI.com, Groq AI & Deepgram STT | Built with Streamlit</p>
    <p style="font-size: 0.9em;">
        This chatbot provides weather-based activity suggestions using AI with Deepgram voice transcription (100+ audio formats supported)<br>
        このチャットボットはAIとDeepgram音声認識を使用して天気ベースのアクティビティ提案を提供します
    </p>
</div>
""", unsafe_allow_html=True)
