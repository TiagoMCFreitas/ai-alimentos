import json
import os

import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import Part
from pydantic import BaseModel

# Carrega variáveis de ambiente
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")


class EntradaImagem(BaseModel):
    data: str
    mime_type: str


class InterpretadorDeImagem:
    def interpretar(self, image_part: EntradaImagem):
        # Configura a API do Gemini
        genai.configure(api_key=google_api_key)
        llm = genai.GenerativeModel(model_name="gemini-2.0-flash")

        template = """
        Você é um nutricionista. Analise visualmente o conteúdo da imagem do prato de comida fornecida.
        Liste os alimentos detectados e estime as calorias totais de forma aproximada.

        Retorne apenas um JSON com esta estrutura:
        [
          {
            "nome": "nome_do_alimento",
            "quantidade": quantidade_em_float,
            "calorias": calorias_em_float,
            "proteinas": proteinas_em_float,
            "carboidratos": carboidratos_em_float,
            "gordura": gordura_em_float,
            "unidade_medida": "unidade",
            "mensagem": "mensagem explicativa"
          }
        ]
        Retorne SOMENTE o JSON.
        """

        # ✅ CONVERSÃO CORRETA PARA O FORMATO QUE O GEMINI ACEITA
        imagem_gemini = Part.from_dict(
            {
                "inline_data": {
                    "mime_type": image_part.mime_type,
                    "data": image_part.data,
                }
            }
        )

        print("MIME ENVIADO AO GEMINI:", image_part.mime_type)

        response = llm.generate_content(
            [
                template,
                imagem_gemini,
            ],
            generation_config={"temperature": 0.4},
            stream=False,
        )

        response.resolve()

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
            print("Não foi possível extrair texto da resposta:")
            print(response)
            raise ValueError("Resposta inválida da API Gemini")

        print("\n--- Saída Bruta do Modelo ---")
        print(output_text)

        cleaned_output = output_text.strip()

        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]
        elif cleaned_output.startswith("```"):
            cleaned_output = cleaned_output[3:]
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]

        cleaned_output = cleaned_output.strip()

        print("\n--- Saída JSON Limpa ---")
        print(cleaned_output)

        try:
            parsed_json = json.loads(cleaned_output)
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
            print(cleaned_output)
            raise
