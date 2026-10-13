"""Voice diagnostic: tries 3 ways of speaking and tells you what happened.
Run:  python voice_diag.py     (from anywhere; needs Windows)"""
import base64, subprocess, sys, time

def enc(script):
    return base64.b64encode(script.encode("utf-16-le")).decode("ascii")

def run_persistent(label, body, lines):
    print(f"\n--- {label} ---")
    script = ("Add-Type -AssemblyName System.Speech\n"
              "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n$s.Volume = 100\n"
              "while ($true) { $l = [Console]::In.ReadLine(); if ($null -eq $l) { break }\n" + body + "}\n")
    p = subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                          "-EncodedCommand", enc(script)],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding="ascii")
    time.sleep(2.0)
    print("process alive after start:", p.poll() is None)
    for t in lines:
        try:
            p.stdin.write(t + "\n"); p.stdin.flush()
        except Exception as e:
            print("write failed:", e)
        time.sleep(2.5)
    try:
        p.stdin.close()
    except Exception:
        pass
    try:
        out, err = p.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill(); out, err = p.communicate()
    print("powershell output:", (out or "").strip() or "(none)")
    print("powershell errors:", (err or "").strip() or "(none)")

if not sys.platform.startswith("win"):
    sys.exit("Run this on Windows.")

print("Listen carefully. Three tests follow; note which ones you HEAR.")
run_persistent("TEST A (async, what the trainer uses): you should hear 'test A one' then 'test A two'",
               "[void]$s.SpeakAsync($l)\n", ["test A one", "test A two"])
run_persistent("TEST B (sync): you should hear 'test B one' then 'test B two'",
               "$s.Speak($l)\n", ["test B one", "test B two"])
print("\n--- TEST C (one process per sentence): you should hear 'test C' ---")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('test C')"])
print("\nDone. Tell me which of A, B, C you heard, and paste everything above.")
