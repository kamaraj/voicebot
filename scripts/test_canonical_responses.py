"""
Quick test to verify canonical responses work for all discipline policy question variations.
"""
import requests
import hashlib

API_URL = "http://localhost:9011/api/v1/conversation"

# All 35 discipline policy question variations
QUESTIONS = [
    # Direct Questions
    "What is your discipline policy?",
    "How do you handle discipline at the center?",
    "What are your behavior management rules?",
    "What is your approach to discipline?",
    "How do you discipline children here?",
    
    # Casual/Informal Tone
    "Hey, what happens if my kid misbehaves?",
    "So how do you guys deal with bad behavior?",
    "What's the deal with discipline here?",
    "How do you handle naughty kids?",
    "What do you do when children act up?",
    
    # Formal/Professional Tone
    "Could you please explain your discipline and behavior management policy?",
    "I would like to understand the procedures for addressing behavioral issues.",
    "What is the standard protocol for disciplinary matters?",
    "Please describe your approach to managing children's conduct.",
    "Kindly outline your behavioral guidelines and disciplinary procedures.",
    
    # Parent Concerns
    "What happens if my child doesn't follow the rules?",
    "How will you handle it if my kid has a tantrum?",
    "Will you inform me if my child misbehaves?",
    "What are the consequences for bad behavior?",
    "Do you use time-outs or other punishments?",
    
    # Specific Scenarios
    "What do you do if a child hits another child?",
    "How do you handle biting incidents?",
    "What's your policy on bullying behavior?",
    "How do you deal with children who don't listen?",
    "What if my child refuses to participate in activities?",
    
    # Frustrated Tone
    "How exactly do you discipline kids without being too harsh?",
    "I need to know your discipline approach - is it fair to all children?",
    "What's your policy? I don't want my child treated unfairly!",
    "Explain to me how you handle behavior problems!",
    "Who decides what punishment a child gets?",
    
    # Confused/Uncertain Tone
    "I'm not sure I understand... what's your discipline method?",
    "Can you help me understand how you handle behavior issues?",
    "What exactly happens when a child breaks the rules?",
    "I'm confused about your discipline approach - can you clarify?",
    "How does discipline work here exactly?"
]


def test_canonical_responses():
    """Test that all questions return the same canonical response."""
    print("=" * 60)
    print("CANONICAL RESPONSE TEST - Discipline Policy Questions")
    print("=" * 60)
    print(f"Testing {len(QUESTIONS)} question variations...\n")
    
    responses = []
    response_hashes = set()
    
    for i, question in enumerate(QUESTIONS, 1):
        try:
            r = requests.post(API_URL, json={"message": question}, timeout=30)
            data = r.json()
            
            response_text = data.get("response", "")
            topic = data.get("metadata", {}).get("topic", "N/A")
            path = data.get("metadata", {}).get("path", "N/A")
            is_canonical = data.get("metadata", {}).get("is_canonical", False)
            
            # Hash the response to check uniqueness
            response_hash = hashlib.md5(response_text.encode()).hexdigest()[:8]
            response_hashes.add(response_hash)
            
            status = "✅" if is_canonical and topic == "discipline_policy" else "❌"
            
            print(f"{status} [{i:02d}/35] Topic: {topic:20s} | Path: {path:10s} | Hash: {response_hash}")
            
            responses.append({
                "question": question,
                "topic": topic,
                "path": path,
                "is_canonical": is_canonical,
                "hash": response_hash
            })
            
        except Exception as e:
            print(f"❌ [{i:02d}/35] ERROR: {str(e)[:50]}")
            responses.append({
                "question": question,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    canonical_count = sum(1 for r in responses if r.get("is_canonical", False))
    correct_topic = sum(1 for r in responses if r.get("topic") == "discipline_policy")
    
    print(f"Total Questions:     {len(QUESTIONS)}")
    print(f"Canonical Responses: {canonical_count}")
    print(f"Correct Topic:       {correct_topic}")
    print(f"Unique Responses:    {len(response_hashes)}")
    
    if len(response_hashes) == 1:
        print("\n🎉 SUCCESS! All questions returned the SAME canonical answer!")
    else:
        print(f"\n⚠️  Found {len(response_hashes)} different responses")
    
    return canonical_count == len(QUESTIONS) and len(response_hashes) == 1


if __name__ == "__main__":
    success = test_canonical_responses()
    exit(0 if success else 1)
