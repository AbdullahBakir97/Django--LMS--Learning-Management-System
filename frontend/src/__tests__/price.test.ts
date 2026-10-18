import { describe, expect, it } from 'vitest'
import { price } from '@/api/learning'

describe('price', () => {
  it('formats cents in the course currency, or says free', () => {
    expect(price({ price_cents: 2900, currency: 'usd' })).toBe('$29.00')
    expect(price({ price_cents: 1250, currency: 'eur' })).toBe('€12.50')
    expect(price({ price_cents: 0, currency: 'usd' })).toBe('Free')
  })
})
