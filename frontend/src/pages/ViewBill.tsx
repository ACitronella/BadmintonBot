import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { fetchBill } from '../api'
import type { Bill } from '../types'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function ViewBill() {
  const { id } = useParams<{ id: string }>()
  const [bill, setBill] = useState<Bill | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    fetchBill(id)
      .then(setBill)
      .catch(() => setError('Bill not found or has expired.'))
  }, [id])

  if (error) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow p-6 text-center space-y-2">
          <div className="text-4xl">😕</div>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  if (!bill) {
    return (
      <div className="min-h-screen bg-green-50 flex items-center justify-center">
        <p className="text-green-600 font-medium">Loading bill…</p>
      </div>
    )
  }

  const totalHours =
    bill.split_mode === 'hours'
      ? bill.players.reduce((s, p) => s + (p.hours ?? 0), 0)
      : null

  return (
    <div className="min-h-screen bg-green-50 pb-10">
      {/* Header */}
      <div className="bg-green-600 text-white px-4 pt-10 pb-6">
        <p className="text-xs opacity-70">🏸 Badminton Bill</p>
        <h1 className="text-2xl font-bold">{bill.court_name || 'Bill Summary'}</h1>
        {bill.host_name && (
          <p className="text-sm opacity-80 mt-0.5">Created by {bill.host_name}</p>
        )}
        <p className="text-xs opacity-60 mt-0.5">{formatDate(bill.created_at)}</p>
      </div>

      <div className="px-4 space-y-4 mt-4">
        {/* Total card */}
        <div className="bg-white rounded-2xl shadow p-4 flex justify-between items-center">
          <div>
            <p className="text-xs text-gray-400 uppercase font-semibold">Total cost</p>
            <p className="text-3xl font-bold text-green-600">
              ฿{bill.total_cost.toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-400 uppercase font-semibold">Split by</p>
            <p className="text-sm font-semibold text-gray-600">
              {bill.split_mode === 'hours' ? '⏱️ Hours played' : '👥 Equal'}
            </p>
            {totalHours !== null && (
              <p className="text-xs text-gray-400">{totalHours.toFixed(1)} hrs total</p>
            )}
          </div>
        </div>

        {bill.note && (
          <div className="bg-yellow-50 border border-yellow-100 rounded-xl px-4 py-2">
            <p className="text-sm text-yellow-700">📝 {bill.note}</p>
          </div>
        )}

        {/* Player breakdown */}
        <div className="bg-white rounded-2xl shadow p-4">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-3">
            {bill.players.length} Players
          </p>
          <div className="space-y-0">
            {bill.players.map((p, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0"
              >
                <div>
                  <p className="font-semibold text-gray-800">{p.name}</p>
                  {p.hours != null && (
                    <p className="text-xs text-gray-400">{p.hours} hrs</p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-green-600">
                    ฿{p.amount.toLocaleString('en', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Per-hour rate if applicable */}
        {bill.split_mode === 'hours' && totalHours && totalHours > 0 && (
          <div className="text-center text-xs text-gray-400">
            ฿{(bill.total_cost / totalHours).toFixed(2)} / hour
          </div>
        )}
      </div>
    </div>
  )
}
