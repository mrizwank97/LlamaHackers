export PATH="$PATH:/root/.local/bin"

apt-get update
apt-get install -y python3-pip jq
pip3 install --user yq

./bin/ollama serve &

pid=$!

sleep 10

echo "Reading from config.yml"
cat ./config.yml

EMBEDDING_MODEL=$(yq -r '.EMBEDDING.MODEL' ./config.yml)
CHAT_MODEL=$(yq -r '.CHAT.MODEL' ./config.yml)

echo "Pulling embedding model: $EMBEDDING_MODEL"
ollama pull $EMBEDDING_MODEL
echo "Pulling chat model: $CHAT_MODEL"
ollama pull $CHAT_MODEL

wait $pid