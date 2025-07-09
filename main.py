import uvicorn
from api import api_router
# from api.nlp.chatbot.gateway import router as gateway_router
from fastapi import APIRouter, FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from utils.rate_limiter import rate_limit_middleware
import os

# Database imports
from core.database import init_database

# Apply nest_asyncio for nested event loops
import nest_asyncio
nest_asyncio.apply()

from shared.log.logger import Logger
# Import the transcription service for preloading

logger = Logger.get_logger()

## Server inits
logger.info("initializing server...")

root_router = APIRouter()
app = FastAPI(
       title="Deep Chatbot Service API",
       openapi_url="/deep-chatbot-service/openapi.json",
       docs_url="/deep-chatbot-service/docs",
       redoc_url="/deep-chatbot-service/redoc",
       debug=True,
       openapi_tags=[
           {"name": "Audio Services", "description": "Audio transcription and SOAP clinical notes generation"}
       ]
   )

# Production database initialization on startup
@app.on_event("startup")
async def startup_event():
    """Initialize production database on startup"""
    try:
        logger.info("🚀 Starting AI SOAP Production Service...")
        success = init_database()
        if not success:
            logger.error("❌ Database initialization failed - service may not work properly")
        else:
            logger.info("✅ Production database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Critical startup error: {str(e)}")
        # Don't raise - let the service start even if DB fails
        logger.warning("⚠️ Service starting with limited functionality")

# Add rate limiter middleware
app.middleware("http")(rate_limit_middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with actual origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the UI
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/deep-chatbot-service/static", StaticFiles(directory=static_dir), name="static")

# Also mount static files at root for direct access
app.mount("/static", StaticFiles(directory=static_dir), name="root_static")


# Add root path handler
@app.get("/", status_code=200, include_in_schema=False)
def root():
    logger.info('Redirecting from root to "/deep-chatbot-service/static/index_summary.html"')
    return RedirectResponse("/deep-chatbot-service/static/index_summary.html")

@root_router.get("/deep-chatbot-service", status_code=200, include_in_schema=False)
def landing_page():
    logger.info('Redirecting response to "/deep-chatbot-service/static/index_summary.html"')
    return RedirectResponse("/deep-chatbot-service/static/index_summary.html")


############ simpler pdf upload ui 
# PDF summary upload UI route
@root_router.get("/deep-chatbot-service/pdf-upload", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def pdf_upload_page():
    logger.info('Serving PDF upload UI')
    try:
        with open(os.path.join(static_dir, "pdf-chatbot-upload.html"), "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving PDF upload UI: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# Add direct route at root level for PDF upload
@root_router.get("/pdf-upload", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def pdf_upload_page_root():
    return pdf_upload_page()


# Audio Transcription UI route
@root_router.get("/deep-chatbot-service/audio-transcription", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def audio_transcription_page():
    logger.info('Serving Audio Transcription UI')
    try:
        with open(os.path.join(static_dir, "audio-transcription.html"), "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving Audio Transcription UI: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# Add direct route at root level for Audio Transcription
@root_router.get("/audio-transcription", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def audio_transcription_page_root():
    return audio_transcription_page()

# Deepaarogya Audio Transcription UI route
@root_router.get("/deep-chatbot-service/deepaarogya-audio-transcription", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def deepaarogya_audio_transcription_page():
    logger.info('Serving Deepaarogya Audio Transcription UI')
    try:
        with open(os.path.join(static_dir, "deepaarogya-audio-transcription.html"), "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving Deepaarogya Audio Transcription UI: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# Add direct route at root level for Deepaarogya Audio Transcription
@root_router.get("/deepaarogya-audio-transcription", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def deepaarogya_audio_transcription_page_root():
    return deepaarogya_audio_transcription_page()

# # Deep Audio Notes UI route
# @root_router.get("/deep-chatbot-service/deep-audio-notes", status_code=200, include_in_schema=False, response_class=HTMLResponse)
# def deep_audio_notes_page():
#     logger.info('Serving Deep Audio Notes UI')
#     try:
#         with open(os.path.join(static_dir, "deep-audio-notes.html"), "r") as f:
#             html_content = f.read()
#         return HTMLResponse(content=html_content)
#     except Exception as e:
#         logger.error(f"Error serving Deep Audio Notes UI: {str(e)}")
#         return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# # Add direct route at root level for Deep Audio Notes
# @root_router.get("/deep-audio-notes", status_code=200, include_in_schema=False, response_class=HTMLResponse)
# def deep_audio_notes_page_root():
#     return deep_audio_notes_page()


@root_router.get("/deep-chatbot-service/deepaarogya-audio-transcription", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def deep_audio_notes_page():
    logger.info('Serving Deep Audio Notes UI')
    try:
        with open(os.path.join(static_dir, "deepaarogya-audio-transcription.html"), "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving Deep Audio Notes UI: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# Add direct route at root level for Deep Audio Notes
@root_router.get("/deepaarogya-audio-transcription", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def deep_audio_notes_page_root():
    return deep_audio_notes_page()


# Keep the old Sarvam route for backward compatibility (redirects to new route)
@root_router.get("/deep-chatbot-service/sarvam-audio-transcription", status_code=200, include_in_schema=False)
def sarvam_audio_transcription_page_redirect():
    logger.info('Redirecting from old sarvam route to new deep-audio-notes route')
    return RedirectResponse("/deep-chatbot-service/deep-audio-notes")

@root_router.get("/sarvam-audio-transcription", status_code=200, include_in_schema=False)
def sarvam_audio_transcription_page_root_redirect():
    return RedirectResponse("/deep-audio-notes")

# PDF Chat UI route
@root_router.get("/deep-chatbot-service/pdf-chat", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def pdf_chat_page():
    logger.info('Serving PDF Chat UI')
    try:
        with open(os.path.join(static_dir, "pdf-chat.html"), "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving PDF Chat UI: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# Add direct route at root level for PDF Chat
@root_router.get("/pdf-chat", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def pdf_chat_page_root():
    return pdf_chat_page()

# PDF Chat UI route
@root_router.get("/deep-chatbot-service/rag-pdf-chat", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def rag_pdf_chat_page():
    logger.info('Serving RAG PDF Chat UI')
    try:
        with open(os.path.join(static_dir, "rag-pdf-chat.html"), "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving RAG PDF Chat UI: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# Add direct route at root level for RAG PDF Chat
@root_router.get("/rag-pdf-chat", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def rag_pdf_chat_page_root():
    return rag_pdf_chat_page()

# AI SOAP Notes UI route
@root_router.get("/deep-chatbot-service/ai-soap", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def ai_soap_page():
    logger.info('Serving AI SOAP Notes UI')
    try:
        with open(os.path.join(static_dir, "ai-soap.html"), "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving AI SOAP UI: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>AI SOAP interface not found. {str(e)}</p></body></html>")

# Add direct route at root level for AI SOAP
@root_router.get("/ai-soap", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def ai_soap_page_root():
    return ai_soap_page()

# SOAP Audio Recorder UI route
@root_router.get("/deep-chatbot-service/soap-audio-recorder", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def soap_audio_recorder_page():
    logger.info('Serving SOAP Audio Recorder UI')
    try:
        with open(os.path.join(static_dir, "soap-audio-recorder.html"), "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving SOAP Audio Recorder UI: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>SOAP Audio Recorder interface not found. {str(e)}</p></body></html>")

# Add direct route at root level for SOAP Audio Recorder
@root_router.get("/soap-audio-recorder", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def soap_audio_recorder_page_root():
    return soap_audio_recorder_page()

# Add this to Deep-Chatbot-service/app/main.py
@app.get("/test-endpoint", tags=["Test"])
def test_endpoint():
    return {"message": "This is a test endpoint"}

@app.get("/health")
def health_check():
    """Health check endpoint for load balancer."""
    return {"status": "healthy"}

@root_router.get("/deep-chatbot-service/lab-extract", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def lab_extract_page():
    logger.info('Serving Lab Extract UI')
    try:
        with open(os.path.join(static_dir, "deep-lab-extractor.html"), "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving Lab Extract UI: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# Add direct route at root level for Lab Extract
@root_router.get("/lab-extract", status_code=200, include_in_schema=False, response_class=HTMLResponse)
def lab_extract_page_root():
    return lab_extract_page()

app.include_router(api_router)
# app.include_router(gateway_router, prefix="/deep-chatbot-service/gateway", tags=["Gateway"])
app.include_router(root_router)

if __name__ == "__main__":
    # Use this for debugging purposes only
    uvicorn.run("main:app", host="0.0.0.0", port=8087, log_level="debug", reload=True)


## new 
#http://localhost:8087/deep-chatbot-service/docs
#http://localhost:8087/deep-chatbot-service/static/index.html
#http://localhost:8087/deep-chatbot-service/static/index_summary.html
#http://localhost:8087/deep-chatbot-service/static/audio-transcription.html