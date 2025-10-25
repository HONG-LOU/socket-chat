from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str

    class Config:
        from_attributes = True


class FriendOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str


class AddFriendRequest(BaseModel):
    friend_email: EmailStr


class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    to_user_id: int
    body: str
