import { useState, useEffect } from "react";
import { courseAPI, reviewAPI } from "../utils/api";
import "./Courses.css";

function Courses() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [enrolling, setEnrolling] = useState(null);
  const [unenrolling, setUnenrolling] = useState(null);
  const [enrolledCourses, setEnrolledCourses] = useState(new Set());
  const [reviewForm, setReviewForm] = useState({
    courseId: null,
    rating: 5,
    comment: "",
  });
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviews, setReviews] = useState({});
  const [showReviews, setShowReviews] = useState({});
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState({
    title: "",
    description: "",
    content_url: "",
  });
  const [creating, setCreating] = useState(false);

  const token = localStorage.getItem("kn_token");

  useEffect(() => {
    fetchCourses();
    if (token) {
      fetchEnrollments();
    }
  }, [token]);

  const fetchCourses = async () => {
  console.log('[Courses] Starting to fetch courses...');
  try {
    console.log('[Courses] Making API call to get all courses...');
    const response = await courseAPI.getAll();
    console.log('[Courses] Received response:', {
      status: response.status,
      statusText: response.statusText,
      data: response.data ? 'Data received' : 'No data'
    });
    
    if (response.data) {
      console.log(`[Courses] Successfully loaded ${response.data.length} courses`);
      setCourses(response.data);
    } else {
      console.warn('[Courses] No courses data in response');
      setError('No courses data received from server');
    }
  } catch (err) {
    console.error('[Courses] Error fetching courses:', {
      name: err.name,
      message: err.message,
      response: err.response ? {
        status: err.response.status,
        statusText: err.response.statusText,
        data: err.response.data
      } : 'No response',
      stack: err.stack
    });

    const message = err.response?.data?.message || 
                  err.response?.data || 
                  err.message || 
                  "Failed to load courses";
    
    console.error('[Courses] Error message to show user:', message);
    setError(message);
  } finally {
    setLoading(false);
  }
};

  const fetchEnrollments = async () => {
    try {
      const response = await courseAPI.getEnrollments();
      const enrolledIds = new Set(response.data.map((e) => e.course_id));
      setEnrolledCourses(enrolledIds);
    } catch (err) {
      console.error("Failed to load enrollments", err);
    }
  };

  const handleEnroll = async (courseId) => {
    if (!token) {
      alert("Please login to enroll");
      return;
    }

    setEnrolling(courseId);
    try {
      await courseAPI.enroll(courseId);
      alert("Successfully enrolled!");
      // Update enrolled courses
      setEnrolledCourses((prev) => new Set([...prev, courseId]));
    } catch (err) {
      alert(err.response?.data?.error || "Enrollment failed");
    } finally {
      setEnrolling(null);
    }
  };

  const handleUnenroll = async (courseId) => {
    if (!token) {
      alert("Please login");
      return;
    }

    if (
      !window.confirm("Are you sure you want to unenroll from this course?")
    ) {
      return;
    }

    setUnenrolling(courseId);
    try {
      await courseAPI.unenroll(courseId);
      alert("Successfully unenrolled!");
      // Remove from enrolled courses
      setEnrolledCourses((prev) => {
        const newSet = new Set(prev);
        newSet.delete(courseId);
        return newSet;
      });
    } catch (err) {
      alert(err.response?.data?.error || "Unenrollment failed");
    } finally {
      setUnenrolling(null);
    }
  };

  const isEnrolled = (courseId) => {
    return enrolledCourses.has(courseId);
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!token) {
      alert("Please login to submit a review");
      return;
    }

    try {
      await reviewAPI.create(reviewForm.courseId, {
        rating: reviewForm.rating,
        comment: reviewForm.comment,
      });
      alert("Review submitted successfully!");
      setShowReviewForm(false);
      setReviewForm({ courseId: null, rating: 5, comment: "" });
    } catch (err) {
      alert(err.response?.data?.error || "Failed to submit review");
    }
  };

  const openReviewForm = (courseId) => {
    setReviewForm({ ...reviewForm, courseId });
    setShowReviewForm(true);
  };

  const fetchReviews = async (courseId) => {
    try {
      const response = await reviewAPI.getByCourse(courseId);
      setReviews({ ...reviews, [courseId]: response.data });
      setShowReviews({ ...showReviews, [courseId]: true });
    } catch (err) {
      console.error("Failed to load reviews", err);
    }
  };

  const toggleReviews = (courseId) => {
    if (showReviews[courseId]) {
      setShowReviews({ ...showReviews, [courseId]: false });
    } else {
      if (!reviews[courseId]) {
        fetchReviews(courseId);
      } else {
        setShowReviews({ ...showReviews, [courseId]: true });
      }
    }
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    if (!token) {
      alert("Please login to create a course");
      return;
    }

    if (!createForm.title.trim()) {
      alert("Course title is required");
      return;
    }

    setCreating(true);
    try {
      await courseAPI.create({
        title: createForm.title,
        description: createForm.description,
        content_url: createForm.content_url,
      });
      alert("Course created successfully!");
      setShowCreateForm(false);
      setCreateForm({ title: "", description: "", content_url: "" });
      fetchCourses(); // Refresh the course list
    } catch (err) {
      alert(err.response?.data?.error || "Failed to create course");
    } finally {
      setCreating(false);
    }
  };

  if (loading)
    return (
      <div className="container">
        <p>Loading courses...</p>
      </div>
    );
  if (error)
    return (
      <div className="container">
        <p className="error">{error}</p>
      </div>
    );

  return (
    <div className="container">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <h1>Available Courses</h1>
        {token && (
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateForm(true)}
            style={{ marginTop: "0" }}
          >
            + Create Course
          </button>
        )}
      </div>

      {courses.length === 0 ? (
        <p>No courses available yet.</p>
      ) : (
        <div className="courses-grid">
          {courses.map((course) => {
            const enrolled = isEnrolled(course.id);
            return (
              <div
                key={course.id}
                className={`course-card ${enrolled ? "enrolled" : ""}`}
              >
                {enrolled && (
                  <div className="enrolled-badge">
                    <span>✓ Enrolled</span>
                  </div>
                )}
                <h3>{course.title}</h3>
                <p>{course.description}</p>
                {course.content_url && (
                  <p className="content-url">
                    <a
                      href={course.content_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View Content
                    </a>
                  </p>
                )}
                <div className="course-actions">
                  {enrolled ? (
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleUnenroll(course.id)}
                      disabled={unenrolling === course.id || !token}
                    >
                      {unenrolling === course.id
                        ? "Unenrolling..."
                        : "Unenroll"}
                    </button>
                  ) : (
                    <button
                      className="btn btn-primary"
                      onClick={() => handleEnroll(course.id)}
                      disabled={enrolling === course.id || !token}
                    >
                      {enrolling === course.id ? "Enrolling..." : "Enroll"}
                    </button>
                  )}
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
                    {showReviews[course.id] ? "Hide Reviews" : "Show Reviews"}
                  </button>
                </div>

                {showReviews[course.id] && reviews[course.id] && (
                  <div className="reviews-section">
                    <h4>Reviews ({reviews[course.id].length})</h4>
                    {reviews[course.id].length === 0 ? (
                      <p className="no-reviews">
                        No reviews yet. Be the first to review!
                      </p>
                    ) : (
                      reviews[course.id].map((review) => (
                        <div key={review.id} className="review-item">
                          <div className="review-header">
                            <span className="review-rating">
                              {"⭐".repeat(review.rating)}
                            </span>
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
            );
          })}
        </div>
      )}

      {showCreateForm && (
        <div className="modal">
          <div className="modal-content">
            <h2>Create New Course</h2>
            <form onSubmit={handleCreateCourse}>
              <div className="form-group">
                <label>Course Title *</label>
                <input
                  type="text"
                  value={createForm.title}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, title: e.target.value })
                  }
                  placeholder="Enter course title"
                  required
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={createForm.description}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      description: e.target.value,
                    })
                  }
                  rows="4"
                  placeholder="Enter course description..."
                />
              </div>
              <div className="form-group">
                <label>Content URL (Optional)</label>
                <input
                  type="url"
                  value={createForm.content_url}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      content_url: e.target.value,
                    })
                  }
                  placeholder="https://example.com/course-content"
                />
              </div>
              <div className="modal-actions">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={creating}
                >
                  {creating ? "Creating..." : "Create Course"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowCreateForm(false);
                    setCreateForm({
                      title: "",
                      description: "",
                      content_url: "",
                    });
                  }}
                  disabled={creating}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
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
                  onChange={(e) =>
                    setReviewForm({
                      ...reviewForm,
                      rating: parseInt(e.target.value),
                    })
                  }
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
                  onChange={(e) =>
                    setReviewForm({ ...reviewForm, comment: e.target.value })
                  }
                  rows="4"
                  placeholder="Share your thoughts about this course..."
                />
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn btn-primary">
                  Submit Review
                </button>
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
  );
}

export default Courses;
