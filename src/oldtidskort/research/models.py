from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl, model_validator


class LocationRole(StrEnum):
    ORIGINAL = "original_location"
    FINDSPOT = "findspot"
    CURRENT = "current_location"
    REGISTERED = "registered_location"
    EARLIEST_KNOWN = "earliest_known_location"


class CoordinateMethod(StrEnum):
    SOURCE_COORDINATE = "source_coordinate"
    RELATED_PLACE_COORDINATE = "related_place_coordinate"
    GEOCODED = "geocoded"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ReviewStatus(StrEnum):
    IMPORTED = "imported"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"


class StoneRecord(BaseModel):
    stone_id: str
    dr_number: str | None = None
    wikidata_id: str | None = None
    runor_id: str | None = None
    name: str
    period: str = "vikingetid"
    scope: str = "present_day_denmark"
    survival_status: str = "unknown"
    record_status: ReviewStatus = ReviewStatus.IMPORTED
    record_note: str


class RegisteredObservation(BaseModel):
    observation_id: str
    source_id: str
    source_record_id: str
    feature_type: str
    label: str
    lon: float
    lat: float
    source_statement: str
    interpretation: str
    review_status: ReviewStatus = ReviewStatus.IMPORTED


class IdentityLink(BaseModel):
    link_id: str
    stone_id: str
    observation_id: str
    method: str
    confidence: Confidence
    rationale: str
    review_status: ReviewStatus = ReviewStatus.IMPORTED


class LocationAssessment(BaseModel):
    location_id: str
    stone_id: str
    role: LocationRole
    label: str | None = None
    lon: float | None = None
    lat: float | None = None
    coordinate_method: CoordinateMethod
    uncertainty_m: int | None = Field(default=None, ge=0)
    confidence: Confidence
    is_estimate: bool
    rationale: str
    review_status: ReviewStatus = ReviewStatus.IMPORTED

    @model_validator(mode="after")
    def coordinates_are_complete(self) -> LocationAssessment:
        if (self.lon is None) != (self.lat is None):
            raise ValueError("lon og lat skal begge være udfyldt eller begge mangle")
        if self.coordinate_method is CoordinateMethod.UNKNOWN and self.lon is not None:
            raise ValueError("ukendt metode må ikke have koordinater")
        if self.coordinate_method is not CoordinateMethod.UNKNOWN and self.lon is None:
            raise ValueError("en kendt koordinatmetode kræver koordinater")
        return self


class EvidenceRecord(BaseModel):
    evidence_id: str
    location_id: str
    source_id: str
    source_property: str | None = None
    source_statement: str
    interpretation: str


class SourceRecord(BaseModel):
    source_id: str
    title: str
    publisher: str
    url: HttpUrl
    license: str
    accessed_at: str
