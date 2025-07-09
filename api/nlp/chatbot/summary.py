from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from schemas.summary_schema import SummaryType
from shared.auth.auth_bearer import JWTBearer
from shared.constants import ErrorResponses
from shared.log.logger import Logger
from shared.aws import AwsUtils
import uuid
import os
from typing import Optional, List

from chains.get_directsummary_chain import Directchainsummary
from promts.summary_promts_selector import get_prompts_for_summary_type
from chains.get_prescription_chain import GetPrescriptionChain
from fastapi.responses import JSONResponse


router = APIRouter()
logger = Logger.get_logger()

# The default table name for document data in LanceDB
DEFAULT_DOCS_TABLE_NAME = "documents_table"

# Directory for temporary file storage
UPLOAD_DIR = "/tmp/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# S3 domain name for medical PDFs
MEDICAL_PDF_DOMAIN = "medical_pdfs"


@router.post(
    "/single_document_summary",
    summary="Generate PDF summary using LlamaParse extraction",
    dependencies=[Depends(JWTBearer())],
    status_code=200,
    responses=ErrorResponses.HTTPErrors,  # type: ignore
)
async def single_document_summary(
    file: UploadFile = File(...),
    type_of_summary: Optional[SummaryType] = Form(SummaryType.CLINICAL_NOTES, description="Type of summary to generate"),
    user_id: str = Form(None, description="User ID for tracking and file organization")
):
    """
    Simple workflow to generate a summary from a PDF file:
    1. User uploads PDF file
    2. System saves file to S3 and associates it with user_id
    3. System extracts content using LlamaParse
    4. System generates summary from extracted content based on specified type
    
    Supported summary types:
    - discharge_summary: Generates a comprehensive discharge summary
    - key_findings_summary: Focuses on key clinical findings and abnormal values
    - clinical_notes_summary: General clinical notes summary (default)
    """
    transaction_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())  # Generate a document ID for reference
    temp_file_path = None
    s3_file_url = None
    
    try:
        logger.info(f"{transaction_id}: Processing medical summary request with type: {type_of_summary}")
        
        # Step 1: Save uploaded file temporarily (needed for processing)
        temp_file_path = os.path.join(UPLOAD_DIR, f"{transaction_id}_{file.filename}")
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        logger.info(f"File temporarily saved at {temp_file_path}")
        
        # Step 2: Upload the file to S3 for permanent storage
        # Create a user-specific folder structure: medical_pdfs/user_id/transaction_id/filename
        user_folder = user_id if user_id else "anonymous"
        s3_domain = f"{MEDICAL_PDF_DOMAIN}/{user_folder}"
        
        # Upload to S3 using the existing AwsUtils
        s3_result = AwsUtils.upload_file_to_s3(
            transaction_id=transaction_id,
            domain_name=s3_domain,
            file_path=temp_file_path,
            upload_file_name=file.filename
        )
        
        # Extract S3 URI and other info
        s3_uri = s3_result["s3_uri"]
        s3_bucket = s3_result["bucket"]
        s3_key = s3_result["key"]
        
        logger.info(f"File permanently saved to S3: {s3_uri}")
        
        # Step 3: Use the prompt selector utility to get the right prompts
        query, main_instruction, prompt_instruction = get_prompts_for_summary_type(type_of_summary)
        logger.info(f"Using prompts for summary type: {type_of_summary}")
        
        # Step 4: Initialize the summarizer with the query and custom instructions if provided
        summarizer = Directchainsummary(
            query=query, 
            main_instruction=main_instruction,
            prompt_instruction=prompt_instruction
        )
        
        # Step 5: Generate summary (extraction and summarization happen inside)
        summary = summarizer.get_answer(temp_file_path)
        
        # Step 6: Return the results including the S3 information and document ID
        return {
            "document_id": document_id,  # Just for reference, not stored in DB
            "file_name": file.filename,
            "s3_uri": s3_uri,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "summary": summary,
            "summary_type": type_of_summary.value if hasattr(type_of_summary, 'value') else str(type_of_summary),
            "transaction_id": transaction_id,
            "user_id": user_id if user_id else "anonymous"
        }
        
    except Exception as e:
        logger.exception(f"Error processing medical summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Clean up temporary file after processing
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"Cleaned up temporary file: {temp_file_path}")

## Support for multiple PDF files need yo do test add things

@router.post(
    "/multi_document_summary",
    summary="Generate combined summary from multiple PDF files",
    dependencies=[Depends(JWTBearer())],
    status_code=200,
    responses=ErrorResponses.HTTPErrors,  # type: ignore
)
async def multi_document_summary(
    files: List[UploadFile] = File(...),
    type_of_summary: Optional[SummaryType] = Form(SummaryType.CLINICAL_NOTES, description="Type of summary to generate"),
    user_id: str = Form(None, description="User ID for tracking and file organization")
):
    """
    Multi-PDF workflow to generate a combined summary from multiple PDF files:
    1. User uploads multiple PDF files
    2. System saves files to S3 and associates them with user_id
    3. System extracts content from all files using LlamaParse batch processing
    4. System generates a combined summary from all extracted content
    
    Supported summary types:
    - discharge_summary: Generates a comprehensive discharge summary
    - key_findings_summary: Focuses on key clinical findings and abnormal values
    - clinical_notes_summary: General clinical notes summary (default)
    """
    transaction_id = str(uuid.uuid4())
    temp_file_paths = []
    s3_results = []
    
    try:
        logger.info(f"{transaction_id}: Processing multi-PDF summary request with type: {type_of_summary}")
        logger.info(f"Number of files uploaded: {len(files)}")
        
        # Step 1: Save uploaded files temporarily (needed for processing)
        for file in files:
            temp_file_path = os.path.join(UPLOAD_DIR, f"{transaction_id}_{file.filename}")
            with open(temp_file_path, "wb") as temp_file:
                content = await file.read()
                temp_file.write(content)
            temp_file_paths.append(temp_file_path)
        
        logger.info(f"Files temporarily saved at {UPLOAD_DIR}")
        
        # Step 2: Upload the files to S3 for permanent storage
        user_folder = user_id if user_id else "anonymous"
        s3_domain = f"{MEDICAL_PDF_DOMAIN}/{user_folder}"
        
        for idx, temp_file_path in enumerate(temp_file_paths):
            file_name = files[idx].filename
            # Upload to S3 using the existing AwsUtils
            s3_result = AwsUtils.upload_file_to_s3(
                transaction_id=transaction_id,
                domain_name=s3_domain,
                file_path=temp_file_path,
                upload_file_name=file_name
            )
            s3_results.append({
                "file_name": file_name,
                "s3_uri": s3_result["s3_uri"],
                "s3_bucket": s3_result["bucket"],
                "s3_key": s3_result["key"]
            })
        
        logger.info(f"All files permanently saved to S3")
        
        # Step 3: Use the prompt selector utility to get the right prompts
        query, main_instruction, prompt_instruction = get_prompts_for_summary_type(type_of_summary)
        logger.info(f"Using prompts for summary type: {type_of_summary}")
        
        # Step 4: Initialize the summarizer with the query and custom instructions if provided
        summarizer = Directchainsummary(
            query=query, 
            main_instruction=main_instruction,
            prompt_instruction=prompt_instruction
        )
        
        # Step 5: Generate combined summary from all files
        summary = summarizer.get_multiple_answers(temp_file_paths)
        
        # Step 6: Return the results including the S3 information
        return {
            "files_info": s3_results,
            "summary": summary,
            "summary_type": type_of_summary.value if hasattr(type_of_summary, 'value') else str(type_of_summary),
            "transaction_id": transaction_id,
            "user_id": user_id if user_id else "anonymous",
            "total_files_processed": len(files)
        }
        
    except Exception as e:
        logger.exception(f"Error processing multi-PDF summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Clean up temporary files after processing
        for temp_file_path in temp_file_paths:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        logger.info(f"Cleaned up all temporary files")


@router.post(
    "/lab-report-extraction",
    summary="Extract lab report values and abnormalities from uploaded PDF",
    status_code=200,
)
async def lab_report_extraction(
    file: UploadFile = File(..., description="PDF file containing the lab report")
):
    """
    Upload a PDF lab report and get extracted patient details, all lab results, and abnormal values.
    """
    try:
        # Save uploaded file to a temp location
        temp_dir = "/tmp/pdf_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"extract_{uuid.uuid4()}_{file.filename}")
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        logger.info(f"Lab report PDF saved at {temp_file_path}")

        # Extract answer using GetPrescriptionChain
        extractor = GetPrescriptionChain()
        answer = extractor.get_answer(temp_file_path)

        # Optionally, remove the temp file after processing
        try:
            os.remove(temp_file_path)
        except Exception as cleanup_err:
            logger.warning(f"Could not remove temp file: {cleanup_err}")

        return JSONResponse(content={"answer": answer})
    except Exception as e:
        logger.exception(f"Error extracting lab report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

