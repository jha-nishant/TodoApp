from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models import Users
from passlib.context import CryptContext
from database import sessionLocal
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt

router = APIRouter(
  prefix='/auth',
  tags=['auth']
)

SECRET_KEY = "1622c043e19ebde49ee2c9fcc7067d25c19fddf8649ae5ca7a050d883c97c8fc"
ALGORITHM = "HS256"

class CreateUserRequest(BaseModel):
  username: str
  email: str
  first_name: str
  last_name: str
  password: str
  role: str

class Token(BaseModel):
  access_token: str
  token_type: str

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

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# path of the token API
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

#! password: test1234
def authenticate_user(username: str, password:str, db: db_dependency):
  user = db.query(Users).filter(Users.username == username).first()
  if not user:
    return False
  if not bcrypt_context.verify(password, user.hashed_password):
    return False
  return user

def create_access_token(username: str, user_id: str, expires_delta: timedelta):
  encode = { "sub": username, "id": user_id }
  #expires = datetime.utcnow() #Depricated
  expires = datetime.now(timezone.utc) + expires_delta
  encode.update({ 'exp': expires })
  return jwt.encode(claims = encode, key = SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token:Annotated[str, Depends(oauth2_bearer)]):
  try:
    payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get('sub')
    user_id: int = payload.get('id')
    if username is None or user_id is None:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
    return { 'username': username, 'id': user_id }
  except JWTError:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
  #? create_user_model = Users(**createUserRequest.model_dump()) wont work because
  #? CreateUserRequest has password while Users has hashed_password 
  create_user_model = Users(
    email=create_user_request.email,
    username=create_user_request.username,
    first_name=create_user_request.first_name,
    last_name=create_user_request.last_name,
    role=create_user_request.role,
    hashed_password=bcrypt_context.hash(create_user_request.password),
    is_active=True
  )

  db.add(create_user_model)
  db.commit()

@router.post("/token", response_model=Token)
async def login_fot_access_token(db:db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
  user = authenticate_user(form_data.username, form_data.password, db)
  if not user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

  token = create_access_token(user.username, user.id, timedelta(minutes = 20))
  return { 'access_token': token, 'token_type': 'bearer' }
