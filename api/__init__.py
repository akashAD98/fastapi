from api.nlp import nlp_router
from fastapi import APIRouter

# all nlp/text routes
api_router = APIRouter()
api_router.include_router(nlp_router)
