import { describe, expect, it } from 'vitest'
import { renderMarkdown } from '@/features/learning/markdown'

describe('renderMarkdown', () => {
  it('renders instructor markdown', () => {
    expect(renderMarkdown('## Title\n\n**bold**')).toContain('<strong>bold</strong>')
  })

  it('strips scripts and inline handlers', () => {
    const html = renderMarkdown('<script>alert(1)</script><img src=x onerror="alert(1)">')
    expect(html).not.toContain('<script')
    expect(html).not.toContain('onerror')
  })
})
