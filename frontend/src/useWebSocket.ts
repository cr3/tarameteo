import { useEffect, useRef, useState, useCallback } from 'react'

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

interface UseWebSocketOptions {
  onMessage?: (data: WeatherData) => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

interface UseWebSocketReturn {
  isConnected: boolean
  error: string | null
  reconnectAttempts: number
  sendMessage: (data: any) => void
}

export function useWebSocket(
  url: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    onMessage,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const shouldReconnectRef = useRef(true)

  const connect = useCallback(() => {
    if (!url) {
      console.log('WebSocket: No URL provided, skipping connection')
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket: Already connected')
      return
    }

    try {
      console.log('WebSocket: Connecting to', url)
      const ws = new WebSocket(url)

      ws.onopen = () => {
        console.log('WebSocket: Connected')
        setIsConnected(true)
        setError(null)
        setReconnectAttempts(0)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WeatherData
          console.log('WebSocket: Received message', data)
          onMessage?.(data)
        } catch (err) {
          console.error('WebSocket: Failed to parse message', err)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket: Error', event)
        setError('WebSocket connection error')
        onError?.(event)
      }

      ws.onclose = (event) => {
        console.log('WebSocket: Closed', event.code, event.reason)
        setIsConnected(false)
        wsRef.current = null

        // Attempt to reconnect if it wasn't a clean close
        if (
          shouldReconnectRef.current &&
          reconnectAttempts < maxReconnectAttempts &&
          event.code !== 1000 // 1000 is normal closure
        ) {
          console.log(
            `WebSocket: Reconnecting in ${reconnectInterval}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`
          )
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts((prev) => prev + 1)
            connect()
          }, reconnectInterval)
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          setError('Max reconnection attempts reached')
        }
      }

      wsRef.current = ws
    } catch (err) {
      console.error('WebSocket: Failed to create connection', err)
      setError('Failed to create WebSocket connection')
    }
  }, [url, onMessage, onError, reconnectAttempts, maxReconnectAttempts, reconnectInterval])

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket: Cannot send message, not connected')
    }
  }, [])

  // Connect on mount or when URL changes
  useEffect(() => {
    shouldReconnectRef.current = true
    connect()

    // Cleanup on unmount or URL change
    return () => {
      shouldReconnectRef.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        console.log('WebSocket: Closing connection')
        wsRef.current.close(1000, 'Component unmounting')
        wsRef.current = null
      }
    }
  }, [url, connect])

  return {
    isConnected,
    error,
    reconnectAttempts,
    sendMessage,
  }
}
