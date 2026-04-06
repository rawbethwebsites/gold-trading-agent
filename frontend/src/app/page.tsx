'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  Bar
} from 'recharts'
import { TrendingUp, TrendingDown, Activity, DollarSign, Bell, Settings, Wallet, Shield, AlertTriangle } from 'lucide-react'

const API_BASE = 'http://localhost:8000/api'
const POLLING_INTERVAL = 5000 // 5 seconds

interface DashboardData {
  status: {
    connected: boolean
    is_trading: boolean
    symbol: string
    can_trade: boolean
    error: string | null
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

export default function GoldTradingDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch data from backend
  const fetchData = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/dashboard`)
      if (!response.ok) {
        throw new Error('Failed to fetch data')
      }
      const dashboardData = await response.json()
      setData(dashboardData)
      setError(null)
    } catch (err) {
      setError('Cannot connect to backend. Is it running on port 8000?')
    } finally {
      setLoading(false)
    }
  }, [])

  // Poll data every 5 seconds
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, POLLING_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchData])

  // Close position handler
  const closePosition = async (ticket: number) => {
    try {
      const response = await fetch(`${API_BASE}/positions/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket })
      })
      if (response.ok) {
        fetchData() // Refresh data
      }
    } catch (err) {
      console.error('Failed to close position:', err)
    }
  }

  const closeAllPositions = async () => {
    try {
      await fetch(`${API_BASE}/positions/close-all`, { method: 'POST' })
      fetchData()
    } catch (err) {
      console.error('Failed to close all positions:', err)
    }
  }

  // Helper to get signal display
  const getSignalDisplay = () => {
    if (!data?.signal) return { text: 'HOLD', color: 'neutral', strength: 'N/A' }
    const signal = data.signal
    return {
      text: signal.type.toUpperCase(),
      color: signal.type === 'buy' ? 'bullish' : signal.type === 'sell' ? 'bearish' : 'neutral',
      strength: `${Math.round(signal.confidence * 100)}% confidence`,
      reasons: signal.reasons
    }
  }

  const signal = getSignalDisplay()
  const indicators = data?.indicators
  const price = data?.price
  const account = data?.account
  const positions = data?.positions || []

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 p-4">
      {/* Error Banner */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-xl p-4 mb-6 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <span className="text-red-200">{error}</span>
        </div>
      )}

      {/* Header */}
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gold-text">Gold Trading Agent</h1>
          <p className="text-slate-400 text-sm mt-1">Exness + MT5 Local-First Trading</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Connection Status */}
          <div className="flex items-center gap-2 bg-slate-900 rounded-lg px-3 py-2">
            <span className={`w-2 h-2 rounded-full ${
              data?.status?.connected ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm text-slate-400">
              {data?.status?.connected ? 'MT5 Connected' : 'Disconnected'}
            </span>
          </div>
          {/* Trading Status */}
          <div className={`flex items-center gap-2 rounded-lg px-3 py-2 ${
            account?.can_trade ? 'bg-green-900/30 border border-green-700' : 'bg-slate-900'
          }`}>
            <Shield className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-400">
              {account?.can_trade ? 'Trading Enabled' : 'Trading Disabled'}
            </span>
          </div>
          <button className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition">
            <Bell className="w-5 h-5" />
          </button>
          <button className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {/* Price Card */}
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-sm">XAU/USD Price</span>
            <DollarSign className="w-5 h-5 text-slate-500" />
          </div>
          <div className="text-3xl font-bold">
            {price ? `$${price.close.toFixed(2)}` : '--'}
          </div>
          <div className="flex items-center gap-2 mt-2 text-slate-400 text-sm">
            <span>Spread: {price && price.ask && price.bid ? (price.ask - price.bid).toFixed(2) : '--'}</span>
          </div>
        </div>

        {/* Signal Card */}
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-sm">Signal</span>
            <Activity className="w-5 h-5 text-slate-500" />
          </div>
          <div className={`text-3xl font-bold ${signal.color}`}>
            {signal.text}
          </div>
          <div className="text-slate-400 text-sm mt-2">{signal.strength}</div>
          {signal.reasons && (
            <div className="text-xs text-slate-500 mt-1">
              {signal.reasons.slice(0, 2).join(', ')}
            </div>
          )}
        </div>

        {/* RSI Card */}
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-sm">RSI (14)</span>
          </div>
          <div className="text-3xl font-bold">
            {indicators?.rsi_14?.toFixed(2) || '--'}
          </div>
          <div className={`text-sm mt-2 ${
            indicators?.rsi_14 && indicators.rsi_14 < 30 ? 'text-green-400' :
            indicators?.rsi_14 && indicators.rsi_14 > 70 ? 'text-red-400' : 'text-slate-400'
          }`}>
            {indicators?.rsi_14 && indicators.rsi_14 < 30 ? 'Oversold' :
             indicators?.rsi_14 && indicators.rsi_14 > 70 ? 'Overbought' : 'Neutral'}
          </div>
        </div>

        {/* Trend Card */}
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 text-sm">Trend</span>
          </div>
          <div className={`text-2xl font-bold ${
            indicators?.trend?.includes('bullish') ? 'bullish' :
            indicators?.trend?.includes('bearish') ? 'bearish' : 'neutral'
          }`}>
            {indicators?.trend?.replace('_', ' ').toUpperCase() || '--'}
          </div>
          <div className="text-slate-400 text-sm mt-2">
            Strength: {(indicators?.signal_strength || 0).toFixed(2)}
          </div>
        </div>
      </div>

      {/* Account & Positions Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Account Info */}
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Wallet className="w-5 h-5 text-slate-400" />
              Account
            </h3>
            <span className={`text-xs px-2 py-1 rounded ${
              account?.account_type === 'demo' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'
            }`}>
              {account?.account_type?.toUpperCase() || 'N/A'}
            </span>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-400">Balance</span>
              <span className="font-mono">${account?.balance?.toFixed(2) || '--'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Equity</span>
              <span className="font-mono">${account?.equity?.toFixed(2) || '--'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Free Margin</span>
              <span className="font-mono">${account?.free_margin?.toFixed(2) || '--'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Margin Level</span>
              <span className={`font-mono ${
                account?.margin_level && account.margin_level < 100 ? 'text-red-400' : ''
              }`}>
                {account?.margin_level?.toFixed(1) || '--'}%
              </span>
            </div>
          </div>
        </div>

        {/* Open Positions */}
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Open Positions ({positions.length})</h3>
            {positions.length > 0 && (
              <button
                onClick={closeAllPositions}
                className="text-xs bg-red-900/50 hover:bg-red-800 text-red-200 px-3 py-1 rounded transition"
              >
                Close All
              </button>
            )}
          </div>
          {positions.length === 0 ? (
            <div className="text-slate-500 text-center py-8">No open positions</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-800">
                    <th className="text-left py-2">Ticket</th>
                    <th className="text-left py-2">Type</th>
                    <th className="text-right py-2">Volume</th>
                    <th className="text-right py-2">Open Price</th>
                    <th className="text-right py-2">Current</th>
                    <th className="text-right py-2">P/L</th>
                    <th className="text-center py-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.ticket} className="border-b border-slate-800/50">
                      <td className="py-2 text-slate-300">#{pos.ticket}</td>
                      <td className={`py-2 font-medium ${
                        pos.type === 'buy' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {pos.type.toUpperCase()}
                      </td>
                      <td className="text-right py-2 font-mono">{pos.volume}</td>
                      <td className="text-right py-2 font-mono">{pos.open_price.toFixed(2)}</td>
                      <td className="text-right py-2 font-mono">{pos.current_price.toFixed(2)}</td>
                      <td className={`text-right py-2 font-mono ${
                        pos.profit >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {pos.profit >= 0 ? '+' : ''}{pos.profit.toFixed(2)}
                      </td>
                      <td className="text-center py-2">
                        <button
                          onClick={() => closePosition(pos.ticket)}
                          className="text-xs bg-slate-800 hover:bg-slate-700 px-2 py-1 rounded transition"
                        >
                          Close
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Price Chart */}
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <h3 className="text-lg font-semibold mb-4">Price Action</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={indicators ? [indicators] : []}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FFD700" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#FFD700" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="timestamp" stroke="#64748b" hide />
                <YAxis stroke="#64748b" domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none' }}
                />
                <Line type="monotone" dataKey="price" stroke="#FFD700" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="ema_9" stroke="#22c55e" dot={false} strokeDasharray="5 5" />
                <Line type="monotone" dataKey="ema_21" stroke="#3b82f6" dot={false} strokeDasharray="5 5" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-4 justify-center text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-yellow-400" />
              <span className="text-slate-400">Price</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-green-500" />
              <span className="text-slate-400">EMA 9</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-blue-500" />
              <span className="text-slate-400">EMA 21</span>
            </div>
          </div>
        </div>

        {/* RSI Chart */}
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <h3 className="text-lg font-semibold mb-4">RSI Indicator</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={indicators ? [indicators] : []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="timestamp" stroke="#64748b" hide />
                <YAxis stroke="#64748b" domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none' }}
                />
                <Area type="monotone" dataKey="rsi_14" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} />
                <Line dataKey={() => 70} stroke="#ef4444" strokeDasharray="3 3" dot={false} />
                <Line dataKey={() => 30} stroke="#22c55e" strokeDasharray="3 3" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-4 justify-center text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-purple-500" />
              <span className="text-slate-400">RSI</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-red-500" />
              <span className="text-slate-400">Overbought (70)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-0.5 bg-green-500" />
              <span className="text-slate-400">Oversold (30)</span>
            </div>
          </div>
        </div>
      </div>

      {/* MACD Chart */}
      <div className="bg-slate-900 rounded-xl p-6 border border-slate-800 mb-6">
        <h3 className="text-lg font-semibold mb-4">MACD</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={indicators ? [indicators] : []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="timestamp" stroke="#64748b" hide />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: 'none' }}
              />
              <Line type="monotone" dataKey="macd" stroke="#3b82f6" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="flex gap-4 mt-4 justify-center text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-blue-500" />
            <span className="text-slate-400">MACD</span>
          </div>
        </div>
      </div>

      {/* Indicators Summary */}
      <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
        <h3 className="text-lg font-semibold mb-4">Technical Indicators</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm">EMA 9</div>
            <div className="text-xl font-mono mt-1">{indicators?.ema_9?.toFixed(2) || '--'}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm">EMA 21</div>
            <div className="text-xl font-mono mt-1">{indicators?.ema_21?.toFixed(2) || '--'}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm">SMA 50</div>
            <div className="text-xl font-mono mt-1">{indicators?.sma_50?.toFixed(2) || '--'}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm">ATR (14)</div>
            <div className="text-xl font-mono mt-1">{indicators?.atr_14?.toFixed(2) || '--'}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm">BB Upper</div>
            <div className="text-xl font-mono mt-1">{indicators?.bb_upper?.toFixed(2) || '--'}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm">BB Lower</div>
            <div className="text-xl font-mono mt-1">{indicators?.bb_lower?.toFixed(2) || '--'}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm">BB %</div>
            <div className={`text-xl font-mono mt-1 ${
              indicators?.bb_percent && indicators.bb_percent < 0 ? 'text-green-400' :
              indicators?.bb_percent && indicators.bb_percent > 1 ? 'text-red-400' : ''
            }`}>
              {indicators?.bb_percent ? (indicators.bb_percent * 100).toFixed(1) + '%' : '--'}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-slate-400 text-sm">MACD Hist</div>
            <div className={`text-xl font-mono mt-1 ${
              indicators?.macd_histogram && indicators.macd_histogram > 0 ? 'text-green-400' :
              indicators?.macd_histogram && indicators.macd_histogram < 0 ? 'text-red-400' : ''
            }`}>
              {indicators?.macd_histogram?.toFixed(4) || '--'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
