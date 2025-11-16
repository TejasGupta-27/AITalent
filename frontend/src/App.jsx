import React, { useState, useEffect } from 'react'
import axios from 'axios'
import ChatInterface from './components/ChatInterface'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [language, setLanguage] = useState('en')
  const [sessionId, setSessionId] = useState(null)
  const [weather, setWeather] = useState(null)
  const [chatHistory, setChatHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [translations, setTranslations] = useState({})

  // Load translations
  useEffect(() => {
    const loadTranslations = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/translations/${language}`)
        setTranslations(response.data)
      } catch (error) {
        console.error('Error loading translations:', error)
      }
    }
    loadTranslations()
  }, [language])

  const t = (key) => translations[key] || key

  const extractLocationFromMessage = (message) => {
    const locationPatterns = [
      /(?:in|at|for|to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)/i,
      /([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:で|の|に|を)/,
    ]
    
    const majorCities = [
      'tokyo', 'new york', 'london', 'paris', 'berlin', 'moscow', 'sydney',
      'melbourne', 'toronto', 'vancouver', 'mumbai', 'delhi', 'bangalore',
      'singapore', 'hong kong', 'seoul', 'beijing', 'shanghai', 'dubai',
      'istanbul', 'cairo', 'rio de janeiro', 'sao paulo', 'mexico city',
      'buenos aires', 'los angeles', 'chicago', 'san francisco', 'miami',
      'boston', 'seattle', 'denver', 'phoenix', 'dallas', 'houston',
      'osaka', 'kyoto', 'yokohama', 'nagoya', 'fukuoka', 'sapporo',
      'sendai', 'hiroshima', 'kobe'
    ]
    
    for (const pattern of locationPatterns) {
      const match = message.match(pattern)
      if (match) {
        const location = match[1] ? match[1].trim() : match[0].trim()
        const locationLower = location.toLowerCase()
        if (majorCities.includes(locationLower) || (location.length >= 2 && location[0] === location[0].toUpperCase())) {
          return location
        }
      }
    }
    return null
  }

  const handleSendMessage = async (query) => {
    if (!query || !query.trim()) return

    // Add user message to chat immediately
    const userMessage = { role: 'user', content: query, type: 'text' }
    setChatHistory(prev => [...prev, userMessage])

    // Check if we need to create a session first
    if (!sessionId) {
      setLoading(true)
      try {
        // Create a simple chat session without forcing weather
        const sessionResponse = await axios.post(
          `${API_BASE_URL}/api/session/create`,
          null,
          { params: { language } }
        )
        const newSessionId = sessionResponse.data.session_id
        setSessionId(newSessionId)

        // Now send the user's query - backend will fetch weather if needed
        await sendQueryToAPI(newSessionId, query)
      } catch (error) {
        console.error('Error creating session:', error)
        const errorMessage = {
          role: 'assistant',
          content: error.response?.data?.detail || 'Error creating chat session',
          type: 'error'
        }
        setChatHistory(prev => [...prev, errorMessage])
        setLoading(false)
      }
    } else {
      // Session exists, just send the query
      await sendQueryToAPI(sessionId, query)
    }
  }

  const sendQueryToAPI = async (sessionId, query) => {
    setLoading(true)
    try {
      const response = await axios.post(`${API_BASE_URL}/api/suggestions`, {
        session_id: sessionId,
        query,
        language
      })

      // Update weather if agent automatically fetched it for a different location
      if (response.data.weather_updated && response.data.weather) {
        setWeather(response.data.weather)
      }

      // Add assistant's response with weather data if available
      const assistantMessage = {
        role: 'assistant',
        content: response.data.suggestion,
        type: 'text'
      }

      // Attach weather data to the message if weather was updated
      if (response.data.weather_updated && response.data.weather) {
        assistantMessage.weather = response.data.weather
      }

      setChatHistory(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error getting suggestions:', error)
      const errorMessage = {
        role: 'assistant',
        content: error.response?.data?.detail || 'Error getting AI response',
        type: 'error'
      }
      setChatHistory(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleClearChat = () => {
    if (sessionId) {
      axios.delete(`${API_BASE_URL}/api/session/${sessionId}/chat`)
        .catch(error => {
          console.error('Error clearing chat:', error)
        })
    }
    setChatHistory([])
    setWeather(null)
    setSessionId(null)
  }

  return (
    <div className="app chat-app">
      <div className="chat-header">
        <div className="header-content">
          <h1>{t('AI Talent Force')}</h1>
          <p className="subtitle">{t('Weather with AI')}</p>
        </div>
        <div className="header-actions">
          <select
            className="language-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="en">🇬🇧 English</option>
            <option value="ja">🇯🇵 日本語</option>
          </select>
          {chatHistory.length > 0 && (
            <button className="clear-btn" onClick={handleClearChat}>
              {t('clear_chat')}
            </button>
          )}
        </div>
      </div>

      <div className="chat-container">
        <ChatInterface
          chatHistory={chatHistory}
          onSendMessage={handleSendMessage}
          placeholder={t('chat_input')}
          language={language}
          loading={loading}
          weather={weather}
          t={t}
        />
      </div>

      <footer className="chat-footer">
        <p>🌤️ Powered by WeatherAPI.com, Groq AI & Deepgram STT | Built with React & FastAPI</p>
      </footer>
    </div>
  )
}

export default App
