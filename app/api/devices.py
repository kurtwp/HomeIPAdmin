"""Device CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, verify_api_key
from app.api.schemas import DeviceCreate, DeviceResponse, DeviceUpdate
from app.models.device import Device

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=list[DeviceResponse])
def list_devices(
    category: str | None = Query(None, description="Filter by device type name"),
    search: str | None = Query(None, description="Search by name, model, or serial"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """List devices with optional filters."""
    q = db.query(Device).options(
        joinedload(Device.device_type),
        joinedload(Device.ip_addresses),
        joinedload(Device.tags),
    )
    if category:
        q = q.join(Device.device_type).filter(Device.device_type.has(name=category))
    if search:
        q = q.filter(
            Device.name.contains(search)
            | Device.model.contains(search)
            | Device.serial_number.contains(search)
        )
    devices = q.order_by(Device.name).offset(offset).limit(limit).all()
    return [DeviceResponse.from_model(d) for d in devices]


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Get a single device by ID."""
    device = (
        db.query(Device)
        .options(
            joinedload(Device.device_type),
            joinedload(Device.ip_addresses),
            joinedload(Device.tags),
        )
        .get(device_id)
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceResponse.from_model(device)


@router.post("", response_model=DeviceResponse, status_code=201)
def create_device(
    body: DeviceCreate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Create a new device."""
    device = Device(**body.model_dump())
    db.add(device)
    db.flush()
    db.refresh(device)
    return DeviceResponse.from_model(device)


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    body: DeviceUpdate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Update an existing device."""
    device = db.query(Device).get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    db.flush()
    db.refresh(device)
    return DeviceResponse.from_model(device)


@router.delete("/{device_id}", status_code=204)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Delete a device."""
    device = db.query(Device).get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(device)
