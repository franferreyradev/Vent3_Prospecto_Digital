#!/usr/bin/env bash
set -e

API_URL="http://localhost:8000"
OPENAPI_FILE="/tmp/vent3-openapi.json"
OUTPUT_FILE="$(dirname "$0")/../src/api.ts"

echo "Descargando schema OpenAPI desde $API_URL/openapi.json..."

if ! curl --silent --fail "$API_URL/openapi.json" -o "$OPENAPI_FILE"; then
  echo "Error: No se pudo conectar a la API en $API_URL"
  echo "Asegurate de que la API esté corriendo: uvicorn src.main:app --reload"
  exit 1
fi

echo "Generando tipos TypeScript..."
npx openapi-typescript "$OPENAPI_FILE" -o "$OUTPUT_FILE"

echo "Tipos generados correctamente en $OUTPUT_FILE"
