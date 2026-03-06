import subprocess
import itertools
import hashlib

tokens = ["nsgjr", "12345667", "4072023370", "123456"]
passwords = set(tokens)

# Add all permutations of tokens (concat)
for i in range(2, 5):
    for perm in itertools.permutations(tokens, i):
        passwords.add("".join(perm))
        passwords.add("_".join(perm))
        passwords.add("-".join(perm))

print(f"Testing {len(passwords)} password combinations...")

def run_openssl(pwd):
    for algo in ["aes-256-cbc", "aes-128-cbc", "des-ede3-cbc", "aria-256-cbc"]:
        for pbkdf2 in [True, False]:
            for md in ["sha256", "md5"]:
                cmd = ["openssl", "enc", f"-{algo}", "-d", "-pass", f"pass:{pwd}", "-in", "problem_file.enc"]
                if pbkdf2: cmd.append("-pbkdf2")
                cmd.extend(["-md", md])
                
                res = subprocess.run(cmd, capture_output=True)
                if res.returncode == 0:
                    try:
                        out = res.stdout.decode('utf-8')
                        if any(c.isalpha() for c in out):
                            print(f"[+] SUCCESS! pwd={pwd} algo={algo} pbkdf2={pbkdf2} md={md}")
                            print(out[:200])
                            return True
                    except:
                        pass
    return False

for p in passwords:
    if run_openssl(p):
        print("Done!")
        import sys
        sys.exit(0)

print("All combinations failed.")
