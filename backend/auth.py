import hashlib
import os
from datetime import datetime, timedelta, timezone
from jwt import encode, decode, InvalidTokenError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import yield_database_session_instance
from models import UserAccount

JWT_SECRET_SIGNING_KEY = "SUPER_SECRET_KEY_REPLACE_THIS_IN_PRODUCTION_2026"
JWT_CRYPTOGRAPHIC_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRATION_MINUTES = 60 * 24

oauth2_security_scheme = OAuth2PasswordBearer(tokenUrl="authentication/login")


def calculate_password_hash(plain_text_password: str) -> str:
    salt_bytes = os.urandom(16)
    key_bytes = hashlib.pbkdf2_hmac(
        'sha256', 
        plain_text_password.encode('utf-8'), 
        salt_bytes, 
        100000
    )
    return f"pbkdf2_sha256$100000${salt_bytes.hex()}${key_bytes.hex()}"


def verify_user_password(plain_text_password: str, hashed_password: str) -> bool:
    try:
        if not hashed_password or "$" not in hashed_password:
            return False
            
        algorithm_name, iterations_string, salt_hex, key_hex = hashed_password.split('$')
        salt_bytes = bytes.fromhex(salt_hex)
        
        new_key_bytes = hashlib.pbkdf2_hmac(
            'sha256', 
            plain_text_password.encode('utf-8'), 
            salt_bytes, 
            int(iterations_string)
        )
        return new_key_bytes.hex() == key_hex
    except (ValueError, AttributeError):
        return False


def create_access_jwt_token(payload_data: dict) -> str:
    data_to_encode_dictionary = payload_data.copy()
    expiration_date_time = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRATION_MINUTES)
    data_to_encode_dictionary.update({"exp": expiration_date_time})
    
    jwt_encoded_string = encode(
        data_to_encode_dictionary, 
        JWT_SECRET_SIGNING_KEY, 
        algorithm=JWT_CRYPTOGRAPHIC_ALGORITHM
    )
    return jwt_encoded_string


def get_current_authenticated_user(
    security_token_string: str = Depends(oauth2_security_scheme),
    database_session_instance: Session = Depends(yield_database_session_instance)
) -> UserAccount:
    authentication_http_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось валидировать предоставленные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        decoded_payload_dictionary = decode(
            security_token_string, 
            JWT_SECRET_SIGNING_KEY, 
            algorithms=[JWT_CRYPTOGRAPHIC_ALGORITHM]
        )
        telegram_user_identifier: str = decoded_payload_dictionary.get("sub")
        
        if telegram_user_identifier is None:
            raise authentication_http_exception
            
    except InvalidTokenError:
        raise authentication_http_exception
        
    authenticated_user_account_instance = database_session_instance.query(UserAccount).filter(
        UserAccount.telegram_user_identifier == telegram_user_identifier
    ).first()
    
    if authenticated_user_account_instance is None:
        raise authentication_http_exception
        
    return authenticated_user_account_instance
