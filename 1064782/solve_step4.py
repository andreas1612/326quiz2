import subprocess
import os
import string

def decrypt_problem():
    with open("decrypted_key.txt", "r") as f:
        aes_key = f.read().strip()
    with open("passphrase.txt", "r") as f:
        passphrase = f.read().strip()
        
    print(f"[*] AES Key: {aes_key}")
    print(f"[*] Passphrase: {passphrase}")
    print("[*] Target: problem_file.enc")
    
    # Let's write an exhaustive OpenSSL decrypted that checks:
    # 1. aes_key as the password
    # 2. passphrase as the password
    # 3. aes_key as a hex key (-K)
    # Using all algorithms and digests
    
    algorithms = ["aes-256-cbc", "aes-128-cbc", "des-cbc", "des-ede3-cbc"]
    digests = ["sha256", "md5", "sha1"]
    
    # We define a helper that runs the command and checks if the output is valid ASCII
    def try_command(cmd, desc):
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode == 0:
            out = proc.stdout
            if len(out) > 10:
                # check if mostly printable
                printable = sum(1 for c in out if chr(c) in string.printable)
                if printable / len(out) > 0.8:
                    print(f"\n[+] SUCCESS! Method: {desc}")
                    try:
                        text = out.decode('utf-8')
                        print(f"Output:\n{text}")
                        # Extract 104 char token
                        tokens = [t.strip() for t in text.split(" ") if len(t.strip()) == 104]
                        if tokens:
                            print(f"\n[*] Found Token 4: {tokens[0]}")
                            with open("answer.txt", "a") as outf:
                                outf.write(f"Token 4: {tokens[0]}\n")
                        return True
                    except:
                        pass
        return False

    print("[*] Starting exhaustive OpenSSL testing...")
    
    for pwd in [aes_key, passphrase, f"{passphrase}\n"]:
        for algo in algorithms:
            for md in digests:
                for pbkdf2 in [True, False]:
                    for nosalt in [False, True]:
                        cmd = ["openssl", "enc", f"-{algo}", "-d", "-pass", f"pass:{pwd}", "-in", "problem_file.enc"]
                        if pkdf2 := pbkdf2: cmd.append("-pbkdf2")
                        if md: cmd.extend(["-md", md])
                        if nosalt: cmd.append("-nosalt")
                        
                        desc = f"{algo} | md:{md} | pbkdf2:{pbkdf2} | nosalt:{nosalt} | pass:{repr(pwd)}"
                        if try_command(cmd, desc):
                            return
                            
    # Try using -kfile (reads from file, handled newlines differently)
    with open("test_pass.txt", "w") as f: f.write(passphrase)
    with open("test_key.txt", "w") as f: f.write(aes_key)
    for fpath in ["test_pass.txt", "test_key.txt"]:
        for algo in algorithms:
            cmd = ["openssl", "enc", f"-{algo}", "-d", "-kfile", fpath, "-in", "problem_file.enc"]
            desc = f"kfile {fpath} with {algo}"
            if try_command(cmd, desc):
                return
                
    print("\n[-] All standard OpenSSL attempts failed. The file may use a custom derivation or different tool.")

if __name__ == "__main__":
    decrypt_problem()
