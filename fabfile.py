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

    pull = conn.run(f"cd {path} && git pull")

    output = (pull.stdout or "") + (pull.stderr or "")
    lower = output.lower()
    updated = not ("already up to date" in lower or "already up-to-date" in lower)

    if updated:
        restart = conn.run("supervisorctl restart python_bot")
        print(
            f"Git updated. Restarted via supervisor.\n"
            f"pull: exit={pull.exited}\n{pull.stdout}\n"
            f"restart: exit={restart.exited}\n{restart.stdout}"
        )
        return restart
    else:
        print(
            f"No updates from git. Skipping supervisor restart.\n"
            f"pull: exit={pull.exited}\n{pull.stdout}"
        )
        return pull
