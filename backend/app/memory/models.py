from pydantic import BaseModel


class PreferenceCreate(BaseModel):
    category: str
    preference_key: str
    preference_value: str


class PreferenceUpdate(BaseModel):
    preference_value: str


class PreferenceResponse(BaseModel):
    id: str
    category: str
    preference_key: str
    preference_value: str
    source: str
    confidence: float
    active: bool
    created_at: str
    updated_at: str
