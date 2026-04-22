import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#1E1E1E', color: '#fff', border: '1px solid #2E2E2E' },
          success: { iconTheme: { primary: '#AE0001', secondary: '#fff' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
