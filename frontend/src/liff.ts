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

export async function getProfile(): Promise<{ userId: string; displayName: string } | null> {
  if (!ready || !liff.isLoggedIn()) return null
  const profile = await liff.getProfile()
  return { userId: profile.userId, displayName: profile.displayName }
}

export async function getDisplayName(): Promise<string | null> {
  return getProfile().then((p) => p?.displayName ?? null)
}

export function getGroupId(): string | null {
  if (!ready) return null
  const ctx = liff.getContext()
  if (!ctx) return null
  if (ctx.type === 'group' && ctx.groupId) return ctx.groupId
  return null
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
