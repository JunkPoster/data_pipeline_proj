FROM python:3.10-slim

# Working directory
WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run entrypoint
CMD ["python", "run_docker.py"]

# Default Entrypoint
ENTRYPOINT ["python", "run_docker.py"]