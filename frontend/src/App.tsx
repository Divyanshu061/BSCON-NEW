import React from 'react';

export default function App() {
  const login = () => {
    // 🔥 This lets the browser handle cookies + redirect natively
    window.location.href = "http://localhost:8000/api/auth/login/google";
  };

  return (
    <div style={{ padding: 20, fontFamily: 'sans-serif' }}>
      <h1>Bank Statement Converter</h1>
      <button onClick={login}>Login with Google</button>
    </div>
  );
}
