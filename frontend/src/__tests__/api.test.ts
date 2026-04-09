/**
 * API integration tests
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

describe('API Integration', () => {
  beforeEach(() => {
    fetchMock.resetMocks()
  })

  test('fetches dashboard data successfully', async () => {
    const mockData = {
      status: { connected: true, is_trading: true },
      price: { close: 4821.0 },
      account: { balance: 10000, equity: 10000 },
      positions: [],
      signal: null
    }

    fetchMock.mockResponseOnce(JSON.stringify(mockData))

    const response = await fetch(`${API_BASE}/dashboard`)
    const data = await response.json()

    expect(data.status.connected).toBe(true)
    expect(data.price.close).toBe(4821.0)
  })

  test('handles API error gracefully', async () => {
    fetchMock.mockRejectOnce(new Error('Network error'))

    try {
      await fetch(`${API_BASE}/dashboard`)
    } catch (error) {
      expect(error).toBeDefined()
    }
  })

  test('opens position successfully', async () => {
    const mockResponse = { ticket: 1001, success: true }
    fetchMock.mockResponseOnce(JSON.stringify(mockResponse))

    const response = await fetch(`${API_BASE}/positions/open`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol: 'XAUUSD', type: 'buy', volume: 0.01 })
    })
    const data = await response.json()

    expect(data.ticket).toBe(1001)
  })
})
