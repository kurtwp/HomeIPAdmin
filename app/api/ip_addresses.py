"""IP Address CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.api.schemas import IPAddressCreate, IPAddressResponse, IPAddressUpdate
from app.models.ip_address import IPAddress, AssignmentType, IPStatus

router = APIRouter(prefix="/ips", tags=["IP Addresses"])


@router.get("", response_model=list[IPAddressResponse])
def list_ips(
    network_id: int | None = Query(None, description="Filter by network ID"),
    status: str | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search by address or hostname"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """List IP addresses with optional filters."""
    q = db.query(IPAddress)
    if network_id is not None:
        q = q.filter(IPAddress.network_id == network_id)
    if status:
        q = q.filter(IPAddress.status == IPStatus(status))
    if search:
        q = q.filter(
            IPAddress.address.contains(search) | IPAddress.hostname.contains(search)
        )
    ips = q.order_by(IPAddress.address).offset(offset).limit(limit).all()
    return [IPAddressResponse.from_model(ip) for ip in ips]


@router.get("/{ip_id}", response_model=IPAddressResponse)
def get_ip(
    ip_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Get a single IP address by ID."""
    ip = db.query(IPAddress).get(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP address not found")
    return IPAddressResponse.from_model(ip)


@router.post("", response_model=IPAddressResponse, status_code=201)
def create_ip(
    body: IPAddressCreate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Create a new IP address record."""
    data = body.model_dump()
    data["assignment_type"] = AssignmentType(data["assignment_type"])
    data["status"] = IPStatus(data["status"])
    ip = IPAddress(**data)
    db.add(ip)
    db.flush()
    db.refresh(ip)
    return IPAddressResponse.from_model(ip)


@router.put("/{ip_id}", response_model=IPAddressResponse)
def update_ip(
    ip_id: int,
    body: IPAddressUpdate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Update an existing IP address."""
    ip = db.query(IPAddress).get(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP address not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "assignment_type" and value is not None:
            value = AssignmentType(value)
        elif field == "status" and value is not None:
            value = IPStatus(value)
        setattr(ip, field, value)
    db.flush()
    db.refresh(ip)
    return IPAddressResponse.from_model(ip)


@router.delete("/{ip_id}", status_code=204)
def delete_ip(
    ip_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Delete an IP address."""
    ip = db.query(IPAddress).get(ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="IP address not found")
    db.delete(ip)
