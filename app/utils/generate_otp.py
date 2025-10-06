import random
import string


def generate_otp(k):
    karakter = string.ascii_uppercase + string.ascii_lowercase + string.digits
    otp = "".join(random.choices(karakter, k=k))
    return otp
