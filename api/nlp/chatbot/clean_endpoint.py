"""
Clean Endpoint Example using Answer Coordinator

This shows how to use core/answer.py in your endpoints with clean design.
Focus on the pattern, not the linter issues.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import uuid
from pathlib import Path

from core.answer import get_answer_coordinator
from shared.log.logger import Logger

logger = Logger.get_logger()
router = APIRouter()

# Get the answer coordinator instance
answer_coordinator = get_answer_coordinator()

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/soap_notes")
async def generate_soap_notes(
    audio_file: UploadFile = File(...),
    template_type: str = Form("general"),
    patient_name: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None)
):
    """
    Generate SOAP notes from audio file.
    
    This shows the clean pattern:
    1. Handle file upload
    2. Use Answer coordinator
    3. Clean up and return
    """
    try:
        # Save uploaded file
        file_path = await save_uploaded_file(audio_file)
        
        # Prepare patient context
        patient_context = {}
        if patient_name:
            patient_context["patient_name"] = patient_name
        
        # Use Answer coordinator - this is the key part!
        response = await answer_coordinator.process_soap_notes(
            audio_file_path=str(file_path),
            template_type=template_type,
            patient_context=patient_context if patient_context else None,
            user_id=user_id
        )
        
        # Clean up file
        cleanup_file(file_path)
        
        # Return clean response
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value,
            "error": response.error
        }
        
    except Exception as e:
        logger.exception(f"Error in SOAP notes endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcription")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    recording_type: str = Form("clinical"),
    use_sarvam: bool = Form(False),
    user_id: Optional[str] = Form(None)
):
    """
    Transcribe audio file using Answer coordinator.
    """
    try:
        # Save uploaded file
        file_path = await save_uploaded_file(audio_file)
        
        # Use Answer coordinator
        response = await answer_coordinator.process_transcription(
            audio_file_path=str(file_path),
            recording_type=recording_type,
            use_sarvam=use_sarvam,
            user_id=user_id
        )
        
        # Clean up file
        cleanup_file(file_path)
        
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value
        }
        
    except Exception as e:
        logger.exception(f"Error in transcription endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/medical-chat")
async def medical_chat(
    query: str = Form(...),
    table_name: str = Form("medical_ai_deeparogyai_v1"),
    user_id: Optional[str] = Form(None)
):
    """
    Medical chat endpoint using Answer coordinator.
    """
    try:
        # Use Answer coordinator
        response = await answer_coordinator.process_medical_chat(
            query=query,
            table_name=table_name,
            user_id=user_id
        )
        
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value
        }
        
    except Exception as e:
        logger.exception(f"Error in medical chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prescription-extraction")
async def extract_prescription(
    document_file: UploadFile = File(...),
    user_id: Optional[str] = Form(None)
):
    """
    Extract prescription from document using Answer coordinator.
    """
    try:
        # Save uploaded file
        file_path = await save_uploaded_file(document_file)
        
        # Use Answer coordinator
        response = await answer_coordinator.process_by_service_type(
            service_type="prescription_extraction",
            file_path=str(file_path),
            user_id=user_id
        )
        
        # Clean up file
        cleanup_file(file_path)
        
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value
        }
        
    except Exception as e:
        logger.exception(f"Error in prescription extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document-summary")
async def summarize_document(
    document_file: UploadFile = File(...),
    summary_type: str = Form("clinical_notes"),
    user_id: Optional[str] = Form(None)
):
    """
    Generate document summary using Answer coordinator.
    """
    try:
        # Save uploaded file
        file_path = await save_uploaded_file(document_file)
        
        # Use Answer coordinator
        response = await answer_coordinator.process_by_service_type(
            service_type="document_summary",
            file_path=str(file_path),
            summary_type=summary_type,
            user_id=user_id
        )
        
        # Clean up file
        cleanup_file(file_path)
        
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value
        }
        
    except Exception as e:
        logger.exception(f"Error in document summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf-chat")
async def pdf_chat(
    user_id: str = Form(...),
    query: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    PDF chat endpoint using Answer coordinator.
    """
    try:
        file_path = None
        if file:
            file_path = await save_uploaded_file(file)
        
        # Use Answer coordinator
        response = await answer_coordinator.process_pdf_chat(
            user_id=user_id,
            query=query,
            session_id=session_id,
            file_path=str(file_path) if file_path else None
        )
        
        # Clean up file if uploaded
        if file_path:
            cleanup_file(file_path)
        
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value
        }
        
    except Exception as e:
        logger.exception(f"Error in PDF chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lab-extract")
async def extract_lab_report(
    document_file: UploadFile = File(...),
    user_id: Optional[str] = Form(None)
):
    """
    Extract lab report using Answer coordinator.
    """
    try:
        # Save uploaded file
        file_path = await save_uploaded_file(document_file)
        
        # Use Answer coordinator
        response = await answer_coordinator.process_lab_extract(
            file_path=str(file_path),
            user_id=user_id
        )
        
        # Clean up file
        cleanup_file(file_path)
        
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value
        }
        
    except Exception as e:
        logger.exception(f"Error in lab extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text-processing")
async def process_text(
    raw_text: str = Form(...),
    processing_type: str = Form("clinical_notes_cleanup"),
    patient_name: Optional[str] = Form(None),
    target_language: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None)
):
    """
    Process text using Answer coordinator.
    """
    try:
        # Use Answer coordinator
        response = await answer_coordinator.process_text_processing(
            raw_text=raw_text,
            processing_type=processing_type,
            patient_name=patient_name,
            target_language=target_language,
            user_id=user_id
        )
        
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value
        }
        
    except Exception as e:
        logger.exception(f"Error in text processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-document-summary")
async def summarize_multiple_documents(
    document_files: list[UploadFile] = File(...),
    summary_type: str = Form("clinical_notes"),
    user_id: Optional[str] = Form(None)
):
    """
    Generate multi-document summary using Answer coordinator.
    """
    try:
        # Save uploaded files
        file_paths = []
        for file in document_files:
            file_path = await save_uploaded_file(file)
            file_paths.append(str(file_path))
        
        # Use Answer coordinator
        response = await answer_coordinator.process_multi_document_summary(
            file_paths=file_paths,
            summary_type=summary_type,
            user_id=user_id
        )
        
        # Clean up files
        for file_path in file_paths:
            cleanup_file(Path(file_path))
        
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value
        }
        
    except Exception as e:
        logger.exception(f"Error in multi-document summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deep-audio-notes")
async def deep_audio_notes(
    audio_file: UploadFile = File(...),
    recording_type: str = Form("clinical"),
    use_sarvam: bool = Form(True),
    user_id: Optional[str] = Form(None)
):
    """
    Generate deep audio notes using Answer coordinator.
    """
    try:
        # Save uploaded file
        file_path = await save_uploaded_file(audio_file)
        
        # Use Answer coordinator
        response = await answer_coordinator.process_deep_audio_notes(
            audio_file_path=str(file_path),
            recording_type=recording_type,
            use_sarvam=use_sarvam,
            user_id=user_id
        )
        
        # Clean up file
        cleanup_file(file_path)
        
        return {
            "success": response.success,
            "data": response.data,
            "processing_time": response.processing_time,
            "transaction_id": response.request.transaction_id,
            "service_type": response.service_type.value
        }
        
    except Exception as e:
        logger.exception(f"Error in deep audio notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_service_stats():
    """
    Get processing statistics from Answer coordinator.
    """
    try:
        stats = answer_coordinator.get_stats()
        return stats
        
    except Exception as e:
        logger.exception(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
async def save_uploaded_file(upload_file: UploadFile) -> Path:
    """Save uploaded file and return path"""
    file_extension = Path(upload_file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    with open(file_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)
    
    logger.info(f"Saved uploaded file: {file_path}")
    return file_path


def cleanup_file(file_path: Path):
    """Clean up temporary file"""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}") 