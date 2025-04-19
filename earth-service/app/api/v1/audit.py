from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, func, select

from app.api.deps import get_db
from app.models.audit import Audit, AuditResult
from app.models.endpoint import Endpoint
from app.models.schema import Schema

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/by-day", summary="Audit logs grouped by day")
def audit_by_day(db: Annotated[Session, Depends(get_db)]):
    """Returns audit counts grouped by day."""
    results = db.exec(
        select(
            func.date_trunc("day", Audit.created_at).label("day"),
            func.count().label("count")
        ).group_by("day").order_by("day")
    ).all()
    return [{"day": r.day.date() if isinstance(r.day, datetime) else r.day, "count": r.count} for r in results] # type: ignore

@router.get("/by-schema", summary="Audit logs grouped by schema")
def audit_by_schema(db: Annotated[Session, Depends(get_db)]):
    """Returns audit counts grouped by schema."""
    results = db.exec(
        select(
            Schema.id,
            Schema.title,
            func.count(col(AuditResult.id)).label("count")
        )
        .join(AuditResult, col(AuditResult.schema_id) == Schema.id)
        .group_by(col(Schema.id), Schema.title)
        .order_by(func.count(col(AuditResult.id)).desc())
    ).all()
    return [{"schema_id": r.id, "schema_title": r.title, "count": r.count} for r in results] # type: ignore

@router.get("/by-endpoint", summary="Audit logs grouped by endpoint")
def audit_by_endpoint(db: Annotated[Session, Depends(get_db)]):
    """Returns audit counts grouped by endpoint."""
    results = db.exec(
        select(
            Endpoint.id,
            Endpoint.path,
            Endpoint.method,
            func.count(col(AuditResult.id)).label("count")
        )
        .join(AuditResult, col(AuditResult.endpoint_id) == Endpoint.id)
        .group_by(col(Endpoint.id), Endpoint.path, Endpoint.method)
        .order_by(func.count(col(AuditResult.id)).desc())
    ).all()
    return [
        { "endpoint_id": r.id, "path": r.path, "method": r.method, "count": r.count}  # type: ignore
        for r in results
    ]


@router.get("/by-endpoint/{endpoint_id}", summary="Fetch audits by endpoint ID")
def audits_by_endpoint_id(
    endpoint_id: UUID,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Returns all audits for a given endpoint ID within the last X days (default 7)."""
    min_date = datetime.utcnow() - timedelta(days=days)
    results = db.exec(
        select(
            AuditResult,
            Audit.query,
            AuditResult.result_count,
            AuditResult.schema_id,
            AuditResult.endpoint_id,
            Audit.id.label("audit_id"),
            Audit.created_at
        )
        .join(Audit, AuditResult.audit_id == Audit.id)
        .where(
            AuditResult.endpoint_id == endpoint_id,
            Audit.created_at >= min_date
        )
        .order_by(col(Audit.created_at).desc())
    ).all()
    if not results:
        raise HTTPException(status_code=404, detail="No audits found for this endpoint in the given date range")
    return [
        {
            "audit_id": r.audit_id,
            "query": r.query,
            "result_count": r.result_count,
            "schema_id": r.schema_id,
            "endpoint_id": r.endpoint_id,
            "timestamp": r.created_at,
        }
        for r in results
    ]

@router.get("/by-schema/{schema_id}", summary="Fetch audits by schema ID")
def audits_by_schema_id(
    schema_id: UUID,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Returns all audits for a given schema ID within the last X days (default 7)."""
    min_date = datetime.utcnow() - timedelta(days=days)
    results = db.exec(
        select(
            AuditResult,
            Audit.query,
            AuditResult.result_count,
            AuditResult.schema_id,
            AuditResult.endpoint_id,
            Audit.id.label("audit_id"),
            Audit.created_at
        )
        .join(Audit, AuditResult.audit_id == Audit.id)
        .where(
            AuditResult.schema_id == schema_id,
            Audit.created_at >= min_date
        )
        .order_by(col(Audit.created_at).desc())
    ).all()
    if not results:
        raise HTTPException(status_code=404, detail="No audits found for this schema in the given date range")
    return [
        {
            "audit_id": r.audit_id,
            "query": r.query,
            "result_count": r.result_count,
            "schema_id": r.schema_id,
            "endpoint_id": r.endpoint_id,
            "timestamp": r.created_at,
        }
        for r in results
    ]
