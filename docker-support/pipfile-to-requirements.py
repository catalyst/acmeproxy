import json
import sys


def parse_pipenv_lock_section(section_data):
    for req_name, req_data in section_data.items():
        if req_data.get("version") and req_data.get("hashes"):
            hashes = " ".join(f"--hash={hash}" for hash in req_data.get("hashes"))
            yield f"{req_name}{req_data['version']} {hashes}"


def main():
    for name in sys.argv[1:]:
        with open(name, "r") as f:
            data = json.load(f)
            for section in ["default", "develop"]:
                for version_spec in parse_pipenv_lock_section(data.get(section, {})):
                    print(version_spec)  # noqa: T001


if __name__ == "__main__":
    main()
