"""Documentation CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.api.schemas import DocCreate, DocResponse, DocUpdate
from app.models.documentation import Documentation, DocCategory

router = APIRouter(prefix="/articles", tags=["Documentation"])


@router.get("", response_model=list[DocResponse])
def list_docs(
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """List all documentation articles."""
    docs = db.query(Documentation).order_by(Documentation.title).all()
    return [DocResponse.from_model(d) for d in docs]


@router.get("/{doc_id}", response_model=DocResponse)
def get_doc(
    doc_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Get a single documentation article by ID."""
    doc = db.query(Documentation).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocResponse.from_model(doc)


@router.post("", response_model=DocResponse, status_code=201)
def create_doc(
    body: DocCreate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Create a new documentation article."""
    data = body.model_dump()
    if data.get("category") is not None:
        data["category"] = DocCategory(data["category"])
    doc = Documentation(**data)
    db.add(doc)
    db.flush()
    db.refresh(doc)
    return DocResponse.from_model(doc)


@router.put("/{doc_id}", response_model=DocResponse)
def update_doc(
    doc_id: int,
    body: DocUpdate,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Update an existing documentation article."""
    doc = db.query(Documentation).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "category" and value is not None:
            value = DocCategory(value)
        setattr(doc, field, value)
    db.flush()
    db.refresh(doc)
    return DocResponse.from_model(doc)


@router.delete("/{doc_id}", status_code=204)
def delete_doc(
    doc_id: int,
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Delete a documentation article."""
    doc = db.query(Documentation).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
