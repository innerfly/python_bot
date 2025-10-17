from fabric import Connection, task
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("DEPLOY_HOST")
user = os.getenv("DEPLOY_USER")
path = os.getenv("DEPLOY_PATH")

if not host or not user or not path:
    missing = [name for name, val in [("DEPLOY_HOST", host), ("DEPLOY_USER", user), ("DEPLOY_PATH", path)] if not val]
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


@task
def deploy(c):
    conn = Connection(host=host, user=user)

    result = conn.run(f"cd {path} && git pull", hide=False)

    print(f"Ran '{result.command}' on {result.connection.host}, exit={result.exited}\n{result.stdout}")

    return result
