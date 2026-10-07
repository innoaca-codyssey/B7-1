from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    provider: str
    multiplier: float
    is_default: bool


class PresetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str


class AdminModelOut(ModelOut):
    max_tokens: int
    is_active: bool
    sort_order: int


class ModelUpdate(BaseModel):
    is_active: bool | None = None
    is_default: bool | None = None
    multiplier: Decimal | None = Field(None, gt=0, le=Decimal("99.99"), decimal_places=2)
    max_tokens: int | None = Field(None, ge=1, le=32000)
    sort_order: int | None = Field(None, ge=0)


class UsageRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    model_code: str
    billed_tokens: int
    requests: int
