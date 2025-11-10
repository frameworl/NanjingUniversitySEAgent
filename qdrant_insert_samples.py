import os
import random
import uuid
from typing import List

from qdrant_utils import insert_points, ensure_collection


def gen_vector(size: int) -> List[float]:
    return [random.random() for _ in range(size)]


def main():
    size = int(os.environ.get("QDRANT_VECTOR_SIZE", "1024"))
    ensure_collection(size=size, distance="cosine")
    items = []
    for i in range(5):
        items.append({
            "id": str(uuid.uuid4()),
            "vector": gen_vector(size),
            "payload": {"title": f"流程样例-{i}", "phase": "demo", "source": "seed"},
        })
    resp = insert_points(items)
    print(f"upserted={resp.get('upserted')} status={resp.get('operation')}")


if __name__ == "__main__":
    main()