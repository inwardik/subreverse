import React, { useEffect, useRef, useState } from 'react'

function AuthWidget() {
  const [open, setOpen] = useState(false)
  const [user, setUser] = useState(null)
  const [token, setToken] = useState('')
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    try {
      const raw = localStorage.getItem('auth')
      if (raw) {
        const a = JSON.parse(raw)
        if (a?.token && a?.user) {
          setToken(a.token)
          setUser(a.user)
        }
      }
    } catch {}
  }, [])

  // React to global auth updates (e.g., after energy changes via /self)
  useEffect(() => {
    function onAuthChanged(e) {
      try {
        if (e && e.detail) {
          const { user: u, token: t } = e.detail
          if (typeof t === 'string') setToken(t)
          if (u) setUser(u)
        } else {
          const raw = localStorage.getItem('auth')
          if (raw) {
            const a = JSON.parse(raw)
            if (a?.token) setToken(a.token)
            if (a?.user) setUser(a.user)
          }
        }
      } catch {}
    }
    window.addEventListener('auth-changed', onAuthChanged)
    return () => window.removeEventListener('auth-changed', onAuthChanged)
  }, [])

  useEffect(() => {
    async function fetchSelf() {
      if (!token) return
      try {
        const res = await fetch('/self', { headers: { 'Authorization': `Bearer ${token}` } })
        const data = await res.json().catch(() => ({}))
        if (res.ok && data && data.username) {
          setUser(prev => ({ ...(prev||{}), ...data }))
          const raw = localStorage.getItem('auth')
          if (raw) {
            try { const a = JSON.parse(raw); a.user = { ...(a.user||{}), ...data }; localStorage.setItem('auth', JSON.stringify(a)) } catch {}
          }
        }
      } catch {}
    }
    fetchSelf()
  }, [token])

  async function apiSignup() {
    setError('')
    try {
      setBusy(true)
      const res = await fetch('/auth/signup', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || 'Signup failed')
      localStorage.setItem('auth', JSON.stringify(data))
      setToken(data.token)
      setUser(data.user)
      setOpen(false)
      try { window.dispatchEvent(new CustomEvent('auth-changed', { detail: { user: data.user, token: data.token } })) } catch {}
    } catch (e) {
      setError(e.message || String(e))
    } finally { setBusy(false) }
  }

  async function apiLogin() {
    setError('')
    try {
      setBusy(true)
      const res = await fetch('/auth/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login: email || username, password })
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data?.detail || 'Login failed')
      localStorage.setItem('auth', JSON.stringify(data))
      setToken(data.token)
      setUser(data.user)
      setOpen(false)
      try { window.dispatchEvent(new CustomEvent('auth-changed', { detail: { user: data.user, token: data.token } })) } catch {}
    } catch (e) {
      setError(e.message || String(e))
    } finally { setBusy(false) }
  }

  function logout() {
    localStorage.removeItem('auth')
    setUser(null)
    setToken('')
    try { window.dispatchEvent(new CustomEvent('auth-changed', { detail: { user: null, token: '' } })) } catch {}
  }

  if (user) {
    const currentEnergy = (typeof user.energy === 'number' ? user.energy : 10)
    const maxEnergy = (typeof user.max_energy === 'number' ? user.max_energy : 10)
    const level = (typeof user.level === 'number' ? user.level : 1)
    const xp = (typeof user.xp === 'number' ? user.xp : 1)
    const maxXp = (typeof user.max_xp === 'number' ? user.max_xp : (level * 10))
    const xpPct = Math.min(100, Math.round((xp / Math.max(1, maxXp)) * 100))
    const energyPct = Math.min(100, Math.round((currentEnergy / Math.max(1, maxEnergy)) * 100))

    return (
      <div className="top-utility">
        <div className="utility-left">
          <div className="mini-stat">
            <div className="mini-row"><span>⭐</span><span className="mini-label">XP</span><span className="mini-num">{xp} / {maxXp}</span></div>
            <div className="mini-bar"><div className="mini-fill xp" style={{ width: `${xpPct}%` }}></div></div>
          </div>
          <div className="mini-stat">
            <div className="mini-row"><span>⚡</span><span className="mini-label">Energy</span><span className="mini-num">{currentEnergy} / {maxEnergy}</span></div>
            <div className="mini-bar"><div className="mini-fill energy" style={{ width: `${energyPct}%` }}></div></div>
          </div>
        </div>
        <div className="utility-right">
          <div className="user-compact" style={{ position: 'relative' }}>
            <div className="user-avatar">👤</div>
            <div className="user-name">{user.username}</div>
            <div className="level-badge">Lv {level}</div>
            <button className="username-btn" onClick={() => setMenuOpen(v => !v)} title="Account">☰</button>
            {menuOpen && (
              <div className="dropdown" onMouseLeave={() => setMenuOpen(false)}>
                <button className="menu-item" onClick={logout}>Logout</button>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="userbox">
      {!open ? (
        <button className="loginbtn" onClick={() => { setOpen(true); setMode('login') }}>Sign in</button>
      ) : (
        <div className="authform">
          <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
            <button type="button" className={`tab${mode==='login'?' active':''}`} onClick={() => setMode('login')}>Login</button>
            <button type="button" className={`tab${mode==='signup'?' active':''}`} onClick={() => setMode('signup')}>Sign up</button>
          </div>
          {mode === 'signup' ? (
            <>
              <input placeholder="Username" value={username} onChange={(e)=>setUsername(e.target.value)} />
              <input placeholder="Email" value={email} onChange={(e)=>setEmail(e.target.value)} />
              <input placeholder="Password" type="password" value={password} onChange={(e)=>setPassword(e.target.value)} />
              <button disabled={busy} onClick={apiSignup}>{busy ? 'Please wait...' : 'Create account'}</button>
            </>
          ) : (
            <>
              <input placeholder="Email or username" value={email || username} onChange={(e)=>{ setEmail(e.target.value); setUsername('') }} />
              <input placeholder="Password" type="password" value={password} onChange={(e)=>setPassword(e.target.value)} />
              <button disabled={busy} onClick={apiLogin}>{busy ? 'Please wait...' : 'Login'}</button>
            </>
          )}
          {error && <div className="error" style={{ marginTop: 6 }}>{error}</div>}
        </div>
      )}
    </div>
  )
}

function Toggle({ label, active, onToggle, disabled }) {
  const on = !!active
  const isDisabled = !!disabled
  return (
    <button
      type="button"
      className={`tag-btn${on ? ' is-on' : ''}${isDisabled ? ' is-disabled' : ''}`}
      data-kind={label}
      onClick={() => { if (!isDisabled) onToggle?.(label) }}
      aria-pressed={on}
      aria-disabled={isDisabled}
      title={isDisabled ? 'No energy left' : undefined}
    >
      {label}
    </button>
  )
}

function Card({ item }) {
  const [detailsVisible, setDetailsVisible] = useState(false)
  const [activeTag, setActiveTag] = useState(item.category ?? null)
  const [enText, setEnText] = useState(item.en || '')
  const [ruText, setRuText] = useState(item.ru || '')
  const [rating, setRating] = useState(typeof item.rating === 'number' ? item.rating : 0)
  // Auth state from localStorage (updates on 'auth-changed')
  const [auth, setAuth] = useState(() => { try { const raw = localStorage.getItem('auth'); return raw ? JSON.parse(raw) : null } catch { return null } })
  const authUser = auth?.user || null
  const authToken = auth?.token || ''
  useEffect(() => {
    function onAuthChanged() {
      try {
        const raw = localStorage.getItem('auth')
        setAuth(raw ? JSON.parse(raw) : null)
      } catch {
        setAuth(null)
      }
    }
    window.addEventListener('auth-changed', onAuthChanged)
    return () => window.removeEventListener('auth-changed', onAuthChanged)
  }, [])
  // Track offsets separately for left/right so arrows don't affect each other
  const [enRightOffset, setEnRightOffset] = useState(0)
  const [enLeftOffset, setEnLeftOffset] = useState(0)
  const [ruRightOffset, setRuRightOffset] = useState(0)
  const [ruLeftOffset, setRuLeftOffset] = useState(0)
  const [busy, setBusy] = useState(false)

  const energyLeft = (authUser && typeof authUser.energy === 'number') ? authUser.energy : null
  const outOfEnergy = !!authUser && energyLeft !== null && energyLeft <= 0

  async function refreshSelf() {
    if (!authToken) return
    try {
      const res = await fetch('/self', { headers: { 'Authorization': `Bearer ${authToken}` } })
      const data = await res.json().catch(() => null)
      if (res.ok && data) {
        try {
          const raw = localStorage.getItem('auth')
          if (raw) {
            const a = JSON.parse(raw)
            a.user = { ...(a.user||{}), ...data }
            localStorage.setItem('auth', JSON.stringify(a))
            window.dispatchEvent(new CustomEvent('auth-changed', { detail: { user: a.user, token: a.token } }))
          }
        } catch {}
      }
    } catch {}
  }

  const metaParts = []
  if (item.file_en && item.time_en) metaParts.push(`${item.file_en} @ ${item.time_en}`)
  if (item.file_ru && item.time_ru) metaParts.push(`${item.file_ru} @ ${item.time_ru}`)
  const meta = metaParts.join(' • ')

  async function fetchByOffset(baseId, delta) {
    try {
      setBusy(true)
      const res = await fetch(`/api/search/${encodeURIComponent(baseId)}/?offset=${delta}`)
      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`)
      return await res.json()
    } finally {
      setBusy(false)
    }
  }

  async function changeRating(delta) {
    if (!authUser) return
    if (outOfEnergy) { try { alert('No energy left') } catch {} return }
    try {
      setBusy(true)
      const res = await fetch(`/api/search/${encodeURIComponent(item._id)}/?delta=${delta}`, { method: 'PATCH', headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {} })
      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`)
      const doc = await res.json()
      if (typeof doc.rating === 'number') setRating(doc.rating)
      setActiveTag(doc.category ?? activeTag)
      await refreshSelf()
    } finally {
      setBusy(false)
    }
  }

  async function onToggleTag(label) {
    // Toggle behavior: if clicking the active -> unset (null); else set to label
    if (!authUser) return
    if (outOfEnergy) { try { alert('No energy left') } catch {} return }
    const nextCategory = (activeTag === label) ? '' : label
    try {
      setBusy(true)
      const res = await fetch(`/api/search/${encodeURIComponent(item._id)}/?category=${encodeURIComponent(nextCategory)}`, { method: 'PATCH', headers: authToken ? { 'Authorization': `Bearer ${authToken}` } : {} })
      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`)
      const doc = await res.json()
      setActiveTag(doc.category ?? null)
      await refreshSelf()
    } finally {
      setBusy(false)
    }
  }

  async function onEnBefore() {
    const next = enLeftOffset - 1
    try {
      const doc = await fetchByOffset(item._id, next)
      if (doc) {
        if (doc.en) setEnText(prev => ` ${doc.en} ${prev}`.trim())
        if (typeof doc.rating === 'number') setRating(doc.rating)
        setActiveTag(doc.category ?? null)
      }
      setEnLeftOffset(next)
    } catch (e) {
      // keep counter unchanged on failure
    }
  }
  async function onEnAfter() {
    const next = enRightOffset + 1
    try {
      const doc = await fetchByOffset(item._id, next)
      if (doc) {
        if (doc.en) setEnText(prev => `${prev} ${doc.en}`.trim())
        if (typeof doc.rating === 'number') setRating(doc.rating)
        setActiveTag(doc.category ?? null)
      }
      setEnRightOffset(next)
    } catch (e) {
      // keep counter unchanged on failure
    }
  }
  async function onRuBefore() {
    const next = ruLeftOffset - 1
    try {
      const doc = await fetchByOffset(item._id, next)
      if (doc) {
        if (doc.ru) setRuText(prev => ` ${doc.ru} ${prev}`.trim())
        if (typeof doc.rating === 'number') setRating(doc.rating)
        setActiveTag(doc.category ?? null)
      }
      setRuLeftOffset(next)
    } catch (e) {
      // keep counter unchanged on failure
    }
  }
  async function onRuAfter() {
    const next = ruRightOffset + 1
    try {
      const doc = await fetchByOffset(item._id, next)
      if (doc) {
        if (doc.ru) setRuText(prev => `${prev} ${doc.ru}`.trim())
        if (typeof doc.rating === 'number') setRating(doc.rating)
        setActiveTag(doc.category ?? null)
      }
      setRuRightOffset(next)
    } catch (e) {
      // keep counter unchanged on failure
    }
  }

  async function toggleDetails() {
    if (!authUser) return;
    if (!detailsVisible) {
      try {
        setBusy(true)
        const doc = await fetchByOffset(item._id, 0)
        if (doc) {
          if (typeof doc.rating === 'number') setRating(doc.rating)
          setActiveTag(doc.category ?? null)
          if (doc.en) setEnText(doc.en)
          if (typeof doc.ru === 'string') setRuText(doc.ru)
        }
        setDetailsVisible(true)
      } finally {
        setBusy(false)
      }
    } else {
      setDetailsVisible(false)
    }
  }

  return (
    <div className="card">
      <div className="en" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span role="button" aria-label="Add before (EN)" className="arrow" onClick={onEnBefore}>←</span>
        <div style={{ flex: 1 }}>{enText}</div>
        <span role="button" aria-label="Add after (EN)" className="arrow" onClick={onEnAfter}>→</span>
      </div>
      {item.ru ? (
        <div className="ru" style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
          <span role="button" aria-label="Add before (RU)" className="arrow" onClick={onRuBefore}>←</span>
          <div style={{ flex: 1 }}>{ruText}</div>
          <span role="button" aria-label="Add after (RU)" className="arrow" onClick={onRuAfter}>→</span>
        </div>
      ) : null}
      {meta ? (
        <div className="meta" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ flex: 1 }}>{meta}</div>
          {authUser ? (
            <span
              className="arrow"
              role="button"
              aria-label={detailsVisible ? 'Hide details' : 'Show details'}
              onClick={toggleDetails}
              title={detailsVisible ? 'Hide rating and tags' : 'Load fresh rating/tags'}
            >{detailsVisible ? '↑' : '↓'}</span>
          ) : null}
        </div>
      ) : (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          {authUser ? (
            <span
              className="arrow"
              role="button"
              aria-label={detailsVisible ? 'Hide details' : 'Show details'}
              onClick={toggleDetails}
              title={detailsVisible ? 'Hide rating and tags' : 'Load fresh rating/tags'}
            >{detailsVisible ? '↑' : '↓'}</span>
          ) : null}
        </div>
      )}
      {detailsVisible && (
        <div className="card-actions" style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', gap: 12, marginTop: 8 }}>
          <div className="rating-wrap" style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', gap: 4 }}>
            <span className={`arrow arrow--subtle${outOfEnergy ? ' disabled' : ''}`} role="button" aria-label="Rating up" aria-disabled={outOfEnergy} title={outOfEnergy ? 'No energy left' : 'Rating up'} onClick={() => { if (!outOfEnergy) changeRating(1) }}>↑</span>
            <span className="rating-num" style={{ minWidth: 18, textAlign: 'center' }}>{rating}</span>
            <span className={`arrow arrow--subtle${outOfEnergy ? ' disabled' : ''}`} role="button" aria-label="Rating down" aria-disabled={outOfEnergy} title={outOfEnergy ? 'No energy left' : 'Rating down'} onClick={() => { if (!outOfEnergy) changeRating(-1) }}>↓</span>
          </div>
          <div className="tags" style={{ display: 'flex', gap: 10, opacity: 0.9 }}>
            <Toggle label="idiom" active={activeTag === 'idiom'} onToggle={(label) => onToggleTag(label)} disabled={outOfEnergy} />
            <Toggle label="quote" active={activeTag === 'quote'} onToggle={(label) => onToggleTag(label)} disabled={outOfEnergy} />
            <Toggle label="wrong" active={activeTag === 'wrong'} onToggle={(label) => onToggleTag(label)} disabled={outOfEnergy} />
          </div>
        </div>
      )}
    </div>
  )
}

function HomePage() {
  const [q, setQ] = useState('')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [totalPhrases, setTotalPhrases] = useState(0)
  const inputRef = useRef(null)

  // Simple hash-based tabs: search (default), idioms, quotes, leaderboard
  const parseHash = () => {
    const h = (typeof window !== 'undefined' ? window.location.hash : '').toLowerCase()
    if (h.includes('idiom')) return 'idioms'
    if (h.includes('quote')) return 'quotes'
    if (h.includes('leader')) return 'leaderboard'
    return 'search'
  }

  // Extract query parameter from hash
  const getQueryFromHash = () => {
    const hash = window.location.hash
    const match = hash.match(/[?&]q=([^&]+)/)
    if (match) {
      try {
        // Remove quotes if present and decode
        let query = decodeURIComponent(match[1])
        query = query.replace(/^["']|["']$/g, '')
        return query
      } catch {
        return ''
      }
    }
    return ''
  }

  const [tab, setTab] = useState(parseHash)

  // Initialize query from hash on mount
  useEffect(() => {
    const queryFromHash = getQueryFromHash()
    if (queryFromHash) {
      setQ(queryFromHash)
      // Trigger search if there's a query in the hash
      doSearch(queryFromHash)
    }
  }, [])

  useEffect(() => {
    function onHash() {
      const newTab = parseHash()
      setTab(newTab)
      // If switched to search tab, check for query in hash
      if (newTab === 'search') {
        const queryFromHash = getQueryFromHash()
        if (queryFromHash && queryFromHash !== q) {
          setQ(queryFromHash)
          doSearch(queryFromHash)
        }
      }
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [q])

  useEffect(() => { inputRef.current?.focus() }, [])
  useEffect(() => {
    let aborted = false
    ;(async () => {
      try {
        const res = await fetch('/api/stats')
        if (!res.ok) return
        const data = await res.json().catch(() => null)
        if (!aborted && data && typeof data.total === 'number') {
          setTotalPhrases(data.total)
        }
      } catch (_) {
        // ignore stats fetch errors
      }
    })()
    return () => { aborted = true }
  }, [])

  async function doSearch(term) {
    const t = term.trim()
    try {
      setLoading(true); setError('')

      // Update hash with query parameter if searching
      if (t) {
        const encodedQuery = encodeURIComponent(t)
        window.location.hash = `#/search?q=${encodedQuery}`
      } else {
        window.location.hash = '#/search'
      }

      if (!t) {
        // Fetch a random record when search line is empty
        const res = await fetch(`/api/get_random`)
        if (!res.ok) {
          const text = await res.text()
          throw new Error(text || `HTTP ${res.status}`)
        }
        const data = await res.json()
        if (data && Object.keys(data).length) {
          setItems([data])
        } else {
          setItems([])
        }
        return
      }
      const res = await fetch(`/api/search?q=${encodeURIComponent(t)}`)
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setItems(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e.message || String(e))
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter') {
      e.preventDefault()
      doSearch(q)
    } else if (e.key === 'Escape') {
      // Clear results if there are any
      if (items.length > 0) {
        setItems([])
        setError('')
      }
    }
  }

  return (
    <>
      <header>
        <AuthWidget />
        <div className="brand"><a href="/" style={{ color: 'inherit', textDecoration: 'none' }}>SubReverse</a></div>
        <div className="tagline">Hunt your idiom among <a href="/content">{totalPhrases.toLocaleString()}</a> phrases</div>
        <div className="navbar">
          <button className={`nav-btn${tab==='search' ? ' active' : ''}`} onClick={() => { setTab('search'); try { window.location.hash = '#/search' } catch {} }}>Search</button>
          <button className={`nav-btn${tab==='idioms' ? ' active' : ''}`} onClick={() => { setTab('idioms'); try { window.location.hash = '#/idioms' } catch {} }}>Idioms</button>
          <button className={`nav-btn${tab==='quotes' ? ' active' : ''}`} onClick={() => { setTab('quotes'); try { window.location.hash = '#/quotes' } catch {} }}>Quotes</button>
          <button className={`nav-btn${tab==='leaderboard' ? ' active' : ''}`} onClick={() => { setTab('leaderboard'); try { window.location.hash = '#/leaderboard' } catch {} }}>Leaderboard</button>
        </div>
        {tab === 'search' && (
          <div className="search-area">
            <div className="search-box with-button">
              <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input ref={inputRef} type="search" placeholder="Search quotes or translations..." value={q}
                     onChange={(e) => setQ(e.target.value)} onKeyDown={onKeyDown} />
              <button className="search-action" type="button" onClick={() => doSearch(q)} aria-label={q.trim() ? 'Search' : 'Get random'}>
                {q.trim() ? 'Search' : 'Get random'}
              </button>
            </div>
            <div className="hint">Press Enter to search English and Russian lines</div>
          </div>
        )}
      </header>

      {tab === 'search' ? (
        <section className="results">
          {loading && <div className="card">Searching...</div>}
          {error && <div className="card" style={{ borderColor: 'rgba(229,9,20,0.5)' }}>Error: {error}</div>}
          {!loading && !error && items.length === 0 && q.trim() && (
            <div className="card">No results found.</div>
          )}
          {!loading && items.map((it) => (
            <Card key={it._id || `${it.en}-${it.time_en}`} item={it} />
          ))}
        </section>
      ) : (
        <section className="results">
          <div className="card">
            {tab === 'idioms' && <IdiomsView />}
            {tab === 'quotes' && <div>Quotes page is coming soon.</div>}
            {tab === 'leaderboard' && <div>Leaderboard is coming soon.</div>}
          </div>
        </section>
      )}
    </>
  )
}

function IdiomsView() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingIdiom, setEditingIdiom] = useState(null)
  const [currentUser, setCurrentUser] = useState(null)

  useEffect(() => {
    try {
      const raw = localStorage.getItem('auth')
      if (raw) {
        const a = JSON.parse(raw)
        if (a?.user) setCurrentUser(a.user)
      }
    } catch {}
  }, [])

  useEffect(() => {
    function onAuthChanged() {
      try {
        const raw = localStorage.getItem('auth')
        if (raw) {
          const a = JSON.parse(raw)
          setCurrentUser(a?.user || null)
        } else {
          setCurrentUser(null)
        }
      } catch {}
    }
    window.addEventListener('auth-changed', onAuthChanged)
    return () => window.removeEventListener('auth-changed', onAuthChanged)
  }, [])

  const loadIdioms = async () => {
    try {
      setLoading(true)
      const headers = {}
      try {
        const raw = localStorage.getItem('auth')
        if (raw) {
          const auth = JSON.parse(raw)
          if (auth?.token) headers['Authorization'] = `Bearer ${auth.token}`
        }
      } catch {}

      const res = await fetch('/api/idioms', { headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json().catch(() => [])
      setItems(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadIdioms()
  }, [])

  const handleEdit = (idiom) => {
    setEditingIdiom(idiom)
  }

  const handleSearch = (title) => {
    // Navigate to search tab with query in hash
    window.location.hash = `#/search?q=${encodeURIComponent(title)}`
  }

  const handleReaction = async (idiom, type) => {
    // Check if user is authenticated
    if (!currentUser) {
      alert('Please login to like/dislike idioms')
      return
    }

    // Check if it's user's own idiom
    if (idiom.user_id === currentUser.id) {
      return // Do nothing for own idioms
    }

    // Determine action based on current state
    let action = type
    if (idiom.like_action === type) {
      // Clicking the same button - toggle (remove)
      action = 'remove'
    }

    try {
      const auth = JSON.parse(localStorage.getItem('auth') || '{}')
      const res = await fetch(`/api/idioms/${idiom._id}/like`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.token}`
        },
        body: JSON.stringify({ action })
      })

      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(error.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()

      // Update the idiom in the list with new counts and user_action
      setItems(prev => prev.map(item => {
        if (item._id === idiom._id) {
          return {
            ...item,
            likes: data.likes,
            dislikes: data.dislikes,
            like_action: data.user_action
          }
        }
        return item
      }))
    } catch (e) {
      console.error('Error handling reaction:', e)
      alert(e.message || 'Failed to submit reaction')
    }
  }

  if (loading) return <div>Loading idioms...</div>
  if (error) return <div style={{ color: '#b00' }}>Error: {error}</div>
  if (!items.length) return <div>No idioms yet.</div>

  return (
    <>
      <div className="idioms-list" style={{ display: 'flex', flexDirection: 'column', gap: 16, width: '100%' }}>
        {items.map((it, idx) => {
          const isOwner = currentUser && currentUser.id === it.user_id
          const canEdit = isOwner && (it.status === 'draft' || it.status === 'published')
          const canLike = it.like_action !== 'not_applicable'
          const likeActive = it.like_action === 'like'
          const dislikeActive = it.like_action === 'dislike'

          return (
            <div
              key={it._id || idx}
              className="idiom-item"
              style={{
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: 8,
                padding: 16,
                backgroundColor: 'rgba(255,255,255,0.02)'
              }}
            >
              {/* Title with edit button */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                {it.title ? (
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 'bold', margin: 0, flex: 1 }}>
                    <span
                      style={{
                        color: '#4a9eff',
                        cursor: 'pointer',
                        textDecoration: 'none'
                      }}
                      onClick={() => handleSearch(it.title)}
                    >
                      {it.title}
                    </span>
                  </h3>
                ) : (
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 'bold', margin: 0, color: '#888', flex: 1 }}>
                    (Untitled)
                  </h3>
                )}

                {/* Edit button next to title */}
                {canEdit && (
                  <button
                    onClick={() => handleEdit(it)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '0.95rem',
                      color: '#4a9eff',
                      padding: '4px 8px'
                    }}
                  >
                    ✏️ Edit
                  </button>
                )}
              </div>

              {/* English & Russian */}
              <div className="en" style={{ fontSize: '1.05rem', marginBottom: 6, fontWeight: '500' }}>{it.en}</div>
              <div className="ru" style={{ opacity: 0.85, marginBottom: 8 }}>{it.ru}</div>

              {/* Explanation */}
              {it.explanation && (
                <div className="explanation" style={{
                  fontSize: '0.95rem',
                  fontStyle: 'italic',
                  opacity: 0.75,
                  marginTop: 10,
                  marginBottom: 8,
                  paddingLeft: 12,
                  borderLeft: '3px solid rgba(74, 158, 255, 0.3)'
                }}>
                  {it.explanation}
                </div>
              )}

              {/* Footer meta with reactions, author, status, source, date, and comments */}
              <div className="meta" style={{
                marginTop: 12,
                fontSize: '0.85rem',
                opacity: 0.75,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                flexWrap: 'wrap'
              }}>
                {/* Like/Dislike buttons */}
                <span
                  onClick={() => canLike && handleReaction(it, 'like')}
                  style={{
                    cursor: canLike ? 'pointer' : 'not-allowed',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 2,
                    opacity: canLike ? 1 : 0.4,
                    color: likeActive ? '#4a9eff' : 'inherit',
                    fontWeight: likeActive ? 'bold' : 'normal'
                  }}
                  title={canLike ? (likeActive ? 'Remove like' : 'Like') : 'Cannot like own idiom'}
                >
                  👍 {it.likes || 0}
                </span>
                <span
                  onClick={() => canLike && handleReaction(it, 'dislike')}
                  style={{
                    cursor: canLike ? 'pointer' : 'not-allowed',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 2,
                    opacity: canLike ? 1 : 0.4,
                    color: dislikeActive ? '#ff6b6b' : 'inherit',
                    fontWeight: dislikeActive ? 'bold' : 'normal'
                  }}
                  title={canLike ? (dislikeActive ? 'Remove dislike' : 'Dislike') : 'Cannot dislike own idiom'}
                >
                  👎 {it.dislikes || 0}
                </span>

                <span>·</span>

                {/* Author */}
                <span>by <strong>{it.username || 'Unknown'}</strong></span>

                {/* Status badge - only show for owner */}
                {isOwner && (
                  <>
                    <span>·</span>
                    <span style={{
                      color: it.status === 'published' ? '#2a5' : it.status === 'deleted' ? '#a22' : '#888',
                      fontSize: '0.8rem',
                      fontWeight: '500'
                    }}>{it.status || 'draft'}</span>
                  </>
                )}

                {/* Source */}
                {it.source && (
                  <>
                    <span>·</span>
                    <span>Source: {it.source}</span>
                  </>
                )}

                {/* Date */}
                {it.created_at && (
                  <>
                    <span>·</span>
                    <span>
                      {new Date(it.created_at).toLocaleDateString()}
                      {it.ai_score !== null && it.ai_score !== undefined && ` AI Score: ${it.ai_score}`}
                    </span>
                  </>
                )}

                {/* Comments link */}
                <span style={{ marginLeft: 'auto' }}>
                  <a
                    href="#"
                    onClick={(e) => { e.preventDefault(); /* TODO: implement comments */ }}
                    style={{ color: '#4a9eff', textDecoration: 'none' }}
                  >
                    comments
                  </a>
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Edit Modal */}
      {editingIdiom && (
        <IdiomEditModal
          idiom={editingIdiom}
          onClose={() => setEditingIdiom(null)}
          onSaved={() => {
            setEditingIdiom(null)
            loadIdioms()
          }}
        />
      )}
    </>
  )
}

function IdiomEditModal({ idiom, onClose, onSaved }) {
  const [formData, setFormData] = useState({
    title: idiom.title || '',
    en: idiom.en || '',
    ru: idiom.ru || '',
    explanation: idiom.explanation || '',
    source: idiom.source || ''
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [dropdownOpen, setDropdownOpen] = useState(false)

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSave = async (newStatus = null) => {
    setSaving(true)
    setError('')

    try {
      let token = null
      try {
        const raw = localStorage.getItem('auth')
        if (raw) {
          const auth = JSON.parse(raw)
          token = auth?.token || null
        }
      } catch {}

      if (!token) {
        setError('You must be logged in')
        return
      }

      const updateData = { ...formData }
      if (newStatus) {
        updateData.status = newStatus
      }

      const res = await fetch(`/api/idioms/${idiom._id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updateData)
      })

      if (!res.ok) {
        const err = await res.text()
        throw new Error(err || `HTTP ${res.status}`)
      }

      onSaved()
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this?')) return

    setSaving(true)
    setError('')

    try {
      let token = null
      try {
        const raw = localStorage.getItem('auth')
        if (raw) {
          const auth = JSON.parse(raw)
          token = auth?.token || null
        }
      } catch {}

      if (!token) {
        setError('You must be logged in')
        return
      }

      // Update status to 'deleted' instead of calling DELETE endpoint
      const res = await fetch(`/api/idioms/${idiom._id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: 'deleted' })
      })

      if (!res.ok) {
        const err = await res.text()
        throw new Error(err || `HTTP ${res.status}`)
      }

      onSaved()
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: 20
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#1a1a1a',
          borderRadius: 12,
          padding: 24,
          maxWidth: 600,
          width: '100%',
          maxHeight: '90vh',
          overflow: 'visible',
          border: '1px solid rgba(255,255,255,0.2)',
          position: 'relative'
        }}
        onClick={(e) => {
          e.stopPropagation()
          // Close dropdown when clicking anywhere in modal
          if (dropdownOpen) setDropdownOpen(false)
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 16,
            right: 16,
            background: 'none',
            border: 'none',
            color: 'rgba(255,255,255,0.6)',
            fontSize: '1.5rem',
            cursor: 'pointer',
            padding: 4,
            lineHeight: 1,
            transition: 'color 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = 'rgba(255,255,255,1)'}
          onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(255,255,255,0.6)'}
          title="Close"
        >
          ×
        </button>
        <h2 style={{ marginTop: 0, marginBottom: 20, color: '#4a9eff', paddingRight: 30 }}>Edit Idiom</h2>

        {error && (
          <div style={{
            padding: 12,
            marginBottom: 16,
            backgroundColor: 'rgba(229,9,20,0.2)',
            border: '1px solid rgba(229,9,20,0.5)',
            borderRadius: 6,
            color: '#ff6b6b'
          }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontSize: '0.9rem', opacity: 0.8 }}>
            Title
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => handleChange('title', e.target.value)}
            style={{
              width: '100%',
              padding: 10,
              backgroundColor: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: 6,
              color: 'white',
              fontSize: '1rem'
            }}
            placeholder="Enter a catchy title..."
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontSize: '0.9rem', opacity: 0.8 }}>
            English
          </label>
          <textarea
            value={formData.en}
            onChange={(e) => handleChange('en', e.target.value)}
            rows={3}
            style={{
              width: '100%',
              padding: 10,
              backgroundColor: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: 6,
              color: 'white',
              fontSize: '1rem',
              resize: 'vertical'
            }}
            placeholder="English text..."
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontSize: '0.9rem', opacity: 0.8 }}>
            Russian
          </label>
          <textarea
            value={formData.ru}
            onChange={(e) => handleChange('ru', e.target.value)}
            rows={3}
            style={{
              width: '100%',
              padding: 10,
              backgroundColor: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: 6,
              color: 'white',
              fontSize: '1rem',
              resize: 'vertical'
            }}
            placeholder="Russian text..."
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, fontSize: '0.9rem', opacity: 0.8 }}>
            Explanation
          </label>
          <textarea
            value={formData.explanation}
            onChange={(e) => handleChange('explanation', e.target.value)}
            rows={4}
            style={{
              width: '100%',
              padding: 10,
              backgroundColor: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: 6,
              color: 'white',
              fontSize: '1rem',
              resize: 'vertical'
            }}
            placeholder="Detailed explanation..."
          />
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', marginBottom: 6, fontSize: '0.9rem', opacity: 0.8 }}>
            Source
          </label>
          <input
            type="text"
            value={formData.source}
            onChange={(e) => handleChange('source', e.target.value)}
            style={{
              width: '100%',
              padding: 10,
              backgroundColor: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: 6,
              color: 'white',
              fontSize: '1rem'
            }}
            placeholder="Source (e.g., movie name)..."
          />
        </div>

        <div style={{ display: 'flex', gap: 1, justifyContent: 'flex-end', alignItems: 'center', position: 'relative' }}>
          {idiom.status === 'draft' ? (
            <>
              {/* Draft status: Publish button with dropdown */}
              <button
                onClick={() => handleSave('published')}
                disabled={saving}
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'rgba(34, 170, 85, 0.8)',
                  border: 'none',
                  borderRadius: '6px 0 0 6px',
                  color: 'white',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  fontSize: '0.95rem',
                  fontWeight: '500',
                  lineHeight: 1,
                  minWidth: '100px'
                }}
              >
                {saving ? 'Publishing...' : 'Publish'}
              </button>

              {/* Dropdown menu button */}
              <div style={{ position: 'relative' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setDropdownOpen(!dropdownOpen)
                  }}
                  disabled={saving}
                  style={{
                    padding: '10px 12px',
                    backgroundColor: 'rgba(34, 170, 85, 0.8)',
                    border: 'none',
                    borderRadius: '0 6px 6px 0',
                    color: 'white',
                    cursor: saving ? 'not-allowed' : 'pointer',
                    fontSize: '0.95rem',
                    fontWeight: '500',
                    lineHeight: 1
                  }}
                  title="More actions"
                >
                  ▼
                </button>

                {dropdownOpen && (
                  <div
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 'calc(-100px - 1px)',
                      marginTop: 4,
                      backgroundColor: '#2a2a2a',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: 6,
                      overflow: 'hidden',
                      zIndex: 1000,
                      minWidth: 'calc(100px + 1px + 36px)'
                    }}
                  >
                    <button
                      onClick={() => { setDropdownOpen(false); handleSave() }}
                      disabled={saving}
                      style={{
                        width: '100%',
                        padding: '10px 16px',
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: 'white',
                        cursor: saving ? 'not-allowed' : 'pointer',
                        fontSize: '0.9rem',
                        textAlign: 'left',
                        transition: 'background-color 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      Save
                    </button>
                    <button
                      onClick={() => { setDropdownOpen(false); handleDelete() }}
                      disabled={saving}
                      style={{
                        width: '100%',
                        padding: '10px 16px',
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: 'rgba(229,9,20,0.9)',
                        cursor: saving ? 'not-allowed' : 'pointer',
                        fontSize: '0.9rem',
                        textAlign: 'left',
                        transition: 'background-color 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : idiom.status === 'published' ? (
            <>
              {/* Published status: Save button with dropdown */}
              <button
                onClick={() => handleSave()}
                disabled={saving}
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'rgba(74, 158, 255, 0.8)',
                  border: 'none',
                  borderRadius: '6px 0 0 6px',
                  color: 'white',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  fontSize: '0.95rem',
                  fontWeight: '500',
                  lineHeight: 1,
                  minWidth: '100px'
                }}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>

              {/* Dropdown menu button */}
              <div style={{ position: 'relative' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setDropdownOpen(!dropdownOpen)
                  }}
                  disabled={saving}
                  style={{
                    padding: '10px 12px',
                    backgroundColor: 'rgba(74, 158, 255, 0.8)',
                    border: 'none',
                    borderRadius: '0 6px 6px 0',
                    color: 'white',
                    cursor: saving ? 'not-allowed' : 'pointer',
                    fontSize: '0.95rem',
                    fontWeight: '500',
                    lineHeight: 1
                  }}
                  title="More actions"
                >
                  ▼
                </button>

                {dropdownOpen && (
                  <div
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 'calc(-100px - 1px)',
                      marginTop: 4,
                      backgroundColor: '#2a2a2a',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: 6,
                      overflow: 'hidden',
                      zIndex: 1000,
                      minWidth: 'calc(100px + 1px + 36px)'
                    }}
                  >
                    <button
                      onClick={() => { setDropdownOpen(false); handleSave('draft') }}
                      disabled={saving}
                      style={{
                        width: '100%',
                        padding: '10px 16px',
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: 'white',
                        cursor: saving ? 'not-allowed' : 'pointer',
                        fontSize: '0.9rem',
                        textAlign: 'left',
                        transition: 'background-color 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      To Draft
                    </button>
                    <button
                      onClick={() => { setDropdownOpen(false); handleDelete() }}
                      disabled={saving}
                      style={{
                        width: '100%',
                        padding: '10px 16px',
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: 'rgba(229,9,20,0.9)',
                        cursor: saving ? 'not-allowed' : 'pointer',
                        fontSize: '0.9rem',
                        textAlign: 'left',
                        transition: 'background-color 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}

function IdiomsPage() {
  const [user, setUser] = useState(null)

  // Load user from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem('auth')
      if (raw) {
        const a = JSON.parse(raw)
        if (a?.user) setUser(a.user)
      }
    } catch {}
  }, [])

  // Listen for auth changes
  useEffect(() => {
    function onAuthChanged() {
      try {
        const raw = localStorage.getItem('auth')
        if (raw) {
          const a = JSON.parse(raw)
          if (a?.user) setUser(a.user)
        } else {
          setUser(null)
        }
      } catch {}
    }
    window.addEventListener('auth-changed', onAuthChanged)
    return () => window.removeEventListener('auth-changed', onAuthChanged)
  }, [])

  const isAdmin = user?.role === 'admin'

  return (
    <>
      <header>
        <AuthWidget />
        <div className="brand"><a href="/" style={{ color: 'inherit', textDecoration: 'none' }}>SubReverse</a></div>
        <div className="tagline">Idioms</div>
        <nav style={{ marginTop: '8px', fontSize: '0.95rem' }}>
          <a href="/" style={{ marginRight: 12 }}>Home</a>
          <a href="/idioms" style={{ marginRight: 12 }}>Idioms</a>
          {isAdmin && <a href="/admin" style={{ marginRight: 12 }}>Admin</a>}
          <a href="/content">Content</a>
        </nav>
      </header>
      <section className="results">
        <div className="card">
          <IdiomsView />
        </div>
      </section>
    </>
  )
}

function AdminPage() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)
  const [summary, setSummary] = useState(null)
  const [user, setUser] = useState(null)
  const [token, setToken] = useState('')

  // Load user and token from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem('auth')
      if (raw) {
        const a = JSON.parse(raw)
        if (a?.token && a?.user) {
          setToken(a.token)
          setUser(a.user)
        }
      }
    } catch {}
  }, [])

  // Listen for auth changes
  useEffect(() => {
    function onAuthChanged() {
      try {
        const raw = localStorage.getItem('auth')
        if (raw) {
          const a = JSON.parse(raw)
          if (a?.token) setToken(a.token)
          if (a?.user) setUser(a.user)
        }
      } catch {}
    }
    window.addEventListener('auth-changed', onAuthChanged)
    return () => window.removeEventListener('auth-changed', onAuthChanged)
  }, [])

  // Check if user is admin
  const isAdmin = user?.role === 'admin'

  async function onSubmit(e) {
    e.preventDefault()
    setStatus('')
    setSummary(null)
    if (!file) { setStatus('Please choose a file first.'); return }
    try {
      setBusy(true)
      const form = new FormData()
      form.append('file', file)
      const lower = file.name.toLowerCase()
      const endpoint = lower.endsWith('.zip') ? '/api/upload_zip' : (lower.endsWith('.ndjson') ? '/api/import_ndjson' : '/api/upload_file')
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch(endpoint, { method: 'POST', headers, body: form })
      const text = await res.text()
      let data
      try { data = JSON.parse(text) } catch { data = { message: text } }
      if (!res.ok) throw new Error(data?.detail || data?.message || `HTTP ${res.status}`)
      if (endpoint === '/api/upload_zip' || endpoint === '/api/import_ndjson') {
        setSummary(data)
        setStatus(endpoint === '/api/upload_zip' ? 'ZIP processed successfully' : 'NDJSON import completed')
      } else {
        setStatus(data?.message || `Uploaded: ${file.name}`)
      }
    } catch (err) {
      setStatus(err.message || String(err))
    } finally {
      setBusy(false)
    }
  }

  async function onClear() {
    setStatus('')
    setSummary(null)
    try {
      setBusy(true)
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch('/api/clear', { method: 'POST', headers })
      const text = await res.text()
      let data
      try { data = JSON.parse(text) } catch { data = { message: text } }
      if (!res.ok) throw new Error(data?.detail || data?.message || `HTTP ${res.status}`)
      const msg = `Cleared duplicates: ${data.documents_deleted || 0} deleted in ${data.duplicate_groups || 0} groups`
      setStatus(msg)
    } catch (err) {
      setStatus(err.message || String(err))
    } finally {
      setBusy(false)
    }
  }

  async function onIndex() {
    setStatus('')
    setSummary(null)
    try {
      setBusy(true)
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch('/api/index_elastic_search', { method: 'POST', headers })
      const text = await res.text()
      let data
      try { data = JSON.parse(text) } catch { data = { message: text } }
      if (!res.ok) throw new Error(data?.detail || data?.message || `HTTP ${res.status}`)
      const msg = `Indexed ${data.indexed || 0} of ${data.total_docs || 0} docs into index '${data.index || 'subtitles'}'`
      setStatus(msg)
    } catch (err) {
      setStatus(err.message || String(err))
    } finally {
      setBusy(false)
    }
  }

  async function onDeleteAll() {
    setStatus('')
    setSummary(null)
    if (!window.confirm('Delete all records from the database and clear Elasticsearch index?')) return
    try {
      setBusy(true)
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch('/api/delete_all', { method: 'POST', headers })
      const text = await res.text()
      let data
      try { data = JSON.parse(text) } catch { data = { message: text } }
      if (!res.ok) throw new Error(data?.detail || data?.message || `HTTP ${res.status}`)
      const msg = data?.message || `Deleted ${data.deleted_docs || 0} documents and cleared index '${data.index || 'subtitles'}'`
      setStatus(msg)
    } catch (err) {
      setStatus(err.message || String(err))
    } finally {
      setBusy(false)
    }
  }

  async function onExport() {
    setStatus('')
    setSummary(null)
    try {
      setBusy(true)
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch('/api/export', { method: 'POST', headers })
      if (!res.ok) {
        const text = await res.text()
        let data
        try { data = JSON.parse(text) } catch { data = { message: text } }
        throw new Error(data?.detail || data?.message || `HTTP ${res.status}`)
      }
      const blob = await res.blob()
      // Try to derive filename from headers
      let filename = 'export.ndjson'
      const disp = res.headers.get('Content-Disposition') || res.headers.get('content-disposition')
      if (disp) {
        const m = /filename\s*=\s*"?([^";]+)"?/i.exec(disp)
        if (m && m[1]) filename = m[1]
      }
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
      setStatus(`Export started: ${filename}`)
    } catch (err) {
      setStatus(err.message || String(err))
    } finally {
      setBusy(false)
    }
  }

  async function onUpdateStats() {
    setStatus('')
    setSummary(null)
    try {
      setBusy(true)
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      const res = await fetch('/api/stats', { method: 'POST', headers })
      const text = await res.text()
      let data
      try { data = JSON.parse(text) } catch { data = { message: text } }
      if (!res.ok) throw new Error(data?.detail || data?.message || `HTTP ${res.status}`)
      const total = typeof data.total === 'number' ? data.total : 0
      const filesCount = Array.isArray(data.files_en) ? data.files_en.length : 0
      setStatus(`System stats updated: ${total.toLocaleString()} phrases across ${filesCount} file(s).`)
    } catch (err) {
      setStatus(err.message || String(err))
    } finally {
      setBusy(false)
    }
  }

  // Show access denied if not admin
  if (!user) {
    return (
      <>
        <header>
          <AuthWidget />
          <div className="brand"><a href="/" style={{ color: 'inherit', textDecoration: 'none' }}>SubReverse</a></div>
          <div className="tagline">Admin Panel</div>
          <nav style={{ marginTop: '8px', fontSize: '0.95rem' }}>
            <a href="/" style={{ marginRight: 12 }}>Home</a>
          </nav>
        </header>
        <section className="results">
          <div className="card" style={{ borderColor: 'rgba(229,9,20,0.5)', textAlign: 'center', padding: '40px 20px' }}>
            <h2>Authentication Required</h2>
            <p>Please log in to access the admin panel.</p>
          </div>
        </section>
      </>
    )
  }

  if (!isAdmin) {
    return (
      <>
        <header>
          <AuthWidget />
          <div className="brand"><a href="/" style={{ color: 'inherit', textDecoration: 'none' }}>SubReverse</a></div>
          <div className="tagline">Admin Panel</div>
          <nav style={{ marginTop: '8px', fontSize: '0.95rem' }}>
            <a href="/" style={{ marginRight: 12 }}>Home</a>
          </nav>
        </header>
        <section className="results">
          <div className="card" style={{ borderColor: 'rgba(229,9,20,0.5)', textAlign: 'center', padding: '40px 20px' }}>
            <h2>Access Denied</h2>
            <p>You do not have permission to access this page.</p>
            <p>Admin role is required.</p>
          </div>
        </section>
      </>
    )
  }

  return (
    <>
      <header>
        <AuthWidget />
        <div className="brand"><a href="/" style={{ color: 'inherit', textDecoration: 'none' }}>SubReverse</a></div>
        <div className="tagline">Search bilingual subtitles like a pro</div>
        <nav style={{ marginTop: '8px', fontSize: '0.95rem' }}>
          <a href="/" style={{ marginRight: 12 }}>Home</a>
          <a href="/admin">Admin</a>
        </nav>
      </header>
      <section className="results">
        {/* Upload block */}
        <div className="card">
          <form onSubmit={onSubmit}>
            <div style={{ marginBottom: 12 }}>
              <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            </div>
            {file && (
              <div style={{ marginBottom: 12, fontSize: '0.9rem', color: '#666' }}>
                Selected: {file.name} ({file.size} bytes)
              </div>
            )}
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" disabled={busy}>
                {busy ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </form>
          {summary && (
            <div style={{ marginTop: 12, fontSize: '0.9rem' }}>
              <div><b>File:</b> {summary.filename}</div>
              <div><b>Extracted:</b> {summary.extracted_files}</div>
              <div><b>Valid pairs:</b> {summary.valid_pairs}</div>
              <div><b>Inserted docs:</b> {summary.inserted_docs}</div>
              {summary.skipped_files?.length ? (
                <details style={{ marginTop: 6 }}>
                  <summary>Skipped files ({summary.skipped_files.length})</summary>
                  <ul>
                    {summary.skipped_files.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </details>
              ) : null}
              {summary.errors?.length ? (
                <details style={{ marginTop: 6, color: '#b00' }}>
                  <summary>Errors ({summary.errors.length})</summary>
                  <ul>
                    {summary.errors.map((s, i) => <li key={i}>{s}</li>)}
                  </ul>
                </details>
              ) : null}
            </div>
          )}
        </div>

        {/* Maintenance block */}
        <div className="card">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button type="button" onClick={onClear} disabled={busy} title="Delete duplicate (en, ru) records from DB">
              {busy ? 'Please wait...' : 'Remove duplicates'}
            </button>
            <button type="button" onClick={onIndex} disabled={busy} title="Reindex all Mongo records into Elasticsearch">
              {busy ? 'Indexing...' : 'Index'}
            </button>
            <button type="button" onClick={onDeleteAll} disabled={busy} title="Delete all records and clear Elasticsearch index">
              {busy ? 'Deleting...' : 'Delete all'}
            </button>
            <button type="button" onClick={onExport} disabled={busy} title="Export all data to a file">
              {busy ? 'Exporting...' : 'Export'}
            </button>
            <button type="button" onClick={onUpdateStats} disabled={busy} title="Compute and store total phrases and file list">
              {busy ? 'Updating stats...' : 'Update system stats'}
            </button>
          </div>
          {status && (
            <div style={{ marginTop: 12 }}>
              {status}
            </div>
          )}
        </div>
      </section>
    </>
  )
}

function ContentPage() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let aborted = false
    ;(async () => {
      try {
        setLoading(true)
        const res = await fetch('/api/stats')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (!aborted) setFiles(Array.isArray(data.files_en) ? data.files_en : [])
      } catch (e) {
        if (!aborted) setError(e.message || String(e))
      } finally {
        if (!aborted) setLoading(false)
      }
    })()
    return () => { aborted = true }
  }, [])

  return (
    <>
      <header>
        <AuthWidget />
        <div className="brand"><a href="/" style={{ color: 'inherit', textDecoration: 'none' }}>SubReverse</a></div>
        <div className="tagline">Content: English subtitle files</div>
        <nav style={{ marginTop: '8px', fontSize: '0.95rem' }}>
          <a href="/" style={{ marginRight: 12 }}>Home</a>
          <a href="/admin">Admin</a>
        </nav>
      </header>
      <section className="results">
        {loading && <div className="card">Loading...</div>}
        {error && <div className="card" style={{ borderColor: 'rgba(229,9,20,0.5)' }}>Error: {error}</div>}
        {!loading && !error && (
          <div className="card">
            {files.length === 0 ? (
              <div>No files found.</div>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {files.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            )}
          </div>
        )}
      </section>
    </>
  )
}

export default function App() {
  const path = (typeof window !== 'undefined' ? window.location.pathname : '/')
    .replace(/\/+$/, '') || '/'

  return (
    <div className="wrap">
      <main>
        {path === '/' ? <HomePage /> : null}
        {path === '/idioms' ? <IdiomsPage /> : null}
        {path === '/admin' ? <AdminPage /> : null}
        {path === '/content' ? <ContentPage /> : null}
        {path !== '/' && path !== '/idioms' && path !== '/admin' && path !== '/content' ? (
          <section className="results"><div className="card">Not found</div></section>
        ) : null}
      </main>

      <footer>
        <a
          href="https://github.com/inwardik/subreverse"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            color: 'inherit',
            textDecoration: 'none',
            opacity: 0.7,
            transition: 'opacity 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
          onMouseLeave={(e) => e.currentTarget.style.opacity = '0.7'}
        >
          <svg height="20" width="20" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
          GitHub
        </a>
      </footer>
    </div>
  )
}
