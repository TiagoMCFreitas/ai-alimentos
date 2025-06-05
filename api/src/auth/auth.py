import redis
import json
from fastapi import Request, HTTPException, status, Depends
class VerifyAuth:
    def __init__(self):

        self.redis = redis.Redis("localhost", 9999)

    def login(self, token):
        if not self.redis.get("usuarios"):
            payload = [
                token
            ]
            self.redis.set("usuarios", json.dumps(payload))
            return payload
        usuarios = json.loads(self.redis.get("usuarios"))
        usuarios.append(token)
        self.redis.set("usuarios", json.dumps(usuarios))
        print("Usuário logado com sucesso!")
        return usuarios
    def verify(self):
        async def __verify(request : Request):
            print(request.headers)
            auth_header = request.headers.get("Authorization")
            print(auth_header)
            if self.redis.get("usuarios"):
                payload = json.loads(self.redis.get("usuarios"))
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token de autenticação inválido"
                    )
                token = auth_header[len("Bearer "):]
                print(token)
                if token in payload:
                    
                    return True
                raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token de autenticação inválido"
                    )
                
        return __verify
        