/** In-app fan-out for live events: the socket emits, any feature listens. */
type Handler = (data: Record<string, unknown>) => void
const handlers = new Map<string, Set<Handler>>()

export const bus = {
  on(event: string, handler: Handler): () => void {
    if (!handlers.has(event)) handlers.set(event, new Set())
    handlers.get(event)!.add(handler)
    return () => handlers.get(event)?.delete(handler)
  },
  emit(event: string, data: Record<string, unknown>) {
    handlers.get(event)?.forEach((h) => h(data))
  },
}
