import { Route, Routes } from 'react-router-dom'
import AdminPage from './pages/AdminPage.tsx'
import ChatPage from './pages/ChatPage.tsx'
import LoginPage from './pages/LoginPage.tsx'
import LogsPage from './pages/LogsPage.tsx'
import SignupPage from './pages/SignupPage.tsx'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/" element={<ChatPage />} />
      <Route path="/logs" element={<LogsPage />} />
      <Route path="/admin" element={<AdminPage />} />
    </Routes>
  )
}

export default App
