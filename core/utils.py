import hashlib


def generate_hash(*args):
    raw = "_".join(str(a) for a in args)
    return hashlib.sha256(raw.encode()).hexdigest()
