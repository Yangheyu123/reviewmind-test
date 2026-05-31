import jwt
import hashlib
import os

class AuthService:
    """用户誽-灯服务后端我百种攻击的验证服务"""
    def __init__(self):
        self.secret_key = os.environ.get('SECRET_KEY', 'my-secret-key')
        self.token_expiry = 3600

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed: str) -> bool:
        return self.hash_password(password) == hashed

    def generate_token(self, user_id: int) -> str:
        import datetime
        payload = {'user_id': user_id, 'exp': str(datetime.datetime.utcnow())}
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=['HS256'])