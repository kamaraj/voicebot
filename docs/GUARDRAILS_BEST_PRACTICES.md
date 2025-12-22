# 🛡️ GUARDRAILS BEST PRACTICES

## 🎯 The Golden Rule

**Use guardrails strategically, not universally!**

```
Development → Minimal/Off (speed for testing)
Staging → Selective (test safety features)
Production → Full (protect users)
Internal Tools → Minimal (trusted users)
Public API → Full (untrusted users)
```

---

## ⚖️ The Trade-Off Matrix

| Scenario | Guardrails | Performance | Safety | Recommendation |
|----------|-----------|-------------|--------|----------------|
| **Development** | ❌ Off | 🚀 Fast | ⚠️ None | Off |
| **Demo/Testing** | ⚡ Minimal | 🏃 Good | ✅ Basic | Selective |
| **Internal Use** | ⚡ Selective | 🏃 Good | ✅ Good | Async |
| **Public Beta** | ✅ On | 🐌 Slower | ✅ High | On |
| **Production** | ✅✅ Full | 🐌 Slowest | ✅✅ Maximum | Async + Cache |

---

## 🎨 RECOMMENDED CONFIGURATIONS

### **Configuration 1: Development Mode** ⚡ FASTEST

**When to use:**
- Local development
- Testing features
- Debugging
- Performance benchmarking

**Settings:**
```bash
# .env.development
GUARDRAILS_ENABLED=false
PII_DETECTION_ENABLED=false
TOXICITY_THRESHOLD=1.0  # Effectively disabled
PROMPT_INJECTION_ENABLED=false

# Performance Impact: 0ms
# Safety Level: None
```

**Pros:**
- ✅ Lightning fast (0ms overhead)
- ✅ Easy debugging
- ✅ Quick iterations

**Cons:**
- ❌ No protection
- ❌ Not suitable for real users

---

### **Configuration 2: Smart Selective** ⚡⚡ BALANCED (RECOMMENDED!)

**When to use:**
- Internal tools
- Trusted users
- Demos
- Beta testing

**Settings:**
```bash
# .env.selective
GUARDRAILS_ENABLED=true

# Only enable critical guardrails
PII_DETECTION_ENABLED=true       # Protect privacy
TOXICITY_THRESHOLD=0.8            # Lenient
PROMPT_INJECTION_ENABLED=false   # Skip for trusted users

# Run async (don't block response)
GUARDRAILS_ASYNC=true             # Key optimization!

# Performance Impact: ~20-50ms (async)
# Safety Level: Medium-High
```

**Pros:**
- ✅ Good performance (~50ms overhead)
- ✅ Protects critical data (PII)
- ✅ Allows most interactions

**Cons:**
- ⚠️ Not suitable for hostile users

**Implementation:**
```python
# Run guardrails in background
async def process_with_async_guardrails(message):
    # 1. Send to LLM immediately (don't wait for guardrails)
    response_task = asyncio.create_task(llm.ainvoke(message))
    
    # 2. Check guardrails in parallel
    guardrails_task = asyncio.create_task(
        guardrails_engine.check_input(message)
    )
    
    # 3. Get LLM response (fast!)
    response = await response_task
    
    # 4. Check guardrails result (already completed or almost done)
    guardrails_result = await guardrails_task
    
    # 5. Log violations (don't block user)
    if not all(r.passed for r in guardrails_result.values()):
        logger.warning("guardrails_violation", violations=guardrails_result)
        # Alert admin, log to database, etc.
    
    return response
```

---

### **Configuration 3: Production Safe** 🛡️ SECURE

**When to use:**
- Public-facing applications
- Untrusted users
- Regulated industries
- Customer-facing bots

**Settings:**
```bash
# .env.production
GUARDRAILS_ENABLED=true

# All guardrails on, strict settings
PII_DETECTION_ENABLED=true
PII_SCORE_THRESHOLD=0.3            # Very sensitive
TOXICITY_THRESHOLD=0.5             # Strict
PROMPT_INJECTION_ENABLED=true
PROMPT_INJECTION_STRICT=true

# Async + caching for performance
GUARDRAILS_ASYNC=true
GUARDRAILS_CACHE_ENABLED=true     # Cache results
GUARDRAILS_CACHE_TTL=3600         # 1 hour

# Performance Impact: ~100-200ms (async + cached)
# Safety Level: Maximum
```

**Pros:**
- ✅ Maximum protection
- ✅ Catches all violations
- ✅ Meets compliance requirements

**Cons:**
- ⚠️ Slower (100-200ms overhead)
- ⚠️ May block legitimate queries

**Optimization:**
```python
# Cache guardrails results for similar queries
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def check_cached_guardrails(message_hash):
    return guardrails_engine.check_input(message)

# Usage
message_hash = hashlib.md5(message.encode()).hexdigest()
result = check_cached_guardrails(message_hash)
```

---

### **Configuration 4: Hybrid Smart** ⚡🛡️ INTELLIGENT

**When to use:**
- Mixed user base (trusted + public)
- High-value applications
- Need both speed and safety

**Settings:**
```bash
# .env.hybrid
GUARDRAILS_ENABLED=true

# Smart adaptive thresholds
GUARDRAILS_ADAPTIVE=true          # Adjust based on user reputation
USER_TRUST_ENABLED=true           # Track user behavior

# Different levels for different users
GUARDRAILS_TRUSTED_USER_LEVEL=minimal
GUARDRAILS_NEW_USER_LEVEL=full
GUARDRAILS_FLAGGED_USER_LEVEL=strict

# Performance Impact: 20-200ms (depends on user)
# Safety Level: Adaptive
```

**Implementation:**
```python
async def smart_guardrails(message, user_id):
    # Get user trust score
    trust_score = await get_user_trust_score(user_id)
    
    if trust_score > 0.8:
        # Trusted user - minimal checks
        return await check_minimal_guardrails(message)
    
    elif trust_score > 0.5:
        # Regular user - selective checks
        return await check_selective_guardrails(message)
    
    else:
        # New/flagged user - full checks
        return await check_full_guardrails(message)
```

---

## 🚀 PERFORMANCE OPTIMIZATION STRATEGIES

### **Strategy 1: Async Guardrails** ⭐ RECOMMENDED

**Don't wait for guardrails - process in parallel!**

```python
# BEFORE (blocking): 300ms LLM + 150ms guardrails = 450ms
result = guardrails.check_input(message)  # Wait 150ms
if result.passed:
    response = llm.invoke(message)        # Wait 300ms

# AFTER (async): max(300ms LLM, 150ms guardrails) = 300ms!
async def process_async():
    # Start both at the same time
    llm_task = asyncio.create_task(llm.ainvoke(message))
    guard_task = asyncio.create_task(guardrails.check_input(message))
    
    # Get LLM response (don't wait for guardrails)
    response = await llm_task
    
    # Check guardrails result (for logging/alerts)
    guard_result = await guard_task
    
    # Log but don't block
    if not guard_result.passed:
        log_violation(guard_result)
    
    return response
```

**Savings: 100-150ms (40-50% faster!)**

---

### **Strategy 2: Selective Guardrails**

**Only check what matters!**

```python
# Check only critical guardrails
async def selective_check(message, is_sensitive=False):
    checks = []
    
    # Always check PII (critical!)
    checks.append(pii_guardrail.check(message))
    
    # Only check toxicity if public-facing
    if is_public_api:
        checks.append(toxicity_guardrail.check(message))
    
    # Only check injection if high-risk query
    if is_sensitive or contains_system_keywords(message):
        checks.append(injection_guardrail.check(message))
    
    # Skip length limits for trusted users
    # Skip content filters for internal tools
    
    return await asyncio.gather(*checks)
```

**Savings: 50-100ms (20-40% faster)**

---

### **Strategy 3: Caching** 💾

**Cache guardrails results for similar queries!**

```python
import hashlib
from datetime import datetime, timedelta

# Simple cache
guardrails_cache = {}

async def cached_guardrails_check(message):
    # Create cache key
    cache_key = hashlib.md5(message.encode()).hexdigest()
    
    # Check cache
    if cache_key in guardrails_cache:
        cached_result, cached_time = guardrails_cache[cache_key]
        
        # Cache valid for 1 hour
        if datetime.now() - cached_time < timedelta(hours=1):
            return cached_result
    
    # Not in cache - check and store
    result = await guardrails_engine.check_input(message)
    guardrails_cache[cache_key] = (result, datetime.now())
    
    return result
```

**Savings: 100-200ms for cached queries (100% faster!)**

---

### **Strategy 4: Smart Throttling**

**Only check periodically for trusted users!**

```python
# Check every Nth request for trusted users
async def throttled_check(message, user_id, check_frequency=10):
    request_count = get_user_request_count(user_id)
    
    # Full check for new users or every 10th request
    if request_count % check_frequency == 0:
        return await full_guardrails_check(message)
    
    # Minimal check for other requests
    return await minimal_guardrails_check(message)
```

**Savings: 90% reduction in overhead for trusted users**

---

## 📊 PERFORMANCE COMPARISON

| Configuration | Overhead | LLM+Guard | Total (with TTS) | Use Case |
|---------------|----------|-----------|------------------|----------|
| **No Guardrails** | 0ms | 300ms | 5.3s | Development |
| **Async (Recommended)** | 0-50ms | 300ms | 5.3-5.4s | ⭐ Best balance |
| **Selective** | 50-100ms | 350-400ms | 5.4-5.5s | Good balance |
| **Cached** | 0-100ms | 300-400ms | 5.3-5.5s | Repeat queries |
| **Full Sync** | 100-200ms | 400-500ms | 5.5-5.7s | Maximum safety |
| **Your Current** | ~3000ms❌ | 3335ms | 8.56s | Initialization lag |

---

## 🎯 RECOMMENDED SETUP

### **For Your VoiceBot Application:**

```bash
# .env.local (RECOMMENDED)

# Enable guardrails but run async
GUARDRAILS_ENABLED=true
GUARDRAILS_ASYNC=true              # ← Key optimization!

# PII protection (important for voice)
PII_DETECTION_ENABLED=true
PII_SCORE_THRESHOLD=0.5            # Moderate sensitivity

# Toxicity (light filtering)
TOXICITY_THRESHOLD=0.7             # Not too strict
TOXIC_KEYWORDS_ENABLED=true

# Prompt injection (for safety)
PROMPT_INJECTION_ENABLED=true
PROMPT_INJECTION_STRICT=false      # Not too strict

# Performance tuning
GUARDRAILS_CACHE_ENABLED=true
GUARDRAILS_CACHE_TTL=1800          # 30 minutes

# Expected Performance:
# - Guardrails overhead: ~50ms (async)
# - LLM time: 300-500ms
# - Total: 5.3-5.5 seconds ✅
```

---

## 🛠️ IMPLEMENTATION

### **Step 1: Add Async Support**

Create `src/guardrails/async_engine.py`:

```python
import asyncio
from src.guardrails.engine import guardrails_engine
import structlog

logger = structlog.get_logger(__name__)

async def check_guardrails_async(message: str):
    """Run guardrails in background"""
    try:
        # Run in executor to not block event loop
        result = await asyncio.to_thread(
            guardrails_engine.check_input,
            message
        )
        
        # Log violations but don't block
        if not all(r.passed for r in result.values()):
            logger.warning(
                "guardrails_violation_detected",
                violations=[r.violations for r in result.values() if r.violations]
            )
        
        return result
        
    except Exception as e:
        logger.error("guardrails_error", error=str(e))
        # Fail open (don't block user on guardrails error)
        return {}
```

### **Step 2: Update Agent**

Modify `src/agents/fast_voice_agent.py`:

```python
from src.guardrails.async_engine import check_guardrails_async

async def process_message_fast(self, user_message, ...):
    # Start guardrails check (don't wait)
    if settings.guardrails_enabled:
        guard_task = asyncio.create_task(
            check_guardrails_async(user_message)
        )
    
    # Process with LLM (don't wait for guardrails!)
    response, llm_duration = await self._fast_path_generate(user_message)
    
    # Log guardrails result (if enabled)
    if settings.guardrails_enabled:
        guard_result = await guard_task
        # Result logged in async_engine
    
    return {...}
```

---

## ✅ QUICK DECISION TREE

```
Are you in development?
├─ YES → Disable guardrails (GUARDRAILS_ENABLED=false)
└─ NO → Continue

Is this a public API?
├─ YES → Enable all guardrails + async
└─ NO → Continue

Are users trusted (internal)?
├─ YES → Enable PII only + async
└─ NO → Enable all guardrails + async

Do you need <500ms response?
├─ YES → Run guardrails 100% async (don't wait)
└─ NO → Run guardrails sync (more control)

Is compliance required (HIPAA/GDPR)?
├─ YES → Enable all + sync (block on violations)
└─ NO → Enable selective + async (log violations)
```

---

## 📝 SUMMARY

### **Best Practices:**

1. **✅ Development:** Guardrails OFF (fastest)
2. **✅ Internal Tools:** PII only + Async (balanced)
3. **✅ Public Beta:** All guardrails + Async (recommended)
4. **✅ Production:** All guardrails + Async + Cache (optimal)
5. **✅ High Security:** All guardrails + Sync (strictest)

### **Key Optimizations:**

- ⚡ **Run async** - Don't block LLM on guardrails
- 🎯 **Be selective** - Only check what matters
- 💾 **Cache results** - Avoid redundant checks
- 🔄 **Throttle checks** - Not every request needs full check
- 📊 **Monitor & adjust** - Track violations vs performance

### **For Your VoiceBot:**

**Recommendation:** Configuration 2 (Smart Selective) with async!

```bash
GUARDRAILS_ENABLED=true
GUARDRAILS_ASYNC=true      # ← This is the key!
PII_DETECTION_ENABLED=true
TOXICITY_THRESHOLD=0.7
```

**Expected Performance:**
- LLM: 300-500ms
- Guardrails: ~50ms (async, doesn't block!)
- Total: 5.3-5.5 seconds ✅

---

**Want me to implement async guardrails for you now?** 🚀
