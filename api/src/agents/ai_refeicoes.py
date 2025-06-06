import json
import os
import random

import pandas as pd
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain_core.output_parsers import JsonOutputParser
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# Configura sua chave da API Gemini
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")


class AlimentosRefeicao(BaseModel):
    nome: str = Field(description="Nome do alimento")
    quantidade: int = Field(description="Quantidade em gramas do alimento selecionado")
    calorias: int = Field(
        description="Quantidade de calorias da porção do alimento selecionado"
    )
    proteinas: int = Field(
        description="Quantidade de proteínas da porção do alimento selecionado"
    )
    carboidratos: int = Field(
        description="Quantidade de carboidratos da porção do alimento selecionado"
    )
    gordura: int = Field(
        description="Quantidade de gorduras da porção do alimento selecionado"
    )
    unidade_medida: str = Field(
        description="Unidade de medida da porção do alimento selecionado"
    )
    mensagem: str = Field(
        description="Mensagem explicativa sobre o alimento selecionado"
    )


class GeradorDeRefeicao(BaseTool):
    name: str = "GeradorDeRefeicao"
    description: str = (
        "Deve retornar uma refeicao baseado nas preferencias do usuario informado, sempre em portugues"
    )

    def _run(
        self,
        objetivo: str,
        peso: float,
        gasto_calorico_basal: float,
        refeicao: str,
        preferencias: list,
        maximo_calorias_por_refeicao: float,
    ):
        df = pd.read_csv("csvAlimentos.csv")
        csv_text = df.to_csv(index=False)

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", temperature=0.4, api_key=google_api_key
        )
        parser = JsonOutputParser(pydantic_object=AlimentosRefeicao)

        template = PromptTemplate(
            template="""
                    Você é um nutricionista que possue um conhecimento vasto em dietas flexíveis com alimentos variados. Baseado na seguinte tabela de alimentos:

                    {csv_text}

                    E nas informações fornecidas:
                    - Objetivo: {objetivo}
                    - Peso: {peso} kg
                    - Gasto calórico basal: {gasto_calorico_basal} kcal
                    - Refeição: {refeicao}
                    - Preferencia: {preferencias}
                    - Máximo de calorias por refeição: {maximo_calorias_por_refeicao} kcal

                    Os valores da base de dados estão todos em 100 gramas, faça a conta quando necessário para receitar menos quantidade, faça a divisão corretamente.

                    Retorne uma lista JSON com alimentos sugeridos para essa refeição, considerando as preferencias alimentares do usuario, **use itens da tabela acima mas mescle com as melhores opções que conhece, busando a harmonia entre os alimentos da refeição**.

                    Dentre as preferências, escolha a que mais se adeque ao momento da refeição informada
                    quando {refeicao} for Café da manhã, o horário do dia é pela manhã
                    quando {refeicao} for almoco, o horário do dia é pela tarde
                    quando {refeicao} for jantar, o horário do dia é pela noite

                    Sempre varie nas sugestões

                    Retorne uma fonte de proteínas, uma fonte de carboidratos, legumes e verduras, e uma fonte de gorduras.

                    Cada item deve conter: nome, quantidade, calorias (calorias no banco são KCAL), proteinas, carboidratos, gordura, unidade de medida, e uma mensagem de explicação, retornando o porque da escolha do alimento escolhido.

                    Mescle os alimentos sugeridos para que eles sejam distribuidos em porções iguais de calorias.

                    Mescle as opções de preferencias alimentares para que eles sejam distribuidos em porções iguais de calorias.

                    Sempre busque variedade na informação da dieta

                    Traduza os nomes para o português.

                    A unidade de medida deve ser separada da quantidade. A quantidade é referente apenas à porção da refeição, e não precisa conter os cálculos de calorias multiplicadas.

                    A refeição completa não pode ultrapassar o máximo de calorias por refeição {maximo_calorias_por_refeicao} kcal, para descobrir a quantidade da dieta, some todas as quantidades de calorias.

                   Você deve retornar a resposta final em uma lista desse formato de saida: Formato de saída:
                    {formato_saida}
                    """,
            input_variables=[
                "objetivo",
                "peso",
                "gasto_calorico_basal",
                "refeicao",
                "preferencias",
                "maximo_calorias_por_refeicao",
            ],
            partial_variables={
                "formato_saida": parser.get_format_instructions(),
                "csv_text": csv_text,
            },
        )
        cadeia = template | llm | parser
        resposta = cadeia.invoke(
            {
                "objetivo": objetivo,
                "peso": peso,
                "gasto_calorico_basal": gasto_calorico_basal,
                "refeicao": refeicao,
                "preferencias": preferencias,
                "maximo_calorias_por_refeicao": maximo_calorias_por_refeicao,
            }
        )

        return resposta
