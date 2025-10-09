import { useState, useEffect } from 'react'
import { courseAPI, reviewAPI } from '../utils/api'
import './Courses.css'

function Courses() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [enrolling, setEnrolling] = useState(null)
  const [reviewForm, setReviewForm] = useState({ courseId: null, rating: 5, comment: '' })
  const [showReviewForm, setShowReviewForm] = useState(false)
  const [reviews, setReviews] = useState({})
  const [showReviews, setShowReviews] = useState({})

  const token = localStorage.getItem('kn_token')

  useEffect(() => {
    fetchCourses()
  }, [])

  const fetchCourses = async () => {
    try {
      const response = await courseAPI.getAll()
      setCourses(response.data)
    } catch (err) {
      setError('Failed to load courses')
    } finally {
      setLoading(false)
    }
  }

  const handleEnroll = async (courseId) => {
    if (!token) {
      alert('Please login to enroll')
      return
    }

    setEnrolling(courseId)
    try {
      await courseAPI.enroll(courseId)
      alert('Successfully enrolled!')
    } catch (err) {
      alert(err.response?.data?.error || 'Enrollment failed')
    } finally {
      setEnrolling(null)
    }
  }

  const handleReviewSubmit = async (e) => {
    e.preventDefault()
    if (!token) {
      alert('Please login to submit a review')
      return
    }

    try {
      await reviewAPI.create(reviewForm.courseId, {
        rating: reviewForm.rating,
        comment: reviewForm.comment,
      })
      alert('Review submitted successfully!')
      setShowReviewForm(false)
      setReviewForm({ courseId: null, rating: 5, comment: '' })
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to submit review')
    }
  }

  const openReviewForm = (courseId) => {
    setReviewForm({ ...reviewForm, courseId })
    setShowReviewForm(true)
  }

  const fetchReviews = async (courseId) => {
    try {
      const response = await reviewAPI.getByCourse(courseId)
      setReviews({ ...reviews, [courseId]: response.data })
      setShowReviews({ ...showReviews, [courseId]: true })
    } catch (err) {
      console.error('Failed to load reviews', err)
    }
  }

  const toggleReviews = (courseId) => {
    if (showReviews[courseId]) {
      setShowReviews({ ...showReviews, [courseId]: false })
    } else {
      if (!reviews[courseId]) {
        fetchReviews(courseId)
      } else {
        setShowReviews({ ...showReviews, [courseId]: true })
      }
    }
  }

  if (loading) return <div className="container"><p>Loading courses...</p></div>
  if (error) return <div className="container"><p className="error">{error}</p></div>

  return (
    <div className="container">
      <h1>Available Courses</h1>
      
      {courses.length === 0 ? (
        <p>No courses available yet.</p>
      ) : (
        <div className="courses-grid">
          {courses.map((course) => (
            <div key={course.id} className="course-card">
              <h3>{course.title}</h3>
              <p>{course.description}</p>
              {course.content_url && (
                <p className="content-url">
                  <a href={course.content_url} target="_blank" rel="noopener noreferrer">
                    View Content
                  </a>
                </p>
              )}
              <div className="course-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => handleEnroll(course.id)}
                  disabled={enrolling === course.id || !token}
                >
                  {enrolling === course.id ? 'Enrolling...' : 'Enroll'}
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => openReviewForm(course.id)}
                  disabled={!token}
                >
                  Write Review
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => toggleReviews(course.id)}
                >
                  {showReviews[course.id] ? 'Hide Reviews' : 'Show Reviews'}
                </button>
              </div>
              
              {showReviews[course.id] && reviews[course.id] && (
                <div className="reviews-section">
                  <h4>Reviews ({reviews[course.id].length})</h4>
                  {reviews[course.id].length === 0 ? (
                    <p className="no-reviews">No reviews yet. Be the first to review!</p>
                  ) : (
                    reviews[course.id].map((review) => (
                      <div key={review.id} className="review-item">
                        <div className="review-header">
                          <span className="review-rating">{'⭐'.repeat(review.rating)}</span>
                          <span className="review-date">
                            {new Date(review.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="review-comment">{review.comment}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showReviewForm && (
        <div className="modal">
          <div className="modal-content">
            <h2>Write a Review</h2>
            <form onSubmit={handleReviewSubmit}>
              <div className="form-group">
                <label>Rating (1-5)</label>
                <select
                  value={reviewForm.rating}
                  onChange={(e) => setReviewForm({ ...reviewForm, rating: parseInt(e.target.value) })}
                >
                  <option value="5">5 - Excellent</option>
                  <option value="4">4 - Good</option>
                  <option value="3">3 - Average</option>
                  <option value="2">2 - Poor</option>
                  <option value="1">1 - Terrible</option>
                </select>
              </div>
              <div className="form-group">
                <label>Comment</label>
                <textarea
                  value={reviewForm.comment}
                  onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
                  rows="4"
                  placeholder="Share your thoughts about this course..."
                />
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn btn-primary">Submit Review</button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowReviewForm(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Courses
