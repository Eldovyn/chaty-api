import os


def load_key_pair(base_dir: str):
    private_key_path = os.path.join(base_dir, "keys", "private.pem")
    public_key_path = os.path.join(base_dir, "keys", "public.pem")

    with open(private_key_path, "rb") as f:
        private_key = f.read()
    with open(public_key_path, "rb") as f:
        public_key = f.read()

    return private_key, public_key
