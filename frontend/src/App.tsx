import React from 'react'

export default function App() {
  const login = () => {
    window.location.href = '/api/auth/login/google'
  }

  return (
    <div style={{ padding: 20, fontFamily: 'sans-serif' }}>
      <h1>Bank Statement Converter</h1>
      <button onClick={login}>
        Login with Google
      </button>
    </div>
  )
}
