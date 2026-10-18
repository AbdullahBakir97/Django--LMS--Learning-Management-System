import DOMPurify from 'dompurify'
import { marked } from 'marked'

/** Lesson content is instructor-authored markdown; sanitize before it touches the DOM. */
export function renderMarkdown(source: string): string {
  return DOMPurify.sanitize(marked.parse(source, { async: false }))
}
