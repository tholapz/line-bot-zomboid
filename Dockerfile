FROM python:3.10-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./main.py /code/

EXPOSE 8000

CMD ["fastapi", "run", "main.py", "--port", "8000"]