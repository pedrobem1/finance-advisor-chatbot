FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

COPY backend/requirements-lambda.txt ${LAMBDA_TASK_ROOT}/
RUN python3.12 -m pip install --no-cache-dir --target "${LAMBDA_TASK_ROOT}" -r requirements-lambda.txt

COPY backend/app ${LAMBDA_TASK_ROOT}/app
COPY backend/data/rag ${LAMBDA_TASK_ROOT}/data/rag
COPY knowledge /var/knowledge

CMD ["app.main.lambda_handler"]
