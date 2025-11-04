# Usa uma imagem oficial do Python
FROM python:3.10

# Instala o Tesseract OCR e dependências básicas
RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev

# Define o diretório de trabalho
WORKDIR /app

# Copia todos os arquivos do seu repositório para o container
COPY . /app

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pelo Flask/Render
EXPOSE 10000

# Comando padrão para iniciar o servidor com Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
