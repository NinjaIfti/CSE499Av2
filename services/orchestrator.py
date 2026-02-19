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
        self.ocr_url = current_app.config['OCR_SERVICE_URL']
        self.whisper_url = current_app.config['WHISPER_SERVICE_URL']
        self.llm_url = current_app.config['LLM_SERVICE_URL']
        self.timeout = current_app.config['SERVICE_TIMEOUT']
        self.poll_interval = current_app.config['POLL_INTERVAL']
        self.max_poll_attempts = current_app.config['MAX_POLL_ATTEMPTS']
    
    def _make_request(self, url, method='GET', data=None, files=None):
        """Make HTTP request to external service"""
        try:
            if method == 'GET':
                response = requests.get(url, timeout=self.timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, timeout=self.timeout)
                else:
                    response = requests.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.Timeout:
            raise Exception(f"Service timeout: {url}")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Service unavailable: {url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error from {url}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling {url}: {str(e)}")
    
    def _get_job_storage_path(self, job_id):
        """Get storage path for a job"""
        storage_base = current_app.config['UPLOAD_FOLDER']
        return os.path.join(storage_base, f'job_{job_id}')
    
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
            
            with open(video_full_path, 'rb') as video_file:
                files = {'video': video_file}
                data = {'job_id': str(job_id)}
                
                ocr_endpoint = f"{self.ocr_url}/process"
                result = self._make_request(ocr_endpoint, method='POST', data=data, files=files)
                
                ocr_output_path = os.path.join(storage_path, 'ocr_output.json')
                with open(ocr_output_path, 'w') as f:
                    json.dump(result, f, indent=2)
                
                job.ocr_status = 'done'
                db.session.commit()
                return result
        except Exception as e:
            job.ocr_status = 'failed'
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
            
            with open(video_full_path, 'rb') as video_file:
                files = {'video': video_file}
                data = {'job_id': str(job_id)}
                
                whisper_endpoint = f"{self.whisper_url}/transcribe"
                result = self._make_request(whisper_endpoint, method='POST', data=data, files=files)
                
                transcript_path = os.path.join(storage_path, 'transcript.json')
                with open(transcript_path, 'w') as f:
                    json.dump(result, f, indent=2)
                
                job.whisper_status = 'done'
                db.session.commit()
                return result
        except Exception as e:
            job.whisper_status = 'failed'
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
            db.session.commit()
            
            return result
        except Exception as e:
            job.llm_status = 'failed'
            job.final_status = 'failed'
            db.session.commit()
            raise Exception(f"LLM processing failed: {str(e)}")
    
    def process_job(self, job_id):
        """Main orchestration method: process a job through all stages"""
        job = Job.query.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        storage_path = self._ensure_storage_directory(job_id)
        video_path = os.path.join(storage_path, 'video.mp4')
        
        try:
            # Step 1: Start OCR and Whisper in parallel
            import threading
            
            ocr_error = None
            whisper_error = None
            
            def run_ocr():
                nonlocal ocr_error
                try:
                    self.start_ocr_processing(job_id, video_path)
                except Exception as e:
                    ocr_error = e
            
            def run_whisper():
                nonlocal whisper_error
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
                if job.ocr_status == 'done' and job.whisper_status == 'done':
                    break
                if job.ocr_status == 'failed' or job.whisper_status == 'failed':
                    raise Exception("OCR or Whisper processing failed")
                time.sleep(self.poll_interval)
                attempts += 1
            
            if attempts >= self.max_poll_attempts:
                raise Exception("Timeout waiting for OCR/Whisper to complete")
            
            # Step 3: Trigger LLM processing
            self.start_llm_processing(job_id)
            
            return True
        except Exception as e:
            job = Job.query.get(job_id)
            job.final_status = 'failed'
            db.session.commit()
            raise Exception(f"Job processing failed: {str(e)}")
