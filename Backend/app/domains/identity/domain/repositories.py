
   
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.domains.identity.domain.entities import Organization, PendingUser, RefreshToken, User


class IPendingUserRepository(ABC):
                                                                             

    @abstractmethod
    async def create(self, pending_user: PendingUser) -> PendingUser: ...

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> PendingUser | None: ...

    @abstractmethod
    async def email_exists(self, email: str) -> bool: ...

    @abstractmethod
    async def slug_exists(self, slug: str) -> bool: ...

    @abstractmethod
    async def delete(self, pending_user_id: uuid.UUID) -> None: ...


class IOrganizationRepository(ABC):
                                                

    @abstractmethod
    async def create(self, org: Organization) -> Organization:
                                                                   
        ...

    @abstractmethod
    async def get_by_id(self, org_id: uuid.UUID) -> Organization | None:
                                                                             
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Organization | None:
                                                                              
        ...

    @abstractmethod
    async def update(self, org: Organization) -> Organization:
                                                          
        ...

    @abstractmethod
    async def slug_exists(self, slug: str) -> bool:
                                                                    
        ...

    @abstractmethod
    async def count_active_users(self, org_id: uuid.UUID) -> int:
                                                                                 
        ...


class IUserRepository(ABC):
                                        

    @abstractmethod
    async def create(self, user: User) -> User:
                                                           
        ...

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID, org_id: uuid.UUID) -> User | None:
                                                                            
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
           
        ...

    @abstractmethod
    async def get_by_email_in_org(self, email: str, org_id: uuid.UUID) -> User | None:
                                                         
        ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
    ) -> list[User]:
                                                               
        ...

    @abstractmethod
    async def get_by_email_verification_token(self, token_hash: str) -> User | None:
                                                                                     
        ...

    @abstractmethod
    async def get_by_password_reset_token(self, token_hash: str) -> User | None:
                                                           
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
                                                  
        ...

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
                                                                     
        ...

    @abstractmethod
    async def update_last_active(self, user_id: uuid.UUID, at: datetime) -> None:
                                                                                   
        ...


class IRefreshTokenRepository(ABC):
                                                 

    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken:
                                          
        ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
                                                        
        ...

    @abstractmethod
    async def mark_used(self, token_id: uuid.UUID, used_at: datetime) -> None:
                                                         
        ...

    @abstractmethod
    async def revoke_by_id(self, token_id: uuid.UUID) -> None:
                                             
        ...

    @abstractmethod
    async def revoke_family(self, family_id: uuid.UUID) -> int:
           
        ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        ...


class IPendingUserRepository(ABC):
    @abstractmethod
    async def create(self, pending_user: PendingUser) -> PendingUser:
        ...

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> PendingUser | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> PendingUser | None:
        ...

    @abstractmethod
    async def list_by_org(self, org_id: uuid.UUID) -> list[PendingUser]:
        ...

    @abstractmethod
    async def update(self, pending_user: PendingUser) -> PendingUser:
        ...

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        ...

    @abstractmethod
    async def slug_exists(self, slug: str) -> bool:
        ...

    @abstractmethod
    async def delete(self, pending_user_id: uuid.UUID) -> None:
        ...
