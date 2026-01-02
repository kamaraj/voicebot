"""
Canonical Response System for VoiceBot.
Ensures consistent answers for similar questions by topic.
"""
from typing import Dict, Optional, List
import re


# Canonical answers for each FAQ topic
CANONICAL_RESPONSES = {
    "discipline_policy": {
        "keywords": [
            # Core terms
            "discipline", "behavior", "behaviour", "misbehave", "misbehaves", "misbehavior",
            "punishment", "punish", "time-out", "timeout", "time out",
            # Behavior descriptors
            "naughty", "bad behavior", "bad behaviour", "rules", "consequences",
            "hitting", "hits", "hit", "biting", "bite", "bullying", "bully",
            "act up", "acting up", "conduct", "behavioral", "behavioural",
            # Parent concerns
            "tantrum", "tantrums", "doesn't follow", "don't follow", "doesn't listen",
            "don't listen", "won't listen", "refuse", "refuses", "not participating",
            # Fairness/approach
            "fair", "fairly", "unfair", "unfairly", "harsh", "harshly",
            "gentle", "positive", "guidance", "redirection",
            # Actions
            "handle", "deal with", "manage", "address", "respond",
            # Questions about policy
            "policy", "policies", "approach", "method", "procedure",
            "guidelines", "guideline", "protocol"
        ],
        "answer": """Our discipline policy is based on positive guidance and age-appropriate expectations. Here's how we handle behavior:

**Our Approach:**
- We use positive reinforcement to encourage good behavior
- Redirection is our first response to unwanted behavior
- We help children understand the impact of their actions
- Time-outs are used sparingly and only when necessary (1 minute per year of age)

**When Issues Arise:**
- Staff will calmly address the behavior with the child
- We teach problem-solving and conflict resolution skills
- Parents are notified of significant behavioral concerns
- We work together with families on consistent approaches

**We Do NOT:**
- Use physical punishment of any kind
- Shame or humiliate children
- Withhold food or outdoor time as punishment

If you have specific concerns about your child's behavior, please speak with our lead teacher to develop a consistent approach together."""
    },
    
    "attendance": {
        "keywords": ["attendance", "check-in", "check in", "sign in", "sign-in", "present", 
                     "absent", "late", "drop off", "pick up", "arrival"],
        "answer": """Here's how to mark daily attendance at our childcare center:

**For Parents:**
1. Use our online parent portal or mobile app
2. Log in with your credentials
3. Navigate to the "Attendance" section
4. Select the date and mark your child as Present, Absent, Late, or On Leave

**At Drop-off:**
- Sign in your child at the front desk or kiosk
- Note the arrival time
- Inform staff of any early pick-up plans

**Important Notes:**
- Please notify us by 9:00 AM if your child will be absent
- Late arrivals (after 9:30 AM) should be noted
- For extended absences, please inform the office in advance

If you need help with the attendance system, our front desk staff is happy to assist you."""
    },
    
    "fees_payment": {
        "keywords": ["fee", "fees", "payment", "cost", "tuition", "price", "pay", "billing",
                     "invoice", "expensive", "discount", "financial", "scholarship"],
        "answer": """Here's our fee structure and payment information:

**Tuition Rates:**
- Full-time (5 days/week): Please contact office for current rates
- Part-time options available
- Sibling discounts offered

**Payment Methods:**
- Online payment through parent portal
- Automatic bank transfer (ACH)
- Credit/debit cards accepted
- Check payments

**Payment Schedule:**
- Tuition is due on the 1st of each month
- Late payment fee applies after the 10th
- A one-time registration fee is required upon enrollment

**Financial Assistance:**
- We accept state childcare subsidies
- Payment plans available upon request
- Please inquire about scholarship opportunities

For specific rates and payment arrangements, please contact our billing department."""
    },
    
    "hours_schedule": {
        "keywords": ["hours", "schedule", "time", "open", "close", "operating", "when", 
                     "early", "late", "holiday", "weekend", "morning", "afternoon"],
        "answer": """Our operating hours and schedule:

**Regular Hours:**
- Monday to Friday: 6:30 AM - 6:30 PM
- We are closed on weekends

**Holidays:**
- We observe major federal holidays
- A holiday calendar is provided at enrollment
- Tuition remains the same for holiday weeks

**Drop-off & Pick-up:**
- Morning drop-off: 6:30 AM - 9:00 AM
- Afternoon pick-up: 3:00 PM - 6:30 PM
- Late pick-up fees apply after 6:30 PM

**Special Programs:**
- Before-school care: 6:30 AM - 8:00 AM
- After-school care: 3:00 PM - 6:30 PM
- Summer camp available

Please notify us in advance if you need early drop-off or late pick-up arrangements."""
    },
    
    "safety_security": {
        "keywords": ["safety", "security", "safe", "secure", "emergency", "pick up", 
                     "authorized", "stranger", "lock", "camera", "supervision"],
        "answer": """Your child's safety is our top priority. Here's how we ensure security:

**Facility Security:**
- Secure entry with key code/fob access
- Security cameras throughout the facility
- Fenced outdoor play areas
- All doors locked during operating hours

**Staff Requirements:**
- Background checks on all employees
- CPR and First Aid certified staff
- Proper child-to-staff ratios maintained
- Staff training on emergency procedures

**Pick-up Procedures:**
- Only authorized individuals may pick up children
- Photo ID required for verification
- Authorization must be on file
- Parents notified immediately of any concerns

**Emergency Preparedness:**
- Monthly fire and safety drills
- Emergency evacuation plans posted
- First aid supplies readily available
- Emergency contact information kept current

Your child is never left unsupervised. Please update your authorized pick-up list promptly."""
    },
    
    "food_nutrition": {
        "keywords": ["food", "meal", "snack", "lunch", "breakfast", "eat", "nutrition",
                     "allergy", "allergies", "diet", "vegetarian", "menu"],
        "answer": """Our food and nutrition program:

**Meals Provided:**
- Morning snack: 9:30 AM
- Lunch: 12:00 PM
- Afternoon snack: 3:00 PM

**Menu Features:**
- Nutritious, balanced meals
- Weekly menu posted for parents
- Fresh fruits and vegetables daily
- Whole grains and lean proteins

**Dietary Accommodations:**
- Food allergies carefully managed
- Vegetarian options available
- Cultural/religious dietary needs respected
- Please inform us of any restrictions

**Food Safety:**
- Licensed commercial kitchen
- Staff food-handler certified
- Proper food storage and handling
- No nuts or peanuts on premises

Menus are provided monthly. Please notify us immediately of any food allergies or dietary restrictions."""
    },
    
    "health_illness": {
        "keywords": ["health", "sick", "ill", "illness", "fever", "medicine", "medication",
                     "doctor", "immunization", "vaccine", "contagious", "symptom"],
        "answer": """Our health and illness policies:

**When to Keep Your Child Home:**
- Fever of 100.4°F or higher
- Vomiting or diarrhea
- Contagious illness (pink eye, strep, etc.)
- Undiagnosed rash
- Must be symptom-free for 24 hours before returning

**Medication Policy:**
- Written authorization required
- Original labeled container only
- Administered by trained staff
- Detailed log maintained

**Health Requirements:**
- Immunizations must be current
- Annual physical required
- Health records on file
- Emergency medical authorization

**If Your Child Becomes Ill:**
- Parents will be notified immediately
- Child will be isolated comfortably
- Pick-up required within 1 hour
- Return requires doctor's clearance if needed

Please keep emergency contact information current at all times."""
    },
    
    "enrollment_admission": {
        "keywords": ["enroll", "enrollment", "admission", "register", "registration",
                     "apply", "application", "waitlist", "age", "requirements", "start"],
        "answer": """Our enrollment and admission process:

**Eligibility:**
- Ages 6 weeks to 5 years (varies by program)
- Toilet training not required for younger programs
- Current immunizations required

**Steps to Enroll:**
1. Schedule a tour of our facility
2. Complete the application form
3. Submit required documents
4. Pay registration fee
5. Complete orientation

**Required Documents:**
- Birth certificate
- Immunization records
- Emergency contact information
- Medical authorization form
- Custody documents (if applicable)

**Waitlist:**
- Priority given to siblings of current students
- Waitlist managed by application date
- You'll be notified when a spot opens

Schedule a tour to learn more! We'd love to show you our program and answer your questions."""
    },
    
    "staff_qualifications": {
        "keywords": ["staff", "teacher", "caregiver", "qualified", "training", "ratio",
                     "experience", "background", "certification", "education"],
        "answer": """Our staff qualifications and standards:

**Education Requirements:**
- Lead teachers: Degree in Early Childhood Education or related field
- All staff: Minimum CDA credential or equivalent
- Ongoing professional development required

**Training:**
- CPR and First Aid certified
- Annual child abuse prevention training
- Health and safety training
- Age-appropriate curriculum training

**Background Checks:**
- FBI fingerprint background check
- State criminal background check
- Child abuse registry check
- Reference verification

**Staff-to-Child Ratios:**
- Infants (0-12 months): 1:4
- Toddlers (1-2 years): 1:6
- Preschool (3-5 years): 1:10
- We often exceed these requirements

Our team is passionate about early childhood education. Feel free to meet your child's teachers during your visit!"""
    },
    
    "daily_activities": {
        "keywords": ["activities", "curriculum", "learning", "play", "schedule", "day",
                     "typical", "routine", "education", "program", "outdoor", "nap"],
        "answer": """A typical day at our childcare center:

**Daily Schedule:**
- 6:30-8:30 AM: Arrival, free play, breakfast
- 8:30-9:00 AM: Circle time, morning greeting
- 9:00-10:30 AM: Learning activities, centers
- 10:30-11:00 AM: Outdoor play
- 11:00-12:00 PM: Lunch and cleanup
- 12:00-2:30 PM: Rest/nap time
- 2:30-3:00 PM: Wake up, snack
- 3:00-4:30 PM: Afternoon activities
- 4:30-6:30 PM: Outdoor play, departure

**Learning Areas:**
- Literacy and language development
- Math and science exploration
- Art and creative expression
- Music and movement
- Social-emotional skills
- Physical development

**Our Philosophy:**
- Play-based learning
- Age-appropriate curriculum
- Individual attention
- Preparation for school readiness

Daily reports keep you informed of your child's activities, meals, and milestones!"""
    }
}


def detect_topic(query: str, rag_results: List[Dict] = None) -> Optional[str]:
    """
    Detect the topic of a query based on keywords and RAG results.
    
    Args:
        query: The user's question
        rag_results: Optional RAG retrieval results
        
    Returns:
        Topic key if detected, None otherwise
    """
    query_lower = query.lower()
    
    # Score each topic by keyword matches
    topic_scores = {}
    
    for topic, data in CANONICAL_RESPONSES.items():
        score = 0
        for keyword in data["keywords"]:
            if keyword.lower() in query_lower:
                score += 1
                # Bonus for exact match
                if keyword.lower() == query_lower:
                    score += 5
        
        if score > 0:
            topic_scores[topic] = score
    
    # Also consider RAG results if available
    if rag_results:
        for result in rag_results:
            source = result.get("source", "").lower()
            topic_name = result.get("topic", "").lower()
            
            # Map source files to topics
            source_topic_map = {
                "policies": "discipline_policy",
                "discipline": "discipline_policy",
                "attendance": "attendance",
                "fees": "fees_payment",
                "payment": "fees_payment",
                "hours": "hours_schedule",
                "schedule": "hours_schedule",
                "safety": "safety_security",
                "security": "safety_security",
                "food": "food_nutrition",
                "nutrition": "food_nutrition",
                "health": "health_illness",
                "illness": "health_illness",
                "enrollment": "enrollment_admission",
                "admission": "enrollment_admission",
                "staff": "staff_qualifications",
                "activities": "daily_activities",
                "daily": "daily_activities"
            }
            
            for key, topic in source_topic_map.items():
                if key in source or key in topic_name:
                    topic_scores[topic] = topic_scores.get(topic, 0) + 3
    
    # Return highest scoring topic
    if topic_scores:
        best_topic = max(topic_scores, key=topic_scores.get)
        if topic_scores[best_topic] >= 1:
            return best_topic
    
    return None


def get_canonical_response(query: str, rag_results: List[Dict] = None) -> Optional[Dict]:
    """
    Get a canonical response for a query if a matching topic is found.
    
    Args:
        query: The user's question
        rag_results: Optional RAG retrieval results
        
    Returns:
        Dict with topic and answer if found, None otherwise
    """
    topic = detect_topic(query, rag_results)
    
    if topic and topic in CANONICAL_RESPONSES:
        return {
            "topic": topic,
            "answer": CANONICAL_RESPONSES[topic]["answer"],
            "is_canonical": True
        }
    
    return None


def get_all_topics() -> List[str]:
    """Get list of all available canonical topics."""
    return list(CANONICAL_RESPONSES.keys())


def get_topic_answer(topic: str) -> Optional[str]:
    """Get the canonical answer for a specific topic."""
    if topic in CANONICAL_RESPONSES:
        return CANONICAL_RESPONSES[topic]["answer"]
    return None
