"""Tag CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.api.schemas import TagCreate, TagResponse
from app.models.tag import Tag

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("", response_model=list[TagResponse])
def list_tags(
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """List all tags."""
    tags = db.query(Tag).order_by(Tag.name).all()
    return [TagResponse.from_model(t) for t in tags]


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Get a single tag by ID."""
    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return TagResponse.from_model(tag)


@router.post("", response_model=TagResponse, status_code=201)
def create_tag(
    body: TagCreate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Create a new tag."""
    tag = Tag(**body.model_dump())
    db.add(tag)
    db.flush()
    db.refresh(tag)
    return TagResponse.from_model(tag)


@router.delete("/{tag_id}", status_code=204)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Delete a tag."""
    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
