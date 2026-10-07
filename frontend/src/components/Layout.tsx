import { Link, NavLink, Outlet } from 'react-router-dom'

function Layout() {
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
          <NavLink to="/admin">관리자</NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  )
}

export default Layout
