## 

FROM python:3.11
WORKDIR /app

# For pyaudio in requirements.txt
RUN apt-get update
RUN apt-get install -y portaudio19-dev
# Copy and install requirements early so they don't mess with caching
COPY ./requirements.txt ./
RUN pip install -r requirements.txt


# Copy the rest of the files
# COPY ./data ./data
# COPY ./djangoBackend ./backend
# COPY ./text_to_query ./text_to_query
COPY ./ ./backend
COPY ./milkOligoDB ./backend/djangoBackend/backend/milkOligoDB
COPY ./llama_service.py ./backend/djangoBackend/backend/llama_service.py

WORKDIR /app/backend/djangoBackend
ENTRYPOINT uvicorn djangoBackend.asgi:application --host 0.0.0.0 --port 8000 --reload