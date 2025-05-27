version=":v1"
cd api/src
cp -r agents/* .

echo AI_AGENTS
cd ..
docker build -t ai-agents${version} .
cd src
rm ai_interpretador_imagem.py
rm ai_plano.py
rm ai_refeicoes.py
