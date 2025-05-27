import json
import os
import random

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain_core.output_parsers import JsonOutputParser
from langchain_experimental.agents import create_pandas_dataframe_agent
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


class EntradaImagem(BaseModel):
    data: str
    mime_type: str


class InterpretadorDeImagem:
    def interpretar(self, image_part: EntradaImagem):
        genai.configure(api_key=google_api_key)
        llm = genai.GenerativeModel(model_name="gemini-2.0-flash")

        template = """
                    Você é um nutricionista. Analise visualmente o conteúdo da imagem do prato de comida fornecida.
                        Liste os alimentos detectados e estime as calorias totais de forma aproximada.
                        Retorne apenas um JSON com esta estrutura:
                        [
                        {
                        Cada item deve conter: nome, quantidade, calorias (calorias no banco são KCAL), proteinas, carboidratos, gordura, unidade de medida, e uma mensagem de explicação, retornando o porque da escolha do alimento escolhido.
                            "nome": "nome_do_alimento",
                            "quantidade": "quantidade_do_alimento",
                            "calorias": "calorias_do_alimento",
                            "proteinas": "proteinas_do_alimento",
                            "carboidratos": "carboidratos_do_alimento",
                            "gordura": "gordura_do_alimento",
                            "unidade_de_medida": "unidade_de_medida_do_alimento",
                            "mensagem": "mensagem_de_explicacao"},
                        ...
                        ]
                        Retorne somente o JSON. Nada mais.
                        """
        response = llm.generate_content(
            [
                template,
                image_part,
            ],
            generation_config={"temperature": 0.4},
            stream=False,
        )
        response.resolve()  # Garante que a resposta foi totalmente processada

        output_text = ""
        if hasattr(response, "text") and response.text:
            output_text = response.text
        elif (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
        ):
            output_text = response.candidates[0].content.parts[0].text
        else:
            print(
                "Não foi possível extrair o texto da resposta. Estrutura da resposta:"
            )
            print(response)
            raise ValueError("Estrutura de resposta inesperada da API Gemini.")

        print("\n--- Saída Bruta do Modelo ---")
        print(output_text)

        # Tenta limpar e parsear o JSON
        # O modelo pode, às vezes, envolver o JSON em ```json ... ```
        cleaned_output = output_text.strip()
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]  # Remove ```json
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]  # Remove ``` no final
        elif cleaned_output.startswith("```"):  # Caso seja apenas ```
            cleaned_output = cleaned_output[3:]
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]

        cleaned_output = cleaned_output.strip()  # Remove espaços em branco extras

        print("\n--- Saída JSON Parseada ---")
        try:
            parsed_json = json.loads(cleaned_output)
            # Imprime de forma bonita, com indentação e suporte a caracteres UTF-8

        except json.JSONDecodeError as e:
            print(f"Erro: O modelo não retornou um JSON válido. {e}")
            print("Saída recebida que causou o erro:")
            print(cleaned_output)
        except Exception as e_parse:
            print(f"Um erro inesperado ocorreu durante o parse do JSON: {e_parse}")
        return parsed_json
