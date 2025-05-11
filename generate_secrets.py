import argparse
import re
import secrets
import string
import tomlkit
import jwt
from datetime import datetime, timedelta, UTC
from pathlib import Path

JWT_PLACEHOLDER = re.compile(r"<JWT:([^:]+):([^!]+)=(.*)>")
RAND_PLACEHOLDER = "<RAND>"
PASSWD_PLACEHOLDER = "<PASSWD>"


def generate_jwt(role, iss, secret, exp=(3600 * 24 * 360)):
    payload = {
        "role": role,
        "iss": iss,
        "exp": datetime.now(UTC) + timedelta(seconds=exp),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def generate_random_string(length=32):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_password(master_password=None):
    return master_password if master_password else generate_random_string(16)


def parse_toml_template(template_path):
    return tomlkit.parse(Path(template_path).read_text())


def parse_existing_secrets(secrets_path):
    secrets_path = Path(secrets_path)
    if secrets_path.exists():
        return tomlkit.parse(secrets_path.read_text())
    return tomlkit.document()


def fill_template(template_doc, existing_doc, master_password=None, overwrite=False):
    def recursive_fill(template_node, existing_node):
        if isinstance(template_node, dict):
            for key, value in template_node.items():
                # Recurse into tables and arrays
                if isinstance(value, dict):
                    existing_sub = existing_node.get(key, tomlkit.table()) if isinstance(existing_node,
                                                                                         dict) else tomlkit.table()
                    template_node[key] = recursive_fill(value, existing_sub)
                elif isinstance(value, list):
                    existing_sub = existing_node.get(key, []) if isinstance(existing_node, dict) else []
                    template_node[key] = recursive_fill(value, existing_sub)
                elif isinstance(value, str):
                    # JWT
                    match_jwt = JWT_PLACEHOLDER.fullmatch(value.strip())
                    if match_jwt:
                        role, iss, jwt_secret_key = match_jwt.groups()
                        if not overwrite and key in existing_node:
                            template_node[key] = existing_node[key]
                        else:
                            # jwt_secret = generate_random_string(32)
                            assert jwt_secret_key in template_node, f"jwt_secret_key:{jwt_secret_key} must be defined BEFORE the JWT_PLACEHOLDER"
                            jwt_secret = template_node[jwt_secret_key]
                            template_node[key] = generate_jwt(role, iss, jwt_secret)
                        continue
                    # RAND
                    if value.strip() == RAND_PLACEHOLDER:
                        if not overwrite and key in existing_node:
                            template_node[key] = existing_node[key]
                        else:
                            template_node[key] = generate_random_string(32)
                        continue
                    # PASSWD
                    if value.strip() == PASSWD_PLACEHOLDER:
                        if not overwrite and key in existing_node:
                            template_node[key] = existing_node[key]
                        else:
                            template_node[key] = generate_password(master_password)
                        continue
        elif isinstance(template_node, list):
            for idx, item in enumerate(template_node):
                existing_item = existing_node[idx] if idx < len(existing_node) else tomlkit.table() if isinstance(item,
                                                                                                                  dict) else ""
                template_node[idx] = recursive_fill(item, existing_item)
        return template_node

    return recursive_fill(template_doc, existing_doc)


def main():
    parser = argparse.ArgumentParser(description="Generate .secrets.toml from template.  \n "
                                                 "The 'template' file specifies the toml keys that need to be generated"
                                                 " or updated as random keys, passwords or JWT tokens\n"
                                                 "for passwords, you can  specify a unique master password "
                                                 "with the --master-password flag.")
    parser.add_argument("--template", default=".secrets.toml.tpl", help="Path to template file.")
    parser.add_argument("--output", default=".secrets.toml", help="Path to output file.")
    parser.add_argument("--master-password", default=None, help="Master password to use for <PASSWD> fields.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing values.")
    args = parser.parse_args()

    template_doc = parse_toml_template(args.template)
    existing_doc = parse_existing_secrets(args.output)
    filled_doc = fill_template(template_doc, existing_doc, args.master_password, args.overwrite)
    Path(args.output).write_text(tomlkit.dumps(filled_doc))
    print(f"Generated {args.output} from {args.template}.")


if __name__ == "__main__":
    main()
