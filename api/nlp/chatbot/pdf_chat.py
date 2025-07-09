from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import Optional
import uuid
import os
from datetime import datetime

from shared.auth.auth_bearer import JWTBearer
from shared.log.logger import Logger
from shared.aws import AwsUtils
from pydantic import BaseModel, Field
from chains.get_qa_chain import QaChain
from schemas.chatbot_schema import ChatpdfResponse


router = APIRouter()
logger = Logger.get_logger()

# Directory for temporary file storage
UPLOAD_DIR = "/tmp/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# S3 domain name for PDFs
MEDICAL_PDF_DOMAIN = "medical_pdfs"

# For simplicity, we'll use an in-memory session store
# In production, use a persistent database
active_sessions = {}

class CleanupRequest(BaseModel):
    """Request model for cleanup endpoint"""
    session_id: str = Field(..., description="Session ID to cleanup")

@router.post("/cleanup", dependencies=[Depends(JWTBearer())])
async def cleanup_session(request: CleanupRequest):
    """Cleanup session and associated resources"""
    if request.session_id in active_sessions:
        try:
            # Get session info
            session = active_sessions[request.session_id]
            
            # Create QA chain instance to access DB
            qa_chain = QaChain(session['temp_file_path'], "")
            
            # Drop the table
            qa_chain.cleanup_table(session['table_name'])
            
            # Remove temporary file if it exists
            if os.path.exists(session['temp_file_path']):
                os.remove(session['temp_file_path'])
                
            # Remove session from active sessions
            del active_sessions[request.session_id]
            
            logger.info(f"Cleaned up session {request.session_id}")
            return {"message": "Session cleaned up successfully"}
            
        except Exception as e:
            logger.exception(f"Error cleaning up session: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return {"message": "Session not found"}

async def _process_file(transaction_id, file, user_id, session_id):
    """Process an uploaded file, save it locally and to S3, and index its content"""
    # Create temporary file path
    temp_file_path = os.path.join(UPLOAD_DIR, f"{transaction_id}_{file.filename}")
    
    # Save file locally
    with open(temp_file_path, "wb") as temp_file:
        content = await file.read()
        temp_file.write(content)
    
    logger.info(f"File temporarily saved at {temp_file_path}")
    
    # Upload to S3
    user_folder = user_id if user_id else "anonymous"
    s3_domain = f"{MEDICAL_PDF_DOMAIN}/{user_folder}"
    
    s3_result = AwsUtils.upload_file_to_s3(
        transaction_id=transaction_id,
        domain_name=s3_domain,
        file_path=temp_file_path,
        upload_file_name=file.filename
    )
    
    logger.info(f"File permanently saved to S3: {s3_result['s3_uri']}")
    
    # Create QA chain and initialize table using filename
    qa_chain = QaChain(temp_file_path, "", None)  # Initialize without table
    table_name = qa_chain.create_table(file.filename)  # Create table using filename
    
    return temp_file_path, table_name

@router.post(
    "/pdf_chat",
    summary="Upload PDF and chat or just chat with existing session",
    dependencies=[Depends(JWTBearer())],
    status_code=200,
    response_model=ChatpdfResponse
)
async def pdf_chat(
    user_id: str = Form(..., description="User ID for session tracking"),
    query: Optional[str] = Form(None, description="Question to ask about the PDF"),
    session_id: Optional[str] = Form(None, description="Session ID for existing conversations"),
    file: Optional[UploadFile] = File(None, description="PDF file to upload (for new sessions)")
):
    """
    Universal endpoint for PDF chat:
    
    - If file is provided: Uploads PDF, indexes it, and starts a new session
    - If session_id is provided: Uses existing session for follow-up questions
    - If both file and session_id are provided: Replaces the document in the existing session
    
    Returns a consistent response with session_id and either an answer or a message.
    """
    try:
        transaction_id = str(uuid.uuid4())
        logger.info(f"{transaction_id}: Processing PDF chat request from user {user_id}")
        
        # Check required parameters
        if not file and not session_id:
            raise HTTPException(
                status_code=400, 
                detail="Either file or session_id must be provided"
            )
        
        # Use existing session if provided and valid
        if session_id and session_id in active_sessions:
            logger.info(f"Using existing session {session_id}")
            table_name = active_sessions[session_id]['table_name']
            
            # If a file is also provided, replace the document in the session
            if file:
                logger.info(f"Replacing document in session {session_id}")
                
                # Clean up old resources
                old_table_name = active_sessions[session_id]['table_name']
                qa_chain = QaChain(active_sessions[session_id]['temp_file_path'], "", None)
                qa_chain.cleanup_table(old_table_name)
                
                # Process the new file and wait for indexing
                temp_file_path, table_name = await _process_file(transaction_id, file, user_id, session_id)
                
                # Update session with new file and table info
                active_sessions[session_id].update({
                    'temp_file_path': temp_file_path,
                    'table_name': table_name
                })
                
                is_new_session = False
            else:
                # Using existing session without a new file
                temp_file_path = active_sessions[session_id]['temp_file_path']
                is_new_session = False
                
        # Create a new session with the uploaded file
        elif file:
            # Generate new session ID
            session_id = str(uuid.uuid4())
            
            # Process and store the file, wait for indexing
            temp_file_path, table_name = await _process_file(transaction_id, file, user_id, session_id)
            
            # Store session info
            active_sessions[session_id] = {
                'user_id': user_id,
                'temp_file_path': temp_file_path,
                'table_name': table_name,
                'created_at': datetime.now()
            }
            
            is_new_session = True
            
        else:
            # Session ID was provided but not found
            raise HTTPException(
                status_code=404,
                detail=f"Session with ID {session_id} not found. It may have expired."
            )
            
        # If no query, just return session info
        if not query:
            return ChatpdfResponse(
                session_id=session_id,
                answer=None,
                message="Document processed and indexed. Send a query to get answers.",
                is_new_session=is_new_session,
                table_name=table_name
            )
            
        # Process the query using the indexed table
        qa_chain = QaChain(temp_file_path, query, table_name=table_name)
        qa_response = qa_chain.get_answer()
        
        # Add session information to response
        return ChatpdfResponse(
            session_id=session_id,
            answer=qa_response.get('answer'),
            message=qa_response.get('message'),
            is_new_session=is_new_session,
            table_name=table_name
        )
            
    except Exception as e:
        logger.exception(f"Error in PDF chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
