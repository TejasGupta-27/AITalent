from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import requests
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Weather Activity Advisor API")

# CORS middleware
# Allow both development and production origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
)

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# In-memory storage (in production, use Redis or database)
sessions = {}


# Request/Response models
class WeatherRequest(BaseModel):
    location: str


class ChatRequest(BaseModel):
    session_id: str
    query: str
    language: str = "en"


class TranscriptionRequest(BaseModel):
    session_id: str
    language: str = "en"


class SessionRequest(BaseModel):
    session_id: Optional[str] = None


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


def fetch_weather(location: str):
    """Fetch weather data from WeatherAPI.com"""
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={location}&aqi=yes"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching weather: {str(e)}")


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
        'local_time': location['localtime'],
        'raw_data': weather_data  # Include raw data for AI context
    }
    return formatted


def transcribe_audio_deepgram(audio_bytes: bytes, audio_format: Optional[str] = None, language: str = "en"):
    """
    Transcribe audio using Deepgram API
    Supports 100+ audio formats: MP3, WAV, FLAC, M4A, OGG, OPUS, WEBM, etc.
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
        
        # Deepgram API parameters
        params = {
            "model": "nova-3",
            "detect_language": "true",
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
            raise HTTPException(status_code=response.status_code, detail=f"Deepgram API Error: {response.text}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")


def extract_location_from_query(query: str, language: str = "en") -> Optional[str]:
    """Extract location name from user query as fallback if tool calling doesn't work"""
    import re
    
    # Common location patterns - improved to capture city names better
    location_patterns = [
        r'(?:in|at|for|to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)(?:\?|\.|,|$|\s+(?:today|tomorrow|now|should|can))',
        r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:で|の|に|を)',
        r'(東京|大阪|京都|横浜|名古屋|福岡|札幌|仙台|広島|神戸)',  # Japanese city names
    ]
    
    # Known major cities for validation
    major_cities = [
        'tokyo', 'new york', 'london', 'paris', 'berlin', 'moscow', 'sydney',
        'melbourne', 'toronto', 'vancouver', 'mumbai', 'delhi', 'bangalore',
        'singapore', 'hong kong', 'seoul', 'beijing', 'shanghai', 'dubai',
        'istanbul', 'cairo', 'rio de janeiro', 'sao paulo', 'mexico city',
        'buenos aires', 'los angeles', 'chicago', 'san francisco', 'miami',
        'boston', 'seattle', 'denver', 'phoenix', 'dallas', 'houston',
        'osaka', 'kyoto', 'yokohama', 'nagoya', 'fukuoka', 'sapporo',
        'sendai', 'hiroshima', 'kobe'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            location = match.group(1).strip() if match.groups() else match.group(0).strip()
            # Filter out common non-location words
            location_lower = location.lower()
            if location_lower not in ['what', 'should', 'do', 'today', 'tomorrow', 'wear', 'activities', 'i', 'can']:
                # Check if it's a known city or looks like a city name (capitalized, 2+ chars)
                if len(location) >= 2 and (location_lower in major_cities or location[0].isupper()):
                    return location
    
    return None


def get_ai_suggestions(weather_data, user_query: Optional[str] = None, language: str = "en", auto_fetch_weather: bool = True, chat_history: Optional[List] = None):
    """Get AI-powered conversational responses with weather tool support"""

    # Define the weather tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather information for a specific location. Use this tool ONLY when the user asks about weather, activities, or things related to weather conditions in a specific location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city name or location to get weather for (e.g., 'Tokyo', 'New York', 'London')"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    # Build system prompt based on language
    if language == 'ja':
        system_prompt = """あなたは親切でフレンドリーな会話型AIアシスタントです。ユーザーと自然に会話し、質問に答えます。

あなたの特別な能力：
- 世界中の都市のリアルタイム天気情報を取得できます
- 天気に基づいて、アクティビティ、服装、外出のアイデアを提案できます

重要な指示：
1. **普通の会話**: 挨拶や一般的な質問には、自然に会話してください。天気に関係ない場合は、天気の話をしないでください。
2. **天気を使うタイミング**: ユーザーが天気、活動、服装、外出プランについて尋ねた時だけ、get_weatherツールを使用してください。
3. **簡潔に**: 短く、フレンドリーに、会話的に応答してください。

例：
- ユーザー: "こんにちは" → あなた: "こんにちは！何かお手伝いできることはありますか？"
- ユーザー: "東京の天気は？" → あなた: get_weatherツールを使用して天気を取得
- ユーザー: "今日何する？" → あなた: get_weatherツールを使用（場所がわかる場合）
-.英語で返信する必要があります。
"""

    else:
        system_prompt = """You are a friendly and helpful conversational AI assistant. You chat naturally with users and answer their questions.

Your special abilities:
- You can fetch real-time weather information for any city in the world
- You can provide activity, outfit, and outing suggestions based on weather

Important instructions:
1. **Normal conversation**: For greetings and general questions, respond naturally. Don't force weather into every conversation.
2. **When to use weather**: Only use the get_weather tool when users ask about weather, activities, what to wear, or plans that depend on weather conditions.
3. **Be concise**: Keep responses short, friendly, and conversational.
4. **You must reply in english.

Examples:
- User: "hi" → You: "Hi! How can I help you today?"
- User: "what's the weather in Tokyo?" → You: Use get_weather tool to fetch weather
- User: "what should I do today?" → You: Use get_weather tool if you know the location, or ask for their location"""
    
    # Build messages with chat history
    messages = [{"role": "system", "content": system_prompt}]

    # Add chat history for context
    if chat_history:
        for msg in chat_history[-10:]:  # Keep last 10 messages for context
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

    # Add current weather context if available (as system knowledge, not forcing it into conversation)
    weather_context = ""
    if weather_data:
        location = weather_data['location']
        current = weather_data['current']
        weather_context = f"""

[Available weather data for {location['name']}, {location['country']}:
Temperature: {current['temp_c']}°C (feels like {current['feelslike_c']}°C)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h
UV Index: {current['uv']}
Precipitation: {current['precip_mm']} mm
Local time: {location['localtime']}]
"""
        # Add weather context to system message if there's existing data
        messages[0]["content"] += weather_context

    # Add user's current query
    if user_query:
        messages.append({
            "role": "user",
            "content": user_query
        })
    else:
        # Initial suggestion when weather is first fetched
        if language == 'ja':
            messages.append({
                "role": "user",
                "content": "この天気に基づいて、簡単なアクティビティや服装の提案をしてください。"
            })
        else:
            messages.append({
                "role": "user",
                "content": "Based on this weather, give me some quick activity and outfit suggestions."
            })
    
    try:
        # Call Groq API with tool support
        max_iterations = 5  # Increased to allow for tool calls + response
        iteration = 0
        final_weather_data = weather_data
        tool_calls_executed = False  # Track if we've executed tools

        while iteration < max_iterations:
            try:
                # After executing tool calls once, disable tool_choice to force final response
                if auto_fetch_weather and not tool_calls_executed:
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.7,
                        max_tokens=1000
                    )
                else:
                    # Either auto_fetch disabled or we already executed tools - get final response
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1000
                    )
            except Exception as tool_error:
                # If tool calling fails, try without tools
                if "tool" in str(tool_error).lower() or "function" in str(tool_error).lower():
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    auto_fetch_weather = False  # Disable tool calling for this request
                else:
                    raise tool_error

            message = response.choices[0].message

            # Check if the model wants to call a tool
            if hasattr(message, 'tool_calls') and message.tool_calls and auto_fetch_weather and not tool_calls_executed:
                # Add assistant's message with tool calls
                messages.append(message)

                # Execute tool calls
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "get_weather":
                        import json
                        args = json.loads(tool_call.function.arguments)
                        location_name = args.get("location")

                        try:
                            # Fetch weather for the requested location
                            fetched_weather = fetch_weather(location_name)
                            final_weather_data = fetched_weather

                            # Format weather data for the model
                            loc = fetched_weather['location']
                            curr = fetched_weather['current']
                            weather_info = f"""
Weather in {loc['name']}, {loc['country']}:
- Temperature: {curr['temp_c']}°C (feels like {curr['feelslike_c']}°C)
- Condition: {curr['condition']['text']}
- Humidity: {curr['humidity']}%
- Wind: {curr['wind_kph']} km/h
- UV Index: {curr['uv']}
- Precipitation: {curr['precip_mm']} mm
- Local time: {loc['localtime']}
"""

                            # Add tool result to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": weather_info
                            })
                        except Exception as e:
                            # Add error to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": f"Error fetching weather for {location_name}: {str(e)}"
                            })

                tool_calls_executed = True  # Mark that we've executed tools
                iteration += 1
                continue  # Continue the loop to get the final response
            
            # No tool calls - check if we should extract location from query as fallback
            if not hasattr(message, 'tool_calls') or not message.tool_calls:
                # Try to extract location from query if no weather data or query mentions a location
                # Only do this once (iteration == 0) and if tools weren't already executed
                if user_query and iteration == 0 and not tool_calls_executed and (not weather_data):
                    extracted_location = extract_location_from_query(user_query, language)
                    if extracted_location:
                        try:
                            fetched_weather = fetch_weather(extracted_location)
                            final_weather_data = fetched_weather

                            # Update context with new weather
                            loc = fetched_weather['location']
                            curr = fetched_weather['current']
                            weather_info = f"""
Weather in {loc['name']}, {loc['country']}:
- Temperature: {curr['temp_c']}°C (feels like {curr['feelslike_c']}°C)
- Condition: {curr['condition']['text']}
- Humidity: {curr['humidity']}%
- Wind: {curr['wind_kph']} km/h
- UV Index: {curr['uv']}
- Precipitation: {curr['precip_mm']} mm
- Local time: {loc['localtime']}
"""

                            # Update the prompt with new weather and ask again
                            if language == 'ja':
                                updated_prompt = f"{weather_info}\n\nユーザーの質問: {user_query}\n\n上記の天気を考慮して、詳細な提案を提供してください。"
                            else:
                                updated_prompt = f"{weather_info}\n\nUser query: {user_query}\n\nProvide detailed suggestions considering the weather above."

                            messages = [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": updated_prompt}
                            ]
                            tool_calls_executed = True  # Mark as executed to prevent further iterations
                            iteration += 1
                            continue
                        except Exception:
                            pass  # Continue with original weather if extraction fails
            
            # No tool calls, return the final response
            final_response = message.content
            
            # Update weather context if we fetched new weather
            if final_weather_data and final_weather_data != weather_data:
                # Rebuild context with new weather
                loc = final_weather_data['location']
                curr = final_weather_data['current']
                weather_context = f"""
Current weather in {loc['name']}, {loc['country']}:
- Temperature: {curr['temp_c']}°C (feels like {curr['feelslike_c']}°C)
- Condition: {curr['condition']['text']}
- Humidity: {curr['humidity']}%
- Wind: {curr['wind_kph']} km/h
- UV Index: {curr['uv']}
- Precipitation: {curr['precip_mm']} mm
- Local time: {loc['localtime']}
"""
            
            return {
                "content": final_response,
                "weather_data": final_weather_data  # Return the weather data used (may be updated)
            }
        
        # If we hit max iterations, return error
        return {
            "content": "Error: Maximum iterations reached while processing your request.",
            "weather_data": final_weather_data
        }
        
    except Exception as e:
        return {
            "content": f"Error getting AI suggestions: {str(e)}",
            "weather_data": weather_data
        }


# API Endpoints

@app.get("/")
def root():
    return {"message": "Weather Activity Advisor API", "status": "running"}


@app.get("/api/translations/{language}")
def get_translations(language: str):
    """Get translations for a specific language"""
    if language not in translations:
        raise HTTPException(status_code=400, detail="Language not supported")
    return translations[language]


@app.post("/api/weather")
def get_weather(request: WeatherRequest):
    """Fetch weather data for a location"""
    weather_data = fetch_weather(request.location)
    formatted = format_weather_data(weather_data)
    return formatted


@app.post("/api/suggestions")
def get_suggestions(request: ChatRequest):
    """Get AI conversational responses with weather tool support"""
    session_id = request.session_id

    # Get or create session
    if session_id not in sessions:
        # Create a new session if it doesn't exist (allow chatting without weather initially)
        import uuid
        sessions[session_id] = {
            'weather_data': None,
            'chat_history': [],
            'language': request.language
        }

    session = sessions[session_id]
    weather_data = session.get('weather_data')
    chat_history = session.get('chat_history', [])

    # Get AI response with chat history context
    result = get_ai_suggestions(
        weather_data,
        request.query,
        request.language,
        auto_fetch_weather=True,
        chat_history=chat_history
    )

    # Update session with new weather data if agent fetched it
    if result.get('weather_data') and result['weather_data'] != weather_data:
        session['weather_data'] = result['weather_data']
        # Format the new weather for display
        session['formatted_weather'] = format_weather_data(result['weather_data'])

    suggestion = result['content']

    # Add to chat history
    if request.query:
        if 'chat_history' not in session:
            session['chat_history'] = []
        session['chat_history'].append({
            'role': 'user',
            'content': request.query
        })
        session['chat_history'].append({
            'role': 'assistant',
            'content': suggestion
        })

    # Return updated weather if it was fetched
    response = {
        "suggestion": suggestion,
        "chat_history": session.get('chat_history', [])
    }

    # Include updated weather if it changed
    if result.get('weather_data') and result['weather_data'] != weather_data:
        response['weather'] = format_weather_data(result['weather_data'])
        response['weather_updated'] = True

    return response


@app.post("/api/weather-with-suggestions")
def get_weather_with_suggestions(request: WeatherRequest, language: str = "en", session_id: Optional[str] = None):
    """Fetch weather and get initial AI suggestions"""
    import uuid

    weather_data = fetch_weather(request.location)
    formatted = format_weather_data(weather_data)

    # Create or update session
    if not session_id:
        session_id = str(uuid.uuid4())

    sessions[session_id] = {
        'weather_data': weather_data,
        'chat_history': [],
        'language': language
    }

    # Get initial suggestion with chat history
    result = get_ai_suggestions(
        weather_data,
        None,
        language,
        auto_fetch_weather=False,
        chat_history=[]
    )
    suggestion = result['content'] if isinstance(result, dict) else result

    return {
        "session_id": session_id,
        "weather": formatted,
        "suggestion": suggestion
    }


@app.post("/api/session/create")
def create_session(language: str = "en"):
    """Create a new chat session without requiring weather data"""
    import uuid

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'weather_data': None,
        'chat_history': [],
        'language': language
    }

    return {
        "session_id": session_id,
        "message": "Session created successfully. You can start chatting!"
    }


@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("en"),
    session_id: Optional[str] = Form(None)
):
    """Transcribe uploaded audio file"""
    audio_bytes = await file.read()
    file_format = file.filename.split('.')[-1].lower() if file.filename else None

    transcript = transcribe_audio_deepgram(audio_bytes, file_format, language)

    if transcript:
        return {"transcript": transcript, "success": True}
    else:
        return {"transcript": None, "success": False, "message": "No speech detected"}


@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    """Get session data"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@app.delete("/api/session/{session_id}/chat")
def clear_chat(session_id: str):
    """Clear chat history for a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    sessions[session_id]['chat_history'] = []
    return {"message": "Chat history cleared"}


@app.get("/api/examples/{language}")
def get_examples(language: str):
    """Get example prompts for a language"""
    if language == 'ja':
        return {
            "examples": [
                "今日は何を着ればいいですか？",
                "外出するのに良い時間は？",
                "雨が降るので、室内でできることは？",
                "この天気でおすすめのスポーツは？"
            ]
        }
    else:
        return {
            "examples": [
                "What should I wear today?",
                "Best time to go outside?",
                "Indoor activities for this weather?",
                "Recommended sports for this weather?"
            ]
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

