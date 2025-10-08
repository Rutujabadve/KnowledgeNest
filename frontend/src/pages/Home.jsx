import { Link } from 'react-router-dom'
import './Home.css'

function Home() {
  return (
    <div className="home">
      <div className="hero">
        <div className="container">
          <h1>Welcome to KnowledgeNest</h1>
          <p>Your gateway to online learning excellence</p>
          <div className="hero-buttons">
            <Link to="/courses">
              <button className="btn btn-primary btn-large">
                Browse Courses
              </button>
            </Link>
            <Link to="/register">
              <button className="btn btn-secondary btn-large">
                Get Started
              </button>
            </Link>
          </div>
        </div>
      </div>
      
      <div className="container">
        <div className="features">
          <div className="feature-card">
            <h3>📚 Quality Content</h3>
            <p>Access high-quality courses from expert instructors</p>
          </div>
          <div className="feature-card">
            <h3>🎯 Learn at Your Pace</h3>
            <p>Study whenever and wherever you want</p>
          </div>
          <div className="feature-card">
            <h3>⭐ Reviews & Ratings</h3>
            <p>See what other students think about courses</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home
