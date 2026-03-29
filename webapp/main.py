# main.py
from fasthtml.common import *
from monsterui.all import *
from fastlite import *
import markdown
from passlib.hash import bcrypt
from datetime import datetime
import os
from dataclasses import dataclass, field

# ---------- Database Setup ----------
DB_FILE = "khan.db"
db = database(DB_FILE)

# ---------- Models ----------
@dataclass
class User:
    id: int = None  # Make id optional with default None
    email: str = ""
    password: str = ""
    name: str = ""
    is_admin: bool = False

@dataclass
class Course:
    id: int = None  # Make id optional
    title: str = ""
    description: str = ""
    image_url: str = "/static/default.jpg"

@dataclass
class Lesson:
    id: int = None
    course_id: int = 0
    title: str = ""
    content: str = ""
    order: int = 0

@dataclass
class Enrollment:
    user_id: int = 0
    course_id: int = 0
    enrolled_at: datetime = None

@dataclass
class Progress:
    user_id: int = 0
    lesson_id: int = 0
    completed: bool = False
    completed_at: datetime = None

# Create tables (if they don't exist)
users = db.create(User, transform=True)
courses = db.create(Course, transform=True, pk='id')
lessons = db.create(Lesson, transform=True)
enrollments = db.create(Enrollment, transform=True, pk=['user_id', 'course_id'])
progress = db.create(Progress, transform=True, pk=['user_id', 'lesson_id'])

# Insert some sample data if empty
if not courses():
    sample_courses = [
        Course(title="Python Basics", description="Learn Python fundamentals", image_url="/static/python.jpg"),
        Course(title="Data Science Intro", description="Start your data journey", image_url="/static/ds.jpg"),
        Course(title="Web Development", description="HTML, CSS, JS basics", image_url="/static/web.jpg")
    ]
    for c in sample_courses:
        courses.insert(c)
    
    # Get the Python course to add lessons
    python_course = courses(where="title='Python Basics'", first=True)
    sample_lessons = [
        Lesson(course_id=python_course.id, title="What is Python?", content="Python is a high-level programming language...", order=1),
        Lesson(course_id=python_course.id, title="Variables and Data Types", content="Variables store data...", order=2),
        Lesson(course_id=python_course.id, title="Control Flow", content="if, else, loops...", order=3)
    ]
    for l in sample_lessons:
        lessons.insert(l)

# ---------- Helper Functions ----------
def get_user_by_email(email):
    return users(where="email=?", args=(email,), first=True)

def authenticate(email, password):
    user = get_user_by_email(email)
    if user and bcrypt.verify(password, user.password):
        return user
    return None

def hash_password(password):
    return bcrypt.hash(password)

def current_user(req):
    auth = req.scope.get('auth')
    if auth:
        return users.get(auth['user_id'])
    return None

def require_auth(req):
    if not current_user(req):
        return RedirectResponse('/login', status_code=303)

def require_admin(req):
    user = current_user(req)
    if not user or not user.is_admin:
        return RedirectResponse('/', status_code=303)

def enrollment_status(user, course):
    if not user:
        return "Not enrolled"
    if enrollments.get((user.id, course.id)):
        return "Enrolled"
    return "Not enrolled"

def course_progress(user, course):
    if not user:
        return 0
    course_lessons = lessons(where="course_id=?", args=(course.id,))
    if not course_lessons:
        return 0
    completed_lessons = progress(where="user_id=? AND lesson_id IN (SELECT id FROM lesson WHERE course_id=?)",
                                  args=(user.id, course.id))
    return len(completed_lessons) / len(course_lessons) * 100

# ---------- FastHTML App ----------
app, rt = fast_app(
    hdrs=Theme.blue.headers(highlightjs=True),
)

# Custom beforeware to handle auth, skipping public routes
def check_auth(req, session):
    # Public routes that don't require authentication
    public_paths = ['/login', '/signup', '/', '/static/']
    if any(req.url.path.startswith(p) for p in public_paths):
        return None  # allow access without auth

    # For all other routes, require authentication
    auth = session.get('auth')
    req.scope['auth'] = auth
    if not auth:
        return RedirectResponse('/login', status_code=303)
    return None

app.before.append(check_auth)

# ---------- Routes ----------
@rt("/")
def index(req):
    user = current_user(req)
    all_courses = courses()
    cards = []
    for c in all_courses:
        status = enrollment_status(user, c)
        enroll_btn = ""
        if user and status == "Not enrolled":
            enroll_btn = Button("Enroll", hx_post=f"/enroll/{c.id}", hx_target=f"#course-{c.id}", hx_swap="outerHTML")
        elif user and status == "Enrolled":
            enroll_btn = Button("Enrolled", disabled=True)
        card = Card(
            Img(src=c.image_url, alt=c.title, cls="w-full h-48 object-cover"),
            H3(c.title),
            P(c.description),
            enroll_btn,
            id=f"course-{c.id}",
            cls="hover:shadow-lg transition-shadow"
        )
        cards.append(card)
    return Titled(
        "Khan Academy Style Platform",
        H1("Welcome to Learning Platform"),
        P("Learn anything, anytime."),
        DivGrid(cards, cols=3)
    )

@rt("/login")
def login_page(req):
    return Titled(
        "Login",
        Form(
            LabelInput("Email", name="email", type="email", required=True),
            LabelInput("Password", name="password", type="password", required=True),
            Button("Log in", type="submit"),
            hx_post="/login", 
            hx_target="body", 
            hx_swap="outerHTML"
        )
    )

@rt("/login", methods=["post"])
def login_post(req, email:str, password:str):
    user = authenticate(email, password)
    if user:
        req.session['auth'] = {'user_id': user.id}
        return RedirectResponse('/', status_code=303)
    else:
        return Titled("Login Failed", P("Invalid email or password"), A("Try again", href="/login"))

@rt("/signup")
def signup_page(req):
    return Titled(
        "Sign Up",
        Form(
            LabelInput("Name", name="name", required=True),
            LabelInput("Email", name="email", type="email", required=True),
            LabelInput("Password", name="password", type="password", required=True),
            Button("Sign up", type="submit"),
            hx_post="/signup", 
            hx_target="body", 
            hx_swap="outerHTML"
        )
    )

@rt("/signup", methods=["post"])
def signup_post(req, name:str, email:str, password:str):
    if get_user_by_email(email):
        return Titled("Signup Failed", P("Email already exists"), A("Try again", href="/signup"))
    hashed = hash_password(password)
    user = User(email=email, password=hashed, name=name)
    users.insert(user)
    req.session['auth'] = {'user_id': user.id}
    return RedirectResponse('/', status_code=303)

@rt("/logout")
def logout(req):
    if 'auth' in req.session:
        del req.session['auth']
    return RedirectResponse('/login', status_code=303)

@rt("/enroll/{course_id}")
def enroll(req, course_id:int):
    user = current_user(req)
    if not user:
        return RedirectResponse('/login', status_code=303)
    if enrollments.get((user.id, course_id)):
        return Button("Enrolled", disabled=True)
    enrollment = Enrollment(user_id=user.id, course_id=course_id, enrolled_at=datetime.now())
    enrollments.insert(enrollment)
    return Button("Enrolled", disabled=True)

@rt("/course/{course_id}")
def course_detail(req, course_id:int):
    user = current_user(req)
    course = courses.get(course_id)
    if not course:
        return Titled("Not Found", P("Course not found"))
    lessons_list = lessons(where="course_id=?", args=(course_id,), order_by="order")
    # Build lesson items with progress
    lesson_items = []
    for l in lessons_list:
        completed = progress.get((user.id, l.id)) if user else None
        check = "✅ " if completed and completed.completed else "📖 "
        lesson_items.append(Li(A(f"{check}{l.title}", href=f"/lesson/{l.id}")))
    # Calculate progress
    prog = course_progress(user, course) if user else 0
    return Titled(
        course.title,
        H2(course.title),
        P(course.description),
        H3(f"Your Progress: {prog:.0f}%"),
        Ul(*lesson_items),
        A("Back to courses", href="/")
    )

@rt("/lesson/{lesson_id}")
def lesson_detail(req, lesson_id:int):
    user = current_user(req)
    lesson = lessons.get(lesson_id)
    if not lesson:
        return Titled("Not Found", P("Lesson not found"))
    course = courses.get(lesson.course_id)
    # Check if enrolled
    if not user or not enrollments.get((user.id, course.id)):
        return Titled("Access Denied", P("You must enroll to view this lesson"), A("Enroll now", href=f"/course/{course.id}"))
    # Markdown rendering
    html_content = markdown.markdown(lesson.content)
    # Progress toggle button
    prog = progress.get((user.id, lesson.id))
    if prog and prog.completed:
        btn = Button("Mark Incomplete", hx_post=f"/toggle_progress/{lesson.id}", hx_target="#progress-btn", hx_swap="outerHTML")
    else:
        btn = Button("Mark Complete", hx_post=f"/toggle_progress/{lesson.id}", hx_target="#progress-btn", hx_swap="outerHTML")
    return Titled(
        f"{course.title}: {lesson.title}",
        Div(NotStr(html_content), cls="prose"),
        Div(btn, id="progress-btn"),
        A("Back to course", href=f"/course/{course.id}")
    )

@rt("/toggle_progress/{lesson_id}", methods=["post"])
def toggle_progress(req, lesson_id:int):
    user = current_user(req)
    if not user:
        return "Unauthorized"
    prog = progress.get((user.id, lesson_id))
    if prog and prog.completed:
        progress.update({'completed': False, 'completed_at': None}, where="user_id=? AND lesson_id=?", args=(user.id, lesson_id))
        btn = Button("Mark Complete", hx_post=f"/toggle_progress/{lesson_id}", hx_target="#progress-btn", hx_swap="outerHTML")
    else:
        progress.upsert(Progress(user_id=user.id, lesson_id=lesson_id, completed=True, completed_at=datetime.now()))
        btn = Button("Mark Incomplete", hx_post=f"/toggle_progress/{lesson_id}", hx_target="#progress-btn", hx_swap="outerHTML")
    return btn

# ---------- Admin Routes ----------
@rt("/admin")
def admin_panel(req):
    user = current_user(req)
    if not user or not user.is_admin:
        return RedirectResponse('/', status_code=303)
    return Titled(
        "Admin Panel",
        H2("Courses"),
        Table(
            Thead(Tr(Th("ID"), Th("Title"), Th("Actions"))),
            Tbody(*[Tr(Td(c.id), Td(c.title), Td(A("Edit", href=f"/admin/course/{c.id}"))) for c in courses()])
        ),
        A("Add Course", href="/admin/course/new")
    )

@rt("/admin/course/{course_id}")
def edit_course(req, course_id:str):
    user = current_user(req)
    if not user or not user.is_admin:
        return RedirectResponse('/', status_code=303)
    course = courses.get(int(course_id)) if course_id != "new" else None
    form_data = {}
    if course:
        form_data = {'title': course.title, 'description': course.description, 'image_url': course.image_url}
    return Titled(
        "Edit Course" if course else "New Course",
        Form(
            LabelInput("Title", name="title", value=form_data.get('title', ''), required=True),
            LabelInput("Description", name="description", value=form_data.get('description', ''), required=True),
            LabelInput("Image URL", name="image_url", value=form_data.get('image_url', ''), required=True),
            Button("Save", type="submit"),
            hx_post=f"/admin/course/{course_id if course else 'new'}", 
            hx_target="body", 
            hx_swap="outerHTML"
        )
    )

@rt("/admin/course/{course_id}", methods=["post"])
def save_course(req, course_id:str, title:str, description:str, image_url:str):
    user = current_user(req)
    if not user or not user.is_admin:
        return RedirectResponse('/', status_code=303)
    if course_id == "new":
        courses.insert(Course(title=title, description=description, image_url=image_url))
    else:
        courses.update({'title': title, 'description': description, 'image_url': image_url}, where="id=?", args=(int(course_id),))
    return RedirectResponse('/admin', status_code=303)

os.makedirs("static", exist_ok=True)

serve()