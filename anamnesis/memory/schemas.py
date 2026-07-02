from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class MemoryType(str, Enum):
    BUG_FIX = "bug_fix"
    COMMIT = "commit"
    RULE = "rule"
    DOCUMENTATION = "documentation"
    REVIEW_NOTE = "review_note"

class BugFixMemory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: Optional[str] = None
    file_path: str = Field(..., description="Path to the file affected by the bug")
    function_name: Optional[str] = Field(None, description="Name of the function or method involved")
    title: str = Field(..., description="Short summary of the bug")
    root_cause: str = Field(..., description="Why the bug occurred")
    fix_description: str = Field(..., description="How the bug was resolved")
    severity: str = Field("medium", description="Bug severity: low, medium, high, critical")
    tags: List[str] = Field(default_factory=list, description="Tags or labels (e.g. null-check, api, payment)")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_memory_text(self) -> str:
        text = f"[BUG FIX] {self.title}\n"
        text += f"File: {self.file_path}\n"
        if self.function_name:
            text += f"Function: {self.function_name}\n"
        text += f"Root Cause: {self.root_cause}\n"
        text += f"Fix Applied: {self.fix_description}\n"
        if self.tags:
            text += f"Tags: {', '.join(self.tags)}\n"
        return text

class CodeRuleMemory(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    rule_title: str = Field(..., description="Concise rule title")
    description: str = Field(..., description="Detailed rule guideline")
    domain: str = Field("general", description="Module or layer affected (e.g. services, controllers)")
    origin_memory_ids: List[str] = Field(default_factory=list, description="IDs of source memories that created this rule")
    provenance_files: List[str] = Field(default_factory=list, description="Files where this rule pattern was observed")
    confidence: float = Field(0.9, description="Confidence score of consolidated rule (0.0 to 1.0)")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_memory_text(self) -> str:
        text = f"[CONSOLIDATED RULE] {self.rule_title}\n"
        text += f"Domain: {self.domain}\n"
        text += f"Rule: {self.description}\n"
        if self.provenance_files:
            text += f"Observed in files: {', '.join(self.provenance_files)}\n"
        text += f"Confidence: {self.confidence}\n"
        return text

class CommitMemory(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    commit_hash: str
    author: str
    summary: str
    files_changed: List[str]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_memory_text(self) -> str:
        text = f"[COMMIT {self.commit_hash[:7]}] {self.summary}\n"
        text += f"Author: {self.author}\n"
        text += f"Files Changed: {', '.join(self.files_changed)}\n"
        return text

class MemoryRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    memory_type: MemoryType
    title: str
    content: str
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    active: bool = True
