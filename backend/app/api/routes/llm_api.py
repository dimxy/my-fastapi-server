from app.models import LlmJobPublic, LlmJobCreate
import os
from pydantic import HttpUrl, BaseModel
import uuid
from litellm import video_generation, video_status, VideoObject
from typing import Any


from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from keycloak_py.keycloak_login import CurrentUser, get_current_user

from app.api.deps import SessionDep
from app.core.config import settings
# from app.crud import create_llm_job
from app.api.llm_impl.structs import ChatResponse, ChatRequest
# from app.api.llm_impl import hf_caller, vllm_caller

router = APIRouter(prefix="/llms", tags=["llms"])


@router.post(
    "/videos",
    dependencies=[Depends(get_current_user)],
    response_model=VideoObject
)
async def videos_post(
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    req: Request
) -> Any:
    """
    Create video generation job.
    """

    '''
    if provider == "hf":
        provider_job = hf_caller.generate_video(prompt)
    elif provider == "vllm":
        provider_job = vllm_caller.generate_video(prompt)
    else:
        raise Exception("unsupported LLM provider")
    job_create = LlmJobCreate(
        prompt=prompt,
        job_id=f'{provider}/{provider_job.job_id}'
    )
    return create_llm_job(session=session, job_in=job_create, owner_id=user_id)
    '''
    return video_generation(** await req.json())


@router.get(
    "/videos",
    dependencies=[Depends(get_current_user)],
    response_model=VideoObject
)
async def videos_get(
    session: SessionDep,
    current_user: CurrentUser,
    req: Request
) -> Any:
    """
    Get video generation job status and result, if completed.
    """

    # return create_llm_job(session=session, job_in=job_create, owner_id=user_id)
    return video_status(**await req.json())

@router.post(
    "/process_chat",
    dependencies=[Depends(get_current_user)],
    response_model=ChatResponse
)
def process_chat(request: ChatRequest) -> Any:
    """
    Process chat message and return response.
    """
    # Simple echo for now, replace with actual chat logic
    response = f"You said: {request.message}"
    return ChatResponse(response=response)

@router.post(
    "/parse_voice",
    dependencies=[Depends(get_current_user)]
)
def parse_voice(audio: UploadFile = File(...)) -> Any:
    """
    Parse voice input and return streamed voice response.
    """
    # For now, just return the audio back as stream
    # In real implementation, process the audio and generate response
    def generate_audio():
        content = audio.file.read()
        yield content

    return StreamingResponse(generate_audio(), media_type="audio/wav")

