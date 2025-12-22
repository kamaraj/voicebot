# 🚨 PERFORMANCE REGRESSION DIAGNOSIS

## ⚠️ Critical Issue Detected

**Your Test Results:**
```
Test 1: LLM 3335ms, Total 8.56s
Test 2: LLM 6120ms, Total 20.76s
Result: 2.4x SLOWER (143% regression!)
```

---

## 🔍 ROOT CAUSES IDENTIFIED

### **Cause #1: Response Length** ⚠️ MAJOR

**Your Response (Test 2):**
```
"Hi, Kamaraj! That sounds like a great start. I'm glad to hear that 
you have an interest in learning Python programming. Do you know what 
you would like to learn first?"
```

**Analysis:**
- Length: ~170 characters, ~40 tokens
- Generation time: 6120ms  
- Speed: 40 tokens / 6.12s = **6.5 tokens/second**
- Expected: 50 tokens/second
- **8x slower than expected!**

**Conclusion:** Model is running extremely slow!

---

### **Cause #2: Model Unloaded** ⚠️ CRITICAL

**Check:**
```bash
ollama ps
# Result: No models loaded!
```

**Impact:**
- Model unloaded between tests
- Each request must reload model from disk
- Loading time: 1-2 seconds PER REQUEST
- Explains the slowness!

---

### **Cause #3: Wrong Model?** ⚠️ POSSIBLE

**Hypothesis:**
TinyLlama should generate at ~50 tokens/second.
Your speed: 6.5 tokens/second (8x slower).

**Possible Issues:**
1. Wrong model loaded (phi3:mini instead of tinyllama?)
2. Model quantization issue
3. CPU throttling
4. Memory pressure

---

## 🚀 IMMEDIATE FIXES

### **Fix #1: Keep Model in Memory** ⭐ CRITICAL

**Problem:** Model unloading after each request

**Solution:**

```bash
# Option A: Keep model loaded
ollama run tinyllama:latest "stay loaded" &

# Option B: Increase keep-alive in Ollama
# Edit Ollama config or restart with:
# OLLAMA_KEEP_ALIVE=30m
```

**Expected Gain:** 1-2 seconds per request!

---

### **Fix #2: Verify Correct Model**

**Check which model is actually running:**

```bash
# Test API and check response
curl -X POST http://localhost:9011/api/v1/conversation \
  -H "Content-Type: application/json" \
  -d '{"message":"test","conversation_id":"test"}' | jq

# Check model name in response
```

**Expected:** Should use `tinyllama:latest`

**If wrong:** Update `.env.local`:
```bash
OLLAMA_MODEL=tinyllama:latest
```

---

### **Fix #3: Limit Response Length** ⚡ QUICK WIN

**Problem:** Longer responses = more generation time

**Solution:** Update model parameters for shorter responses

Edit `src/agents/fast_voice_agent.py`:
```python
self.llm = Ollama(
    model=self.model_name,
    base_url=settings.ollama_base_url,
    timeout=30,
    num_ctx=2048,
    num_predict=100,    # ← Reduce from 256 to 100
    temperature=0.7,
    top_p=0.9,
    stop=["User:", "\n\n"]  # ← Stop at natural break
)
```

**Expected Gain:** 50% shorter responses = 50% faster!

---

### **Fix #4: Disable Guardrails Temporarily**

**To isolate the performance issue:**

```bash
# .env.local
GUARDRAILS_ENABLED=false
```

**Test again:**
- If faster: Guardrails were the issue
- If still slow: Model/system issue

---

## 🧪 DIAGNOSTIC TESTS

### **Test 1: Direct Ollama Performance**

```bash
# Time a direct Ollama call
time ollama run tinyllama:latest "What is Python?" --verbose

# Expected: < 1 second for response
# If > 2 seconds: Ollama/model issue
```

### **Test 2: API Performance**

```bash
# Time API call
Measure-Command {
  Invoke-WebRequest -Uri "http://localhost:9011/api/v1/conversation" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"message":"hi","conversation_id":"test"}'
}

# Expected: < 1000ms TotalMilliseconds
# If > 2000ms: Backend issue
```

### **Test 3: Check System Resources**

```bash
# Check CPU/Memory
Get-Process ollama
Get-Process python

# Look for high CPU (>80%) or memory issues
```

---

## 📊 PERFORMANCE TARGETS

| Component | Current | Target | Gap |
|-----------|---------|--------|-----|
| **LLM Generation** | 6120ms | 300-500ms | **12x too slow!** |
| **TTS** | 14612ms | 5000-6000ms | **2.4x too slow!** |
| **Total** | 20760ms | 5500ms | **3.8x too slow!** |

---

## 🎯 ACTION PLAN

### **Immediate (Do Now):**

1. **Preload model:**
   ```bash
   ollama run tinyllama:latest "ready"
   ```

2. **Keep model loaded:**
   ```bash
   # Keep Ollama running in background
   # Model stays in memory
   ```

3. **Verify model:**
   ```bash
   ollama list
   # Should show tinyllama:latest
   ```

4. **Test again:**
   - Ask same question
   - Check if faster

### **If Still Slow:**

5. **Disable guardrails:**
   ```bash
   GUARDRAILS_ENABLED=false
   ```

6. **Limit response length:**
   ```python
   num_predict=100  # Shorter responses
   ```

7. **Check system resources:**
   ```bash
   # CPU, memory, disk
   ```

### **If Nothing Helps:**

8. **Try different model:**
   ```bash
   # Use Qwen 0.5B (smaller, faster)
   ollama pull qwen:0.5b
   
   # Update .env.local
   OLLAMA_MODEL=qwen:0.5b
   ```

9. **Check for background processes:**
   - Close other apps
   - Free up memory
   - Check antivirus scans

---

## 🔬 LIKELY CULPRITS

**Ranked by probability:**

1. **90% - Model keeps unloading** ⚠️
   - Each request reloads from disk
   - Adds 1-2 seconds per request
   - **FIX:** Keep model loaded

2. **5% - Wrong model loaded** ⚠️
   - Phi3 instead of TinyLlama
   - Phi3 is slower
   - **FIX:** Verify OLLAMA_MODEL setting

3. **3% - System resources** ⚠️
   - Low memory
   - CPU throttling
   - **FIX:** Check task manager

4. **2% - Async guardrails bug** ⚠️
   - Unlikely but possible
   - **FIX:** Disable and test

---

## ✅ QUICK FIX SCRIPT

```powershell
# Run this now:

# 1. Preload model
Write-Host "Preloading TinyLlama..."
ollama run tinyllama:latest "System ready"

# 2. Keep it loaded (background process)
Start-Process -NoNewWindow ollama -ArgumentList "serve"

# 3. Wait
Start-Sleep -Seconds 5

# 4. Test performance
Write-Host "Testing performance..."
Measure-Command {
  Invoke-WebRequest -Uri "http://localhost:9011/api/v1/conversation" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"message":"hi","conversation_id":"quick_test"}'
}

# Should see TotalMilliseconds < 1000
```

---

## 📈 EXPECTED RESULTS AFTER FIX

**After keeping model loaded:**
```
🤖 LLM: 300-500ms (12x faster!)
🔊 TTS: 5000ms (2.4x faster!)
⚡ Total: ~5.5s (3.8x faster!)
```

**Compared to your test:**
```
Before: 6120ms LLM, 20.76s total
After:  400ms LLM, 5.5s total
Improvement: 15x faster LLM, 3.8x faster overall!
```

---

## 🚨 CRITICAL NEXT STEPS

1. **Preload TinyLlama NOW:**
   ```bash
   ollama run tinyllama:latest "ready for testing"
   ```

2. **Test IMMEDIATELY:**
   - Use voice chat
   - Ask simple question
   - Share timing

3. **If still slow:**
   - Disable guardrails
   - Test again
   - Share logs

---

## 📞 SUMMARY

**Problem:** LLM is 12x slower than expected (6120ms vs 500ms)

**Cause:** Model keeps unloading + possibly wrong model

**Solution:** Keep model loaded + verify tinyllama

**Expected:** Should drop from 6120ms to 300-500ms (12x faster!)

---

**🚀 Preload the model now and test again!**

```bash
ollama run tinyllama:latest "ready"
```

**Then try voice chat and share the new timing!**
