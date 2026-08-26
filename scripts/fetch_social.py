import json
import os
from datetime import datetime, timezone


OUT = "data/social.json"


def load():

    if not os.path.exists(
        OUT
    ):
        return {
            "items": []
        }

    with open(
        OUT,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def main():

    data = load()

    if "items" not in data:
        data["items"] = []

    data["generated_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        OUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        "Social monitoring storage ready."
    )


if __name__ == "__main__":
    main()
