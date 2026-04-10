from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from pydantic import EmailStr
from pwdlib import PasswordHash

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    reviews: List["Review"] = Relationship(back_populates="author")

    def check_password(self, plaintext_password: str):
        return PasswordHash.recommended().verify(password=plaintext_password, hash=self.password)

class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    programme: str
    year_started: int
    picture: str

    reviews: List["Review"] = Relationship(back_populates="student")

class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    rating: int = Field(ge=0, le=5)

    student_id: Optional[int] = Field(default=None, foreign_key="student.id")
    author_id: Optional[int] = Field(default=None, foreign_key="user.id")

    student: Optional[Student] = Relationship(back_populates="reviews")
    author: Optional[User] = Relationship(back_populates="reviews")