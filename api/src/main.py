import base64
import io
import os
import sys

import uvicorn
from agents.ai_interpretador_imagem import InterpretadorDeImagem
from agents.ai_plano import GeradorDePlanoAlimentar
from agents.ai_refeicoes import GeradorDeRefeicao
from auth.auth import VerifyAuth
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
async def post_refeicao(
    preferencias_usuario: PreferenciaUsuario,
):

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
async def post_plano(
    preferencias_usuario: PlanoAlimentar,
):
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
async def post_imagem(imagem: UploadFile = File(...)):
    conteudo = await imagem.read()
    base64_str = base64.b64encode(conteudo).decode("utf-8")

    # Define um mime_type válido. Se content_type for inválido ou application/octet-stream, usa image/jpeg por padrão
    mime_type = imagem.content_type
    if (
        not mime_type
        or mime_type == "application/octet-stream"
        or not mime_type.startswith("image/")
    ):
        # Tenta detectar o tipo pela assinatura do arquivo (magic bytes)
        if conteudo.startswith(b"\xff\xd8\xff"):
            mime_type = "image/jpeg"
        elif conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
            mime_type = "image/png"
        elif conteudo.startswith(b"GIF87a") or conteudo.startswith(b"GIF89a"):
            mime_type = "image/gif"
        elif conteudo.startswith(b"RIFF") and b"WEBP" in conteudo[:20]:
            mime_type = "image/webp"
        else:
            # Fallback para jpeg se não conseguir detectar
            mime_type = "image/jpeg"

    gerarPlano = InterpretadorDeImagem().interpretar(
        image_part={"data": base64_str, "mime_type": mime_type}
    )
    return gerarPlano


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
