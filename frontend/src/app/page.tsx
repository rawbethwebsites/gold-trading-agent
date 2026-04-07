'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  ReferenceLine,
  Scatter
} from 'recharts'
import { Activity, Bell, AlertTriangle, ChevronDown, ChevronUp, Settings } from 'lucide-react'

const API_BASE = 'http://localhost:8000/api'
const POLLING_INTERVAL = 5000 // 5 seconds

interface DashboardData {
  status: {
    connected: boolean
    is_trading: boolean
    symbol: string
    can_trade: boolean
    error: string | null
    active_source?: string
  }
  price: {
    timestamp: string
    symbol: string
    bid: number
    ask: number
    open: number
    high: number
    low: number
    close: number
    volume: number
  } | null
  indicators: {
    timestamp: string
    symbol: string
    price: number
    ema_9: number | null
    ema_21: number | null
    sma_50: number | null
    macd: number | null
    macd_histogram: number | null
    rsi_14: number | null
    bb_upper: number | null
    bb_lower: number | null
    bb_percent: number | null
    atr_14: number | null
    trend: string
    signal_strength: number
  } | null
  account: {
    balance: number
    equity: number
    margin: number
    free_margin: number
    margin_level: number
    open_positions: number
    account_type: string
    can_trade: boolean
  } | null
  positions: Array<{
    ticket: number
    symbol: string
    type: string
    volume: number
    open_price: number
    current_price: number
    profit: number
    swap: number
    open_time: string
  }>
  signal: {
    timestamp: string
    symbol: string
    type: string
    price: number
    confidence: number
    strength: number
    reasons: string[]
    suggested_sl: number | null
    suggested_tp: number | null
  } | null
}

// Asset configurations with realistic base prices
const ASSET_CONFIG: Record<string, { basePrice: number; tickSize: number; pipValue: number; name: string; contractSize: number }> = {
  XAUUSD: { basePrice: 4650, tickSize: 0.01, pipValue: 0.01, name: 'Gold', contractSize: 100 },
  BTCUSD: { basePrice: 83000, tickSize: 0.1, pipValue: 0.01, name: 'Bitcoin', contractSize: 1 }
}

// Calculate EMA
function calculateEMA(prices: number[], period: number): number {
  if (prices.length < period) return prices[prices.length - 1] || 0
  const multiplier = 2 / (period + 1)
  let ema = prices.slice(0, period).reduce((a, b) => a + b, 0) / period
  for (let i = period; i < prices.length; i++) {
    ema = (prices[i] - ema) * multiplier + ema
  }
  return ema
}

// Generate realistic price movement
function generateNextTick(currentPrice: number, volatility: number, tickSize: number): number {
  const maxMove = tickSize * volatility * (Math.random() * 2 + 1) // Random factor 1-3
  const move = (Math.random() - 0.5) * maxMove
  return Math.max(currentPrice + move, tickSize)
}

export default function GoldTradingDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Custom states
  const [isLive, setIsLive] = useState(true)
  const [apiEnabled, setApiEnabled] = useState<boolean>(true)
  const [historicalData, setHistoricalData] = useState<any[]>([])
  const [currentTick, setCurrentTick] = useState<any>(null)
  const hasSeeded = useRef(false)
  const tickIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Timeframe state - M1=1 minute, M5=5 minute, M15=15 minute, H1=1 hour, H4=4 hour, D1=1 day
  const [timeframe, setTimeframe] = useState<string>('H1')
  const timeframeMap: Record<string, string> = {
    '1M': 'M1', '5M': 'M5', '15M': 'M15', '1H': 'H1', '4H': 'H4', '1D': 'D1'
  }

  // Asset state - XAUUSD (Gold) or BTCUSD (Bitcoin)
  const [asset, setAsset] = useState<string>('XAUUSD')
  const [assetPrices, setAssetPrices] = useState<Record<string, number>>({})

  // Controls panel state
  const [showControls, setShowControls] = useState(true)
  const [basePrice, setBasePrice] = useState<number>(ASSET_CONFIG.XAUUSD.basePrice)
  const [volatility, setVolatility] = useState<number>(5)
  const [tickSpeed, setTickSpeed] = useState<number>(1500)
  const [lotSize, setLotSize] = useState<number>(0.01)
  const [riskPercent, setRiskPercent] = useState<number>(1)
  const [accountBalance, setAccountBalance] = useState<number>(10000)

  // Fetch asset prices
  const fetchAssetPrices = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/assets`)
      if (res.ok) {
        const data = await res.json()
        setAssetPrices(data.prices || {})
        // If we have an active asset from backend, update it
        if (data.active && data.active !== asset) {
          setAsset(data.active)
        }
      }
    } catch (err) {
      console.error('Failed to fetch asset prices:', err)
    }
  }, [asset])

  // Converter & Alerts States
  const [convAmount, setConvAmount] = useState<number>(1)
  const [convUnit, setConvUnit] = useState<string>('oz')
  const [convCurrency, setConvCurrency] = useState<string>('USD')
  const [alertTarget, setAlertTarget] = useState<string>('')
  const [alertCond, setAlertCond] = useState<string>('above')
  const [alertsList, setAlertsList] = useState<Array<{p: number, cond: string}>>([])

  // AI/MCP Results states
  const [aiAnalysis, setAIAnalysis] = useState<any>(null)
  const [aiDebate, setAIDebate] = useState<any>(null)
  const [aiRisk, setAIRisk] = useState<any>(null)

  const FX: Record<string, number> = {USD:1, NGN:1650, EUR:0.92, GBP:0.79}
  const UNIT: Record<string, number> = {oz:1, g:0.0321507, kg:32.1507, tola:0.374878}

  const getConvertedValue = () => {
     const price = currentTick?.price || basePrice
     const oz = convAmount * UNIT[convUnit]
     const usd = oz * price
     return usd * FX[convCurrency]
  }

  // Trading calculations
  const currentPrice = currentTick?.price || basePrice
  const config = ASSET_CONFIG[asset]
  const positionValue = lotSize * config.contractSize * currentPrice
  const riskAmount = accountBalance * (riskPercent / 100)
  const pipValue = asset === 'XAUUSD'
    ? (lotSize * 10) // Gold: $10 per pip per lot
    : (lotSize * 1)  // Bitcoin: $1 per pip per lot

  // Initialize price simulation based on asset
  useEffect(() => {
    const config = ASSET_CONFIG[asset]
    setBasePrice(config.basePrice)
    // Reset chart when asset changes
    const initialData = []
    const now = Date.now()
    let price = config.basePrice
    for (let i = 50; i > 0; i--) {
      price = generateNextTick(price, volatility / 2, config.tickSize)
      const timestamp = new Date(now - i * tickSpeed).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})
      initialData.push({
        timestamp,
        price,
        ema_9: price,
        ema_21: price,
        rsi_14: 50 + (Math.random() - 0.5) * 20
      })
    }
    setHistoricalData(initialData)
    setCurrentTick(initialData[initialData.length - 1])
    // Clear AI results on asset switch
    setAIAnalysis(null)
    setAIDebate(null)
    setAIRisk(null)
  }, [asset])

  // Initialize from localStorage and fetch API status
  useEffect(() => {
    const saved = localStorage.getItem('livePrices')
    if (saved !== null) {
      setIsLive(saved === 'true')
    }

    // Fetch Twelve Data API status
    const fetchApiStatus = async () => {
       try {
          const res = await fetch(`${API_BASE}/config/api-status`)
          if (res.ok) {
             const data = await res.json()
             setApiEnabled(data.api_calls_enabled)
          }
       } catch (err) {
          console.error('Failed to fetch API status:', err)
       }
    }
    fetchApiStatus()
  }, [])

  // Live tick simulation
  useEffect(() => {
    if (!isLive) {
      if (tickIntervalRef.current) {
        clearInterval(tickIntervalRef.current)
        tickIntervalRef.current = null
      }
      return
    }

    const config = ASSET_CONFIG[asset]
    tickIntervalRef.current = setInterval(() => {
      setHistoricalData(prevData => {
        if (prevData.length === 0) return prevData

        const lastPrice = prevData[prevData.length - 1]?.price || basePrice
        const newPrice = generateNextTick(lastPrice, volatility, config.tickSize)
        const prices = [...prevData.map(d => d.price), newPrice]
        const ema9 = calculateEMA(prices.slice(-10), 9)
        const ema21 = calculateEMA(prices.slice(-22), 21)

        const newTick = {
          timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}),
          price: newPrice,
          ema_9: ema9,
          ema_21: ema21,
          rsi_14: 50 + (Math.random() - 0.5) * 20
        }

        setCurrentTick(newTick)
        // Keep last 100 ticks for smooth scrolling
        return [...prevData.slice(-99), newTick]
      })
    }, tickSpeed)

    return () => {
      if (tickIntervalRef.current) {
        clearInterval(tickIntervalRef.current)
      }
    }
  }, [isLive, tickSpeed, volatility, asset, basePrice])

  const toggleLive = () => {
    const next = !isLive
    setIsLive(next)
    localStorage.setItem('livePrices', String(next))
  }

  const toggleApi = async () => {
     try {
        const next = !apiEnabled
        // Optimistic update
        setApiEnabled(next)
        const res = await fetch(`${API_BASE}/config/toggle-api`, {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ enabled: next })
        })
        if (!res.ok) {
           // Revert if failed
           setApiEnabled(!next)
           console.error('Failed to toggle API status')
        }
     } catch (err) {
        setApiEnabled(!apiEnabled)
        console.error('Failed to toggle API status:', err)
     }
  }

  // Fetch historical rates for selected timeframe - disabled in favor of simulation
  const fetchTimeframeData = useCallback(async () => {
    // Simulation generates its own data, no need to fetch from backend
    return
  }, [timeframe, isLive, loading])

  // Fetch data from backend
  const fetchData = useCallback(async () => {
    // Skip if paused, unless we are on the very first load
    if (!isLive && !loading) return

    try {
      const response = await fetch(`${API_BASE}/dashboard`)
      if (!response.ok) {
        throw new Error('Failed to fetch data')
      }
      const dashboardData = await response.json()

      // Backend data is received but simulation generates its own prices
      // Only use backend data for account/positions, not for price simulation
      setData(dashboardData)
      setError(null)
    } catch (err) {
      setError('Cannot connect to backend. Is it running on port 8000?')
    } finally {
      if (loading) setLoading(false)
    }
  }, [isLive, loading])

  // Poll data
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, POLLING_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchData])

  // Fetch timeframe data when timeframe changes
  useEffect(() => {
    fetchTimeframeData()
    const interval = setInterval(fetchTimeframeData, POLLING_INTERVAL * 2)
    return () => clearInterval(interval)
  }, [fetchTimeframeData, timeframe])

  // Switch active asset
  const switchAsset = useCallback(async (sym: string) => {
    try {
      const res = await fetch(`${API_BASE}/assets/switch?symbol=${sym}`, {
        method: 'POST'
      })
      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          setAsset(sym)
          // Update price immediately from response
          if (data.price && data.price.close) {
            setAssetPrices(prev => ({ ...prev, [sym]: data.price.close }))
          }
          // Refresh all data
          fetchData()
          fetchTimeframeData()
        }
      }
    } catch (err) {
      console.error('Failed to switch asset:', err)
    }
  }, [fetchData, fetchTimeframeData])

  // Close position handler
  const closePosition = async (ticket: number) => {
    try {
      const response = await fetch(`${API_BASE}/positions/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket })
      })
      if (response.ok) fetchData()
    } catch (err) {
      console.error('Failed to close position:', err)
    }
  }

  // Request alert permissions
  const enableAlerts = async () => {
    if ('Notification' in window) {
      const perm = await Notification.requestPermission()
      if (perm === 'granted') {
         new Notification("Alerts Enabled", { body: "Browser notifications are now active." })
      }
    }
  }

  // Helpers
  const getSignalDisplay = () => {
    if (!data?.signal) return { text: 'HOLD', color: 'text-muted', strength: 'N/A' }
    const signal = data.signal
    return {
      text: signal.type.toUpperCase(),
      color: signal.type === 'buy' ? 'text-green' : signal.type === 'sell' ? 'text-red' : 'text-gold',
      strength: `${Math.round(signal.confidence * 100)}%`,
      reasons: signal.reasons
    }
  }

  const signal = getSignalDisplay()
  const price = data?.price
  const account = data?.account
  const positions = data?.positions || []

  // Use simulated price if live, otherwise use backend data
  const displayPrice = currentTick?.price || price?.close || basePrice
  const lastClose = historicalData.length > 1 ? historicalData[historicalData.length - 2]?.price : displayPrice
  const change = displayPrice - lastClose
  const pctChange = lastClose ? (change / lastClose) * 100 : 0
  const isUp = change >= 0

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    )
  }

  return (
    <div className="container" style={{maxWidth: '100%', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px', padding: '24px'}}>
      
      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          <span className="text-red-200 text-sm font-semibold">{error}</span>
        </div>
      )}

      {/* Main Single Dashboard Grid */}
      <div style={{display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '20px', alignItems: 'start', width: '100%'}}>
        
        {/* Left Column: Core Data & Operations */}
        <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
          
          {/* Main Quote Card */}
          <div className="quote-card flex flex-col">
            <div className="panel-head top" style={{padding: '14px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between'}}>
              <div className="flex items-center gap-3">
                <div style={{width: '28px', height: '28px', borderRadius: '999px', border: '1px solid var(--border)', display: 'grid', placeItems: 'center', background: 'rgba(255,255,255,.03)', color: 'var(--muted)', fontSize: '14px'}}>×</div>
                <div>
                  <h1 className="text-lg font-bold">{asset === 'XAUUSD' ? 'XAU/USD (Gold)' : 'BTC/USD (Bitcoin)'}</h1>
                  <p className="text-xs text-muted">{asset} · FX · {account?.account_type?.toUpperCase() || 'DEMO'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <button
                   onClick={toggleApi}
                   className={`toggle-btn ${apiEnabled ? 'active' : 'inactive'}`}
                   title="Toggle Twelve Data API requests to save token limits"
                >
                   {apiEnabled ? '🔑 12Data ON' : '🔑 12Data OFF'}
                </button>
                <button
                   onClick={toggleLive}
                   className={`toggle-btn ${isLive ? 'active' : 'inactive'}`}
                >
                   {isLive ? '🟢 Live ON' : '🔴 Paused'}
                </button>
                <div className={`badge ${data?.status?.connected ? 'badge-up' : 'badge-down'}`}>
                  {data?.status?.connected ? 'MT5 Connected' : 'Disconnected'}
                </div>
                <div className="badge flex items-center gap-1" style={{background: data?.status?.active_source === '12Data' ? 'rgba(88,209,122,.11)' : 'rgba(240,195,107,.11)', color: data?.status?.active_source === '12Data' ? '#58d17a' : '#f0c36b', border: '1px solid currentColor'}}>
                  <span style={{fontSize: '9px'}}>{data?.status?.active_source === '12Data' ? '🟢' : '🟡'}</span>
                  {data?.status?.active_source === '12Data' ? 'Source: 12Data' : `Backup Live: ${data?.status?.active_source || 'Unknown'}`}
                </div>
                <button style={{padding: '8px 12px', borderRadius: '999px', border: '1px solid var(--border)', background: 'rgba(255,255,255,.03)', fontSize: '13px', color: '#d7d8dc'}}>☆ Follow</button>
              </div>
            </div>

            <div className="headline" style={{display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid var(--border)'}}>
              <div className="headline-box" style={{padding: '14px 16px', minHeight: '80px', borderRight: '1px solid var(--border)'}}>
                <div className="price-line" style={{display: 'flex', gap: '8px', alignItems: 'baseline'}}>
                  <div className="price mono" style={{fontSize: '31px', letterSpacing: '-0.03em'}}>
                    {displayPrice > 0 ? displayPrice.toLocaleString(undefined, {minimumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0, maximumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0}) : '--'}
                  </div>
                  <div className={`move ${isUp ? 'text-green' : 'text-red'}`} style={{fontSize: '14px', fontWeight: 600}}>
                    {change > 0 ? '+' : ''}{change.toFixed(2)} {isUp ? '↗' : '↘'} {Math.abs(pctChange).toFixed(2)}%
                  </div>
                </div>
                <div className="stamp text-muted text-xs mt-1">
                   {isLive ? `Live Tick Data: ${new Date().toLocaleTimeString()}` : 'Data Fetching Paused'}
                   {currentTick && <span className="ml-2" style={{color: '#58d17a', animation: 'pulse 1s infinite'}}>●</span>}
                </div>
              </div>
              <div className="headline-box" style={{padding: '14px 16px', minHeight: '80px'}}>
                <div className="price-line" style={{display: 'flex', gap: '8px', alignItems: 'baseline'}}>
                   <div className="text-sm font-semibold text-muted">Trading Signal:</div>
                   <div className={`text-xl font-bold mono ${signal.color}`}>{signal.text}</div>
                </div>
                <div className="stamp text-muted text-xs mt-2">
                   Confidence: {signal.strength}
                   {signal.reasons && signal.reasons.length > 0 && ` · ${signal.reasons[0]}`}
                </div>
              </div>
            </div>

            <div className="controls" style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
                padding: '10px 14px', borderBottom: '1px solid var(--border)', background: 'rgba(255,255,255,.01)'
            }}>
              <div className="flex gap-2">
                {/* Asset Selector */}
                {['XAUUSD', 'BTCUSD'].map((sym) => (
                  <button
                    key={sym}
                    className={`chip ${asset === sym ? 'active' : ''}`}
                    onClick={() => switchAsset(sym)}
                    style={{
                      background: asset === sym ? '#58d17a' : '#202227',
                      color: asset === sym ? '#000' : '#d8dbe0',
                      borderColor: asset === sym ? '#58d17a' : 'var(--border)',
                      fontWeight: asset === sym ? 600 : 400
                    }}
                  >
                    {sym === 'XAUUSD' ? 'Gold' : 'Bitcoin'}
                  </button>
                ))}
                <div className="w-px bg-slate-700 mx-1" />
                {/* Timeframe Selector */}
                {['1M', '5M', '15M', '1H'].map((tf) => (
                  <button
                    key={tf}
                    className={`chip ${timeframe === tf ? 'active' : ''}`}
                    onClick={() => setTimeframe(tf)}
                    style={{
                      background: timeframe === tf ? '#f0c36b' : '#202227',
                      color: timeframe === tf ? '#000' : '#d8dbe0',
                      borderColor: timeframe === tf ? '#f0c36b' : 'var(--border)'
                    }}
                  >
                    {tf}
                  </button>
                ))}
                <button className="icon-chip"><Activity size={14}/></button>
              </div>
              <div className="text-xs text-faint">Multi-Asset Trading</div>
            </div>

            <div className="chart-area flex flex-col gap-2 relative">
               {historicalData.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center z-10 bg-black/40">
                    <div className="text-muted text-sm border border-slate-700 bg-slate-900 px-4 py-2 rounded-lg">Seeding Charts...</div>
                  </div>
               )}
               
               <div style={{height: '300px', width: '100%', marginTop: '10px', position: 'relative'}}>
                 <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={historicalData}>
                      <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="timestamp" stroke="#767b84" tick={{fontSize: 11}} axisLine={false} tickLine={false} minTickGap={30} />
                      <YAxis domain={['auto', 'auto']} stroke="#767b84" tick={{fontSize: 11}} axisLine={false} tickLine={false} tickFormatter={(v)=>v.toFixed(ASSET_CONFIG[asset].tickSize < 0.1 ? 1 : 0)} orientation="right" />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1f1f20', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', color: '#fff', fontSize: '13px' }}
                        itemStyle={{ fontFamily: 'var(--font-mono)' }}
                      />
                      <Line type="monotone" dataKey="price" stroke="#f0c36b" dot={false} strokeWidth={2} isAnimationActive={false} />
                      <Line type="monotone" dataKey="ema_9" stroke="#58d17a" dot={false} strokeWidth={1} strokeDasharray="4 4" isAnimationActive={false} />
                      <Line type="monotone" dataKey="ema_21" stroke="#3b82f6" dot={false} strokeWidth={1} strokeDasharray="4 4" isAnimationActive={false} />
                      {/* Current price dot */}
                      {historicalData.length > 0 && (
                        <Scatter
                          data={[historicalData[historicalData.length - 1]]}
                          fill="#f0c36b"
                          shape={(props: any) => {
                            const { cx, cy } = props;
                            return (
                              <g>
                                <circle cx={cx} cy={cy} r={6} fill="#f0c36b" opacity={0.3}>
                                  <animate attributeName="r" values="6;10;6" dur="1s" repeatCount="indefinite" />
                                  <animate attributeName="opacity" values="0.3;0;0.3" dur="1s" repeatCount="indefinite" />
                                </circle>
                                <circle cx={cx} cy={cy} r={4} fill="#f0c36b" />
                              </g>
                            );
                          }}
                        />
                      )}
                    </ComposedChart>
                 </ResponsiveContainer>
                 {/* Live indicator overlay */}
                 {isLive && currentTick && (
                   <div style={{
                     position: 'absolute',
                     top: '10px',
                     right: '10px',
                     background: 'rgba(0,0,0,0.7)',
                     padding: '6px 12px',
                     borderRadius: '6px',
                     fontSize: '12px',
                     color: '#58d17a',
                     display: 'flex',
                     alignItems: 'center',
                     gap: '6px'
                   }}>
                     <span style={{width: '8px', height: '8px', background: '#58d17a', borderRadius: '50%', animation: 'pulse 1s infinite'}}></span>
                     LIVE {currentTick.price.toLocaleString(undefined, {maximumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0})}
                   </div>
                 )}
               </div>
               
               <div style={{height: '100px', width: '100%', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '10px'}}>
                 <ResponsiveContainer width="100%" height="100%">
                   <ComposedChart data={historicalData}>
                     <YAxis domain={[0, 100]} hide />
                     <Tooltip
                        contentStyle={{ backgroundColor: '#1f1f20', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', color: '#fff', fontSize: '13px' }}
                        itemStyle={{ fontFamily: 'var(--font-mono)' }}
                     />
                     <ReferenceLine y={70} stroke="rgba(255,109,140,0.5)" strokeDasharray="3 3" />
                     <ReferenceLine y={30} stroke="rgba(88,209,122,0.5)" strokeDasharray="3 3" />
                     <Line type="monotone" dataKey="rsi_14" stroke="#a2a9b3" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                   </ComposedChart>
                 </ResponsiveContainer>
               </div>
            </div>

            <div className="stats-row" style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', borderTop: '1px solid var(--border)'}}>
                <div className="stat" style={{padding: '14px 16px', borderRight: '1px solid var(--border)'}}><div className="stat-label" style={{fontSize: '12px', color: 'var(--muted)', marginBottom: '6px'}}>Prev Close</div><div className="stat-value mono" style={{fontSize: '18px', letterSpacing: '-0.02em'}}>{lastClose.toLocaleString(undefined, {minimumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0, maximumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0})}</div></div>
                <div className="stat" style={{padding: '14px 16px', borderRight: '1px solid var(--border)'}}><div className="stat-label" style={{fontSize: '12px', color: 'var(--muted)', marginBottom: '6px'}}>Open</div><div className="stat-value mono" style={{fontSize: '18px', letterSpacing: '-0.02em'}}>{historicalData[0]?.price?.toLocaleString(undefined, {minimumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0, maximumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0}) || '--'}</div></div>
                <div className="stat" style={{padding: '14px 16px', borderRight: '1px solid var(--border)'}}><div className="stat-label" style={{fontSize: '12px', color: 'var(--muted)', marginBottom: '6px'}}>Day Range</div><div className="stat-value mono text-sm flex items-center h-full">{historicalData.length > 0 ? Math.min(...historicalData.map(d => d.price)).toLocaleString(undefined, {minimumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0}) : '--'} — {historicalData.length > 0 ? Math.max(...historicalData.map(d => d.price)).toLocaleString(undefined, {minimumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0}) : '--'}</div></div>
                <div className="stat" style={{padding: '14px 16px', borderRight: '1px solid var(--border)'}}><div className="stat-label" style={{fontSize: '12px', color: 'var(--muted)', marginBottom: '6px'}}>Volume</div><div className="stat-value mono" style={{fontSize: '18px', letterSpacing: '-0.02em'}}>{Math.floor(Math.random() * 10000 + 5000).toLocaleString()}</div></div>
                <div className="stat" style={{padding: '14px 16px'}}><div className="stat-label" style={{fontSize: '12px', color: 'var(--muted)', marginBottom: '6px'}}>Spread</div><div className="stat-value mono" style={{fontSize: '18px', letterSpacing: '-0.02em'}}>{ASSET_CONFIG[asset].tickSize.toFixed(ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 1)}</div></div>
            </div>
          </div>

          {/* Trading Controls Panel */}
          <div className="panel" style={{marginTop: '20px'}}>
            <div
              className="panel-head"
              style={{cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}
              onClick={() => setShowControls(!showControls)}
            >
              <div>
                <h2>Trading Controls</h2>
                <p>Configure simulation & position sizing</p>
              </div>
              <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                <Settings size={18} className="text-muted" />
                {showControls ? <ChevronUp size={18} className="text-muted" /> : <ChevronDown size={18} className="text-muted" />}
              </div>
            </div>
            {showControls && (
            <div className="panel-body" style={{padding: '16px'}}>
              <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px'}}>
                {/* Price Controls */}
                <div style={{background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border)'}}>
                  <div style={{fontSize: '12px', fontWeight: 600, marginBottom: '10px', color: '#f0c36b', textTransform: 'uppercase'}}>Price Simulation</div>

                  <div style={{marginBottom: '10px'}}>
                    <label style={{display: 'block', fontSize: '11px', color: 'var(--muted)', marginBottom: '4px'}}>Base Price</label>
                    <input
                      type="number"
                      value={basePrice}
                      onChange={(e) => setBasePrice(parseFloat(e.target.value) || ASSET_CONFIG[asset].basePrice)}
                      style={{width: '100%', height: '36px', borderRadius: '6px', border: '1px solid var(--border)', background: '#1f2125', padding: '0 10px', color: '#fff', fontSize: '13px'}}
                    />
                  </div>

                  <div style={{marginBottom: '10px'}}>
                    <label style={{display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--muted)', marginBottom: '4px'}}>
                      <span>Volatility</span>
                      <span style={{color: '#fff'}}>{volatility}/10</span>
                    </label>
                    <input
                      type="range"
                      min={1}
                      max={10}
                      value={volatility}
                      onChange={(e) => setVolatility(parseInt(e.target.value))}
                      style={{width: '100%', accentColor: '#58d17a'}}
                    />
                    <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--muted)', marginTop: '2px'}}>
                      <span>Low</span>
                      <span>High</span>
                    </div>
                  </div>

                  <div>
                    <label style={{display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--muted)', marginBottom: '4px'}}>
                      <span>Tick Speed</span>
                      <span style={{color: '#fff'}}>{tickSpeed}ms</span>
                    </label>
                    <input
                      type="range"
                      min={500}
                      max={5000}
                      step={100}
                      value={tickSpeed}
                      onChange={(e) => setTickSpeed(parseInt(e.target.value))}
                      style={{width: '100%', accentColor: '#3b82f6'}}
                    />
                    <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--muted)', marginTop: '2px'}}>
                      <span>Fast</span>
                      <span>Slow</span>
                    </div>
                  </div>
                </div>

                {/* Trade Size Controls */}
                <div style={{background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border)'}}>
                  <div style={{fontSize: '12px', fontWeight: 600, marginBottom: '10px', color: '#58d17a', textTransform: 'uppercase'}}>Position Size</div>

                  <div style={{marginBottom: '10px'}}>
                    <label style={{display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--muted)', marginBottom: '4px'}}>
                      <span>Lot Size</span>
                      <span style={{color: '#fff'}}>{lotSize.toFixed(2)}</span>
                    </label>
                    <input
                      type="number"
                      min={0.01}
                      max={100}
                      step={0.01}
                      value={lotSize}
                      onChange={(e) => setLotSize(parseFloat(e.target.value) || 0.01)}
                      style={{width: '100%', height: '36px', borderRadius: '6px', border: '1px solid var(--border)', background: '#1f2125', padding: '0 10px', color: '#fff', fontSize: '13px'}}
                    />
                  </div>

                  <div style={{marginBottom: '10px'}}>
                    <label style={{display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--muted)', marginBottom: '4px'}}>
                      <span>Risk %</span>
                      <span style={{color: '#fff'}}>{riskPercent}%</span>
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={riskPercent}
                      onChange={(e) => setRiskPercent(parseFloat(e.target.value) || 1)}
                      style={{width: '100%', height: '36px', borderRadius: '6px', border: '1px solid var(--border)', background: '#1f2125', padding: '0 10px', color: '#fff', fontSize: '13px'}}
                    />
                  </div>

                  <div>
                    <label style={{fontSize: '11px', color: 'var(--muted)', marginBottom: '4px'}}>Account Balance</label>
                    <input
                      type="number"
                      value={accountBalance}
                      onChange={(e) => setAccountBalance(parseFloat(e.target.value) || 10000)}
                      style={{width: '100%', height: '36px', borderRadius: '6px', border: '1px solid var(--border)', background: '#1f2125', padding: '0 10px', color: '#fff', fontSize: '13px'}}
                    />
                  </div>
                </div>

                {/* Calculated Values */}
                <div style={{background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border)'}}>
                  <div style={{fontSize: '12px', fontWeight: 600, marginBottom: '10px', color: '#3b82f6', textTransform: 'uppercase'}}>Calculated Values</div>

                  <div style={{marginBottom: '12px', padding: '8px', background: 'rgba(59,130,246,0.1)', borderRadius: '6px'}}>
                    <div style={{fontSize: '10px', color: '#3b82f6'}}>Position Value</div>
                    <div style={{fontSize: '16px', fontWeight: 'bold', color: '#fff', fontFamily: 'var(--font-mono)'}}>${positionValue.toLocaleString(undefined, {maximumFractionDigits: 0})}</div>
                    <div style={{fontSize: '10px', color: 'var(--muted)'}}>{lotSize} lots @ {displayPrice.toLocaleString(undefined, {maximumFractionDigits: ASSET_CONFIG[asset].tickSize < 0.1 ? 2 : 0})}</div>
                  </div>

                  <div style={{marginBottom: '12px', padding: '8px', background: 'rgba(255,109,140,0.1)', borderRadius: '6px'}}>
                    <div style={{fontSize: '10px', color: '#ff6d8c'}}>Risk Amount</div>
                    <div style={{fontSize: '16px', fontWeight: 'bold', color: '#ff6d8c', fontFamily: 'var(--font-mono)'}}>${riskAmount.toFixed(2)}</div>
                    <div style={{fontSize: '10px', color: 'var(--muted)'}}>{riskPercent}% of ${accountBalance.toLocaleString()}</div>
                  </div>

                  <div style={{padding: '8px', background: 'rgba(88,209,122,0.1)', borderRadius: '6px'}}>
                    <div style={{fontSize: '10px', color: '#58d17a'}}>Pip Value</div>
                    <div style={{fontSize: '16px', fontWeight: 'bold', color: '#fff', fontFamily: 'var(--font-mono)'}}>${pipValue.toFixed(4)}</div>
                    <div style={{fontSize: '10px', color: 'var(--muted)'}}>per 1 pip move</div>
                  </div>
                </div>
              </div>
            </div>
            )}
          </div>

          {/* Trade History & Positions */}
          <div className="panel">
              <div className="panel-head">
                  <div>
                      <h2>Trade History & Positions</h2>
                      <p>Live active trades from MT5 terminal</p>
                  </div>
              </div>
              <div className="panel-body">
                 {positions.length > 0 ? (
                     <div className="overflow-x-auto">
                       <table className="finance-table w-full">
                          <thead>
                             <tr>
                                <th style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700, padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)', textAlign: 'left'}}>Ticket</th>
                                <th style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700, padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)', textAlign: 'left'}}>Type</th>
                                <th style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700, padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)', textAlign: 'left'}}>Vol</th>
                                <th style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700, padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)', textAlign: 'left'}}>Open</th>
                                <th style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700, padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)', textAlign: 'left'}}>Current</th>
                                <th style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700, padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)', textAlign: 'left'}}>P/L</th>
                                <th style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700, padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)', textAlign: 'left'}}>Action</th>
                             </tr>
                          </thead>
                          <tbody>
                             {positions.map(pos => (
                               <tr key={pos.ticket}>
                                  <td className="text-muted" style={{padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)'}}>#{pos.ticket}</td>
                                  <td style={{padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)'}}><span className={`badge ${pos.type === 'buy' ? 'badge-up' : 'badge-down'}`}>{pos.type.toUpperCase()}</span></td>
                                  <td className="mono" style={{padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)'}}>{pos.volume}</td>
                                  <td className="mono" style={{padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)'}}>{pos.open_price.toFixed(2)}</td>
                                  <td className="mono" style={{padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)'}}>{pos.current_price.toFixed(2)}</td>
                                  <td className={`mono ${pos.profit >= 0 ? 'text-green' : 'text-red'}`} style={{padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)'}}>{pos.profit >= 0 ? '+' : ''}{pos.profit.toFixed(2)}</td>
                                  <td style={{padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,.05)'}}>
                                    <button onClick={() => closePosition(pos.ticket)} className="btn-primary" style={{height: '26px', fontSize: '11px', padding: '0 8px'}}>Close</button>
                                  </td>
                               </tr>
                             ))}
                          </tbody>
                       </table>
                     </div>
                 ) : <div className="text-muted text-sm text-center py-6">No open positions</div>}
              </div>
          </div>
        </div>

        {/* Right Column: Account Status & Utilities */}
        <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
           
           {/* Account Stats Panel */}
           <div className="panel">
              <div className="panel-head">
                 <div>
                     <h2>Account Status</h2>
                     <p>{account?.account_type ? account.account_type.toUpperCase() : 'Loading...'}</p>
                 </div>
              </div>
              <div className="panel-body" style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
                 <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', borderBottom: '1px solid var(--grid)'}}>
                    <span className="text-sm font-semibold text-muted tracking-wider" style={{textTransform: 'uppercase'}}>Balance</span>
                    <span className="mono text-2xl text-text">${account?.balance?.toFixed(2) || '--'}</span>
                 </div>
                 <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', borderBottom: '1px solid var(--grid)'}}>
                    <span className="text-sm font-semibold text-muted tracking-wider" style={{textTransform: 'uppercase'}}>Equity</span>
                    <span className="mono text-xl text-text">${account?.equity?.toFixed(2) || '--'}</span>
                 </div>
                 <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', borderBottom: '1px solid var(--grid)'}}>
                    <span className="text-sm font-semibold text-muted tracking-wider" style={{textTransform: 'uppercase'}}>Free Margin</span>
                    <span className="mono text-xl text-text">${account?.free_margin?.toFixed(2) || '--'}</span>
                 </div>
                 <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <span className="text-sm font-semibold text-muted tracking-wider" style={{textTransform: 'uppercase'}}>Margin Level</span>
                    <span className={`mono text-xl ${account?.margin_level && account.margin_level < 100 ? 'text-red' : 'text-green'}`}>{account?.margin_level?.toFixed(1) || '--'}%</span>
                 </div>
              </div>
           </div>

           {/* AI Trading Intelligence Panel */}
           <div className="panel">
              <div className="panel-head">
                 <div>
                     <h2>AI Trading Intelligence</h2>
                     <p>Multi-agent analysis & risk assessment</p>
                 </div>
              </div>
              <div className="panel-body" style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
                 {/* MCP Action Buttons */}
                 <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px'}}>
                    <button
                      onClick={async () => {
                        try {
                          const res = await fetch(`${API_BASE}/mcp/market-analysis`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              asset: asset,
                              current_price: currentPrice,
                              support: [currentPrice * 0.99, currentPrice * 0.98],
                              resistance: [currentPrice * 1.01, currentPrice * 1.02],
                              rsi: data?.indicators?.rsi_14,
                              trend: data?.indicators?.trend?.toLowerCase() || 'neutral',
                              price_change_24h: pctChange
                            })
                          })
                          if (res.ok) {
                            const result = await res.json()
                            setAIAnalysis(result)
                          }
                        } catch (err) {
                          console.error('AI Analysis failed:', err)
                        }
                      }}
                      style={{
                        height: '38px',
                        borderRadius: '10px',
                        fontSize: '12px',
                        fontWeight: 600,
                        background: 'rgba(88,209,122,.15)',
                        border: '1px solid rgba(88,209,122,.3)',
                        color: '#58d17a',
                        cursor: 'pointer'
                      }}
                    >
                      Analyze Market
                    </button>
                    <button
                      onClick={async () => {
                        try {
                          const res = await fetch(`${API_BASE}/mcp/run-debate`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              asset: asset,
                              current_price: currentPrice,
                              rounds: 3
                            })
                          })
                          if (res.ok) {
                            const result = await res.json()
                            setAIDebate(result)
                          }
                        } catch (err) {
                          console.error('Debate failed:', err)
                        }
                      }}
                      style={{
                        height: '38px',
                        borderRadius: '10px',
                        fontSize: '12px',
                        fontWeight: 600,
                        background: 'rgba(240,195,107,.15)',
                        border: '1px solid rgba(240,195,107,.3)',
                        color: '#f0c36b',
                        cursor: 'pointer'
                      }}
                    >
                      Run Debate
                    </button>
                 </div>
                 <button
                   onClick={async () => {
                     try {
                       const res = await fetch(`${API_BASE}/mcp/check-risk`, {
                         method: 'POST',
                         headers: { 'Content-Type': 'application/json' },
                         body: JSON.stringify({
                           assets: [asset],
                           portfolio_value: account?.equity || 10000
                         })
                       })
                       if (res.ok) {
                         const result = await res.json()
                         setAIRisk(result)
                       }
                     } catch (err) {
                       console.error('Risk check failed:', err)
                     }
                   }}
                   style={{
                     height: '38px',
                     borderRadius: '10px',
                     fontSize: '12px',
                     fontWeight: 600,
                     background: 'rgba(255,109,140,.15)',
                     border: '1px solid rgba(255,109,140,.3)',
                     color: '#ff6d8c',
                     cursor: 'pointer'
                   }}
                 >
                   Check Risk
                 </button>

                 {/* AI Analysis Results */}
                 {aiAnalysis && aiAnalysis.success && (
                   <div style={{marginTop: '8px', padding: '12px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)'}}>
                      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px'}}>
                         <strong style={{fontSize: '12px', color: 'var(--text)'}}>Sentiment</strong>
                         <span style={{
                           fontSize: '11px',
                           fontWeight: 600,
                           padding: '2px 8px',
                           borderRadius: '6px',
                           background: aiAnalysis.sentiment === 'BULLISH' ? 'rgba(88,209,122,.2)' : aiAnalysis.sentiment === 'BEARISH' ? 'rgba(255,109,140,.2)' : 'rgba(162,169,179,.2)',
                           color: aiAnalysis.sentiment === 'BULLISH' ? '#58d17a' : aiAnalysis.sentiment === 'BEARISH' ? '#ff6d8c' : '#a2a9b3'
                         }}>
                           {aiAnalysis.sentiment}
                         </span>
                      </div>
                      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '8px'}}>
                         <span style={{fontSize: '11px', color: 'var(--muted)'}}>Confidence</span>
                         <span style={{fontSize: '11px', color: 'var(--text)'}}>{Math.round(aiAnalysis.confidence * 100)}%</span>
                      </div>
                      {aiAnalysis.bullish_points?.length > 0 && (
                        <div style={{marginBottom: '8px'}}>
                           <span style={{fontSize: '10px', color: '#58d17a', textTransform: 'uppercase'}}>Bullish</span>
                           <ul style={{margin: '4px 0 0 0', paddingLeft: '16px', fontSize: '11px', color: 'var(--muted)'}}>
                              {aiAnalysis.bullish_points.slice(0, 2).map((p: string, i: number) => (
                                <li key={i}>{p}</li>
                              ))}
                           </ul>
                        </div>
                      )}
                      {aiAnalysis.bearish_points?.length > 0 && (
                        <div>
                           <span style={{fontSize: '10px', color: '#ff6d8c', textTransform: 'uppercase'}}>Bearish</span>
                           <ul style={{margin: '4px 0 0 0', paddingLeft: '16px', fontSize: '11px', color: 'var(--muted)'}}>
                              {aiAnalysis.bearish_points.slice(0, 2).map((p: string, i: number) => (
                                <li key={i}>{p}</li>
                              ))}
                           </ul>
                        </div>
                      )}
                   </div>
                 )}

                 {/* Debate Results */}
                 {aiDebate && aiDebate.success && (
                   <div style={{marginTop: '8px', padding: '12px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)'}}>
                      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px'}}>
                         <strong style={{fontSize: '12px', color: 'var(--text)'}}>Debate Verdict</strong>
                         <span style={{
                           fontSize: '11px',
                           fontWeight: 600,
                           padding: '2px 8px',
                           borderRadius: '6px',
                           background: aiDebate.verdict?.includes('BULL') ? 'rgba(88,209,122,.2)' : aiDebate.verdict?.includes('BEAR') ? 'rgba(255,109,140,.2)' : 'rgba(162,169,179,.2)',
                           color: aiDebate.verdict?.includes('BULL') ? '#58d17a' : aiDebate.verdict?.includes('BEAR') ? '#ff6d8c' : '#a2a9b3'
                         }}>
                           {aiDebate.verdict?.replace(/_/g, ' ')}
                         </span>
                      </div>
                      <div style={{display: 'flex', gap: '8px'}}>
                         <div style={{flex: 1, padding: '8px', borderRadius: '8px', background: 'rgba(88,209,122,.1)'}}>
                            <span style={{fontSize: '10px', color: '#58d17a'}}>BULL WINS</span>
                            <div style={{fontSize: '16px', fontWeight: 'bold', color: '#58d17a'}}>{aiDebate.bull_wins}</div>
                         </div>
                         <div style={{flex: 1, padding: '8px', borderRadius: '8px', background: 'rgba(255,109,140,.1)'}}>
                            <span style={{fontSize: '10px', color: '#ff6d8c'}}>BEAR WINS</span>
                            <div style={{fontSize: '16px', fontWeight: 'bold', color: '#ff6d8c'}}>{aiDebate.bear_wins}</div>
                         </div>
                      </div>
                   </div>
                 )}

                 {/* Risk Results */}
                 {aiRisk && aiRisk.success && (
                   <div style={{marginTop: '8px', padding: '12px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)'}}>
                      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px'}}>
                         <strong style={{fontSize: '12px', color: 'var(--text)'}}>Risk Level</strong>
                         <span style={{
                           fontSize: '11px',
                           fontWeight: 600,
                           padding: '2px 8px',
                           borderRadius: '6px',
                           background: aiRisk.risk_level === 'LOW' ? 'rgba(88,209,122,.2)' : aiRisk.risk_level === 'MEDIUM' ? 'rgba(240,195,107,.2)' : 'rgba(255,109,140,.2)',
                           color: aiRisk.risk_level === 'LOW' ? '#58d17a' : aiRisk.risk_level === 'MEDIUM' ? '#f0c36b' : '#ff6d8c'
                         }}>
                           {aiRisk.risk_level}
                         </span>
                      </div>
                      <div style={{marginBottom: '8px'}}>
                         <div style={{fontSize: '10px', color: 'var(--muted)', marginBottom: '4px'}}>Risk Score</div>
                         <div style={{height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.1)', overflow: 'hidden'}}>
                            <div style={{
                              width: `${Math.round(aiRisk.risk_score * 100)}%`,
                              height: '100%',
                              background: aiRisk.risk_score < 0.3 ? '#58d17a' : aiRisk.risk_score < 0.6 ? '#f0c36b' : '#ff6d8c'
                            }} />
                         </div>
                         <div style={{fontSize: '10px', color: 'var(--muted)', textAlign: 'right', marginTop: '2px'}}>{Math.round(aiRisk.risk_score * 100)}%</div>
                      </div>
                      {aiRisk.alerts && aiRisk.alerts.length > 0 && (
                        <div style={{fontSize: '11px', color: '#ff6d8c'}}>
                           ⚠️ {aiRisk.alerts.length} risk alert{aiRisk.alerts.length > 1 ? 's' : ''}
                        </div>
                      )}
                   </div>
                 )}
              </div>
           </div>

           {/* Indicator Summary Panel */}
           <div className="panel">
               <div className="panel-head">
                   <div>
                       <h2>Indicator Summary</h2>
                       <p>Real-time derived metrics</p>
                   </div>
               </div>
               <div className="panel-body">
                  <div className="source-list" style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px'}}>
                     <div className="source-item" style={{background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '12px', border: '1px solid var(--border)'}}>
                        <strong style={{display: 'block', fontSize: '13px'}}>Trend</strong>
                        <span className="mono" style={{fontSize: '12px', color: 'var(--muted)'}}>{data?.indicators?.trend?.replace('_', ' ').toUpperCase() || '--'}</span>
                     </div>
                     <div className="source-item" style={{background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '12px', border: '1px solid var(--border)'}}>
                        <strong style={{display: 'block', fontSize: '13px'}}>MACD Hist</strong>
                        <span className="mono" style={{fontSize: '12px', color: 'var(--muted)'}}>{data?.indicators?.macd_histogram?.toFixed(4) || '--'}</span>
                     </div>
                     <div className="source-item" style={{background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '12px', border: '1px solid var(--border)'}}>
                        <strong style={{display: 'block', fontSize: '13px'}}>ATR (14)</strong>
                        <span className="mono" style={{fontSize: '12px', color: 'var(--muted)'}}>{data?.indicators?.atr_14?.toFixed(2) || '--'}</span>
                     </div>
                     <div className="source-item" style={{background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '12px', border: '1px solid var(--border)'}}>
                        <strong style={{display: 'block', fontSize: '13px'}}>BB Width</strong>
                        <span className="mono" style={{fontSize: '12px', color: 'var(--muted)'}}>{data?.indicators?.bb_percent ? (data.indicators.bb_percent * 100).toFixed(1) + '%' : '--'}</span>
                     </div>
                  </div>
               </div>
           </div>

           {/* Gold Converter Panel */}
           <div className="panel">
              <div className="panel-head">
                 <div>
                     <h2>Gold Converter</h2>
                     <p>Secondary utility, kept below the quote card</p>
                 </div>
              </div>
              <div className="panel-body">
                 <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px'}}>
                    <div style={{display: 'flex', flexDirection: 'column', gap: '6px'}}>
                       <label style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700}}>Amount</label>
                       <input type="number" value={convAmount} onChange={(e) => setConvAmount(Number(e.target.value))} style={{height: '42px', borderRadius: '12px', border: '1px solid var(--border)', background: '#1f2125', padding: '0 12px', outline: 'none', color: 'var(--text)'}} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', gap: '6px'}}>
                       <label style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700}}>Unit</label>
                       <select value={convUnit} onChange={(e) => setConvUnit(e.target.value)} style={{height: '42px', borderRadius: '12px', border: '1px solid var(--border)', background: '#1f2125', padding: '0 12px', outline: 'none', color: 'var(--text)'}}>
                          <option value="oz">Troy oz</option>
                          <option value="g">Grams</option>
                          <option value="kg">Kilograms</option>
                          <option value="tola">Tola</option>
                       </select>
                    </div>
                 </div>
                 <div style={{display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '12px'}}>
                    <label style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700}}>Currency</label>
                    <select value={convCurrency} onChange={(e) => setConvCurrency(e.target.value)} style={{height: '42px', borderRadius: '12px', border: '1px solid var(--border)', background: '#1f2125', padding: '0 12px', outline: 'none', color: 'var(--text)'}}>
                       <option value="USD">USD</option>
                       <option value="NGN">NGN</option>
                       <option value="EUR">EUR</option>
                       <option value="GBP">GBP</option>
                    </select>
                 </div>
                 <div style={{marginTop: '12px', padding: '12px', borderRadius: '12px', border: '1px solid var(--border)', background: '#1d1f23'}}>
                    <strong style={{display: 'block', fontSize: '18px'}}>{new Intl.NumberFormat('en-US', {style: 'currency', currency: convCurrency, maximumFractionDigits: convCurrency === 'NGN' ? 0 : 2}).format(getConvertedValue())}</strong>
                    <div style={{fontSize: '12px', color: 'var(--muted)'}}>{convAmount} {convUnit} of gold in {convCurrency}</div>
                 </div>
              </div>
           </div>

           {/* Data Sources API Status Panel */}
           <div className="panel">
              <div className="panel-head">
                 <div>
                     <h2>Data Sources Race</h2>
                     <p>Live API status & standby endpoints</p>
                 </div>
                 <Activity className="text-muted w-4 h-4" />
              </div>
              <div className="panel-body">
                 <div style={{display: 'flex', flexDirection: 'column', gap: '8px'}}>
                     {/* Twelve Data */}
                     <div style={{display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: '10px', background: data?.status?.active_source === '12Data' ? 'rgba(88,209,122,.05)' : 'var(--surface-3)', border: data?.status?.active_source === '12Data' ? '1px solid rgba(88,209,122,.2)' : '1px solid var(--border)'}}>
                         <div>
                             <strong style={{display: 'block', fontSize: '13px', color: data?.status?.active_source === '12Data' ? '#58d17a' : 'var(--text)'}}>Twelve Data API</strong>
                             <span style={{fontSize: '11px', color: 'var(--muted)'}}>Primary XAU/USD feed</span>
                         </div>
                         <div style={{textAlign: 'right'}}>
                             <span className="badge" style={{background: 'transparent', border: 'none', padding: 0, color: data?.status?.active_source === '12Data' ? '#58d17a' : 'var(--muted)', fontSize: '11px'}}>{data?.status?.active_source === '12Data' ? '🟢 ACTIVE' : '⏸ STANDBY'}</span>
                         </div>
                     </div>
                     {/* Binance */}
                     <div style={{display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: '10px', background: data?.status?.active_source === 'Binance' ? 'rgba(240,195,107,.05)' : 'var(--surface-3)', border: data?.status?.active_source === 'Binance' ? '1px solid rgba(240,195,107,.2)' : '1px solid var(--border)'}}>
                         <div>
                             <strong style={{display: 'block', fontSize: '13px', color: data?.status?.active_source === 'Binance' ? '#f0c36b' : 'var(--text)'}}>Binance (PAXG)</strong>
                             <span style={{fontSize: '11px', color: 'var(--muted)'}}>Proxy fallback race</span>
                         </div>
                         <div style={{textAlign: 'right'}}>
                             <span className="badge" style={{background: 'transparent', border: 'none', padding: 0, color: data?.status?.active_source === 'Binance' ? '#f0c36b' : 'var(--muted)', fontSize: '11px'}}>{data?.status?.active_source === 'Binance' ? '🟡 BACKUP LIVE' : '⏸ STANDBY'}</span>
                         </div>
                     </div>
                     {/* Kraken */}
                     <div style={{display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: '10px', background: data?.status?.active_source === 'Kraken' ? 'rgba(240,195,107,.05)' : 'var(--surface-3)', border: data?.status?.active_source === 'Kraken' ? '1px solid rgba(240,195,107,.2)' : '1px solid var(--border)'}}>
                         <div>
                             <strong style={{display: 'block', fontSize: '13px', color: data?.status?.active_source === 'Kraken' ? '#f0c36b' : 'var(--text)'}}>Kraken (PAXG)</strong>
                             <span style={{fontSize: '11px', color: 'var(--muted)'}}>Proxy fallback race</span>
                         </div>
                         <div style={{textAlign: 'right'}}>
                             <span className="badge" style={{background: 'transparent', border: 'none', padding: 0, color: data?.status?.active_source === 'Kraken' ? '#f0c36b' : 'var(--muted)', fontSize: '11px'}}>{data?.status?.active_source === 'Kraken' ? '🟡 BACKUP LIVE' : '⏸ STANDBY'}</span>
                         </div>
                     </div>
                     {/* CoinGecko */}
                     <div style={{display: 'flex', justifyContent: 'space-between', padding: '10px 12px', borderRadius: '10px', background: data?.status?.active_source === 'CoinGecko' ? 'rgba(240,195,107,.05)' : 'var(--surface-3)', border: data?.status?.active_source === 'CoinGecko' ? '1px solid rgba(240,195,107,.2)' : '1px solid var(--border)'}}>
                         <div>
                             <strong style={{display: 'block', fontSize: '13px', color: data?.status?.active_source === 'CoinGecko' ? '#f0c36b' : 'var(--text)'}}>CoinGecko (PAXG)</strong>
                             <span style={{fontSize: '11px', color: 'var(--muted)'}}>Proxy fallback race</span>
                         </div>
                         <div style={{textAlign: 'right'}}>
                             <span className="badge" style={{background: 'transparent', border: 'none', padding: 0, color: data?.status?.active_source === 'CoinGecko' ? '#f0c36b' : 'var(--muted)', fontSize: '11px'}}>{data?.status?.active_source === 'CoinGecko' ? '🟡 BACKUP LIVE' : '⏸ STANDBY'}</span>
                         </div>
                     </div>
                 </div>
              </div>
           </div>

           {/* Alerts Panel */}
           <div className="panel">
              <div className="panel-head">
                 <div>
                     <h2>Price Alerts</h2>
                     <p>Keep alerts, but quieter than the main market card</p>
                 </div>
              </div>
              <div className="panel-body">
                 <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px'}}>
                    <div style={{display: 'flex', flexDirection: 'column', gap: '6px'}}>
                       <label style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700}}>Target</label>
                       <input type="number" placeholder="4660" value={alertTarget} onChange={(e) => setAlertTarget(e.target.value)} style={{height: '42px', borderRadius: '12px', border: '1px solid var(--border)', background: '#1f2125', padding: '0 12px', outline: 'none', color: 'var(--text)'}} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', gap: '6px'}}>
                       <label style={{fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--faint)', fontWeight: 700}}>Condition</label>
                       <select value={alertCond} onChange={(e) => setAlertCond(e.target.value)} style={{height: '42px', borderRadius: '12px', border: '1px solid var(--border)', background: '#1f2125', padding: '0 12px', outline: 'none', color: 'var(--text)'}}>
                          <option value="above">Price ≥</option>
                          <option value="below">Price ≤</option>
                       </select>
                    </div>
                 </div>
                 <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '12px'}}>
                    <button onClick={() => {
                       if(alertTarget && !isNaN(Number(alertTarget))) {
                          setAlertsList([...alertsList, {p: Number(alertTarget), cond: alertCond}])
                          setAlertTarget('')
                       }
                    }} style={{height: '42px', borderRadius: '12px', fontSize: '13px', fontWeight: 600, background: '#262a31', border: '1px solid var(--border)', color: 'var(--text)'}}>Add Alert</button>
                    <button onClick={enableAlerts} style={{height: '42px', borderRadius: '12px', fontSize: '13px', fontWeight: 600, background: 'rgba(240,195,107,.11)', border: '1px solid rgba(240,195,107,.18)', color: 'var(--gold)'}}>Enable Notify</button>
                 </div>
                 
                 <div style={{display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '12px'}}>
                    {alertsList.length === 0 ? (
                       <div style={{padding: '12px', borderRadius: '12px', border: '1px solid var(--border)', background: '#1d1f23'}}>
                          <strong style={{display: 'block', fontSize: '13px'}}>No alerts yet</strong>
                          <span style={{fontSize: '12px', color: 'var(--muted)'}}>Add one above to monitor price</span>
                       </div>
                    ) : (
                       alertsList.map((a, i) => (
                           <div key={i} style={{padding: '12px', borderRadius: '12px', border: '1px solid var(--border)', background: '#1d1f23'}}>
                              <strong style={{display: 'block', fontSize: '13px'}}>Gold {a.cond === 'above' ? '≥' : '≤'} {a.p.toLocaleString()}</strong>
                              <span style={{fontSize: '12px', color: 'var(--muted)'}}>Browser alert active</span>
                           </div>
                       ))
                    )}
                 </div>
                 <div style={{fontSize: '11px', color: 'var(--faint)', marginTop: '12px'}}>Alerts fire in-browser only. Trading stays broker-first.</div>
              </div>
           </div>
           
        </div>
      </div>
    </div>
  )
}

