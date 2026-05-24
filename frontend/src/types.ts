export interface PlayerInput {
  name: string
  hours: string // string so the form input stays editable
  pictureUrl?: string // set when added from group; undefined for manual entries
}

export interface GroupMember {
  userId: string
  displayName: string
  pictureUrl: string
}

export interface PlayerResult {
  name: string
  hours: number | null
  amount: number
}

export interface Bill {
  id: string
  total_cost: number
  court_name: string | null
  note: string | null
  split_mode: 'equal' | 'hours'
  host_name: string | null
  created_at: string
  session_hours: number | null
  players: PlayerResult[]
}
