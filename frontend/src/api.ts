import type { Bill, GroupMember, PlayerInput } from './types'

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
  }
}

const BASE = (import.meta.env.VITE_API_BASE ?? '') + '/api'

export async function createBill(payload: {
  total_cost: number
  court_name: string
  note: string
  split_mode: 'equal' | 'hours'
  players: PlayerInput[]
  host_name: string | null
  group_id: string | null
  session_hours: number | null
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
      group_id: payload.group_id,
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

export async function fetchGroupMembers(groupId: string): Promise<GroupMember[]> {
  const res = await fetch(`${BASE}/group/${groupId}/members`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new ApiError(err.detail ?? 'Failed to fetch group members', res.status)
  }
  const data = await res.json()
  return data.members as GroupMember[]
}
