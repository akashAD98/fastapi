"""
NLP Chatbot API Endpoints

This module provides endpoints for various AI-powered document and conversation services:

1. **Summary Service**: Document processing and summarization
2. **Medical Chatbot**: Healthcare-focused conversational AI
3. **PDF Chat**: Interactive Q&A with PDF documents

## Key Features:
- Unified interface for document upload and querying
- Session-based conversation management
- Multi-format document support
- Healthcare-specific AI responses

## Usage:
- On first interaction: Send document + query + session_id + user_id
- Follow-up questions: Send only query + session_id + user_id (no file)
- Maintain same session_id for conversation continuity
"""

from fastapi import APIRouter
from api.nlp.chatbot import summary, chatbot, pdf_chat, gateway, clean_endpoint

router = APIRouter()

# Clean, organized router structure
router.include_router(summary.router, prefix="/summary", tags=["Document Summary"])
router.include_router(chatbot.router, prefix="/chatbot", tags=["Medical AI Chatbot"])
router.include_router(pdf_chat.router, prefix="/pdf-chat", tags=["PDF Q&A"])
router.include_router(gateway.router, prefix="/gateway", tags=["Gateway for all services"])
router.include_router(clean_endpoint.router, prefix="/clean", tags=["Clean API using Answer Coordinator"])
