from fabric import Connection, task
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("DEPLOY_HOST")
user = os.getenv("DEPLOY_USER")
path = os.getenv("DEPLOY_PATH")


@task
def deploy(c):
    conn = Connection(host=host, user=user)

    conn.put('.env', path)
    conn.run(f"""
        cd {path} \
         && git pull \
         && python3 -m pip install --upgrade -r requirements.txt \
        && supervisorctl restart python_bot
    """, hide=False)
