   
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class GetOrgDashboardQuery:
                                                                 
    org_id: uuid.UUID


@dataclass(frozen=True)
class GetWorkerDashboardQuery:
                                                                 
    user_id: uuid.UUID
    org_id: uuid.UUID
    upcoming_days: int = 7                                                     


@dataclass(frozen=True)
class GetUserReliabilityQuery:
                                                                         
    user_id: uuid.UUID
    org_id: uuid.UUID
    days: int = 30                                                  


@dataclass(frozen=True)
class GetAllReliabilityQuery:
                                                                     
    org_id: uuid.UUID


@dataclass(frozen=True)
class GetMeetingAnalyticsQuery:
                                                                        
    meeting_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class GetMeetingROIQuery:
       
    meeting_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class RefreshReliabilityQuery:
       
    org_id: uuid.UUID
