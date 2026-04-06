from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# --- LLM Contract 1: Extract Entities ---
class ExtractedEntity(BaseModel):
    name: str = Field(description="Name of the entity or topic (e.g., 'Python Asyncio', 'Model Context Protocol')")
    summary: str = Field(description="Brief summary of what the raw text says about this entity")

class ExtractionResponse(BaseModel):
    entities: List[ExtractedEntity]

# --- LLM Contract 2: Read-and-Compare (Conflict Resolution) ---
class FactAction(BaseModel):
    text: str = Field(description="The exact text of the fact to be placed in the markdown file")
    status: Literal['KEEP', 'UPDATE', 'CONFLICT', 'NEW'] = Field(
        description="Action to take. 'KEEP' for existing accurate facts, 'UPDATE' to replace, 'CONFLICT' if logical contradiction, 'NEW' for novel information."
    )
    sources: List[str] = Field(description="List of UUIDs that support this fact.")

class ComparisonResponse(BaseModel):
    facts: List[FactAction]
    reasoning: str = Field(description="Chain of thought explaining any updates or conflicts.")
