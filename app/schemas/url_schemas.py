from pydantic import BaseModel, HttpUrl


# Properties shared by models wanting them.
class URLBase(BaseModel):
    original_url: HttpUrl  # Use HttpUrl for built-in validation


# Properties to receive via API on creation
class URLCreate(URLBase):
    pass


class URLStats(BaseModel):
    original_url: HttpUrl
    short_code: str
    visit_count: int

    class Config:
        from_attributes = True


# Properties to return to client
class URLResponse(BaseModel):
    original_url: HttpUrl
    short_code: str

    class Config:
        from_attributes = True
