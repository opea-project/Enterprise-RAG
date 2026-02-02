import io
import numpy as np
import os
import soundfile as sf
import uvicorn

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, status, HTTPException
from pydub import AudioSegment
from pydantic import BaseModel

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from comps.cores.utils.utils import sanitize_env
from model_handler import TTSModel

logger = get_opea_logger("TTS FastAPI Model Server")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
app = FastAPI(title="OpenAI-Compatible TTS Server")

tts = TTSModel(sanitize_env(os.getenv('TTS_MODEL_NAME')))

class SpeechRequest(BaseModel):
    input: str
    voice: str | None = "default"
    instructions: str | None = None
    response_format: str | None = "mp3"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"A validation error occured: {exc.errors()}. Check whether the request body and all fields you provided are correct.")
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}))


@app.post("/v1/audio/speech")
def create_speech(req: SpeechRequest):
    logger.info(f"Received TTS request with voice: {req.voice}, instructions: {req.instructions}, response_format: {req.response_format}")

    try:
        speech_output, sample_rate = tts.generate_audio(req.input, voice=req.voice, instructions=req.instructions)
    except ValueError as e:
        error_message = f"A ValueError occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    except ConnectionError as e:
        error_message = f"A Connection error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=404, detail=error_message)
    except NotImplementedError as e:
        error_message = f"A NotImplementedError occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=501, detail=error_message)
    except Exception as e:
        error_message = f"An error occurred while processing: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message)

    if not isinstance(speech_output, np.ndarray):
        speech_output = speech_output.numpy()

    if req.response_format.lower() == "mp3":
        audio_array = (speech_output * 32767).astype(np.int16)
        audio_segment = AudioSegment(
            audio_array.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )

        audio_buffer = io.BytesIO()
        audio_segment.export(audio_buffer, format="mp3", bitrate="128k")

        return Response(
            content=audio_buffer.getvalue(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3"
            },
        )
    elif req.response_format.lower() == "wav":
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, speech_output, samplerate=sample_rate, format='WAV')

        return Response(
            content=audio_buffer.getvalue(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=speech.wav"
            },
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported response format: {req.response_format}. Supported formats are 'mp3' and 'wav'.")


@app.get("/health")
def health() -> Response:
    if tts.ready:
        return Response(status_code=200)
    else:
        raise HTTPException(status_code=503, detail="TTS model not ready")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('ASR_USVC_PORT', default=8008)))