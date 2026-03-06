import hashlib
import sys

def crack_passphrase():
    target_hash = ""
    with open("hash.txt", "r") as f:
        target_hash = f.read().strip()
        
    print(f"[*] Target Hash: {target_hash}")
    
    # We know from Step 1 that the passphrase is "id concatenated with two magic digits"
    base_id = "123456"
    
    # Try all 2-digit combinations (00-99)
    # The wording "concatenated" usually means append, but we also try prepend.
    # The hash could be computed with or without a trailing newline.
    
    for i in range(100):
        digits = f"{i:02d}"  # Zero-padded (00-99)
        variants = [
            f"{base_id}{digits}",          # append
            f"{base_id}{digits}\n",        # append with newline
            f"{digits}{base_id}",          # prepend
            f"{digits}{base_id}\n",        # prepend with newline
            f"{base_id}{i}",               # append unpadded
            f"{base_id}{i}\n",             # append unpadded with newline
            f"{i}{base_id}",               # prepend unpadded
            f"{i}{base_id}\n"              # prepend unpadded with newline
        ]
        
        for p in variants:
            h = hashlib.sha256(p.encode('utf-8')).hexdigest()
            if h == target_hash:
                print(f"[+] SUCCESS! Found passphrase: {p.strip()}")
                print(f"    (Used exact string: {repr(p)})")
                with open("passphrase.txt", "w") as out:
                    out.write(p.strip())  # Save just the clean password without newline for later steps
                return p.strip()
                
    print("[-] Failed to crack passphrase. Target might not be SHA256 or ID+digits.")
    return None

if __name__ == "__main__":
    pw = crack_passphrase()
    if pw:
        # Save as Token 2 (8-10 chars)
        if 8 <= len(pw) <= 10:
            print(f"[*] Found Token 2: {pw}")
            with open("answer.txt", "a") as out:
                out.write(f"Token 2: {pw}\n")
        else:
            print(f"[*] Password {pw} is length {len(pw)}, maybe not Token 2.")
