"""Whitelist Service"""
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from fastapi import HTTPException, status

from app.models.whitelist import UserWhitelist
from app.models.activation_code import ActivationCode
from app.models.user import User
from app.schemas.activation import (
    WhitelistCreate,
    WhitelistUpdate,
    WhitelistResponse,
    WhitelistListResponse,
    SupervisorInfo
)


class WhitelistService:
    """Service for managing user whitelist"""

    def __init__(self, db: Session):
        self.db = db

    def create_whitelist_entry(
        self,
        data: WhitelistCreate,
        created_by_user_id: int
    ) -> UserWhitelist:
        """
        Create new whitelist entry.
        
        Validates:
        - Identifier is unique
        - Supervisor exists and has correct role (if brigadista)
        - Role-specific requirements
        """
        # Check if identifier already exists
        existing = self.db.query(UserWhitelist).filter(
            UserWhitelist.identifier == data.identifier
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Identifier {data.identifier} is already in whitelist"
            )

        # If role is brigadista, supervisor is required
        if data.assigned_role == "brigadista":
            if not data.assigned_supervisor_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Supervisor is required for brigadista role"
                )
            
            # Verify supervisor exists and has correct role
            supervisor = self.db.query(User).filter(User.id == data.assigned_supervisor_id).first()
            if not supervisor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Supervisor with ID {data.assigned_supervisor_id} not found"
                )
            
            if supervisor.role.value not in ["admin", "encargado"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Supervisor must have admin or encargado role"
                )

        # Create whitelist entry
        whitelist_entry = UserWhitelist(
            identifier=data.identifier,
            identifier_type=data.identifier_type.value,
            full_name=data.full_name,
            phone=data.phone,
            assigned_role=data.assigned_role,
            assigned_supervisor_id=data.assigned_supervisor_id,
            notes=data.notes,
            created_by=created_by_user_id
        )

        self.db.add(whitelist_entry)
        self.db.commit()
        self.db.refresh(whitelist_entry)

        return whitelist_entry

    def get_whitelist_entry(self, whitelist_id: int) -> Optional[UserWhitelist]:
        """Get whitelist entry by ID with relationships"""
        return self.db.query(UserWhitelist).options(
            joinedload(UserWhitelist.assigned_supervisor),
            joinedload(UserWhitelist.activated_user),
            joinedload(UserWhitelist.creator),
            joinedload(UserWhitelist.activation_codes)
        ).filter(UserWhitelist.id == whitelist_id).first()

    def list_whitelist_entries(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,  # all, pending, activated
        role: Optional[str] = None,
        search: Optional[str] = None,
        supervisor_id: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> WhitelistListResponse:
        """
        List whitelist entries with filtering and pagination.
        """
        query = self.db.query(UserWhitelist).options(
            joinedload(UserWhitelist.assigned_supervisor),
            joinedload(UserWhitelist.activated_user),
            joinedload(UserWhitelist.creator),
            joinedload(UserWhitelist.activation_codes)
        )

        # Apply filters
        if status == "pending":
            query = query.filter(UserWhitelist.is_activated == False)
        elif status == "activated":
            query = query.filter(UserWhitelist.is_activated == True)
        
        if role:
            query = query.filter(UserWhitelist.assigned_role == role)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    UserWhitelist.identifier.ilike(search_pattern),
                    UserWhitelist.full_name.ilike(search_pattern)
                )
            )
        
        if supervisor_id:
            query = query.filter(UserWhitelist.assigned_supervisor_id == supervisor_id)

        # Get total count before pagination
        total_items = query.count()

        # Apply sorting
        if sort_by == "full_name":
            order_column = UserWhitelist.full_name
        elif sort_by == "identifier":
            order_column = UserWhitelist.identifier
        else:  # created_at
            order_column = UserWhitelist.created_at
        
        if sort_order == "asc":
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())

        # Apply pagination
        offset = (page - 1) * limit
        entries = query.offset(offset).limit(limit).all()

        # Calculate pagination info
        total_pages = (total_items + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        # Convert to response format
        items = []
        for entry in entries:
            # Check for active codes
            has_active_code = False
            code_expires_at = None
            if entry.activation_codes:
                for code in entry.activation_codes:
                    if not code.is_used and not code.is_expired and not code.is_locked:
                        has_active_code = True
                        code_expires_at = code.expires_at
                        break

            items.append(WhitelistResponse(
                id=entry.id,
                identifier=entry.identifier,
                identifier_type=entry.identifier_type,
                full_name=entry.full_name,
                phone=entry.phone,
                assigned_role=entry.assigned_role,
                assigned_supervisor=SupervisorInfo(
                    id=entry.assigned_supervisor.id,
                    name=entry.assigned_supervisor.full_name
                ) if entry.assigned_supervisor else None,
                is_activated=entry.is_activated,
                has_active_code=has_active_code,
                code_expires_at=code_expires_at,
                activated_at=entry.activated_at,
                activated_user_name=entry.activated_user.full_name if entry.activated_user else None,
                created_at=entry.created_at,
                created_by_name=entry.creator.full_name,
                notes=entry.notes
            ))

        return WhitelistListResponse(
            items=items,
            pagination={
                "page": page,
                "limit": limit,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            },
            filters_applied={
                "status": status or "all",
                "role": role,
                "search": search,
                "supervisor_id": supervisor_id,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        )

    def update_whitelist_entry(
        self,
        whitelist_id: int,
        data: WhitelistUpdate
    ) -> UserWhitelist:
        """
        Update whitelist entry. Only allowed if not yet activated.
        """
        entry = self.get_whitelist_entry(whitelist_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Whitelist entry {whitelist_id} not found"
            )

        if entry.is_activated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update whitelist entry that has already been activated"
            )

        # Update fields if provided
        if data.full_name is not None:
            entry.full_name = data.full_name
        if data.assigned_role is not None:
            entry.assigned_role = data.assigned_role
        if data.assigned_supervisor_id is not None:
            # Verify supervisor exists
            supervisor = self.db.query(User).filter(User.id == data.assigned_supervisor_id).first()
            if not supervisor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Supervisor with ID {data.assigned_supervisor_id} not found"
                )
            entry.assigned_supervisor_id = data.assigned_supervisor_id
        if data.phone is not None:
            entry.phone = data.phone
        if data.notes is not None:
            entry.notes = data.notes

        self.db.commit()
        self.db.refresh(entry)

        return entry

    def delete_whitelist_entry(self, whitelist_id: int) -> None:
        """
        Delete whitelist entry. Only allowed if not yet activated.
        Cascades to activation codes.
        """
        entry = self.get_whitelist_entry(whitelist_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Whitelist entry {whitelist_id} not found"
            )

        if entry.is_activated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete whitelist entry that has already been activated"
            )

        self.db.delete(entry)
        self.db.commit()

    def get_by_identifier(self, identifier: str) -> Optional[UserWhitelist]:
        """Get whitelist entry by identifier"""
        return self.db.query(UserWhitelist).filter(
            UserWhitelist.identifier == identifier
        ).first()
