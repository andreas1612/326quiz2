import subprocess
import os

ALPHABETS = {
    '1':  'abcdefghijklmnopqrstuvwxyz',
    '2':  'abcdefghijklmnopqrstuvwxyz ',
    '3':  ' abcdefghijklmnopqrstuvwxyz',
}

COMMON_WORDS = ['the','and','you','are','for','key','aes','secret','token', 'stop','congratulations','solution']

def score_text(text):
    t = text.lower()
    return sum(1 for w in COMMON_WORDS if w in t)

def caesar_decrypt(text, key, alpha):
    res = ""
    for c in text:
        if c in alpha:
            res += alpha[(alpha.index(c) - key) % len(alpha)]
        else:
            res += c
    return res

pwd = "4072023370"
in_file = "problem_file.enc"

# Get all ciphers from openssl
r = subprocess.run(["openssl", "list", "-cipher-commands"], capture_output=True, text=True)
ciphers = r.stdout.split()

print(f"Testing {len(ciphers)} ciphers...")

for cipher in ciphers:
    if cipher.startswith("-"): cipher = cipher[1:]
    for kdf in [["-pbkdf2"], ["-md", "md5"], ["-md", "sha1"], []]:
        cmd = ["openssl", "enc", "-d", f"-{cipher}"] + kdf + ["-pass", f"pass:{pwd}", "-in", in_file, "-provider", "default", "-provider", "legacy"]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            text = r.stdout.decode('utf-8', errors='replace')
            # Check for English or Caesar English
            for alpha in ALPHABETS.values():
                for shift in range(len(alpha)):
                    dt = caesar_decrypt(text, shift, alpha)
                    if score_text(dt) >= 2:
                        print(f"SUCCESS! Cipher: {cipher}, KDF: {kdf}, Shift: {shift}")
                        print(f"Plaintext: {dt}")
                        with open("final_answer.txt", "w") as f:
                            f.write(dt)
                        exit(0)
