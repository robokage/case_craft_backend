import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


class AuthUtils:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

    def __init__(self) -> None:
        self.secret_key = os.getenv("SECRET_KEY", "")
        self.jwt_algo = os.getenv("JWT_ALGORITHM", "")
        self.token_exp_time = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "0"))


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