from api.nlp.chatbot import router as chatbot_router
from api.nlp.transcribe import router as transcribe_router
from fastapi import APIRouter

# Main NLP API Router - Clean and Organized
nlp_router = APIRouter(prefix="/nlp/v1")

# Chatbot Services (Document Summary, Medical AI, PDF Q&A)
nlp_router.include_router(chatbot_router, prefix="/chatbot")

# Audio Services (SOAP Notes, Transcription, Speech Processing)
nlp_router.include_router(transcribe_router, prefix="/transcribe")
