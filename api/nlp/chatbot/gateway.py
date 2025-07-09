"""
API Gateway Endpoint

This provides a unified entry point for all services while maintaining
backward compatibility with existing endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Dict, Any, Optional

from schemas.chatbot_schema import ChatbotInput, ChatbotOutput, ChatpdfResponse
from schemas.transcription_schema import EnhancedTranscriptionResponse
from schemas.patient_schema import AISOAPTranscriptionResponse
from schemas.text_processing_schema import (
    TextProcessingRequest, 
    TextProcessingResponse
)
from schemas.summary_schema import SummaryType
from services.api_gateway import get_api_gateway, APIGateway
from shared.auth.auth_bearer import JWTBearer

router = APIRouter()


@router.post(
    "/medical-chat", 
    response_model=ChatbotOutput,
    dependencies=[Depends(JWTBearer())]
)
async def medical_chat_gateway(
    input_data: ChatbotInput,
    gateway: APIGateway = Depends(get_api_gateway)
) -> ChatbotOutput:
    """
    Unified medical chat endpoint through API Gateway.
    
    This endpoint provides the same functionality as the existing /chat 
    endpoint but routes through the API Gateway for centralized logging and 
    monitoring.
    
    Args:
        input_data: The chatbot input data
        gateway: The API Gateway instance
        
    Returns:
        ChatbotOutput: The chatbot response
    """
    try:
        return await gateway.route_medical_chat(input_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error: {str(e)}"
        )


@router.post(
    "/pdf-chat",
    response_model=ChatpdfResponse,
    dependencies=[Depends(JWTBearer())]
)
async def pdf_chat_gateway(
    user_id: str = Form(..., description="User ID for session tracking"),
    query: Optional[str] = Form(
        None, description="Question to ask about the PDF"
    ),
    session_id: Optional[str] = Form(
        None, description="Session ID for existing conversations"
    ),
    file: Optional[UploadFile] = File(None, description="PDF file to upload"),
    gateway: APIGateway = Depends(get_api_gateway)
) -> ChatpdfResponse:
    """
    Unified PDF chat endpoint through API Gateway.
    
    This endpoint provides the same functionality as the existing PDF chat
    endpoint but routes through the API Gateway for centralized logging and
    monitoring.
    
    Args:
        user_id: User ID for session tracking
        query: Question to ask about the PDF
        session_id: Session ID for existing conversations
        file: PDF file to upload
        gateway: The API Gateway instance
        
    Returns:
        ChatpdfResponse: The PDF chat response
    """
    try:
        return await gateway.route_pdf_chat(
            user_id=user_id,
            query=query,
            session_id=session_id,
            file=file
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error: {str(e)}"
        )


@router.post(
    "/lab-extract",
    dependencies=[Depends(JWTBearer())]
)
async def lab_extract_gateway(
    file: UploadFile = File(..., description="PDF file containing lab report"),
    gateway: APIGateway = Depends(get_api_gateway)
) -> Dict[str, Any]:
    """
    Unified lab extraction endpoint through API Gateway.
    
    This endpoint provides the same functionality as the existing lab extract
    endpoint but routes through the API Gateway for centralized logging and
    monitoring.
    
    Args:
        file: PDF file containing lab report
        gateway: The API Gateway instance
        
    Returns:
        Dict containing extracted lab report data
    """
    try:
        return await gateway.route_lab_extract(file)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error: {str(e)}"
        )


@router.post(
    "/audio-transcription",
    response_model=EnhancedTranscriptionResponse,
    dependencies=[Depends(JWTBearer())]
)
async def audio_transcription_gateway(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    recording_type: Optional[str] = Form("clinical", description="Recording type"),
    gateway: APIGateway = Depends(get_api_gateway)
) -> EnhancedTranscriptionResponse:
    """
    Unified audio transcription endpoint through API Gateway.
    
    This endpoint provides the same functionality as the existing audio
    transcription endpoint but routes through the API Gateway for centralized
    logging and monitoring.
    
    Args:
        audio: Audio file to transcribe
        recording_type: Type of recording (clinical or prescription)
        gateway: The API Gateway instance
        
    Returns:
        EnhancedTranscriptionResponse: The transcription response
    """
    try:
        return await gateway.route_audio_transcription(audio, recording_type)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error: {str(e)}"
        )


@router.post(
    "/deep-audio-notes",
    response_model=EnhancedTranscriptionResponse,
    dependencies=[Depends(JWTBearer())]
)
async def deep_audio_notes_gateway(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    recording_type: Optional[str] = Form("clinical", description="Recording type"),
    gateway: APIGateway = Depends(get_api_gateway)
) -> EnhancedTranscriptionResponse:
    """
    Unified deep audio notes endpoint through API Gateway.
    
    This endpoint provides the same functionality as the existing deep audio
    notes endpoint but routes through the API Gateway for centralized logging
    and monitoring.
    
    Args:
        audio: Audio file to transcribe
        recording_type: Type of recording (clinical or prescription)
        gateway: The API Gateway instance
        
    Returns:
        EnhancedTranscriptionResponse: The transcription response
    """
    try:
        return await gateway.route_deep_audio_notes(audio, recording_type)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error: {str(e)}"
        )


@router.post(
    "/soap-notes",
    response_model=AISOAPTranscriptionResponse,
    dependencies=[Depends(JWTBearer())]
)
async def soap_notes_gateway(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    template_type: str = Form("general", description="SOAP template type"),
    patient_name: Optional[str] = Form(None, description="Patient's full name"),
    visit_type: str = Form("Returning Patient", description="Type of visit"),
    pronouns: str = Form("Unknown", description="Patient pronouns"),
    note_length: str = Form("Standard", description="Note length preference"),
    past_context: Optional[str] = Form(None, description="Past medical history"),
    session_id: Optional[str] = Form(None, description="Session ID"),
    gateway: APIGateway = Depends(get_api_gateway)
) -> AISOAPTranscriptionResponse:
    """
    Unified SOAP notes endpoint through API Gateway.
    
    This endpoint provides the same functionality as the existing SOAP notes
    endpoint but routes through the API Gateway for centralized logging and
    monitoring.
    
    Args:
        audio: Audio file to transcribe
        template_type: SOAP template type
        patient_name: Patient's full name
        visit_type: Type of visit
        pronouns: Patient pronouns
        note_length: Note length preference
        past_context: Past medical history
        session_id: Session ID
        gateway: The API Gateway instance
        
    Returns:
        AISOAPTranscriptionResponse: The SOAP notes response
    """
    try:
        return await gateway.route_soap_notes(
            audio=audio,
            template_type=template_type,
            patient_name=patient_name,
            visit_type=visit_type,
            pronouns=pronouns,
            note_length=note_length,
            past_context=past_context,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error: {str(e)}"
        )


@router.post(
    "/process-text",
    response_model=TextProcessingResponse,
    dependencies=[Depends(JWTBearer())]
)
async def process_text_gateway(
    request: TextProcessingRequest,
    gateway: APIGateway = Depends(get_api_gateway)
) -> TextProcessingResponse:
    """
    Unified text processing endpoint through API Gateway.
    
    This endpoint provides the same functionality as the existing text
    processing endpoint but routes through the API Gateway for centralized
    logging and monitoring.
    
    Args:
        request: Text processing request
        gateway: The API Gateway instance
        
    Returns:
        TextProcessingResponse: The processed text response
    """
    try:
        return await gateway.route_process_text(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error: {str(e)}"
        )


@router.post(
    "/document-summary",
    dependencies=[Depends(JWTBearer())]
)
async def document_summary_gateway(
    file: UploadFile = File(..., description="PDF file to summarize"),
    type_of_summary: SummaryType = Form(SummaryType.CLINICAL_NOTES, description="Type of summary to generate"),
    user_id: Optional[str] = Form(None, description="User ID for tracking"),
    gateway: APIGateway = Depends(get_api_gateway)
) -> Dict[str, Any]:
    """
    Unified document summary endpoint through API Gateway.
    
    This endpoint provides the same functionality as the existing document
    summary endpoint but routes through the API Gateway for centralized
    logging and monitoring.
    
    Args:
        file: PDF file to summarize
        type_of_summary: Type of summary to generate
        user_id: User ID for tracking
        gateway: The API Gateway instance
        
    Returns:
        Dict containing the summary and metadata
    """
    try:
        return await gateway.route_document_summary(
            file=file,
            type_of_summary=type_of_summary,
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error: {str(e)}"
        )


@router.post(
    "/multiple-document-summary",
    dependencies=[Depends(JWTBearer())]
)
async def multi_document_summary_gateway(
    files: list[UploadFile] = File(..., description="PDF files to summarize"),
    type_of_summary: SummaryType = Form(SummaryType.CLINICAL_NOTES, description="Type of summary to generate"),
    user_id: Optional[str] = Form(None, description="User ID for tracking"),
    gateway: APIGateway = Depends(get_api_gateway)
) -> Dict[str, Any]:
    """
    Unified multi-document summary endpoint through API Gateway.
    
    This endpoint provides the same functionality as the existing multi-document
    summary endpoint but routes through the API Gateway for centralized
    logging and monitoring.
    
    Args:
        files: List of PDF files to summarize
        type_of_summary: Type of summary to generate
        user_id: User ID for tracking
        gateway: The API Gateway instance
        
    Returns:
        Dict containing the combined summary and metadata
    """
    try:
        return await gateway.route_multi_document_summary(
            files=files,
            type_of_summary=type_of_summary,
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gateway error: {str(e)}"
        )


@router.get("/health")
async def health_check(
    gateway: APIGateway = Depends(get_api_gateway)
) -> Dict[str, Any]:
    """
    Health check endpoint for the API Gateway.
    
    Returns:
        Dict containing health status and metrics
    """
    return gateway.get_health_status()


@router.get("/metrics")
async def get_metrics(
    gateway: APIGateway = Depends(get_api_gateway)
) -> Dict[str, Any]:
    """
    Get API Gateway metrics.
    
    Returns:
        Dict containing request metrics and statistics
    """
    return {
        "total_requests": gateway.request_count,
        "status": "operational",
        "services": {
            "medical_chat": "available",
            "pdf_chat": "available",
            "lab_extract": "available",
            "audio_transcription": "available",
            "deep_audio_notes": "available",
            "soap_notes": "available",
            "process_text": "available",
            "document_summary": "available",
            "multi_document_summary": "available"
        }
    } 