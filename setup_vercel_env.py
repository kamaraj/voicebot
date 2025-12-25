import os
import subprocess
from pathlib import Path

def load_env_file(path):
    env_vars = {}
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return env_vars
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"').strip("'")
                env_vars[key.strip()] = value
    return env_vars

def set_vercel_env(key, value):
    # We only set for 'production' and 'preview' and 'development' (all)
    # Actually, let's just do production for now to be safe.
    # vercel env add <name> [environment]
    # We'll map to 'production'
    
    print(f"Setting {key}...")
    
    # Run for production
    try:
        # Pass value via stdin to avoid exposing in process list args (though ps shows args)
        # But here subprocess.run input=value covers stdin.
        cmd = ["vercel", "env", "add", key, "production"]
        
        # We need to simulate the environment selection if not passed as arg?
        # Usage: vercel env add <name> [environment]
        # If [environment] is provided, it shouldn't prompt.
        
        # However, vercel env add might fail if exists.
        # Check if exists first? `vercel env ls`?
        # We'll just try and ignore error.
        
        process = subprocess.run(
            cmd,
            input=value.encode(),
            capture_output=True,
            shell=True # shell=True needed on windows to find 'vercel' command sometimes?
             # No, verify 'vercel' path.
             # On windows 'vercel' is a batch file or cmd.
        )
        
        # On Windows, 'vercel' might be 'vercel.cmd'.
        # Let's try shell=True.
        
        if process.returncode == 0:
            print(f"✅ Set {key}")
        else:
            stderr = process.stderr.decode()
            if "already exists" in stderr:
                # Try rm and add? Or just skip.
                print(f"⚠️ {key} already exists (skipping)")
            else:
                print(f"❌ Failed to set {key}: {stderr}")
                
    except Exception as e:
        print(f"❌ Error setting {key}: {str(e)}")

def main():
    env_path = ".env.local"
    env_vars = load_env_file(env_path)
    
    if not env_vars:
        print("No env vars found or empty file.")
        return

    print(f"Found {len(env_vars)} variables.")
    
    keys_to_set = ["GROQ_API_KEY", "GOOGLE_API_KEY"]
    # Also generic ones if in file
    
    for key, value in env_vars.items():
        if key in keys_to_set or "API_KEY" in key or "TOKEN" in key or "ENABLED" in key:
             set_vercel_env(key, value)

if __name__ == "__main__":
    main()
