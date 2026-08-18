# K8TRE egress creation service

This is a service to create egress requests inside the TRE. It takes the files from
the JupyterServer extension, uploads them to an S3 bucket and sends out an email 
with a link to the request in the egress request checker.

## Structure
This service consists of 3 endpoints:

create-egress - creates a session id for the egress request
upload-file - uploads a file
request-egress - generates a token and sends an email for the egress request

upload-file and request-egress require a session id created in create-egress to work.

The workflow is:
-create-egress
-foreach file:
    --upload-file
-request-egress

## Setup
### Requirements
This is designed to work with a JupyterHub instance with the k8tre-egress-jupyter
extension installed. It also needs either AWS S3 access or a compatible alternative 
(e.g. SeaweedFS) 

### To run

1. Create a virtualenv and activate it
2. Install requirements.txt
```
pip install -r requirements.txt
```
3. Copy .env.example to .env and set values appropriately
4. Run
```
uvicorn app.main:app --reload
```

### To run tests
```
pytest
```