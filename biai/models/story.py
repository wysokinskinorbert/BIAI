"""Data storytelling models."""

from enum import Enum

from pydantic import BaseModel, Field


class StoryNarrativeType(str, Enum):
    """Type of narrative structure."""
    TREND = "trend"
    COMPARISON = "comparison"
    ANOMALY = "anomaly"
    DISTRIBUTION = "distribution"
    GENERAL = "general"


class StorySection(BaseModel):
    """A single section of a data story."""
    heading: str = ""
    content: str = ""
    highlight_numbers: list[str] = Field(default_factory=list)


class DataStory(BaseModel):
    """Complete data narrative."""
    narrative_type: StoryNarrativeType = StoryNarrativeType.GENERAL
    context: str = ""
    key_findings: list[str] = Field(default_factory=list)
    implications: str = ""
    recommendations: list[str] = Field(default_factory=list)
    raw_text: str = ""
