import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import WeatherDisplay from './WeatherDisplay'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function ChatInterface({ chatHistory, onSendMessage, placeholder, language, loading, weather, t }) {
  const [input, setInput] = useState('')
  const [audioBlob, setAudioBlob] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState(null)
  const [transcribing, setTranscribing] = useState(false)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !loading) {
      onSendMessage(input)
      setInput('')
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      const chunks = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data)
        }
      }

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' })
        setAudioBlob(blob)
        stream.getTracks().forEach(track => track.stop())
        // Auto-transcribe after recording stops
        transcribeAudio(blob, 'wav')
      }

      recorder.start()
      setMediaRecorder(recorder)
      setIsRecording(true)
    } catch (error) {
      console.error('Error starting recording:', error)
      alert('Error accessing microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop()
      setIsRecording(false)
    }
  }

  const transcribeAudio = async (audioBlob, format = 'wav') => {
    setTranscribing(true)
    try {
      const formData = new FormData()
      formData.append('file', audioBlob, `audio.${format}`)
      formData.append('language', language)

      const response = await axios.post(
        `${API_BASE_URL}/api/transcribe`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      if (response.data.success && response.data.transcript) {
        // Send transcribed text as message
        onSendMessage(response.data.transcript)
        setAudioBlob(null)
      } else {
        alert('No speech detected in the audio.')
      }
    } catch (error) {
      console.error('Error transcribing audio:', error)
      alert(error.response?.data?.detail || 'Error transcribing audio')
    } finally {
      setTranscribing(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (file) {
      const format = file.name.split('.').pop().toLowerCase()
      await transcribeAudio(file, format)
      e.target.value = '' // Reset input
    }
  }

  const renderMessage = (message, index) => {
    if (message.type === 'weather' && message.weather) {
      return (
        <div key={index} className="chat-message weather-message">
          <div className="message-header">
            <strong>🌤️ {message.content}</strong>
          </div>
          <WeatherDisplay weather={message.weather} compact={true} />
        </div>
      )
    }

    return (
      <div
        key={index}
        className={`chat-message ${
          message.role === 'user' ? 'user-message' : 'assistant-message'
        }`}
      >
        <div className="message-content">
          {message.role === 'user' ? (
            <div className="user-bubble">
              <span className="message-text">{message.content}</span>
            </div>
          ) : (
            <>
              <div className="assistant-bubble">
                <div className="message-text" dangerouslySetInnerHTML={{ 
                  __html: message.content.replace(/\n/g, '<br>') 
                }} />
              </div>
              {message.weather && (
                <div className="weather-in-message">
                  <WeatherDisplay weather={message.weather} compact={true} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="chat-interface-full">
      <div className="chat-messages-container">
        {chatHistory.length === 0 ? (
          <div className="welcome-message">
            <h2>👋 {language === 'ja' ? 'ようこそ！' : 'Welcome!'}</h2>
            <p>{language === 'ja' 
              ? '天気に基づいたアクティビティ提案を取得するには、メッセージを送信するか音声で話しかけてください。'
              : 'Send a message or use voice input to get weather-based activity suggestions.'}</p>
            <div className="example-prompts">
              <p className="examples-title">{t('example_prompts')}</p>
              <div className="example-buttons">
                <button onClick={() => onSendMessage('What should I do today in Tokyo?')}>
                  What should I do today in Tokyo?
                </button>
                <button onClick={() => onSendMessage('What should I wear today?')}>
                  What should I wear today?
                </button>
                <button onClick={() => onSendMessage('Best time to go outside?')}>
                  Best time to go outside?
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            {chatHistory.map((message, index) => renderMessage(message, index))}
            {loading && (
              <div className="chat-message assistant-message">
                <div className="assistant-bubble">
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <div className="input-actions">
          <button
            className={`record-btn ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={loading || transcribing}
            title={isRecording ? 'Stop Recording' : 'Start Recording'}
          >
            {isRecording ? '⏹️' : '🎤'}
          </button>
          <button
            className="upload-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading || transcribing}
            title="Upload Audio File"
          >
            📎
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </div>
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            disabled={loading || transcribing}
            className="chat-input"
          />
          <button 
            type="submit" 
            disabled={loading || transcribing || !input.trim()}
            className="send-btn"
          >
            {transcribing ? '⏳' : '➤'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default ChatInterface
