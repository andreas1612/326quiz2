import hashlib

target = "bb651bbbcfc6cdf592964bdd4eddea21b81d674d0716ec699d6f2c8e5055628f30b0bf4e9f71b04a76438a6d71f047e973f94f82f7eec8ae2f26af31282df24d"
base = "1064782"

for i in range(1000):
   digits = f"{i:03d}"
   pwd = base + digits
   if hashlib.sha512(pwd.encode()).hexdigest() == target:
       print(f"FOUND: {pwd}")
       with open("passphrase.txt", "w") as f:
           f.write(pwd)
       exit(0)
   pwd_nl = pwd + "\n"
   if hashlib.sha512(pwd_nl.encode()).hexdigest() == target:
       print(f"FOUND (with newline): {pwd}")
       with open("passphrase.txt", "w") as f:
           f.write(pwd_nl)
       exit(0)
print("Not found")
