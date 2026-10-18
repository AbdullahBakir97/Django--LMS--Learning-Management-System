const month = new Intl.DateTimeFormat(undefined, { month: 'short', year: 'numeric' })

export function dateRange(start: string, end: string | null): string {
  const from = month.format(new Date(start))
  return `${from} – ${end ? month.format(new Date(end)) : 'present'}`
}
