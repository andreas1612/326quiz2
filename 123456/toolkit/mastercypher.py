import string
import collections
import itertools
import math
import re
import sys
import os
import platform
import subprocess

# =============================================================================
# 1. CONFIGURATION & SCORING ALGORITHMS
# =============================================================================

# Common English words for "Bonus Points"
COMMON_WORDS = {"the", "and", "that", "have", "for", "not", "with", "you", "this", "but", 
                "magic", "cipher", "code", "flag", "key", "pass", "word", "secret", "message"}

# Standard English Letter Frequency (for Chi-Squared)
ENGLISH_FREQ = {
    'a': 0.0817, 'b': 0.0150, 'c': 0.0278, 'd': 0.0425, 'e': 0.1270, 'f': 0.0223,
    'g': 0.0202, 'h': 0.0609, 'i': 0.0697, 'j': 0.0015, 'k': 0.0077, 'l': 0.0403,
    'm': 0.0241, 'n': 0.0675, 'o': 0.0751, 'p': 0.0193, 'q': 0.0010, 'r': 0.0599,
    's': 0.0633, 't': 0.0906, 'u': 0.0276, 'v': 0.0098, 'w': 0.0236, 'x': 0.0015,
    'y': 0.0197, 'z': 0.0007
}

class CryptoSolver:
    def __init__(self, ciphertext):
        # CLEANUP: Remove newlines to treat as one long string
        self.ciphertext = ciphertext.replace("\n", "").replace("\r", "")
        self.results = []
        self.alphabet = self._detect_alphabet(self.ciphertext)
        self.N = len(self.alphabet)
        
        # --- NEW SECTION: Printing Cipher Info at the beginning ---
        print("="*80)
        print("ORIGINAL CIPHER ANALYSIS")
        print("="*80)
        print(f"CIPHERTEXT : {self.ciphertext}")
        print(f"LENGTH     : {len(self.ciphertext)} characters")
        print(f"ALPHABET   : '{self.alphabet}' ({self.N} chars)")
        print("="*80 + "\n")
        
    def _detect_alphabet(self, text):
        """Automatically builds the alphabet based on characters found."""
        base = string.ascii_lowercase
        extras = ""
        # Check for specific separators common in custom ciphers
        if " " in text: extras += " "
        if "," in text: extras += ","
        if "." in text: extras += "."
        if "-" in text: extras += "-"
        
        # If text has Uppercase, add them
        if any(c.isupper() for c in text):
            base += string.ascii_uppercase
        # If text has numbers, add them
        if any(c.isdigit() for c in text):
            base += string.digits
            
        return base + extras

    def score_text(self, text):
        """Calculates a score. Higher is better."""
        if not text: return 0
        score = 0
        text_lower = text.lower()
        
        # 1. Word Matching (High Value)
        for word in COMMON_WORDS:
            if word in text_lower:
                score += 15
        
        # 2. Chi-Squared Frequency Match
        counts = collections.Counter([c for c in text_lower if c in string.ascii_lowercase])
        total_letters = sum(counts.values())
        if total_letters == 0: return 0
        
        chi_score = 0
        for char, expected_pct in ENGLISH_FREQ.items():
            observed = counts[char]
            expected = total_letters * expected_pct
            diff = observed - expected
            chi_score += (diff * diff) / (expected + 0.0001)
        
        # Lower Chi-Square is better, so we subtract it from a baseline
        score += (1000 - chi_score) / 10
        
        return score

    def add_result(self, method, key, text):
        score = self.score_text(text)
        res = {'method': method, 'key': str(key), 'text': text, 'score': score}
        self.results.append(res)
        # Print immediately (will be redirected to file)
        safe_text = text[:75].replace("\n", "")
        print(f"[{method:<20}] Key: {str(key):<15} | Score: {int(score):<4} | {safe_text}...")

    # =========================================================================
    # DECRYPTION METHODS
    # =========================================================================

    def run_transposition(self):
        print("\n" + "="*80 + "\nRUNNING TRANSPOSITION ATTEMPTS\n" + "="*80)
        for key in range(2, 99):
            try:
                dec = self._transposition_decrypt(self.ciphertext, key)
                self.add_result("Transposition", key, dec)
            except: pass

    def run_caesar(self):
        print("\n" + "="*80 + "\nRUNNING CAESAR ATTEMPTS\n" + "="*80)
        for shift in range(1, self.N):
            dec = self._caesar_decrypt(self.ciphertext, shift)
            self.add_result("Caesar", shift, dec)

    def run_vigenere_bruteforce(self):
        print("\n" + "="*80 + "\nRUNNING VIGENERE (SHORT KEYS)\n" + "="*80)
        common_keys = ["abc", "key", "pass", "flag", "code", "magic", "cipher"]
        for key in common_keys:
            dec = self._vigenere_decrypt(self.ciphertext, key)
            self.add_result("Vigenere (Dict)", key, dec)
            
        chars = string.ascii_lowercase
        print("[*] Brute forcing all 2-letter Vigenere keys (676 combinations)...")
        for k1 in chars:
            for k2 in chars:
                key = k1 + k2
                dec = self._vigenere_decrypt(self.ciphertext, key)
                self.add_result("Vigenere (BF 2)", key, dec)

    def run_combinations(self):
        print("\n" + "="*80 + "\nRUNNING COMBINATION ATTEMPTS (Top Candidates Only)\n" + "="*80)
        top_caesar = sorted([r for r in self.results if r['method'] == 'Caesar'], key=lambda x: x['score'], reverse=True)[:5]
        for item in top_caesar:
            c_text = item['text']
            shift = item['key']
            for t_key in range(2, 12): 
                dec = self._transposition_decrypt(c_text, t_key)
                self.add_result("Comb:Caesar->Trans", f"S:{shift}/K:{t_key}", dec)

        top_trans = sorted([r for r in self.results if r['method'] == 'Transposition'], key=lambda x: x['score'], reverse=True)[:5]
        for item in top_trans:
            t_text = item['text']
            t_key = item['key']
            for s_key in range(1, self.N):
                dec = self._caesar_decrypt(t_text, s_key)
                self.add_result("Comb:Trans->Caesar", f"K:{t_key}/S:{s_key}", dec)

    # --- CORE MATH FUNCTIONS ---
    def _caesar_decrypt(self, text, shift):
        res = []
        for char in text:
            if char in self.alphabet:
                idx = self.alphabet.index(char)
                new_idx = (idx - shift) % self.N
                res.append(self.alphabet[new_idx])
            else:
                res.append(char)
        return "".join(res)

    def _transposition_decrypt(self, text, key):
        n = len(text)
        cols = (n + key - 1) // key
        rows = key
        shaded = (cols * rows) - n
        grid = [''] * cols
        c, r = 0, 0
        for char in text:
            grid[c] += char
            c += 1
            if (c == cols) or (c == cols - 1 and r >= rows - shaded):
                c = 0
                r += 1
        return "".join(grid)

    def _vigenere_decrypt(self, text, key):
        res = []
        key_idxs = [self.alphabet.index(k) for k in key if k in self.alphabet]
        if not key_idxs: return text
        ki = 0
        for char in text:
            if char in self.alphabet:
                c_idx = self.alphabet.index(char)
                k_idx = key_idxs[ki % len(key_idxs)]
                new_idx = (c_idx - k_idx) % self.N
                res.append(self.alphabet[new_idx])
                ki += 1
            else:
                res.append(char)
        return "".join(res)

    def print_final_analysis(self):
        print("\n" + "="*80)
        print("FINAL ALGORITHM ANALYSIS - TOP 5 CANDIDATES")
        print("="*80)
        self.results.sort(key=lambda x: x['score'], reverse=True)
        for i, r in enumerate(self.results[:7]):
            print(f"RANK {i+1} | SCORE: {int(r['score'])}")
            print(f"METHOD : {r['method']}")
            print(f"KEY    : {r['key']}")
            print(f"TEXT   : {r['text'][:1000]}...") 
            print("-" * 80)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # 1. Setup File Path (Documents folder)
    docs_folder = os.path.join(os.path.expanduser("~"), "Documents")
    output_file = os.path.join(docs_folder, "crypto_analysis_results.txt")

    quiz_input = """i1rw!zdpr2!3rgokuxdudglx!m1zu4vi!3ukyooou2!mr4q3!wlvhg4gwy!wlvhg,grx!mrkv3dv!1rkg2agikuwh1vge1lxjgi1h2kgs1rnxmhi!mkoh2hi!kqn!rrxh8bgzrlvhgysvswyu2!3d2wo!2lwsvhggsvrh2agqod1!3ko!mrkv3bggsyou2!mkofu!qhkui!lrkw2!nhzd1wgrx!3lwhi!kqn!muoz2!vrq!nhzwr!kqn!kl1agvypo!nd8vgv3d1wgd3!cbgo4qmkgfypovgd3!.5i!kqn!oyoqsqq!6dvn2!oqn!l1g5.agi1rw!mrkv3!3rgpyxxwklxvi!m1zu4vgevhxg2!rl2wyu8bgqkw4uobgdxgggklv1gosio!sqgrxhgvwdvogl2okqnch !"""
    # 2. Open file and redirect stdout
    with open(output_file, "w", encoding="utf-8") as f:
        original_stdout = sys.stdout
        sys.stdout = f
        
        try:
            solver = CryptoSolver(quiz_input)
            
            # Run all modules
            solver.run_transposition()
            solver.run_caesar()
            solver.run_vigenere_bruteforce()
            solver.run_combinations()
            
            # Show the winner
            solver.print_final_analysis()
        finally:
            # Restore stdout
            sys.stdout = original_stdout

    # 3. Force open the file
    print(f"[!] Analysis complete. Results saved to: {output_file}")
    if platform.system() == "Windows":
        os.startfile(output_file)
    elif platform.system() == "Darwin": # macOS
        subprocess.run(["open", output_file])
    else: # Linux
        subprocess.run(["xdg-open", output_file])