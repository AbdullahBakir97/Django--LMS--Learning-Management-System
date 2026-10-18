import { PhHandHeart, PhLightbulb, PhConfetti, PhThumbsUp } from '@phosphor-icons/vue'
import type { ReactionKind, ReactionSummary } from '@/api/engagement'

export const reactionKinds: { kind: ReactionKind; label: string; icon: typeof PhThumbsUp }[] = [
  { kind: 'like', label: 'Like', icon: PhThumbsUp },
  { kind: 'celebrate', label: 'Celebrate', icon: PhConfetti },
  { kind: 'insightful', label: 'Insightful', icon: PhLightbulb },
  { kind: 'support', label: 'Support', icon: PhHandHeart },
]

export const total = (s: ReactionSummary) => Object.values(s.counts).reduce((a, b) => a + (b ?? 0), 0)

/** The summary after the viewer picks `kind` (or clears it), applied before the server answers. */
export function applyReaction(s: ReactionSummary, kind: ReactionKind | null): ReactionSummary {
  const counts = { ...s.counts }
  if (s.mine) counts[s.mine] = (counts[s.mine] ?? 1) - 1
  if (kind) counts[kind] = (counts[kind] ?? 0) + 1
  for (const k of Object.keys(counts) as ReactionKind[]) if (!counts[k]) delete counts[k]
  return { counts, mine: kind }
}
