"""Network CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.api.schemas import NetworkCreate, NetworkResponse, NetworkUpdate
from app.models.network import Network

router = APIRouter(prefix="/networks", tags=["Networks"])


@router.get("", response_model=list[NetworkResponse])
def list_networks(
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """List all networks."""
    networks = db.query(Network).order_by(Network.name).all()
    return [NetworkResponse.from_model(n) for n in networks]


@router.get("/{network_id}", response_model=NetworkResponse)
def get_network(
    network_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Get a single network by ID."""
    net = db.query(Network).get(network_id)
    if not net:
        raise HTTPException(status_code=404, detail="Network not found")
    return NetworkResponse.from_model(net)


@router.post("", response_model=NetworkResponse, status_code=201)
def create_network(
    body: NetworkCreate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Create a new network."""
    net = Network(**body.model_dump())
    db.add(net)
    db.flush()
    db.refresh(net)
    return NetworkResponse.from_model(net)


@router.put("/{network_id}", response_model=NetworkResponse)
def update_network(
    network_id: int,
    body: NetworkUpdate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Update an existing network."""
    net = db.query(Network).get(network_id)
    if not net:
        raise HTTPException(status_code=404, detail="Network not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(net, field, value)
    db.flush()
    db.refresh(net)
    return NetworkResponse.from_model(net)


@router.delete("/{network_id}", status_code=204)
def delete_network(
    network_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Delete a network."""
    net = db.query(Network).get(network_id)
    if not net:
        raise HTTPException(status_code=404, detail="Network not found")
    db.delete(net)
