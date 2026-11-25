import os
from functools import lru_cache

import boto3


@lru_cache(maxsize=1)
def get_api_key() -> str:
    """Local: variable ALERTS_API_KEY. En AWS: secreto de Secrets Manager (ALERTS_API_KEY_SECRET_ID)."""
    local_key = os.environ.get("ALERTS_API_KEY")
    if local_key:
        return local_key
    secret_id = os.environ["ALERTS_API_KEY_SECRET_ID"]
    response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_id)
    return response["SecretString"]
