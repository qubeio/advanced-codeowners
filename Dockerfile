# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install uv
RUN pip install uv

# Create and activate a virtual environment, then install dependencies
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install .

# Ensure we use the Python from the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Run main.py when the container launches
CMD ["python", "src/main.py"]
