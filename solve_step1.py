import string
import collections

# Simplified frequency scoring (similar to mastercypher)
COMMON_WORDS = {"the", "and", "that", "have", "for", "not", "with", "you", "this", "but", 
                "magic", "cipher", "code", "flag", "key", "pass", "word", "secret", "message",
                "stop", "hash", "decrypt"}

def score_text(text):
    if not text: return 0
    score = 0
    text_lower = text.lower()
    for word in COMMON_WORDS:
        if f" {word} " in f" {text_lower} ":
            score += 15
    return score

def solve_caesar(ciphertext):
    # Try different alphabet variants.
    # Variant 1: space at start
    alphabets = [
        " " + string.ascii_lowercase,
        string.ascii_lowercase + " "
    ]
    
    best_text = ""
    best_score = -1
    best_shift = 0
    
    for alphabet in alphabets:
        n = len(alphabet)
        for shift in range(1, n):
            res = []
            for char in ciphertext:
                if char in alphabet:
                    idx = alphabet.index(char)
                    new_idx = (idx - shift) % n
                    res.append(alphabet[new_idx])
                else:
                    res.append(char)
            pt = "".join(res)
            s = score_text(pt)
            if s > best_score:
                best_score = s
                best_text = pt
                best_shift = shift
                
    return best_text, best_shift, best_score

if __name__ == "__main__":
    with open("details_file.txt", "r") as f:
        ct = f.read().strip()
        
    print(f"[*] Analyzing details_file.txt (length: {len(ct)})")
    pt, shift, score = solve_caesar(ct)
    
    print(f"\n[+] Best Decryption (Score: {score}, Shift: {shift}):")
    print(pt)
    
    # Extract Token 1 (5 characters at the end)
    # the text says "... submit the first solution to blackboard which is nsgjr"
    parts = pt.split()
    if parts:
        token1 = parts[-1]
        if len(token1) == 5:
            print(f"\n[SUCCESS] Token 1 Found: {token1}")
            with open("answer.txt", "w") as out:
                out.write(f"Token 1: {token1}\n")
            print("[*] Saved Token 1 to answer.txt")
        else:
            print("\n[-] Could not automatically extract 5-char Token 1")
