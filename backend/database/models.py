import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    email = Column(String(256), unique=True, nullable=True)


class ClientLead(Base):
    __tablename__ = "client_leads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    source = Column(String(128), nullable=True)
    data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(256), nullable=False)
    project_summary = Column(Text, nullable=False)
    proposal_text = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, server_default="draft")
    sent_to = Column(String(256), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
