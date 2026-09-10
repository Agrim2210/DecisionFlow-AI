   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AddDependencyCommand:
       
    org_id: uuid.UUID
    upstream_id: uuid.UUID                                      
    downstream_id: uuid.UUID                           
    dependency_type: str = "finish_to_start"
    created_by: uuid.UUID | None = None                       


@dataclass(frozen=True)
class RemoveDependencyCommand:
                                                                 
    dep_id: uuid.UUID
    org_id: uuid.UUID
    removed_by: uuid.UUID


@dataclass(frozen=True)
class BulkAddDependenciesCommand:
       
    org_id: uuid.UUID
    edges: list[dict] = field(default_factory=list)
                  
                            
                              
                               
                                  
       
