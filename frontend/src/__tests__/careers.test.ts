import { describe, expect, it } from 'vitest'
import { salary } from '@/api/careers'

describe('salary', () => {
  it('formats a band, an open end, or nothing', () => {
    expect(salary({ salary_min: 1200, salary_max: 1800, currency: 'JOD' })).toBe('1,200–1,800 JOD')
    expect(salary({ salary_min: 900, salary_max: null, currency: 'EUR' })).toBe('from 900 EUR')
    expect(salary({ salary_min: null, salary_max: 50000, currency: 'USD' })).toBe('up to 50,000 USD')
    expect(salary({ salary_min: null, salary_max: null, currency: '' })).toBe('')
  })
})
