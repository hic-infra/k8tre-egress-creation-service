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

Files are uploaded into the S3 bucket as
/{project_id}/{session-id}/{file}.
Once request-egress has been called no more files can be uploaded.
This is enforced by request-egress creating a .done file in the S3 "folder"
upload-file checks for this.
If request-egress is not called on a session id then the bucket is still editable

## Setup
### Requirements
This is designed to work with a JupyterHub instance with the k8tre-egress-jupyter
extension installed. It also needs either AWS S3 access or a compatible alternative 
(e.g. SeaweedFS) 

### To run
#### Natively
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

#### With docker
1. Copy .env.example to .env and set values appropriately
2. ```docker build -t hic-egress-creation-service .```
3. ```docker run -p 8080:80 hic-egress-creation-service```

### To run tests
```
pytest
```