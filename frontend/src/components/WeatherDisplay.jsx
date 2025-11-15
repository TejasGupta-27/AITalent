import React from 'react'

function WeatherDisplay({ weather, compact = false }) {
  if (!weather) return null

  if (compact) {
    return (
      <div className="weather-display-compact">
        <div className="weather-compact-header">
          {weather.icon && (
            <img src={`https:${weather.icon}`} alt={weather.condition} className="weather-icon-small" />
          )}
          <div className="weather-compact-main">
            <div className="weather-temp">{weather.temperature.split(' / ')[0]}</div>
            <div className="weather-condition">{weather.condition}</div>
          </div>
        </div>
        <div className="weather-compact-details">
          <span>💧 {weather.humidity}</span>
          <span>💨 {weather.wind.split(' ')[0]} km/h</span>
          <span>☀️ UV {weather.uv_index}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="weather-display">
      <h3>🌡️ {weather.location}</h3>
      <p><strong>{weather.condition}</strong></p>
      {weather.icon && (
        <div className="weather-icon">
          <img src={`https:${weather.icon}`} alt={weather.condition} width="100" />
        </div>
      )}
      <div className="weather-details">
        <p><strong>Temperature:</strong> {weather.temperature}</p>
        <p><strong>Feels like:</strong> {weather.feels_like}</p>
        <p><strong>Humidity:</strong> {weather.humidity}</p>
        <p><strong>Wind:</strong> {weather.wind}</p>
        <p><strong>UV Index:</strong> {weather.uv_index}</p>
        <p><strong>Precipitation:</strong> {weather.precipitation}</p>
        <p><strong>Visibility:</strong> {weather.visibility}</p>
        <p><strong>Local Time:</strong> {weather.local_time}</p>
      </div>
    </div>
  )
}

export default WeatherDisplay


