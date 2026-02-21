import os
import json
import time
import requests
from datetime import datetime
from flask import current_app
from models import db, Job, Lecture

class OrchestratorService:
    """Orchestrates processing across OCR, Whisper, and LLM services"""
    
    def __init__(self):
        def _strip_trailing_slash(url):
            return url.rstrip('/') if url else url
        self.ocr_url = _strip_trailing_slash(current_app.config['OCR_SERVICE_URL'])
        self.whisper_url = _strip_trailing_slash(current_app.config['WHISPER_SERVICE_URL'])
        self.llm_url = _strip_trailing_slash(current_app.config['LLM_SERVICE_URL'])
        self.timeout = current_app.config['SERVICE_TIMEOUT']
        self.poll_interval = current_app.config['POLL_INTERVAL']
        self.max_poll_attempts = current_app.config['MAX_POLL_ATTEMPTS']
        self.upload_folder = current_app.config['UPLOAD_FOLDER']
    
    def _make_request(self, url, method='GET', data=None, files=None):
        """Make HTTP request to external service"""
        try:
            if method == 'GET':
                response = requests.get(url, timeout=self.timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, timeout=self.timeout)
                else:
                    response = requests.post(url, json=data, timeout=(30, self.timeout))
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.Timeout:
            raise Exception(f"Service timeout (response took too long): {url}")
        except requests.exceptions.SSLError as e:
            raise Exception(
                f"SSL error talking to {url}. "
                "Ensure the Colab notebook and ngrok tunnel are running; try again in a moment."
            )
        except requests.exceptions.ConnectionError as e:
            err = str(e).lower()
            if "timed out" in err or "timeout" in err:
                raise Exception(
                    f"Upload timed out while sending video to {url}. "
                    "Try a smaller video or increase SERVICE_TIMEOUT in .env (e.g. 1200 for 20 min)."
                )
            raise Exception(
                f"Connection failed to {url}. "
                "Check that the service (Colab + ngrok) is running and the URL in .env is correct."
            )
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error from {url}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling {url}: {str(e)}")
    
    def _post_with_files_retry(self, url, data, video_path, max_attempts=1):
        """POST with file upload. No retries so we never send the video twice (avoids OCR/Whisper running twice)."""
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                with open(video_path, 'rb') as video_file:
                    files = {'video': video_file}
                    response = requests.post(url, data=data, files=files, timeout=self.timeout)
                response.raise_for_status()
                return response.json() if response.content else {}
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                last_error = e
                if attempt < max_attempts:
                    time.sleep(5)
                    continue
                if isinstance(e, requests.exceptions.SSLError):
                    raise Exception(
                        f"SSL error talking to {url}. "
                        "Ensure the Colab notebook and ngrok tunnel are running; try again later."
                    )
                err = str(e).lower()
                if "timed out" in err or "timeout" in err:
                    raise Exception(
                        f"Upload timed out while sending video to {url}. "
                        "Try a smaller video or increase SERVICE_TIMEOUT in .env."
                    )
                raise Exception(
                    f"Connection failed to {url}. "
                    "Check that the service (Colab + ngrok) is running and the URL in .env is correct."
                )
            except requests.exceptions.Timeout:
                raise Exception(f"Service timeout (response took too long): {url}")
            except requests.exceptions.HTTPError as e:
                raise Exception(f"HTTP error from {url}: {str(e)}")
        raise last_error or Exception(f"Error calling {url}")
    
    def _get_job_storage_path(self, job_id):
        """Get storage path for a job"""
        return os.path.join(self.upload_folder, f'job_{job_id}')
    
    def _ensure_storage_directory(self, job_id):
        """Ensure storage directory exists for a job"""
        storage_path = self._get_job_storage_path(job_id)
        os.makedirs(storage_path, exist_ok=True)
        return storage_path
    
    def start_ocr_processing(self, job_id, video_path):
        """Start OCR processing for a video"""
        job = Job.query.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        try:
            job.ocr_status = 'running'
            db.session.commit()
            
            storage_path = self._get_job_storage_path(job_id)
            video_full_path = os.path.join(storage_path, 'video.mp4')
            
            data = {'job_id': str(job_id)}
            ocr_endpoint = f"{self.ocr_url}/process"
            result = self._post_with_files_retry(ocr_endpoint, data, video_full_path)
            
            ocr_output_path = os.path.join(storage_path, 'ocr_output.json')
            with open(ocr_output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            job.ocr_status = 'done'
            job.status_message = None
            db.session.commit()
            return result
        except Exception as e:
            job.ocr_status = 'failed'
            job.status_message = f"OCR: {str(e)}"
            db.session.commit()
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def start_whisper_processing(self, job_id, video_path):
        """Start Whisper processing for a video"""
        job = Job.query.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        try:
            job.whisper_status = 'running'
            db.session.commit()
            
            storage_path = self._get_job_storage_path(job_id)
            video_full_path = os.path.join(storage_path, 'video.mp4')
            
            data = {'job_id': str(job_id)}
            whisper_endpoint = f"{self.whisper_url}/transcribe"
            result = self._post_with_files_retry(whisper_endpoint, data, video_full_path)
            
            transcript_path = os.path.join(storage_path, 'transcript.json')
            with open(transcript_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            job.whisper_status = 'done'
            job.status_message = None
            db.session.commit()
            return result
        except Exception as e:
            job.whisper_status = 'failed'
            job.status_message = f"Whisper: {str(e)}"
            db.session.commit()
            raise Exception(f"Whisper processing failed: {str(e)}")
    
    def start_llm_processing(self, job_id):
        """Start LLM processing after OCR and Whisper complete"""
        job = Job.query.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.ocr_status != 'done' or job.whisper_status != 'done':
            raise ValueError("OCR and Whisper must be completed before LLM processing")
        
        try:
            job.llm_status = 'running'
            db.session.commit()
            
            storage_path = self._get_job_storage_path(job_id)
            ocr_path = os.path.join(storage_path, 'ocr_output.json')
            transcript_path = os.path.join(storage_path, 'transcript.json')
            
            with open(ocr_path, 'r') as f:
                ocr_data = json.load(f)
            with open(transcript_path, 'r') as f:
                transcript_data = json.load(f)
            
            llm_payload = {
                'job_id': str(job_id),
                'ocr_output': ocr_data,
                'transcript': transcript_data
            }
            
            llm_endpoint = f"{self.llm_url}/process"
            result = self._make_request(llm_endpoint, method='POST', data=llm_payload)
            
            final_notes_path = os.path.join(storage_path, 'final_notes.json')
            with open(final_notes_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            lecture = Lecture.query.filter_by(job_id=job_id).first()
            if not lecture:
                lecture = Lecture(job_id=job_id)
                db.session.add(lecture)
            
            lecture.summary = result.get('summary', '')
            lecture.notes_path = final_notes_path
            lecture.transcript_path = transcript_path
            
            job.llm_status = 'done'
            job.final_status = 'done'
            job.status_message = None
            db.session.commit()
            
            return result
        except Exception as e:
            job.llm_status = 'failed'
            job.final_status = 'failed'
            job.status_message = f"LLM: {str(e)}"
            db.session.commit()
            raise Exception(f"LLM processing failed: {str(e)}")
    
    def process_job(self, job_id, flask_app=None):
        """Main orchestration method: process a job through all stages.
        flask_app: pass the Flask app instance so worker threads can use app.app_context().
        """
        job = Job.query.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.final_status == 'cancelled':
            return False
        
        storage_path = self._ensure_storage_directory(job_id)
        video_path = os.path.join(storage_path, 'video.mp4')
        
        app = flask_app or current_app._get_current_object()
        
        try:
            # Step 1: Start OCR and Whisper in parallel (each thread needs its own app context)
            import threading
            
            ocr_error = None
            whisper_error = None
            
            def run_ocr():
                nonlocal ocr_error
                with app.app_context():
                    try:
                        self.start_ocr_processing(job_id, video_path)
                    except Exception as e:
                        ocr_error = e
            
            def run_whisper():
                nonlocal whisper_error
                with app.app_context():
                    try:
                        self.start_whisper_processing(job_id, video_path)
                    except Exception as e:
                        whisper_error = e
            
            ocr_thread = threading.Thread(target=run_ocr)
            whisper_thread = threading.Thread(target=run_whisper)
            
            ocr_thread.start()
            whisper_thread.start()
            
            ocr_thread.join()
            whisper_thread.join()
            
            if ocr_error:
                raise ocr_error
            if whisper_error:
                raise whisper_error
            
            # Step 2: Wait for both to complete, then trigger LLM
            attempts = 0
            while attempts < self.max_poll_attempts:
                job = Job.query.get(job_id)
                if job.final_status == 'cancelled':
                    return False
                if job.ocr_status == 'done' and job.whisper_status == 'done':
                    break
                if job.ocr_status == 'failed' or job.whisper_status == 'failed':
                    raise Exception("OCR or Whisper processing failed")
                time.sleep(self.poll_interval)
                attempts += 1
            
            if attempts >= self.max_poll_attempts:
                raise Exception("Timeout waiting for OCR/Whisper to complete")
            
            job = Job.query.get(job_id)
            if job.final_status == 'cancelled':
                return False
            
            # Step 3: Trigger LLM processing
            self.start_llm_processing(job_id)
            
            return True
        except Exception as e:
            job = Job.query.get(job_id)
            if job.final_status != 'cancelled':
                job.final_status = 'failed'
                if not job.status_message:
                    job.status_message = str(e)
                if job.ocr_status in ('pending', 'running'):
                    job.ocr_status = 'failed'
                if job.whisper_status in ('pending', 'running'):
                    job.whisper_status = 'failed'
                if job.llm_status in ('pending', 'running'):
                    job.llm_status = 'failed'
                db.session.commit()
            raise Exception(f"Job processing failed: {str(e)}")
