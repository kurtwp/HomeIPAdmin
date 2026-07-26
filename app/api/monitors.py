"""Uptime monitor CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.api.schemas import MonitorCreate, MonitorResponse, MonitorUpdate
from app.models.uptime_monitor import MonitoredHost

router = APIRouter(prefix="/monitors", tags=["Uptime Monitors"])


@router.get("", response_model=list[MonitorResponse])
def list_monitors(
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """List all monitored hosts."""
    hosts = db.query(MonitoredHost).order_by(MonitoredHost.name).all()
    return [MonitorResponse.from_model(h) for h in hosts]


@router.get("/{monitor_id}", response_model=MonitorResponse)
def get_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Get a single monitor by ID."""
    host = db.query(MonitoredHost).get(monitor_id)
    if not host:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return MonitorResponse.from_model(host)


@router.post("", response_model=MonitorResponse, status_code=201)
def create_monitor(
    body: MonitorCreate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Create a new uptime monitor."""
    host = MonitoredHost(**body.model_dump())
    db.add(host)
    db.flush()
    db.refresh(host)
    return MonitorResponse.from_model(host)


@router.put("/{monitor_id}", response_model=MonitorResponse)
def update_monitor(
    monitor_id: int,
    body: MonitorUpdate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Update an existing monitor."""
    host = db.query(MonitoredHost).get(monitor_id)
    if not host:
        raise HTTPException(status_code=404, detail="Monitor not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(host, field, value)
    db.flush()
    db.refresh(host)
    return MonitorResponse.from_model(host)


@router.delete("/{monitor_id}", status_code=204)
def delete_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Delete a monitor."""
    host = db.query(MonitoredHost).get(monitor_id)
    if not host:
        raise HTTPException(status_code=404, detail="Monitor not found")
    db.delete(host)
