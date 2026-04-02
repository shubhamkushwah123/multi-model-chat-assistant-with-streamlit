from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str
    label: str
    provider: str


class SessionInfo(BaseModel):
    id: str
    title: str
    created_at: str


class MessageRecord(BaseModel):
    session_id: str
    role: str
    model: str | None = None
    content: str
    created_at: str


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1)
    models: list[str] = Field(min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    responses: list[MessageRecord]
