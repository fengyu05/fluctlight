FROM python:3.11-slim

WORKDIR /app/home

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Add the application
ADD fluctlight ./fluctlight
ADD tests ./tests
ADD setup.py ./setup.py
ADD alembic.ini ./alembic.ini

# Install the app
RUN pip install -e .
# Set the default command
CMD ["fluctlight", "start"]
