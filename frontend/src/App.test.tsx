import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App component', () => {
  it('renders the logos and heading', () => {
    render(<App />)

    // the Vite + React + TypeScript heading
    expect(
      screen.getByRole('heading', { name: /vite \+ react \+ typescript/i })
    ).toBeInTheDocument()

    // both logos should be present
    expect(screen.getByAltText(/vite logo/i)).toBeInTheDocument()
    expect(screen.getByAltText(/react logo/i)).toBeInTheDocument()
  })

  it('increments the count when the button is clicked', async () => {
    const user = userEvent.setup()
    render(<App />)

    const button = screen.getByRole('button', { name: /count is 0/i })
    expect(button).toBeInTheDocument()

    await user.click(button)
    expect(screen.getByRole('button', { name: /count is 1/i })).toBeInTheDocument()
  })
})

