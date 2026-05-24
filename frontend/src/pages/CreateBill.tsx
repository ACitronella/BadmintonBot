import { useEffect, useState } from 'react'
import { createBill } from '../api'
import { getDisplayName, shareUrl } from '../liff'
import type { PlayerInput } from '../types'

const EMPTY_PLAYER: PlayerInput = { name: '', hours: '' }

function calcPreview(
  total: number,
  mode: 'equal' | 'hours',
  players: PlayerInput[],
): { name: string; amount: number }[] {
  const valid = players.filter((p) => p.name.trim())
  if (!valid.length || total <= 0) return []

  if (mode === 'equal') {
    const each = total / valid.length
    return valid.map((p) => ({ name: p.name, amount: each }))
  }

  const totalHours = valid.reduce((s, p) => s + (parseFloat(p.hours) || 0), 0)
  if (totalHours <= 0) return []
  return valid.map((p) => ({
    name: p.name,
    amount: ((parseFloat(p.hours) || 0) / totalHours) * total,
  }))
}

export default function CreateBill() {
  const [total, setTotal] = useState('')
  const [courtName, setCourtName] = useState('')
  const [note, setNote] = useState('')
  const [mode, setMode] = useState<'equal' | 'hours'>('hours')
  const [players, setPlayers] = useState<PlayerInput[]>([
    { ...EMPTY_PLAYER },
    { ...EMPTY_PLAYER },
  ])
  const [hostName, setHostName] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [billId, setBillId] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    getDisplayName().then(setHostName)
  }, [])

  const totalNum = parseFloat(total) || 0
  const preview = calcPreview(totalNum, mode, players)

  function updatePlayer(i: number, field: keyof PlayerInput, value: string) {
    setPlayers((prev) => prev.map((p, idx) => (idx === i ? { ...p, [field]: value } : p)))
  }

  function addPlayer() {
    setPlayers((prev) => [...prev, { ...EMPTY_PLAYER }])
  }

  function removePlayer(i: number) {
    setPlayers((prev) => prev.filter((_, idx) => idx !== i))
  }

  async function handleSubmit() {
    setError('')
    const validPlayers = players.filter((p) => p.name.trim())
    if (!totalNum || totalNum <= 0) return setError('Please enter a valid total amount')
    if (validPlayers.length < 1) return setError('Add at least one player')
    if (mode === 'hours' && validPlayers.some((p) => !(parseFloat(p.hours) > 0))) {
      return setError('All players need hours greater than 0')
    }

    setLoading(true)
    try {
      const res = await createBill({
        total_cost: totalNum,
        court_name: courtName.trim(),
        note: note.trim(),
        split_mode: mode,
        players: validPlayers,
        host_name: hostName,
      })
      setBillId(res.id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const billUrl = billId
    ? `${window.location.origin}/bill/${billId}`
    : null

  async function handleShare() {
    if (!billUrl || !billId) return
    const msg =
      `🏸 Badminton Bill — ${courtName || 'Court'}\n` +
      `Total: ฿${totalNum.toLocaleString()}\n` +
      `View your share: ${billUrl}`
    await shareUrl(billUrl, msg)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // ── Bill created screen ──────────────────────────────────────────────────
  if (billId && billUrl) {
    return (
      <div className="min-h-screen bg-green-50 flex flex-col items-center justify-center p-6 gap-4">
        <div className="bg-white rounded-2xl shadow p-6 w-full max-w-sm text-center space-y-4">
          <div className="text-4xl">🏸</div>
          <h1 className="text-xl font-bold text-green-700">Bill Created!</h1>
          <p className="text-sm text-gray-500 break-all">{billUrl}</p>
          <button
            onClick={handleShare}
            className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 rounded-xl transition"
          >
            {copied ? '✅ Copied!' : '📤 Share to Group'}
          </button>
          <button
            onClick={() => {
              setBillId(null)
              setTotal('')
              setPlayers([{ ...EMPTY_PLAYER }, { ...EMPTY_PLAYER }])
            }}
            className="w-full text-sm text-gray-400 underline"
          >
            Create another bill
          </button>
        </div>

        {preview.length > 0 && (
          <div className="bg-white rounded-2xl shadow p-4 w-full max-w-sm">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Summary</p>
            {preview.map((p) => (
              <div key={p.name} className="flex justify-between py-1.5 border-b last:border-0">
                <span className="text-gray-700">{p.name}</span>
                <span className="font-semibold text-green-600">
                  ฿{p.amount.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // ── Create bill form ─────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-green-50 pb-10">
      <div className="bg-green-600 text-white px-4 pt-10 pb-6">
        <p className="text-xs opacity-70">🏸 Badminton</p>
        <h1 className="text-2xl font-bold">Create Bill</h1>
        {hostName && <p className="text-sm opacity-80 mt-0.5">Host: {hostName}</p>}
      </div>

      <div className="px-4 space-y-4 mt-4">
        {/* Court info */}
        <div className="bg-white rounded-2xl shadow p-4 space-y-3">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase">Court name</label>
            <input
              className="w-full border-b border-gray-200 py-1.5 text-sm focus:outline-none focus:border-green-400"
              placeholder="e.g. Supersport Arena Court 3"
              value={courtName}
              onChange={(e) => setCourtName(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase">
              Total cost (THB) <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              inputMode="decimal"
              className="w-full border-b border-gray-200 py-1.5 text-2xl font-bold text-green-600 focus:outline-none focus:border-green-400"
              placeholder="0"
              value={total}
              onChange={(e) => setTotal(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase">Note</label>
            <input
              className="w-full border-b border-gray-200 py-1.5 text-sm focus:outline-none focus:border-green-400"
              placeholder="Optional note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
        </div>

        {/* Split mode */}
        <div className="bg-white rounded-2xl shadow p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Split by</p>
          <div className="flex gap-2">
            {(['hours', 'equal'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-2 rounded-xl text-sm font-semibold transition ${
                  mode === m
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {m === 'hours' ? '⏱️ Hours played' : '👥 Equal split'}
              </button>
            ))}
          </div>
        </div>

        {/* Players */}
        <div className="bg-white rounded-2xl shadow p-4 space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-gray-500 uppercase">Players</p>
            <button
              onClick={addPlayer}
              className="text-xs text-green-600 font-semibold"
            >
              + Add player
            </button>
          </div>

          {players.map((p, i) => (
            <div key={i} className="flex gap-2 items-center">
              <input
                className="flex-1 border-b border-gray-200 py-1.5 text-sm focus:outline-none focus:border-green-400"
                placeholder={`Player ${i + 1} name`}
                value={p.name}
                onChange={(e) => updatePlayer(i, 'name', e.target.value)}
              />
              {mode === 'hours' && (
                <input
                  type="number"
                  inputMode="decimal"
                  className="w-16 border-b border-gray-200 py-1.5 text-sm text-center focus:outline-none focus:border-green-400"
                  placeholder="hrs"
                  value={p.hours}
                  onChange={(e) => updatePlayer(i, 'hours', e.target.value)}
                />
              )}
              {players.length > 1 && (
                <button
                  onClick={() => removePlayer(i)}
                  className="text-gray-300 hover:text-red-400 text-lg leading-none"
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Live preview */}
        {preview.length > 0 && totalNum > 0 && (
          <div className="bg-green-50 border border-green-100 rounded-2xl p-4 space-y-1">
            <p className="text-xs font-semibold text-green-600 uppercase mb-2">Preview</p>
            {preview.map((p) => (
              <div key={p.name} className="flex justify-between text-sm">
                <span className="text-gray-600">{p.name}</span>
                <span className="font-semibold text-green-700">฿{p.amount.toFixed(2)}</span>
              </div>
            ))}
          </div>
        )}

        {error && (
          <p className="text-red-500 text-sm text-center">{error}</p>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white font-bold py-4 rounded-2xl text-base transition"
        >
          {loading ? 'Creating…' : '✅ Create Bill'}
        </button>
      </div>
    </div>
  )
}
