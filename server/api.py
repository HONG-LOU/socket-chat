from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from .deps import get_current_user, get_db
from .models import Friendship, Message, User
from .schemas import (
    AddFriendRequest,
    AuthToken,
    FriendOut,
    LoginRequest,
    MessageOut,
    RegisterRequest,
    SendMessageRequest,
    UserOut,
)
from .security import create_access_token, hash_password, verify_password


router = APIRouter()


@router.post("/auth/register", response_model=UserOut)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    exists = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已注册"
        )
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=AuthToken)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误"
        )
    token = create_access_token(str(user.id))
    return AuthToken(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/friends/add", response_model=FriendOut)
def add_friend(
    payload: AddFriendRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.friend_email == user.email:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")
    friend = db.execute(
        select(User).where(User.email == payload.friend_email)
    ).scalar_one_or_none()
    if not friend:
        raise HTTPException(status_code=404, detail="未找到该用户")
    exists = db.execute(
        select(Friendship).where(
            and_(Friendship.user_id == user.id, Friendship.friend_user_id == friend.id)
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="已是好友")
    db.add(Friendship(user_id=user.id, friend_user_id=friend.id))
    db.add(Friendship(user_id=friend.id, friend_user_id=user.id))
    db.commit()
    return FriendOut(id=friend.id, email=friend.email, display_name=friend.display_name)


@router.get("/friends", response_model=List[FriendOut])
def list_friends(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(User)
        .join(Friendship, Friendship.friend_user_id == User.id)
        .where(Friendship.user_id == user.id)
        .order_by(User.display_name)
    ).scalars()
    return [
        FriendOut(id=r.id, email=r.email, display_name=r.display_name) for r in rows
    ]


@router.get("/messages/{friend_id}", response_model=List[MessageOut])
def history(
    friend_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.execute(
        select(Message)
        .where(
            or_(
                and_(Message.sender_id == user.id, Message.receiver_id == friend_id),
                and_(Message.sender_id == friend_id, Message.receiver_id == user.id),
            )
        )
        .order_by(Message.created_at)
    ).scalars()
    return list(rows)
