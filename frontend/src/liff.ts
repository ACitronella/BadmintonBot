import liff from '@line/liff'

let ready = false

async function fetchLiffId(): Promise<string | null> {
  try {
    const res = await fetch('/api/config')
    const data = await res.json()
    return data.liff_id || null
  } catch {
    return null
  }
}

export async function initLiff(): Promise<void> {
  if (ready) return
  const liffId = await fetchLiffId()
  if (!liffId) {
    console.warn('LIFF_ID not configured — running in browser-only mode')
    return
  }
  await liff.init({ liffId })
  ready = true
}

export async function getDisplayName(): Promise<string | null> {
  if (!ready || !liff.isLoggedIn()) return null
  const profile = await liff.getProfile()
  return profile.displayName
}

export function getGroupId(): string | null {
  if (!ready) return null
  const ctx = liff.getContext()
  console.log('[LIFF] context:', JSON.stringify(ctx))
  if (!ctx) return null
  // LINE Mini App uses groupId for group chats
  if (ctx.type === 'group' && ctx.groupId) return ctx.groupId
  return null
}

export async function sendBillToChat(
  url: string,
  billName: string,
  total: number,
  players: { name: string; amount: number }[],
): Promise<boolean> {
  if (!ready) {
    console.warn('[LIFF] sendBillToChat: LIFF not ready')
    return false
  }
  if (!liff.isApiAvailable('sendMessages')) {
    console.warn('[LIFF] sendBillToChat: sendMessages not available. Check that chat_message.write scope is enabled in LINE Developer Console → Mini App settings.')
    return false
  }

  const MAX_ROWS = 8
  const playerRows = players.slice(0, MAX_ROWS).map((p) => ({
    type: 'box', layout: 'horizontal',
    contents: [
      { type: 'text', text: p.name, size: 'sm', color: '#374151', flex: 1, wrap: true },
      { type: 'text', text: `฿${p.amount.toFixed(2)}`, size: 'sm', weight: 'bold', color: '#16a34a', align: 'end' },
    ],
  }))
  if (players.length > MAX_ROWS) {
    playerRows.push({ type: 'text', text: `…and ${players.length - MAX_ROWS} more`, size: 'xs', color: '#9ca3af' } as never)
  }

  try {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  await liff.sendMessages([({
    type: 'flex',
      altText: `🏸 ${billName || 'Badminton Bill'} — ฿${total.toLocaleString()}`,
      contents: {
        type: 'bubble',
        header: {
          type: 'box', layout: 'vertical', backgroundColor: '#16a34a', paddingAll: '16px',
          contents: [
            { type: 'text', text: '🏸 New Bill', size: 'xs', color: '#bbf7d0' },
            { type: 'text', text: billName || 'Badminton Bill', size: 'lg', weight: 'bold', color: '#ffffff', wrap: true },
          ],
        },
        body: {
          type: 'box', layout: 'vertical', spacing: 'sm', paddingAll: '16px',
          contents: [
            {
              type: 'box', layout: 'horizontal',
              contents: [
                { type: 'text', text: 'Total', size: 'sm', color: '#6b7280', flex: 1 },
                { type: 'text', text: `฿${total.toLocaleString('en', { minimumFractionDigits: 2 })}`, size: 'sm', weight: 'bold', color: '#16a34a', align: 'end' },
              ],
            },
            { type: 'separator', margin: 'sm' },
            ...playerRows,
          ],
        },
        footer: {
          type: 'box', layout: 'vertical', paddingAll: '12px',
          contents: [
            {
              type: 'button', style: 'primary', color: '#22c55e',
              action: { type: 'uri', label: 'View My Share', uri: url },
            },
          ],
        },
      },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    }) as any])
    console.log('[LIFF] sendBillToChat: success')
    return true
  } catch (e) {
    console.error('[LIFF] sendBillToChat failed:', e)
    return false
  }
}

export async function shareUrl(url: string, message: string): Promise<void> {
  if (!ready) {
    // Fallback: copy to clipboard
    await navigator.clipboard.writeText(url)
    return
  }
  if (liff.isApiAvailable('shareTargetPicker')) {
    await liff.shareTargetPicker([
      {
        type: 'text',
        text: message,
      },
    ])
  } else {
    await navigator.clipboard.writeText(url)
  }
}
