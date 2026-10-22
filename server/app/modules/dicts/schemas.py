from pydantic import BaseModel, ConfigDict, Field


class DictItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_key: str
    item_value: str
    sort_order: int
    enabled: bool


class DictTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type_code: str
    name: str
    version: int
    description: str | None = None
    items: list[DictItemOut]


class DictSnapshot(BaseModel):
    version: int
    types: list[DictTypeOut]


class DictTypeCreate(BaseModel):
    type_code: str = Field(min_length=1, max_length=50, pattern="^[A-Z0-9_]+$")
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class DictItemCreate(BaseModel):
    type_code: str = Field(min_length=1, max_length=50)
    item_key: str = Field(min_length=1, max_length=100)
    item_value: str = Field(min_length=1, max_length=200)
    sort_order: int = 0
    enabled: bool = True


class DictItemUpdate(BaseModel):
    item_value: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = None
    enabled: bool | None = None
