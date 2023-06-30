FROM python:3.11
WORKDIR /opt/waterbowl
COPY src/ api/
ENV PYTHONPATH "/opt/waterbowl:/opt/waterbowl/api:/opt/waterbowl/api/waterbowl_api"
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "api.waterbowl_api.app:app", "--host", "0.0.0.0", "--port", "80"]
