import subprocess
import os

def decrypt_aes_key():
    passphrase = ""
    with open("passphrase.txt", "r") as f:
        passphrase = f.read().strip()
        
    print(f"[*] Assumed Passphrase for RSA: {passphrase}")
    
    # Run OpenSSL to decrypt the AES key using the private RSA key and the passphrase
    cmd = [
        "openssl", "pkeyutl", 
        "-decrypt", 
        "-inkey", "private.pem", 
        "-passin", f"pass:{passphrase}",
        "-in", "encryptedKeyAES.txt", 
        "-out", "decrypted_key.txt"
    ]
    
    print(f"[*] Running command: {' '.join(cmd)}")
    
    # Also redirect stderr to stdout to catch errors
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[+] SUCCESS! Decrypted AES key")
        with open("decrypted_key.txt", "r") as f:
            aes_key = f.read().strip()
            # Token 3 is 10 chars
            if len(aes_key) == 10:
                print(f"[*] Found Token 3 (AES Key): {aes_key}")
                with open("answer.txt", "a") as out:
                    out.write(f"Token 3: {aes_key}\n")
            else:
                print(f"[*] Raw AES Key (len {len(aes_key)}): {aes_key}")
                with open("answer.txt", "a") as out:
                    out.write(f"AES Key: {aes_key}\n")
            return aes_key
    else:
        print("[-] FAILED to decrypt AES key")
        print("Error output:\n" + result.stderr)
        return None

if __name__ == "__main__":
    decrypt_aes_key()
