export interface PlayerInput {
  name: string
  hours: string // string so the form input stays editable
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
  players: PlayerResult[]
}
