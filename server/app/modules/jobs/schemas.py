from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    city: str
    batch: str
    category: str | None = None
    salary_text: str | None = None
    description: str
    source_url: str | None = None
    status: str
    published_at: datetime


class JobPage(BaseModel):
    items: list[JobOut]
    total: int
    page: int
    page_size: int


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=50)
    batch: str = Field(min_length=1, max_length=20)
    category: str | None = Field(default=None, max_length=50)
    salary_text: str | None = Field(default=None, max_length=100)
    description: str = ""
    source_url: str | None = Field(default=None, max_length=500)


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    company: str | None = Field(default=None, min_length=1, max_length=200)
    city: str | None = Field(default=None, min_length=1, max_length=50)
    batch: str | None = Field(default=None, min_length=1, max_length=20)
    category: str | None = Field(default=None, max_length=50)
    salary_text: str | None = Field(default=None, max_length=100)
    description: str | None = None
    source_url: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, pattern="^(PUBLISHED|OFFLINE)$")
