import { Link, useNavigate } from 'react-router-dom'
import './Navbar.css'

function Navbar() {
  const navigate = useNavigate()
  const token = localStorage.getItem('kn_token')

  const handleLogout = () => {
    localStorage.removeItem('kn_token')
    localStorage.removeItem('kn_user')
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="container navbar-content">
        <Link to="/" className="navbar-brand">
          🎓 KnowledgeNest
        </Link>
        <div className="navbar-links">
          <Link to="/courses">Courses</Link>
          {token ? (
            <>
              <span className="user-info">
                {JSON.parse(localStorage.getItem('kn_user') || '{}').email}
              </span>
              <button onClick={handleLogout} className="btn btn-secondary">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login">
                <button className="btn btn-secondary">Login</button>
              </Link>
              <Link to="/register">
                <button className="btn btn-primary">Register</button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar
