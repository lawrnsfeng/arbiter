import boto3
import httpx
import paramiko
from redis import Redis


def fetch_holds(base_url: str, member: str) -> list:
    with httpx.Client(base_url=base_url) as http:  # expect: R8
        reply = http.get(f"/members/{member}/holds")
        reply.raise_for_status()
        return reply.json()


def upload_cover(isbn: str, image: bytes) -> None:
    store = boto3.client("s3")  # expect: R8
    store.put_object(Bucket="covers", Key=f"{isbn}.jpg", Body=image)


def count_waiting(url: str, isbn: str) -> int:
    queue = Redis.from_url(url)  # expect: R8
    try:
        return queue.llen(f"waitlist:{isbn}")
    finally:
        queue.close()


def sync_branch(host: str) -> None:
    shell = paramiko.SSHClient()  # expect: R8
    shell.load_system_host_keys()
    shell.connect(host)
    shell.exec_command("catalogue-sync")


def renew(http, loan_id: str) -> None:  # expect-llm: R8
    http.post(f"/loans/{loan_id}/renew").raise_for_status()


def count_visit(url: str) -> None:
    counter = Redis.from_url(url)  # expect-llm: R8
    counter.incr("visits")
