import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { BrowserRouter as Router, Routes, Route, useSearchParams, useNavigate } from 'react-router'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format, subDays, parseISO } from 'date-fns'
import axios from 'axios'
import { useWebSocket } from './useWebSocket'
import './App.css'

// Types based on the OpenAPI spec
interface WeatherData {
  sensor: string
  timestamp: string
  temperature: number
  humidity: number
  pressure: number
  altitude?: number | null
  rssi?: number | null
  retry_count?: number | null
}

interface SensorStatistics {
  total_readings: number
  first_reading: string | null
  last_reading: string | null
  last_24h_readings: number
  average_temperature: number | null
  average_humidity: number | null
  average_pressure: number | null
  average_rssi: number | null
}

interface Sensor {
  name: string
  created: string
  modified: string
  statistics: SensorStatistics
}

// Additional interfaces for API operations
interface SensorCreate {
  name: string
}

interface SensorUpdate {
  name?: string | null
}

interface WeatherDataRequest {
  timestamp: string | number
  temperature: number
  humidity: number
  pressure: number
  altitude?: number | null
  rssi?: number | null
  retry_count?: number | null
}

// Main Weather Dashboard Component
function WeatherDashboard() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  
  // Get initial state from URL parameters
  const getInitialSensors = (): string[] => {
    const sensorsParam = searchParams.get('sensors')
    return sensorsParam ? sensorsParam.split(',').filter(s => s.trim()) : []
  }
  
  const getInitialDateRange = () => {
    const startParam = searchParams.get('start')
    const endParam = searchParams.get('end')
    
    if (startParam && endParam) {
      return {
        start: startParam,
        end: endParam
      }
    }
    
    // Default to last 7 days
    return {
      start: format(subDays(new Date(), 7), "yyyy-MM-dd'T'HH:mm"),
      end: format(new Date(), "yyyy-MM-dd'T'HH:mm")
    }
  }

  const [sensors, setSensors] = useState<Sensor[]>([])
  const [selectedSensors, setSelectedSensors] = useState<string[]>(getInitialSensors)
  const [weatherData, setWeatherData] = useState<WeatherData[]>([])
  const [selectedSensorInfo, setSelectedSensorInfo] = useState<Sensor | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sensorInput, setSensorInput] = useState<string>('')
  const [dateRange, setDateRange] = useState(getInitialDateRange)
  const [urlUpdating, setUrlUpdating] = useState(false)
  const [useWebSocketMode, setUseWebSocketMode] = useState(true)

  // Refs to access current state values
  const selectedSensorsRef = useRef(selectedSensors)
  const dateRangeRef = useRef(dateRange)
  const isUpdatingFromStateRef = useRef(false)

  // Generate WebSocket URL based on selected sensors
  const wsUrl = useMemo(() => {
    if (!useWebSocketMode || selectedSensors.length === 0) return null

    // Use wss:// for HTTPS, ws:// for HTTP
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host

    // For now, connect to first sensor only (can be extended to handle multiple)
    if (selectedSensors.length === 1) {
      return `${protocol}//${host}/ws/sensors/${selectedSensors[0]}/weather`
    }

    // For multiple sensors, use the general weather endpoint
    return `${protocol}//${host}/ws/weather`
  }, [selectedSensors, useWebSocketMode])

  // WebSocket connection for real-time updates
  const { isConnected: wsConnected, error: wsError, reconnectAttempts } = useWebSocket(wsUrl, {
    onMessage: (data: WeatherData) => {
      console.log('WebSocket: New weather data received', data)

      // Only add data if it matches our selected sensors
      if (selectedSensors.includes(data.sensor)) {
        setWeatherData((prev) => {
          // Check if this exact data point already exists
          const exists = prev.some(
            (item) => item.sensor === data.sensor && item.timestamp === data.timestamp
          )

          if (exists) {
            return prev
          }

          // Add new data and sort by timestamp
          const newData = [...prev, data]
          newData.sort((a, b) => parseISO(a.timestamp).getTime() - parseISO(b.timestamp).getTime())
          return newData
        })
      }
    },
    onError: (event) => {
      console.error('WebSocket error:', event)
      setError('WebSocket connection error')
    },
    maxReconnectAttempts: 10,
    reconnectInterval: 3000,
  })

  // Update refs when state changes
  useEffect(() => {
    selectedSensorsRef.current = selectedSensors
  }, [selectedSensors])

  useEffect(() => {
    dateRangeRef.current = dateRange
  }, [dateRange])

  // Listen for URL changes (back/forward navigation)
  useEffect(() => {
    // Skip sync if we're in the middle of updating URL from state changes
    if (isUpdatingFromStateRef.current) {
      console.log('Skipping URL sync - state is being updated')
      return
    }

    const syncStateFromURL = async () => {
      const urlSensors = getInitialSensors()
      const urlDateRange = getInitialDateRange()

      // Use refs to get current state values
      const currentSelectedSensors = selectedSensorsRef.current
      const currentDateRange = dateRangeRef.current

      // Only update if there are actual changes
      if (JSON.stringify(urlSensors) !== JSON.stringify(currentSelectedSensors) ||
          JSON.stringify(urlDateRange) !== JSON.stringify(currentDateRange)) {

        console.log('URL sync: URL state differs from component state')
        console.log('URL sensors:', urlSensors, 'Current sensors:', currentSelectedSensors)

        setUrlUpdating(true)

        // Update sensors if needed
        if (JSON.stringify(urlSensors) !== JSON.stringify(currentSelectedSensors)) {
          setSelectedSensors(urlSensors)

          // Fetch sensor info for new sensors
          const newSensors: Sensor[] = []
          for (const sensorName of urlSensors) {
            const sensor = await fetchSensorByName(sensorName)
            if (sensor) {
              newSensors.push(sensor)
            }
          }
          setSensors(newSensors)

          // Set selected sensor info to first one
          if (newSensors.length > 0) {
            setSelectedSensorInfo(newSensors[0])
          } else {
            setSelectedSensorInfo(null)
          }
        }

        // Update date range if needed
        if (JSON.stringify(urlDateRange) !== JSON.stringify(currentDateRange)) {
          setDateRange(urlDateRange)
        }

        setUrlUpdating(false)
      }
    }

    syncStateFromURL()
  }, [searchParams])

  // Update URL when state changes
  const updateURL = useCallback((sensors: string[], start: string, end: string) => {
    console.log('updateURL called with sensors:', sensors)
    isUpdatingFromStateRef.current = true

    const params = new URLSearchParams()

    if (sensors.length > 0) {
      params.set('sensors', sensors.join(','))
    }

    if (start) {
      params.set('start', start)
    }

    if (end) {
      params.set('end', end)
    }

    console.log('Setting search params:', params.toString())
    setSearchParams(params)

    // Reset the flag after a delay to allow URL sync to skip
    setTimeout(() => {
      console.log('Resetting isUpdatingFromStateRef flag')
      isUpdatingFromStateRef.current = false
    }, 200)
  }, [setSearchParams])

  // Update URL whenever selectedSensors or dateRange changes
  useEffect(() => {
    console.log('URL update effect triggered')
    console.log('selectedSensors:', selectedSensors)
    console.log('dateRange:', dateRange)
    console.log('isUpdatingFromStateRef.current:', isUpdatingFromStateRef.current)

    if (!urlUpdating) {
      updateURL(selectedSensors, dateRange.start, dateRange.end)
    }
  }, [selectedSensors, dateRange.start, dateRange.end, updateURL, urlUpdating])

  // Function to copy current URL to clipboard
  const copyShareableURL = async () => {
    try {
      const currentURL = window.location.href
      await navigator.clipboard.writeText(currentURL)
      setError(null)
      // Show temporary success message
      const originalError = error
      setError('URL copied to clipboard!')
      setTimeout(() => setError(originalError), 2000)
    } catch (err) {
      setError('Failed to copy URL to clipboard')
      console.error('Error copying URL:', err)
    }
  }

  // Function to reset to default state
  const resetToDefaults = () => {
    const defaultDateRange = {
      start: format(subDays(new Date(), 7), "yyyy-MM-dd'T'HH:mm"),
      end: format(new Date(), "yyyy-MM-dd'T'HH:mm")
    }
    setSelectedSensors([])
    setSensors([])
    setSelectedSensorInfo(null)
    setDateRange(defaultDateRange)
    setWeatherData([])
    setError(null)
  }

  // Utility function to convert local datetime string to UTC ISO string
  const convertLocalToUTC = (localDateTimeString: string): string => {
    // Create a Date object from the local datetime string
    const localDate = new Date(localDateTimeString)
    
    // Convert to UTC ISO string
    return localDate.toISOString()
  }

  // Function to fetch sensor by name
  const fetchSensorByName = async (sensorName: string) => {
    try {
      setError(null)
      const response = await axios.get<Sensor>(`/api/sensors/${sensorName}`)
      return response.data
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setError(`Sensor '${sensorName}' not found`)
      } else {
        setError(`Failed to fetch sensor '${sensorName}'`)
      }
      console.error('Error fetching sensor:', err)
      return null
    }
  }

  // Function to add sensor to selection
  const addSensor = async () => {
    if (!sensorInput.trim()) return
    
    const sensorName = sensorInput.trim()
    console.log('Adding sensor:', sensorName)
    console.log('Current selectedSensors before:', selectedSensors)
    
    // Check if sensor is already selected
    if (selectedSensors.includes(sensorName)) {
      setError(`Sensor '${sensorName}' is already selected`)
      return
    }
    
    // Fetch sensor info
    const sensor = await fetchSensorByName(sensorName)
    if (sensor) {
      console.log('Sensor fetched successfully:', sensor)
      
      // Update states first
      const newSelectedSensors = [...selectedSensors, sensorName]
      const newSensors = [...sensors, sensor]
      
      console.log('New selectedSensors array:', newSelectedSensors)
      console.log('New sensors array:', newSensors)
      
      setSelectedSensors(newSelectedSensors)
      setSensors(newSensors)
      setSelectedSensorInfo(sensor)
      setSensorInput('')
      setError(null)
      
      // Fetch weather data with the updated sensor list
      // Use the new state values directly to avoid race conditions
      setTimeout(() => {
        console.log('Fetching weather data for sensors:', newSelectedSensors)
        fetchWeatherDataWithSensors(newSelectedSensors)
      }, 100)
    } else {
      console.log('Failed to fetch sensor:', sensorName)
    }
  }

  const handleSensorInputKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      addSensor()
    }
  }

  // Fetch weather data when sensors or date range changes
  const fetchWeatherData = useCallback(async () => {
    if (selectedSensors.length === 0) return

    setLoading(true)
    setError(null)

    try {
      const allData: WeatherData[] = []
      
      // Convert local datetime inputs to UTC ISO strings
      const startUTC = convertLocalToUTC(dateRange.start)
      const endUTC = convertLocalToUTC(dateRange.end)
      
      console.log(`Local date range: ${dateRange.start} to ${dateRange.end}`) // Debug log
      console.log(`UTC date range: ${startUTC} to ${endUTC}`) // Debug log
      
      for (const sensorName of selectedSensors) {
        console.log(`Fetching weather for sensor: ${sensorName}`) // Debug log
        
        const response = await axios.get<WeatherData[]>(`/api/sensors/${sensorName}/weather`, {
          params: {
            start: startUTC,
            end: endUTC
          }
        })
        console.log(`Response for ${sensorName}:`, response.data) // Debug log
        allData.push(...response.data)
      }

      // Sort by timestamp
      allData.sort((a, b) => parseISO(a.timestamp).getTime() - parseISO(b.timestamp).getTime())
      console.log('Fetched weather data:', allData) // Debug log
      console.log('Selected sensors:', selectedSensors) // Debug log
      setWeatherData(allData)
    } catch (err) {
      setError('Failed to fetch weather data')
      console.error('Error fetching weather data:', err)
    } finally {
      setLoading(false)
    }
  }, [selectedSensors, dateRange])

  // Helper function to fetch weather data with specific sensors (for addSensor)
  const fetchWeatherDataWithSensors = useCallback(async (sensorsToFetch: string[]) => {
    if (sensorsToFetch.length === 0) return

    console.log('fetchWeatherDataWithSensors called with sensors:', sensorsToFetch)
    setLoading(true)
    setError(null)

    try {
      const allData: WeatherData[] = []
      
      // Convert local datetime inputs to UTC ISO strings
      const startUTC = convertLocalToUTC(dateRange.start)
      const endUTC = convertLocalToUTC(dateRange.end)
      
      console.log(`Local date range: ${dateRange.start} to ${dateRange.end}`) // Debug log
      console.log(`UTC date range: ${startUTC} to ${endUTC}`) // Debug log
      
      for (const sensorName of sensorsToFetch) {
        console.log(`Fetching weather for sensor: ${sensorName}`) // Debug log
        
        const response = await axios.get<WeatherData[]>(`/api/sensors/${sensorName}/weather`, {
          params: {
            start: startUTC,
            end: endUTC
          }
        })
        console.log(`Response for ${sensorName}:`, response.data) // Debug log
        allData.push(...response.data)
      }

      // Sort by timestamp
      allData.sort((a, b) => parseISO(a.timestamp).getTime() - parseISO(b.timestamp).getTime())
      console.log('Fetched weather data:', allData) // Debug log
      console.log('Selected sensors:', sensorsToFetch) // Debug log
      
      // Update weather data state
      setWeatherData(allData)
      console.log('Weather data state updated with:', allData)
    } catch (err) {
      setError('Failed to fetch weather data')
      console.error('Error fetching weather data:', err)
    } finally {
      setLoading(false)
    }
  }, [dateRange])

  // Remove the automatic fetchWeatherData useEffect to prevent race conditions
  // useEffect(() => {
  //   fetchWeatherData()
  // }, [fetchWeatherData])

  // Load initial weather data when component mounts with initial sensors
  useEffect(() => {
    if (selectedSensors.length > 0) {
      console.log('Loading initial weather data for sensors:', selectedSensors)
      fetchWeatherDataWithSensors(selectedSensors)
    }
  }, []) // Only run once on mount

  // Refresh weather data when date range changes
  useEffect(() => {
    if (selectedSensors.length > 0) {
      console.log('Date range changed, refreshing weather data for sensors:', selectedSensors)
      fetchWeatherDataWithSensors(selectedSensors)
    }
  }, [dateRange.start, dateRange.end]) // Only depend on date range values

  // Removed this useEffect to prevent conflicts with addSensor
  // useEffect(() => {
  //   fetchWeatherData()
  // }, [fetchWeatherData])

  const handleSensorChange = (sensorName: string) => {
    // Remove sensor from selection
    setSelectedSensors(prev => {
      const newSelectedSensors = prev.filter(name => name !== sensorName)
      
      // Clear selected sensor info if this was the one being displayed
      if (selectedSensorInfo?.name === sensorName) {
        setSelectedSensorInfo(null)
      }
      
      // If there are still selected sensors, show info for the first one
      if (newSelectedSensors.length > 0) {
        fetchSensorInfo(newSelectedSensors[0])
      }
      
      return newSelectedSensors
    })
    
    setSensors(prev => prev.filter(sensor => sensor.name !== sensorName))
  }

  const fetchSensorInfo = async (sensorName: string) => {
    try {
      const response = await axios.get<Sensor>(`/api/sensors/${sensorName}`)
      setSelectedSensorInfo(response.data)
    } catch (err) {
      console.error('Error fetching sensor info:', err)
    }
  }

  const handleDateChange = (field: 'start' | 'end', value: string) => {
    setDateRange(prev => ({ ...prev, [field]: value }))
  }

  // Transform weather data for charts (group by timestamp, then by sensor)
  const getTransformedChartData = (dataKey: keyof Omit<WeatherData, 'sensor' | 'timestamp'>) => {
    if (weatherData.length === 0) {
      console.log('No weather data available for chart transformation') // Debug log
      return []
    }
    
    console.log(`Transforming chart data for ${dataKey}`) // Debug log
    console.log('Weather data:', weatherData) // Debug log
    console.log('Selected sensors for transformation:', selectedSensors) // Debug log
    
    // Group data by timestamp
    const groupedByTimestamp = new Map<string, Map<string, number | null>>() // Allow null for missing data
    
    weatherData.forEach(item => {
      const timestamp = item.timestamp
      if (!groupedByTimestamp.has(timestamp)) {
        groupedByTimestamp.set(timestamp, new Map())
      }
      
      const sensorData = groupedByTimestamp.get(timestamp)!
      sensorData.set(item.sensor, item[dataKey] as number | null) // Cast to allow null
    })
    
    console.log('Grouped by timestamp:', groupedByTimestamp) // Debug log
    
    // Convert to array format for Recharts
    const result = Array.from(groupedByTimestamp.entries()).map(([timestamp, sensorValues]) => {
      const dataPoint: any = { timestamp }
      selectedSensors.forEach(sensorName => {
        dataPoint[sensorName] = sensorValues.get(sensorName) || null
      })
      return dataPoint
    })
    
    console.log('Final chart data:', result) // Debug log
    console.log('Chart data keys:', result.length > 0 ? Object.keys(result[0]) : 'No data') // Debug log
    return result
  }

  const renderChart = (dataKey: keyof Omit<WeatherData, 'sensor' | 'timestamp'>, title: string, unit: string) => {
    const chartData = getTransformedChartData(dataKey)
    console.log(`Chart data for ${dataKey}:`, chartData) // Debug log
    console.log(`Selected sensors in renderChart:`, selectedSensors) // Debug log
    console.log(`Weather data in renderChart:`, weatherData) // Debug log
    
    return (
      <div className="chart-container">
        <h2>{title}</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(timestamp) => {
                // Convert UTC timestamp to local time for display
                const utcDate = parseISO(timestamp)
                return format(utcDate, 'MM/dd HH:mm')
              }}
            />
            <YAxis
              label={{ value: unit, angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              labelFormatter={(timestamp) => {
                // The timestamp from API is in UTC, convert to local for display
                const utcDate = parseISO(timestamp as string)
                const localTime = format(utcDate, 'PPpp')
                const utcTime = format(utcDate, 'PPpp') + ' UTC'
                return `${localTime} (${utcTime})`
              }}
              formatter={(value: number) => [`${value} ${unit}`, '']}
            />
            <Legend />
            {selectedSensors.map(sensorName => (
              <Line
                key={sensorName}
                type="monotone"
                dataKey={sensorName}
                name={sensorName}
                stroke={`#${Math.floor(Math.random()*16777215).toString(16)}`}
                dot={false}
                connectNulls={true}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Weather Dashboard</h1>
        <div className="timezone-info">
          <small>Local Timezone: {Intl.DateTimeFormat().resolvedOptions().timeZone}</small>
        </div>
      </header>

      <main className="App-main">
        <div className="controls">
          <div className="controls-header">
            <h2>Dashboard Controls</h2>
            <div className="control-actions">
              <button onClick={copyShareableURL} className="share-btn" title="Copy shareable URL">
                📋 Share URL
              </button>
              <button onClick={resetToDefaults} className="reset-btn" title="Reset to defaults">
                🔄 Reset
              </button>
            </div>
          </div>
          
          <div className="url-status">
            <small>
              <strong>Current URL:</strong> {window.location.pathname}{window.location.search}
            </small>
            <small>
              {urlUpdating ? (
                <span className="url-updating">🔄 Updating from URL...</span>
              ) : (
                <span className="url-ready">✅ URL Ready</span>
              )}
            </small>
          </div>

          {useWebSocketMode && selectedSensors.length > 0 && (
            <div className="websocket-status">
              <small>
                <strong>WebSocket:</strong>{' '}
                {wsConnected ? (
                  <span className="ws-connected">🟢 Connected</span>
                ) : wsError ? (
                  <span className="ws-error">
                    🔴 Error {reconnectAttempts > 0 && `(Reconnect attempt ${reconnectAttempts})`}
                  </span>
                ) : (
                  <span className="ws-connecting">🟡 Connecting...</span>
                )}
              </small>
              <small>
                <label>
                  <input
                    type="checkbox"
                    checked={useWebSocketMode}
                    onChange={(e) => setUseWebSocketMode(e.target.checked)}
                  />
                  Real-time updates
                </label>
              </small>
            </div>
          )}
          
          <div className="url-preview">
            <details>
              <summary>URL Preview</summary>
              <div className="preview-content">
                <p><strong>What the URL will contain:</strong></p>
                <div className="preview-params">
                  {selectedSensors.length > 0 && (
                    <div className="preview-param">
                      <strong>Sensors:</strong> {selectedSensors.join(', ')}
                    </div>
                  )}
                  <div className="preview-param">
                    <strong>Start Date:</strong> {dateRange.start}
                  </div>
                  <div className="preview-param">
                    <strong>End Date:</strong> {dateRange.end}
                  </div>
                </div>
                <p className="preview-note">
                  <small>💡 This URL can be bookmarked or shared to restore your exact dashboard state!</small>
                </p>
              </div>
            </details>
          </div>

          <div className="sensor-selector">
            <h2>Add Sensors</h2>
            <p className="sensor-instructions">
              Enter sensor names to monitor. You can add multiple sensors by entering them one at a time.
            </p>
            <div className="sensor-input-container">
              <input
                type="text"
                placeholder="Enter sensor name (e.g., test-sensor-01)"
                value={sensorInput}
                onChange={(e) => setSensorInput(e.target.value)}
                onKeyPress={handleSensorInputKeyPress}
                className="sensor-input"
              />
              <button onClick={addSensor} className="add-sensor-btn" disabled={!sensorInput.trim()}>
                Add Sensor
              </button>
            </div>
            <div className="selected-sensors">
              <h3>Selected Sensors</h3>
              {selectedSensors.length === 0 ? (
                <p className="no-sensors">No sensors selected. Add a sensor above to get started.</p>
              ) : (
                <div className="sensor-tags">
                  {selectedSensors.map(sensorName => (
                    <div key={sensorName} className="sensor-tag">
                      <span>{sensorName}</span>
                      <button
                        onClick={() => handleSensorChange(sensorName)}
                        className="remove-sensor-btn"
                        title="Remove sensor"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
              {selectedSensors.length > 0 && (
                <div className="debug-controls">
                  <button onClick={fetchWeatherData} className="debug-btn">
                    Refresh Weather Data
                  </button>
                  <button onClick={() => console.log('Current state:', { weatherData, selectedSensors, sensors })} className="debug-btn">
                    Log State
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="date-range">
            <h2>Date Range</h2>
            <p className="date-instructions">
              Select a date range in your local timezone. Dates will be automatically converted to UTC when sent to the API.
            </p>
            <div className="date-inputs">
              <div>
                <label htmlFor="start-date">Start:</label>
                <input
                  id="start-date"
                  type="datetime-local"
                  value={dateRange.start}
                  onChange={(e) => handleDateChange('start', e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="end-date">End:</label>
                <input
                  id="end-date"
                  type="datetime-local"
                  value={dateRange.end}
                  onChange={(e) => handleDateChange('end', e.target.value)}
                />
              </div>
            </div>
            {selectedSensors.length > 0 && (
              <div className="utc-info">
                <small>
                  <strong>UTC Range:</strong> {convertLocalToUTC(dateRange.start)} to {convertLocalToUTC(dateRange.end)}
                </small>
              </div>
            )}
            <div className="timezone-debug">
              <details>
                <summary>Timezone Conversion Details</summary>
                <div className="debug-content">
                  <p><strong>Your Local Timezone:</strong> {Intl.DateTimeFormat().resolvedOptions().timeZone}</p>
                  <p><strong>Local Start:</strong> {dateRange.start}</p>
                  <p><strong>Local End:</strong> {dateRange.end}</p>
                  <p><strong>UTC Start:</strong> {convertLocalToUTC(dateRange.start)}</p>
                  <p><strong>UTC End:</strong> {convertLocalToUTC(dateRange.end)}</p>
                  <p><strong>Note:</strong> The API receives UTC timestamps, ensuring consistent data across all timezones.</p>
                </div>
              </details>
            </div>
          </div>
        </div>

        {/* Sensor Statistics */}
        {selectedSensorInfo && (
          <div className="sensor-statistics">
            <h2>Sensor Statistics: {selectedSensorInfo.name}</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Total Readings:</span>
                <span className="stat-value">{selectedSensorInfo.statistics.total_readings}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Last 24h Readings:</span>
                <span className="stat-value">{selectedSensorInfo.statistics.last_24h_readings}</span>
              </div>
              {selectedSensorInfo.statistics.average_temperature !== null && (
                <div className="stat-item">
                  <span className="stat-label">Avg Temperature:</span>
                  <span className="stat-value">{selectedSensorInfo.statistics.average_temperature.toFixed(1)}°C</span>
                </div>
              )}
              {selectedSensorInfo.statistics.average_humidity !== null && (
                <div className="stat-item">
                  <span className="stat-label">Avg Humidity:</span>
                  <span className="stat-value">{selectedSensorInfo.statistics.average_humidity.toFixed(1)}%</span>
                </div>
              )}
              {selectedSensorInfo.statistics.average_pressure !== null && (
                <div className="stat-item">
                  <span className="stat-label">Avg Pressure:</span>
                  <span className="stat-value">{selectedSensorInfo.statistics.average_pressure.toFixed(1)} hPa</span>
                </div>
              )}
              {selectedSensorInfo.statistics.average_rssi !== null && (
                <div className="stat-item">
                  <span className="stat-label">Avg WiFi Signal:</span>
                  <span className="stat-value">{selectedSensorInfo.statistics.average_rssi} dBm</span>
                </div>
              )}
              {selectedSensorInfo.statistics.first_reading && (
                <div className="stat-item">
                  <span className="stat-label">First Reading:</span>
                  <span className="stat-value">{format(parseISO(selectedSensorInfo.statistics.first_reading), 'PPpp')}</span>
                </div>
              )}
              {selectedSensorInfo.statistics.last_reading && (
                <div className="stat-item">
                  <span className="stat-label">Last Reading:</span>
                  <span className="stat-value">{format(parseISO(selectedSensorInfo.statistics.last_reading), 'PPpp')}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {loading ? (
          <div className="loading">Loading weather data...</div>
        ) : (
          <div className="charts">
            {renderChart('temperature', 'Temperature', '°C')}
            {renderChart('humidity', 'Humidity', '%')}
            {renderChart('pressure', 'Pressure', 'hPa')}
            {renderChart('altitude', 'Altitude', 'm')}
            {renderChart('rssi', 'WiFi Signal Strength', 'dBm')}
          </div>
        )}
      </main>
    </div>
  )
}

// Main App Component with Router
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<WeatherDashboard />} />
      </Routes>
    </Router>
  )
}

export default App
