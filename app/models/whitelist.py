"""User Whitelist Model"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserWhitelist(Base):
    """
    Pre-authorized users who can activate accounts.
    An entry in this table allows a user to create an account using an activation code.
    """
    __tablename__ = "user_whitelist"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Identifier (user must provide this to activate)
    identifier = Column(String(255), nullable=False, unique=True, index=True)
    identifier_type = Column(String(20), nullable=False)  # email, phone, national_id

    # Pre-assigned user information
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    assigned_role = Column(String(20), nullable=False)  # admin, encargado, brigadista
    assigned_supervisor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Activation tracking
    is_activated = Column(Boolean, nullable=False, default=False, index=True)
    activated_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    notes = Column(Text, nullable=True)

    # Relationships
    assigned_supervisor = relationship("User", foreign_keys=[assigned_supervisor_id], back_populates="supervised_whitelist")
    activated_user = relationship("User", foreign_keys=[activated_user_id], back_populates="whitelist_activation")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_whitelist")
    activation_codes = relationship("ActivationCode", back_populates="whitelist_entry", cascade="all, delete-orphan")
    audit_logs = relationship("ActivationAuditLog", back_populates="whitelist_entry")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "identifier_type IN ('email', 'phone', 'national_id')",
            name="check_identifier_type"
        ),
        CheckConstraint(
            "assigned_role IN ('admin', 'encargado', 'brigadista')",
            name="check_assigned_role"
        ),
        CheckConstraint(
            """
            (is_activated = TRUE AND activated_user_id IS NOT NULL AND activated_at IS NOT NULL)
            OR (is_activated = FALSE AND activated_user_id IS NULL AND activated_at IS NULL)
            """,
            name="check_activated_consistency"
        ),
    )

    def __repr__(self) -> str:
        return f"<UserWhitelist(id={self.id}, identifier={self.identifier}, role={self.assigned_role}, activated={self.is_activated})>"
