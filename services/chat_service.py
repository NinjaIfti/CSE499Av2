import os
import json
import requests
from flask import current_app
from models import db, Chat, Lecture

class ChatService:
    """Handles chat interactions with LLM service"""
    
    def __init__(self):
        self.llm_url = current_app.config['LLM_SERVICE_URL']
        self.timeout = current_app.config['CHAT_TIMEOUT']
    
    def _make_request(self, url, data):
        """Make HTTP request to LLM service"""
        try:
            response = requests.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise Exception("Chat service timeout")
        except requests.exceptions.ConnectionError:
            raise Exception("Chat service unavailable")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error from chat service: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling chat service: {str(e)}")
    
    def _load_lecture_context(self, lecture_id):
        """Load lecture notes and transcript for context"""
        lecture = Lecture.query.get(lecture_id)
        if not lecture:
            raise ValueError(f"Lecture {lecture_id} not found")
        
        context = {
            'summary': lecture.summary or '',
            'notes': None,
            'transcript': None
        }
        
        if lecture.notes_path and os.path.exists(lecture.notes_path):
            with open(lecture.notes_path, 'r') as f:
                context['notes'] = json.load(f)
        
        if lecture.transcript_path and os.path.exists(lecture.transcript_path):
            with open(lecture.transcript_path, 'r') as f:
                context['transcript'] = json.load(f)
        
        return context
    
    def _get_conversation_history(self, lecture_id, limit=10):
        """Get recent conversation history for context"""
        chats = Chat.query.filter_by(lecture_id=lecture_id)\
            .order_by(Chat.created_at.desc())\
            .limit(limit)\
            .all()
        
        history = []
        for chat in reversed(chats):
            history.append({
                'question': chat.question,
                'answer': chat.answer
            })
        
        return history
    
    def ask_question(self, lecture_id, user_id, question):
        """Process a user question and return answer"""
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        try:
            context = self._load_lecture_context(lecture_id)
            history = self._get_conversation_history(lecture_id)
            
            chat_payload = {
                'lecture_id': str(lecture_id),
                'question': question,
                'context': context,
                'history': history
            }
            
            chat_endpoint = f"{self.llm_url}/chat"
            result = self._make_request(chat_endpoint, chat_payload)
            
            answer = result.get('answer', 'Sorry, I could not generate a response.')
            
            chat = Chat(
                lecture_id=lecture_id,
                user_id=user_id,
                question=question,
                answer=answer
            )
            db.session.add(chat)
            db.session.commit()
            
            return answer
        except Exception as e:
            raise Exception(f"Failed to process question: {str(e)}")
    
    def get_chat_history(self, lecture_id, limit=50):
        """Get chat history for a lecture"""
        chats = Chat.query.filter_by(lecture_id=lecture_id)\
            .order_by(Chat.created_at.asc())\
            .limit(limit)\
            .all()
        
        return [chat.to_dict() for chat in chats]
