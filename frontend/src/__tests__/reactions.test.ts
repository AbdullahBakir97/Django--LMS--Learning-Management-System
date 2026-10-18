import { describe, expect, it } from 'vitest'
import { applyReaction, total } from '@/features/engagement/reactions'

describe('applyReaction', () => {
  it('adds, switches and clears the viewer reaction', () => {
    const start = { counts: { like: 2 }, mine: null }
    const liked = applyReaction(start, 'like')
    expect(liked).toEqual({ counts: { like: 3 }, mine: 'like' })
    const switched = applyReaction(liked, 'insightful')
    expect(switched).toEqual({ counts: { like: 2, insightful: 1 }, mine: 'insightful' })
    expect(applyReaction(switched, null)).toEqual({ counts: { like: 2 }, mine: null })
  })

  it('drops kinds that reach zero and totals the rest', () => {
    const only = applyReaction({ counts: { support: 1 }, mine: 'support' }, null)
    expect(only).toEqual({ counts: {}, mine: null })
    expect(total({ counts: { like: 2, celebrate: 3 }, mine: null })).toBe(5)
  })
})
