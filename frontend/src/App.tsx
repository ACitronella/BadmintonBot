import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { initLiff } from './liff'
import CreateBill from './pages/CreateBill'
import ViewBill from './pages/ViewBill'

export default function App() {
  const [liffReady, setLiffReady] = useState(false)

  useEffect(() => {
    initLiff().finally(() => setLiffReady(true))
  }, [])

  if (!liffReady) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-green-50">
        <p className="text-green-600 font-medium">Loading…</p>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CreateBill />} />
        <Route path="/bill/:id" element={<ViewBill />} />
      </Routes>
    </BrowserRouter>
  )
}
