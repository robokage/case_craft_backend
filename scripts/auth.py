import os
import redis
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sympy import N


class AuthUtils:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

    def __init__(self) -> None:
        self.secret_key = os.getenv("SECRET_KEY", "")
        self.jwt_algo = os.getenv("JWT_ALGORITHM", "")
        self.token_exp_time = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "0"))
        config_data = {
            "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
            "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
            "SECRET_KEY": self.secret_key,
        }
        config = Config(environ=config_data)
        self.google_oauth = OAuth(config=config)
        self.google_oauth.register(
            name='google',
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            access_token_url=os.getenv("GOOGLE_TOKEN_URL"),
            access_token_params=None,
            authorize_url=os.getenv("GOGGLE_AUTHORIZATION_URL"),
            authorize_params={"prompt": "consent", 
                              "access_type": "offline", 
                              "scope": os.getenv("GOOGLE_API_SCOPE")},
            api_base_url=os.getenv("GOOGLE_BASE_URL"),
            client_kwargs={"scope": os.getenv("GOOGLE_API_SCOPE")},
            server_metadata_url=os.getenv("GOOGLE_SERVER_METADATA_URL")
        )
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    def create_access_token(self, data: dict, exp_min: int = 0):
        """_summary_

        Args:
            data (dict): _description_
            exp_min (int, optional): _description_. Defaults to 0.

        Returns:
            _type_: _description_
        """
        to_encode = data.copy()
        exp_min = exp_min if exp_min else self.token_exp_time
        expire = (datetime.now() + timedelta(minutes=exp_min)).timestamp()
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.jwt_algo)
    
    def get_current_user_id(self, token: str = Depends(oauth2_scheme)):
        """_summary_

        Args:
            token (str, optional): _description_. Defaults to Depends(oauth2_scheme).

        Raises:
            HTTPException: _description_
            HTTPException: _description_

        Returns:
            _type_: _description_
        """
        user_id = None
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algo])
            if payload:
                user_id = payload.get('public_id')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                detail="Invalid token")
        return user_id
    
    def get_reset_link(self, user_email: str):
        """_summary_

        Args:
            user_email (str): _description_

        Returns:
            _type_: _description_
        """
        token = self.create_access_token(data={"email": user_email})
        reset_link = f"{os.getenv('FRONTEND_URL')}/reset-password?token={token}"
        self.r.setex(f"reset_token:{token}", 930, user_email) 
        return reset_link

    def validate_reset_token(self, token: str):
        """_summary_

        Args:
            token (str): _description_

        Raises:
            HTTPException: _description_
            HTTPException: _description_

        Returns:
            _type_: _description_
        """
        is_valid = self.r.get(f"reset_token:{token}")
        print("???", type(is_valid))
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail="Reset link has expired. Kindly try")
        user_email = None 
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algo])
            if payload:
                user_email = payload.get('email')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                detail="Invalid token")
        return user_email
    
    def delete_reset_token(self, token):
        self.r.delete(f"reset_token:{token}")