import type { Bill, PlayerInput } from './types'

const BASE = (import.meta.env.VITE_API_BASE ?? '') + '/api'

export async function createBill(payload: {
  total_cost: number
  court_name: string
  note: string
  split_mode: 'equal' | 'hours'
  players: PlayerInput[]
  host_name: string | null
}): Promise<{ id: string }> {
  const res = await fetch(`${BASE}/bills`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...payload,
      players: payload.players.map((p) => ({
        name: p.name,
        hours: payload.split_mode === 'hours' ? parseFloat(p.hours) : undefined,
      })),
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? 'Failed to create bill')
  }
  return res.json()
}

export async function fetchBill(id: string): Promise<Bill> {
  const res = await fetch(`${BASE}/bills/${id}`)
  if (!res.ok) throw new Error('Bill not found')
  return res.json()
}
