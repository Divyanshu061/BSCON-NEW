import React, { useEffect, useState } from 'react'

interface User {
  id: number
  email: string
  name: string
  profile_picture?: string
}

export default function Callback() {
  const [user, setUser] = useState<User | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/auth/me', {
      credentials: 'include'
    })
      .then(async res => {
        if (!res.ok) throw new Error(await res.text())
        return res.json() as Promise<User>
      })
      .then(setUser)
      .catch(err => setError(err.message))
  }, [])

  if (error) return <div>Error: {error}</div>
  if (!user) return <div>Loading user info…</div>

  return (
    <div style={{ padding: 20, fontFamily: 'sans-serif' }}>
      <h2>Welcome, {user.name}</h2>
      <p>Email: {user.email}</p>
      {user.profile_picture && (
        <img src={user.profile_picture} alt="Profile" width={80} />
      )}
    </div>
  )
}
