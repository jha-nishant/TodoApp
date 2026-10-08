from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from models import Todos
from database import sessionLocal
from starlette import status
from .auth import get_current_user
import logging

router = APIRouter(
  prefix="/todos",
  tags=['todos']
)

#? No, you don't need to write __enter__/__exit__ yourself. 
#? The yield plus try/finally is the standard FastAPI dependency pattern. 
#? FastAPI wraps the generator in a context manager and runs the code after yield once the response is done, even if the endpoint raises.
def get_db():
  db = sessionLocal()
  try:
    yield db
  finally:
    db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# Get the uvicorn error logger
logger = logging.getLogger("uvicorn.error")

class TodoRequest(BaseModel):
  title: str = Field(min_length = 3)
  description: str = Field(min_length = 3, max_length=100)
  priority: int = Field(gt=0, lt=6)
  complete: bool

@router.get("/")
async def get_all(db: db_dependency):
  """
  get all todos
  """
  return db.query(Todos).all()

@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def get_by_id(db: db_dependency, todo_id: int = Path(gt=0)):
  """
  get Todo by id
  """

  #? Another was to do the same thing. This useful when te comparison is on some other field other that id
  #? todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
  todo_model = db.get(Todos, todo_id)
  if todo_model is not None:
    return todo_model
  return HTTPException(status_code=404, detail="todo not found")
 
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(user:user_dependency, db: db_dependency, todo_request: TodoRequest):
  """
  Create a new Todo
  """

  #? Without the **, you'd be passing the whole dict as a single positional argument, and Todos would fail or misbehave because it expects keyword arguments for its columns.
  #? It saves you from writing out every field by hand, and it keeps working if you add fields to the request model later. (The single * does the same thing for lists/tuples, unpacking them into positional arguments.)
  
  #? **todo_request.dict() to **todo_request.model_dump()
  
  #? Dependency 401: the dependency runs before the endpoint body. If the 401 comes from the dependency, the endpoint never runs, 
  #? so your logger and print never fire. That happens when the Authorization: Bearer <token> header is missing or the token is invalid or expired
  
  logger.error(f'user: {user}')
  if user is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
  todo_model = Todos(**todo_request.model_dump(), owner_id=user.get('id'))
  db.add(todo_model)
  db.commit()

@router.put("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: db_dependency,
                      todo_request: TodoRequest,
                      todo_id: int = Path(gt=0)):
  """
  Update Toto
  """

  #! THIS IS RISKY, it bypasses SQLAlchemy attributes instrumentation which notices that the object is dirty
  #! It is possible that it wont save anything
  #? Copy all fields from todo_request into todo_model
  #? todo_model.__dict__.update(todo_request.__dict__)
  #? Otherwise we have to copy 1 by 1
  #? 3rd option is for


  #? todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
  todo_model = db.get(Todos, todo_id)
  if todo_model is None:
    raise HTTPException(status_code=404, details="Todo not found")
  
  # Copy all fields from todo_request into todo_model
  for key, value in todo_request.model_dump().items():
    setattr(todo_model, key, value)
  db.add(todo_model)
  db.commit()

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
  todo_model = db.get(Todos, todo_id)
  if todo_model is None:
    raise HTTPException(status_code=404, detail="Todo not found")
  type(todo_model)
  db.delete(todo_model)
  db.commit()

