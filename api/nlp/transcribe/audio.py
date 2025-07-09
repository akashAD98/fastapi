from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
import os
import tempfile
import time
from typing import Optional

from schemas.transcription_schema import EnhancedTranscriptionResponse, RawTranscription
from schemas.patient_schema import AISOAPTranscriptionResponse, PatientInfo
from shared.log.logger import Logger
from shared.auth.auth_bearer import JWTBearer
from core.database import get_db
from sqlalchemy.orm import Session

from chains.get_sarvam_transcribe_chain import SarvamTranscribeChain
# Import the proper SOAP chain from existing file
from chains.get_soap_chain import SOAP_Chain
from services.ai_soap_service import AISOAPService

from schemas.text_processing_schema import (
    TextProcessingRequest, 
    TextProcessingResponse, 
    TextProcessingType,
    AvailableProcessingTypesResponse,
    ProcessingTypeQuickReference,
    PROCESSING_TYPE_OPTIONS
)
from chains.get_content_modificaton_chain import ContentModificationChain
from promts.text_processing_selector import get_processing_type_info, get_context_suggestions

router = APIRouter()
logger = Logger.get_logger()

# Initialize chains
# transcribe_chain = TranscribeChain()

# =============================================================================
# SOAP NOTES ENDPOINTS - Clean and Professional
# =============================================================================

@router.post(
    "/soap_notes",
    response_model=AISOAPTranscriptionResponse,
    summary="Generate SOAP Notes from Audio",
    description="Upload audio file to generate professional SOAP clinical notes with multiple template options",
    tags=["Audio Services"],
    dependencies=[Depends(JWTBearer())]
)
async def create_soap_notes_from_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe (wav, mp3, m4a, etc.)"),
    template_type: str = Form(default="general", description="SOAP template: general, lite, combined_ap, detailed"),
    patient_name: Optional[str] = Form(None, description="Patient's full name"),
    visit_type: str = Form(default="Returning Patient", description="Type of visit"),
    pronouns: str = Form(default="Unknown", description="Patient pronouns (he/him, she/her, they/them)"),
    note_length: str = Form(default="Standard", description="Note length preference"),
    past_context: Optional[str] = Form(None, description="Past medical history or relevant context"),
    session_id: Optional[str] = Form(None, description="Existing session ID (optional)"),
    db: Session = Depends(get_db)
):
    """
    Generate professional SOAP clinical notes from audio recordings.
    Clean implementation using existing SOAP chain.
    """
    start_time = time.time()
    logger.info("=== SOAP NOTES GENERATION STARTED ===")
    logger.info(f"Request: template={template_type}, patient={patient_name}")
    
    try:
        # Validate inputs
        if not audio or not audio.filename:
            raise HTTPException(status_code=400, detail="No audio file provided")
        
        valid_templates = ["general", "lite", "combined_ap", "detailed"]
        if template_type not in valid_templates:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid template type. Choose from: {', '.join(valid_templates)}"
            )
        
        # Save audio temporarily
        contents = await audio.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        try:
            # Prepare patient context
            patient_context = {
                "patient_name": patient_name,
                "visit_type": visit_type,
                "pronouns": pronouns,
                "note_length": note_length,
                "past_context": past_context
            }
            
            # Use existing SOAP chain - clean and simple
            logger.info(f"🎯 Processing with SOAP template: {template_type}")
            soap_chain = SOAP_Chain()
            result = await soap_chain.get_answer(
                audio_file_path=temp_path,
                template_type=template_type,
                patient_context=patient_context
            )
            
            logger.info("✅ SOAP processing completed")
            
            # Check if we got an empty transcription
            if not result.get("raw_transcription"):
                return AISOAPTranscriptionResponse(
                    session_id=str(__import__('uuid').uuid4()),
                    note_id=str(__import__('uuid').uuid4()),
                    template_type=template_type,
                    patient_name=patient_name,
                    raw_transcription="",
                    clinical_note="No audio content detected. Please check audio quality or try recording again.",
                    patient_context=patient_context,
                    timestamp=result.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S")),
                    processing_time=time.time() - start_time
                )
            
            # Handle database operations with graceful fallback
            session_id_generated = session_id or str(__import__('uuid').uuid4())
            note_id_generated = str(__import__('uuid').uuid4())
            
            try:
                soap_service = AISOAPService(db)
                patient = soap_service.create_or_get_patient(
                    patient_name=patient_name or "Unknown Patient",
                    pronouns=pronouns
                )
                
                if session_id:
                    session = soap_service.get_session_by_id(session_id) or soap_service.create_session(
                        patient=patient, template_type=template_type, visit_type=visit_type,
                        note_length=note_length, past_context=past_context, session_id=session_id
                    )
                else:
                    session = soap_service.create_session(
                        patient=patient, template_type=template_type, visit_type=visit_type,
                        note_length=note_length, past_context=past_context
                    )
                
                session_id_generated = session.session_id
                logger.info(f"✅ Database operations successful - Session: {session_id_generated}")
                
            except Exception as db_error:
                logger.warning(f"Database unavailable: {str(db_error)}")
            
            # Structure response properly - just keep the raw text as string
            raw_transcription_data = result["raw_transcription"]
            
            response = AISOAPTranscriptionResponse(
                session_id=session_id_generated,
                note_id=note_id_generated,
                template_type=template_type,
                patient_name=patient_name,
                raw_transcription=raw_transcription_data,
                clinical_note=result["clinical_note"],
                patient_context=patient_context,
                timestamp=result["timestamp"],
                processing_time=time.time() - start_time
            )
            
            logger.info("=== SOAP NOTES GENERATION COMPLETED SUCCESSFULLY ===")
            return response
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in SOAP notes generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate SOAP notes: {str(e)}")

@router.get(
    "/soap_templates",
    summary="Get Available SOAP Templates",
    description="Retrieve list of available SOAP note templates with descriptions",
    tags=["Audio Services"],
    dependencies=[Depends(JWTBearer())]
)
async def get_soap_templates(db: Session = Depends(get_db)):
    """
    Get available SOAP note templates and their descriptions.
    
    **Available Templates:**
    - **General**: Standard SOAP format with all four sections
    - **Lite**: Simplified SOAP for quick clinical notes
    - **Combined A&P**: Combined Assessment & Plan section
    - **Detailed**: Comprehensive SOAP format with additional sections
    """
    templates = {
        "general": {
            "name": "General SOAP Note",
            "description": "Standard SOAP format with Subjective, Objective, Assessment, and Plan sections",
            "sections": ["Subjective", "Objective", "Assessment", "Plan"],
            "use_case": "Comprehensive clinical documentation"
        },
        "lite": {
            "name": "Lite SOAP Note", 
            "description": "Simplified SOAP format for quick clinical notes",
            "sections": ["Subjective", "Assessment & Plan"],
            "use_case": "Quick consultations and follow-ups"
        },
        "combined_ap": {
            "name": "Combined Assessment & Plan",
            "description": "SOAP format with combined Assessment and Plan section",
            "sections": ["Subjective", "Objective", "Assessment & Plan"],
            "use_case": "Streamlined clinical documentation"
        },
        "detailed": {
            "name": "Detailed SOAP Note",
            "description": "Comprehensive SOAP format with additional sections",
            "sections": ["Subjective", "Objective", "Assessment", "Plan", "Follow-up"],
            "use_case": "Complex cases requiring detailed documentation"
        }
    }
    
    return {
        "status": "success",
        "templates": templates,
        "default_template": "general",
                "total_templates": len(templates)
    }

### Prescription & medical Audio Notes
@router.post(
    "/deep_audio_notes",
    response_model=EnhancedTranscriptionResponse,
    summary="Transcribe audio file to prescription or medical notes",
    description="Upload an audio file to get both the raw transcription and a well-formatted clinical note with multilingual support.sarvam ai ",
    tags=["Audio Services"],
    dependencies=[Depends(JWTBearer())]
)
async def deep_audio_notes(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    recording_type: Optional[str] = Form(None, description="Recording type (clinical or prescription)")
):
    """
    Transcribe audio file and convert it to a well-formatted clinical note.
    
    Parameters:
    - audio: Audio file to transcribe (wav, mp3, etc)
    - recording_type: Type of recording (clinical or prescription)
    
    Returns:
    - EnhancedTranscriptionResponse object with raw text transcription and formatted clinical note
    """
    logger.info("=== DEEP AUDIO NOTES TRANSCRIPTION ENDPOINT CALLED ===")
    logger.info(f"Request received with recording_type: {recording_type}")
    
    try:
        logger.info(f"Received audio file for Deep Audio Notes transcription: {audio.filename}, size: {audio.size} bytes, content_type: {audio.content_type}")
        
        # Read the file content
        logger.info("Reading audio file content...")
        contents = await audio.read()
        if not contents:
            logger.error("Empty audio file received")
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        logger.info(f"Successfully read {len(contents)} bytes from audio file")
        
        # Save to temporary file
        logger.info("Creating temporary file...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        
        logger.info(f"Audio file saved to temporary path: {temp_path}")
        
        try:
            # Initialize Deep Audio Notes transcription chain
            logger.info("Initializing Deep Audio Notes transcription chain...")
            sarvam_transcribe_chain = SarvamTranscribeChain()
            
            # Process with Deep Audio Notes transcribe chain
            logger.info(f"Processing audio file with Deep Audio Notes transcription chain")
            logger.info(f"Recording type: {recording_type or 'clinical'}")
            
            result = await sarvam_transcribe_chain.get_answer(temp_path, recording_type=recording_type or "clinical")
            logger.info("Deep Audio Notes transcription chain processing completed successfully")
            logger.info(f"Result keys: {list(result.keys())}")
            

            # Log raw transcription details
            raw_trans = result["raw_transcription"]
            logger.info(f"Raw transcription text length: {len(raw_trans['text'])}")
            logger.info(f"Raw transcription language: {raw_trans['language']}")
            logger.info(f"Raw transcription text preview: {raw_trans['text'][:100]}...")
            
            # Ensure raw_transcription matches the expected schema
            raw_transcription = RawTranscription(
                text=result["raw_transcription"]["text"],
                language=result["raw_transcription"]["language"],
                language_probability=result["raw_transcription"]["language_probability"],
                segments=result["raw_transcription"]["segments"]
            )
            logger.info("Raw transcription schema validation successful")
            
            # Get the formatted output (clinical_note or prescription)
            formatted_output = result.get("clinical_note") or result.get("prescription", "")
            logger.info(f"Formatted output length: {len(formatted_output)}")
            logger.info(f"Formatted output preview: {formatted_output[:200]}...")
            
            # Create response
            response = EnhancedTranscriptionResponse(
                raw_transcription=raw_transcription,
                clinical_note=formatted_output
            )
            logger.info("Deep Audio Notes transcription response created successfully")
            logger.info("=== DEEP AUDIO NOTES TRANSCRIPTION COMPLETED SUCCESSFULLY ===")
            
            # Return the enhanced response
            return response
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.info(f"Temporary file cleaned up: {temp_path}")

    except Exception as e:
        logger.error(f"Error in Deep Audio Notes transcription: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")

# =============================================================================
# TEXT PROCESSING ENDPOINTS - New Feature
# =============================================================================

@router.post(
    "/process_text",
    response_model=TextProcessingResponse,
    summary="Content modify using AI ",
    description="Apply various AI processing operations to raw medical text",
    tags=["Text Processing"],
    dependencies=[Depends(JWTBearer())]
)
async def process_medical_text(
    request: TextProcessingRequest,
    db: Session = Depends(get_db)
):
    """
    Process raw medical text with selectable AI operations.
    
    **Available Processing Types:**
    - **Translation**: Translate medical text to different languages
    - **After Visit Summary**: Create patient-friendly visit summaries
    - **Referral Letter**: Generate professional referral letters
    - **Case Summary**: Comprehensive clinical case summaries
    - **Clinical Notes Cleanup**: Clean and organize clinical documentation
    - **Discharge Instructions**: Create clear discharge instructions
    - **Patient Education**: Generate educational materials about conditions
    """
    start_time = time.time()
    logger.info("=== TEXT PROCESSING ENDPOINT CALLED ===")
    logger.info(f"Processing type: {request.processing_type}")
    logger.info(f"Text length: {len(request.raw_text)}")
    logger.info(f"Patient name: {request.patient_name}")
    
    try:
        # Validate input
        if not request.raw_text or not request.raw_text.strip():
            raise HTTPException(status_code=400, detail="Raw text cannot be empty")
        
        # Validate translation requirements
        if request.processing_type == TextProcessingType.TRANSLATION:
            if not request.target_language:
                raise HTTPException(
                    status_code=400, 
                    detail="Target language is required for translation"
                )
        
        # Initialize the content modification chain
        content_chain = ContentModificationChain()
        
        # Process the text
        logger.info(f"🎯 Processing text with type: {request.processing_type}")
        result = content_chain.process_text(
            processing_type=request.processing_type,
            raw_text=request.raw_text,
            patient_name=request.patient_name,
            target_language=request.target_language,
            additional_context=request.additional_context
        )
        
        logger.info("✅ Text processing completed successfully")
        
        # Create enhanced response
        type_info = PROCESSING_TYPE_OPTIONS.get(request.processing_type, {})
        response = TextProcessingResponse(
            processed_text=result["processed_text"],
            processing_type=request.processing_type,
            processing_type_name=type_info.get("name", request.processing_type),
            original_text_length=len(request.raw_text),
            processed_text_length=len(result["processed_text"]),
            processing_time=time.time() - start_time,
            patient_name=request.patient_name,
            target_language=request.target_language,
            additional_metadata=result["metadata"]
        )
        
        logger.info("=== TEXT PROCESSING COMPLETED SUCCESSFULLY ===")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text processing: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to process text: {str(e)}")

@router.get(
    "/processing_types",
    response_model=AvailableProcessingTypesResponse,
    summary="Get Available Text Processing Types",
    description="Retrieve list of available text processing operations with descriptions and context suggestions",
    tags=["Text Processing"],
    dependencies=[Depends(JWTBearer())]
)
async def get_available_processing_types(db: Session = Depends(get_db)):
    """
    Get available text processing types and their descriptions.
    
    **Returns detailed information about:**
    - 🌐 **Translation**: Language translation capabilities
    - 📋 **After Visit Summary**: Patient communication summaries  
    - 📄 **Referral Letter**: Professional referral documentation
    - 📊 **Case Summary**: Comprehensive case documentation
    - ✨ **Clinical Notes Cleanup**: Documentation improvement
    - 🏠 **Discharge Instructions**: Patient discharge guidance
    - 📚 **Patient Education**: Educational content generation
    """
    try:
        processing_info = get_processing_type_info()
        
        return AvailableProcessingTypesResponse(
            processing_types=processing_info,
            total_types=len(processing_info)
        )
        
    except Exception as e:
        logger.error(f"Error getting processing types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing types: {str(e)}")

@router.get(
    "/processing_options",
    response_model=ProcessingTypeQuickReference,
    summary="Get Processing Type Quick Reference",
    description="Get a quick reference guide of all available processing types with emoji indicators",
    tags=["Text Processing"]
)
async def get_processing_options():
    """
    Get a quick reference of all available processing types.
    
    **Quick Reference:**
    - 🌐 translation: Translate medical text to other languages
    - 📋 after_visit_summary: Patient-friendly visit summaries
    - 📄 referral_letter: Professional referral letters
    - 📊 case_summary: Comprehensive case documentation
    - ✨ clinical_notes_cleanup: Clean and organize clinical notes
    - 🏠 discharge_instructions: Clear discharge instructions
    - 📚 patient_education: Educational materials for patients
    """
    return ProcessingTypeQuickReference()

@router.get(
    "/context_suggestions/{processing_type}",
    summary="Get Context Suggestions for Processing Type",
    description="Get recommended additional context fields for a specific processing type",
    tags=["Text Processing"]
)
async def get_context_suggestions_for_type(processing_type: str):
    """
    Get context field suggestions for a specific processing type.
    
    **Parameters:**
    - processing_type: One of the available processing types
    
    **Returns:**
    - Dictionary of recommended context fields with descriptions
    """
    try:
        if processing_type not in PROCESSING_TYPE_OPTIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid processing type. Available types: {list(PROCESSING_TYPE_OPTIONS.keys())}"
            )
        
        suggestions = get_context_suggestions(processing_type)
        type_info = PROCESSING_TYPE_OPTIONS[processing_type]
        
        return {
            "processing_type": processing_type,
            "name": type_info["name"],
            "description": type_info["description"],
            "requires_target_language": type_info["requires_target_language"],
            "context_suggestions": suggestions,
            "example_context": {
                field: f"Example value for {field}" 
                for field in suggestions.keys()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get context suggestions: {str(e)}")
