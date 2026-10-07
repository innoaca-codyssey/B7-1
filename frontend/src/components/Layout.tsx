import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.ts'

function Layout() {
  const { user, logout } = useAuth()

  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">
          AI 챗봇
        </Link>
        <nav>
          <NavLink to="/" end>
            채팅
          </NavLink>
          <NavLink to="/logs">내 대화 기록</NavLink>
          {user?.role === 'admin' && <NavLink to="/admin">관리자</NavLink>}
        </nav>
        <span className="user">{user?.username}</span>
        <button type="button" onClick={logout}>
          로그아웃
        </button>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  )
}

export default Layout
