import os
import json
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Job, Lecture, Chat
from services.orchestrator import OrchestratorService
from services.chat_service import ChatService
import threading

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

def get_orchestrator():
    """Get orchestrator service instance"""
    return OrchestratorService()

def get_chat_service():
    """Get chat service instance"""
    return ChatService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def init_db():
    """Initialize database and create tables"""
    with app.app_context():
        db.create_all()
        
        # Create default user if none exists
        if User.query.count() == 0:
            default_user = User(
                name='Admin',
                email='admin@example.com'
            )
            default_user.set_password('admin123')
            db.session.add(default_user)
            db.session.commit()

# Authentication helpers
def login_required(f):
    """Decorator for routes that require authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged-in user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# Routes
@app.route('/')
def index():
    """Home page"""
    user = get_current_user()
    if user:
        jobs = Job.query.filter_by(user_id=user.id).order_by(Job.created_at.desc()).limit(10).all()
        return render_template('index.html', user=user, recent_jobs=jobs)
    return render_template('index.html', user=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload lecture video"""
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video file provided.', 'error')
            return redirect(request.url)
        
        file = request.files['video']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Allowed: mp4, avi, mov, mkv, webm', 'error')
            return redirect(request.url)
        
        user = get_current_user()
        
        # Create job entry
        job = Job(user_id=user.id, video_path='')
        db.session.add(job)
        db.session.commit()
        
        # Create storage directory
        storage_path = os.path.join(app.config['UPLOAD_FOLDER'], f'job_{job.id}')
        os.makedirs(storage_path, exist_ok=True)
        
        # Save video file
        filename = secure_filename(file.filename)
        video_path = os.path.join(storage_path, 'video.mp4')
        file.save(video_path)
        
        # Update job with video path
        job.video_path = video_path
        db.session.commit()
        
        # Start processing in background thread
        def process_in_background():
            with app.app_context():
                try:
                    orchestrator = get_orchestrator()
                    orchestrator.process_job(job.id)
                except Exception as e:
                    app.logger.error(f"Job {job.id} processing error: {str(e)}")
        
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
        
        flash(f'Video uploaded successfully! Job ID: {job.id}. Processing started.', 'success')
        return redirect(url_for('job_status', job_id=job.id))
    
    return render_template('upload.html')

@app.route('/jobs')
@login_required
def jobs():
    """List all jobs for current user"""
    user = get_current_user()
    jobs = Job.query.filter_by(user_id=user.id).order_by(Job.created_at.desc()).all()
    return render_template('jobs.html', jobs=jobs)

@app.route('/jobs/<int:job_id>')
@login_required
def job_status(job_id):
    """View job status"""
    user = get_current_user()
    job = Job.query.get_or_404(job_id)
    
    if job.user_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('jobs'))
    
    return render_template('job_status.html', job=job)

@app.route('/api/jobs/<int:job_id>/status')
@login_required
def api_job_status(job_id):
    """API endpoint for job status"""
    user = get_current_user()
    job = Job.query.get_or_404(job_id)
    
    if job.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(job.to_dict())

@app.route('/lectures/<int:lecture_id>')
@login_required
def lecture_view(lecture_id):
    """View lecture notes"""
    user = get_current_user()
    lecture = Lecture.query.get_or_404(lecture_id)
    job = lecture.job
    
    if job.user_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('jobs'))
    
    notes_data = None
    transcript_data = None
    
    if lecture.notes_path and os.path.exists(lecture.notes_path):
        with open(lecture.notes_path, 'r') as f:
            notes_data = json.load(f)
    
    if lecture.transcript_path and os.path.exists(lecture.transcript_path):
        with open(lecture.transcript_path, 'r') as f:
            transcript_data = json.load(f)
    
    return render_template('lecture_view.html', 
                         lecture=lecture, 
                         job=job,
                         notes=notes_data,
                         transcript=transcript_data)

@app.route('/lectures/<int:lecture_id>/chat', methods=['GET', 'POST'])
@login_required
def lecture_chat(lecture_id):
    """Chat interface for lecture"""
    user = get_current_user()
    lecture = Lecture.query.get_or_404(lecture_id)
    job = lecture.job
    
    if job.user_id != user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('jobs'))
    
    if request.method == 'POST':
        question = request.form.get('question') or request.json.get('question')
        if not question:
            return jsonify({'error': 'Question required'}), 400
        
        try:
            chat_service = get_chat_service()
            answer = chat_service.ask_question(lecture_id, user.id, question)
            return jsonify({'answer': answer})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # GET request - show chat page
    chat_service = get_chat_service()
    chat_history = chat_service.get_chat_history(lecture_id)
    return render_template('chat.html', lecture=lecture, job=job, chat_history=chat_history)

@app.route('/api/lectures/<int:lecture_id>/chat', methods=['POST'])
@login_required
def api_chat(lecture_id):
    """API endpoint for chat"""
    user = get_current_user()
    lecture = Lecture.query.get_or_404(lecture_id)
    job = lecture.job
    
    if job.user_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question required'}), 400
    
    try:
        chat_service = get_chat_service()
        answer = chat_service.ask_question(lecture_id, user.id, question)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
