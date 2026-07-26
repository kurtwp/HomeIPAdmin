"""Global search endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.api.schemas import (
    DeviceResponse,
    DocResponse,
    IPAddressResponse,
    NetworkResponse,
    SearchResult,
)
from app.models.device import Device
from app.models.documentation import Documentation
from app.models.ip_address import IPAddress
from app.models.network import Network

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResult)
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Global search across networks, IPs, devices, and docs."""
    networks = (
        db.query(Network)
        .filter(Network.name.contains(q) | Network.cidr.contains(q))
        .limit(limit)
        .all()
    )
    ips = (
        db.query(IPAddress)
        .filter(IPAddress.address.contains(q) | IPAddress.hostname.contains(q))
        .limit(limit)
        .all()
    )
    devices = (
        db.query(Device)
        .filter(
            Device.name.contains(q)
            | Device.model.contains(q)
            | Device.serial_number.contains(q)
            | Device.mac_address.contains(q)
        )
        .limit(limit)
        .all()
    )
    docs = (
        db.query(Documentation)
        .filter(Documentation.title.contains(q) | Documentation.body.contains(q))
        .limit(limit)
        .all()
    )
    return SearchResult(
        networks=[NetworkResponse.from_model(n) for n in networks],
        ip_addresses=[IPAddressResponse.from_model(ip) for ip in ips],
        devices=[DeviceResponse.from_model(d) for d in devices],
        docs=[DocResponse.from_model(d) for d in docs],
    )
