import os
from pydantic import HttpUrl, BaseModel
import uuid
from typing import Any
from gradio_client import Client, handle_file

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from keycloak_py.keycloak_login import CurrentUser, get_current_user

from app.api.deps import SessionDep
from app.core.config import settings

router = APIRouter(prefix="/llms", tags=["llms"])

app_dir = os.getcwd()

# Models
class VideoPublic(BaseModel):
    file_path: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.get(
    "/generate_video",
    dependencies=[Depends(get_current_user)],
response_model=VideoPublic)
def generate_video(
    prompt: str
) -> Any:
    """
    Retrieve items.
    """

    print(f'app_dir={app_dir}')
    client = Client("r3gm/wan2-2-fp8da-aoti-preview", token=settings.HF_TOKEN, download_files=f'{app_dir}/static')
    client_result = client.predict(
        input_image=handle_file('https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png'),
        last_image=handle_file('https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png'),
        prompt=prompt,
        steps=6,
        negative_prompt="",
        duration_seconds=3.5,
        guidance_scale=1,
        guidance_scale_2=1,
        seed=42,
        randomize_seed=True,
        quality=6,
        scheduler="UniPCMultistep",
        flow_shift=3,
        frame_multiplier=16,
        video_component=True,
        api_name="/generate_video"
    )
    print(f'client_result={client_result}')
    result = VideoPublic(
        file_path = f'static/{client_result[1]}'
    )

    '''
    result = VideoPublic(
        file_path = "static/tmpcmd0irph.mp4"
    )
    '''
    return result

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
