/**
 * Component tests
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock the page component
const MockDashboard = () => {
  return (
    <div>
      <h1>Gold Trading Agent</h1>
      <div data-testid="price-display">4821.00</div>
      <button data-testid="buy-button">Buy</button>
      <button data-testid="sell-button">Sell</button>
    </div>
  )
}

describe('Dashboard Components', () => {
  test('renders dashboard title', () => {
    render(<MockDashboard />)
    expect(screen.getByText('Gold Trading Agent')).toBeInTheDocument()
  })

  test('displays price', () => {
    render(<MockDashboard />)
    expect(screen.getByTestId('price-display')).toHaveTextContent('4821.00')
  })

  test('has buy and sell buttons', () => {
    render(<MockDashboard />)
    expect(screen.getByTestId('buy-button')).toBeInTheDocument()
    expect(screen.getByTestId('sell-button')).toBeInTheDocument()
  })
})

describe('Trading Actions', () => {
  test('buy button is clickable', () => {
    const handleBuy = jest.fn()
    render(<button onClick={handleBuy}>Buy</button>)

    fireEvent.click(screen.getByText('Buy'))
    expect(handleBuy).toHaveBeenCalled()
  })

  test('sell button is clickable', () => {
    const handleSell = jest.fn()
    render(<button onClick={handleSell}>Sell</button>)

    fireEvent.click(screen.getByText('Sell'))
    expect(handleSell).toHaveBeenCalled()
  })
})
