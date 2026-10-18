const day = new Intl.DateTimeFormat('en', { weekday: 'short', day: 'numeric', month: 'short' })
const time = new Intl.DateTimeFormat('en', { hour: 'numeric', minute: '2-digit' })
const month = new Intl.DateTimeFormat('en', { month: 'short' })

/** The date tile: "OCT" over "24". */
export const tile = (iso: string) => {
  const d = new Date(iso)
  return { month: month.format(d).toUpperCase(), day: String(d.getDate()) }
}

/** "Fri 24 Oct, 6:00 PM – 8:00 PM", or both dates when it spans days. */
export function when(startIso: string, endIso: string): string {
  const s = new Date(startIso)
  const e = new Date(endIso)
  const sameDay = s.toDateString() === e.toDateString()
  return sameDay
    ? `${day.format(s)}, ${time.format(s)} – ${time.format(e)}`
    : `${day.format(s)}, ${time.format(s)} – ${day.format(e)}, ${time.format(e)}`
}

/** A value for <input type="datetime-local"> from a Date, in local time. */
export function localInput(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
