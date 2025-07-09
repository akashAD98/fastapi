from fastapi import APIRouter
from api.nlp.transcribe.audio import router as audio_router

router = APIRouter()
router.include_router(audio_router, prefix="/audio", tags=["Audio Services"]) 