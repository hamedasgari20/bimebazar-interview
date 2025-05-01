from pydantic import BaseModel, HttpUrl


# Properties shared by models wanting them.
class URLBase(BaseModel):
    original_url: HttpUrl  # Use HttpUrl for built-in validation


# Properties to receive via API on creation
class URLCreate(URLBase):
    pass


# Properties to return to client
class URLResponse(BaseModel):
    original_url: HttpUrl
    short_code: str

    class Config:
        from_attributes = True
