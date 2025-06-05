import base64
import io
import os
import sys

import uvicorn
from agents.ai_interpretador_imagem import InterpretadorDeImagem
from agents.ai_plano import GeradorDePlanoAlimentar
from agents.ai_refeicoes import GeradorDeRefeicao
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth.auth import VerifyAuth
app = FastAPI()
from fastapi import Depends

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PreferenciaUsuario(BaseModel):
    objetivo: str
    peso: float
    gasto_calorico_basal: float
    refeicao: str
    preferencias: list
    maximo_calorias_por_refeicao: float

class PlanoAlimentar(BaseModel):
    objetivo: str
    peso: float
    gasto_calorico_basal: float
    preferencias: list
    maximo_calorias_por_refeicao: float



@app.post("/refeicao")
async def post_refeicao(preferencias_usuario: PreferenciaUsuario , token: str = Depends(VerifyAuth().verify())):
    
    gerarRefeicoes = GeradorDeRefeicao().invoke(
        {
            "objetivo": preferencias_usuario.objetivo,
            "peso": preferencias_usuario.peso,
            "gasto_calorico_basal": preferencias_usuario.gasto_calorico_basal,
            "refeicao": preferencias_usuario.refeicao,
            "preferencias": preferencias_usuario.preferencias,
            "maximo_calorias_por_refeicao": preferencias_usuario.maximo_calorias_por_refeicao,
        }
    )
    return gerarRefeicoes


@app.post("/plano")
async def post_plano(preferencias_usuario: PlanoAlimentar, token: str = Depends(VerifyAuth().verify())):
    print(preferencias_usuario)
    gerarPlano = GeradorDePlanoAlimentar().invoke(
        {
            "objetivo": preferencias_usuario.objetivo,
            "peso": preferencias_usuario.peso,
            "gasto_calorico_basal": preferencias_usuario.gasto_calorico_basal,
            "preferencias": preferencias_usuario.preferencias,
            "maximo_calorias_por_refeicao": preferencias_usuario.maximo_calorias_por_refeicao,
        }
    )
    return gerarPlano


@app.post("/processar_imagem")
async def post_imagem(imagem: UploadFile = File(...), token: str = Depends(VerifyAuth().verify())):
    conteudo = await imagem.read()
    base64_str = base64.b64encode(conteudo).decode("utf-8")

    gerarPlano = InterpretadorDeImagem().interpretar(
        image_part={"data": base64_str, "mime_type": imagem.content_type}
    )
    return gerarPlano

class Token(BaseModel):
    token: str
@app.post("/login")
async def login(token : Token):
    auth = VerifyAuth()
    status = {
        "status" : True
    }
    
    return status if auth.login(token.token) else False
    

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
