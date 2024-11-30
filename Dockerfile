FROM python:3.9-slim
WORKDIR /app
COPY . /app
ENV PYTHONPATH /app
RUN pip install --no-cache-dir -r requirements.txt
RUN python setup.py install

EXPOSE 5000
CMD ["python", "src/app.py"]