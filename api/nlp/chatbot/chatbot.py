from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from schemas.chatbot_schema import ChatbotInput, ChatbotOutput
from agents.med_chatbot_agent import MedChatbotAgent

from shared.auth.auth_bearer import JWTBearer

router = APIRouter()


@router.post("/healthcare_chat", response_model=ChatbotOutput, dependencies=[Depends(JWTBearer())])
async def healthcare_chat(input_data: ChatbotInput) -> ChatbotOutput:
    """
    Endpoint for chatting with the medical assistant.
    
    Args:
        input_data: The input data containing the user's query and thread_id
        
    Returns:
        ChatbotOutput: The chatbot's response
    """
    try:
        # Create and use the MedChatbotAgent
        agent = MedChatbotAgent(input_data.query)
        result = agent.process_query()
        print(result)
        # Return the response in the expected format
        return ChatbotOutput(
            answer=result or "",
            answer_found=True if result else False,
            related_articles=[],
            llm_error_occurred=False,
            conversation_id=input_data.conversation_id,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )
