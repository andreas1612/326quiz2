import subprocess
import string
import re

with open("/home/andre/win_desktop_copy/quiz2_326/secret-file", "r") as f:
    words = re.findall(r'\b\w+\b', f.read())

words = list(set(words))
words.extend(["4072023370", "123456", "12345667", "nsgjr"])

print(f"[*] Testing {len(words)} words...")
for w in words:
    for algo in ["aes-256-cbc", "aes-128-cbc", "des-ede3-cbc"]:
        cmd = ["openssl", "enc", f"-{algo}", "-d", "-pbkdf2", "-in", "problem_file.enc", "-pass", f"pass:{w}"]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0:
            print(f"[+] SUCCESS! Password is {w} with {algo}")
            print(res.stdout)
