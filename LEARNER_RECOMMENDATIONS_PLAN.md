# Learner-Material Recommendation System - Implementation Plan

## 📋 Overview

**Goal:** Analyze individual student chatbot interactions to create personalized course material recommendations, tailored learning paths, and identify knowledge gaps.

**Status:** Architecture & Planning Phase
**Priority:** High - Enables adaptive learning

---

## 🏗️ Current Data Infrastructure

### Existing Models
```
ChatbotConversation (user, question, created_at)
  ↓
ChatbotResponse (response, sources, response_type, created_at)
  ↓
ChatbotCache (question_hash, question, answer)
```

### Existing Logging
- **File:** `main/data/student_searches.yaml`
- **Content:** Queries, timestamps, actor info, sources, metadata
- **Frequency:** Real-time on each chatbot interaction

---

## 🎯 System Architecture

### Phase 1: Learning Profile Extraction (Weeks 1-2)

#### 1.1 Create Learner Profile Model
```python
# main/models/learner_profile.py

class LearnerProfile(models.Model):
    """Aggregates learning data for personalized recommendations."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Topic mastery scores (0-100)
    topics_queried = models.JSONField(default=dict)  
    # Example: {"algebra": 15, "trigonometry": 8, "calculus": 2}
    
    concepts_weak = models.JSONField(default=list)
    # Example: ["quadratic_equations", "derivatives", "matrices"]
    
    concepts_strong = models.JSONField(default=list)
    # Example: ["basic_arithmetic", "linear_equations"]
    
    avg_question_depth = models.FloatField(default=1.0)
    # 1-5 scale: how advanced are questions?
    
    category_interests = models.JSONField(default=dict)
    # Example: {"Math": 0.8, "Science": 0.4, "English": 0.2}
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Learner Profile"
        verbose_name_plural = "Learner Profiles"
```

#### 1.2 Extract Topics from Questions
```python
# main/utils/topic_extraction.py

def extract_topics(question: str) -> dict:
    """
    Uses NLP to extract learning topics from a question.
    Returns: {"topic": "algebra", "subtopics": ["quadratic_equations"], "difficulty": 1-5}
    
    Strategy:
    1. Query extraction (Pattern matching keywords)
    2. Named Entity Recognition (NER) for concepts
    3. Difficulty classification (simple/intermediate/advanced)
    """
    # Implementation options:
    # - spaCy NLP model
    # - Regex patterns + domain knowledge
    # - Gemini API analysis (prompt engineering)
    pass
```

#### 1.3 Create Concept Taxonomy
```yaml
# main/data/concept_taxonomy.yaml
# Maps questions/keywords to learning concepts

Math:
  Algebra:
    - linear_equations
    - quadratic_equations
    - polynomials
    - factoring
  Calculus:
    - derivatives
    - integrals
    - limits
  Geometry:
    - angles
    - triangles
    - circles

Science:
  Physics:
    - kinematics
    - forces
    - energy
  Chemistry:
    - atomic_structure
    - chemical_bonds
    - reactions
```

---

### Phase 2: Recommendation Engine (Weeks 3-4)

#### 2.1 Material Matching Algorithm
```python
# main/utils/recommendation_engine.py

class RecommendationEngine:
    """
    Generates personalized material recommendations.
    """
    
    def get_recommendations(self, user_id: int, limit: int = 5) -> List[Recommendation]:
        """
        Algorithm:
        1. Load learner profile
        2. Identify weak concepts (low query count)
        3. Match course materials to weak concepts
        4. Rank by: (relevance × urgency × engagement_score)
        5. Filter out already-learned materials
        6. Return top N recommendations
        """
        
        # Scoring function:
        # score = (concept_weakness * 0.5 + 
        #         material_relevance * 0.3 + 
        #         difficulty_progression * 0.2)
        pass
    
    def identify_knowledge_gaps(self, user_id: int) -> List[dict]:
        """
        Returns concepts student hasn't explored yet.
        Ranks by prerequisite importance.
        
        Example output:
        [
            {"concept": "derivatives", "importance": 0.95, "prerequisite_for": ["integrals", "optimization"]},
            {"concept": "matrix_operations", "importance": 0.7, "prerequisite_for": ["linear_algebra_applications"]},
        ]
        """
        pass
```

#### 2.2 Create Recommendation Model
```python
# main/models/recommendations.py

class Recommendation(models.Model):
    """Personalized material recommendations for learners."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource = models.ForeignKey(CourseResource, on_delete=models.CASCADE)
    
    reason_type = models.CharField(
        max_length=20,
        choices=[
            ('weak_concept', 'Addresses Weak Concept'),
            ('prerequisite', 'Missing Prerequisite'),
            ('continuation', 'Natural Continuation'),
            ('related_interest', 'Related to Interests'),
        ]
    )
    
    confidence_score = models.FloatField(0, 1)  # 0-1 recommendation confidence
    target_concept = models.CharField(max_length=100)  # What concept does it teach?
    
    created_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True)  # Track student engagement
    
    class Meta:
        unique_together = ('user', 'resource')
        ordering = ['-confidence_score']
```

---

### Phase 3: UI Integration (Weeks 5-6)

#### 3.1 New API Endpoint
```python
# Path: /api/recommendations/

class RecommendationsAPI(APIView):
    """
    GET /api/recommendations/?limit=5
    
    Returns:
    {
        "recommendations": [
            {
                "resource_id": 42,
                "title": "Understanding Quadratic Equations",
                "reason": "Addresses Weak Concept: quadratic_equations",
                "type": "video",
                "confidence": 0.92,
                "difficulty_next": "intermediate"
            }
        ],
        "knowledge_gaps": [
            {"concept": "derivatives", "importance": 0.95}
        ],
        "profile": {
            "strong_areas": ["linear_equations"],
            "weak_areas": ["calculus"],
            "engagement_level": "high"
        }
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        recommendations = RecommendationEngine().get_recommendations(request.user.id)
        return JsonResponse(serialize_recommendations(recommendations))
```

#### 3.2 New UI Component
```html
<!-- main/templates/components/learning_recommendations.html -->

<div id="learning-recommendations" class="widget">
    <h3>📚 Recommended For You</h3>
    
    <div id="profile-summary">
        <!-- Shows learning profile stats -->
        <p>Strong: <span id="strong-areas"></span></p>
        <p>Need Help: <span id="weak-areas"></span></p>
    </div>
    
    <div id="recommendations-list">
        <!-- Dynamically populated -->
    </div>
    
    <script>
        async function loadRecommendations() {
            const res = await fetch('/api/recommendations/?limit=5');
            const data = await res.json();
            
            // Render recommendations
            data.recommendations.forEach(rec => {
                // Create recommendation card
                // Include reason, materials, difficulty level
            });
        }
    </script>
</div>
```

---

### Phase 4: Analytics & Insights (Weeks 7-8)

#### 4.1 Student Dashboard Metrics
```python
# Metrics to display per student:

Dashboard Metrics:
├── Learning Velocity (questions/week trend)
├── Topic Breadth (# distinct topics explored)
├── Concept Mastery (% weak concepts resolved)
├── Knowledge Graph (visual map of learned concepts)
├── Recommended Materials Engagement (% clicked)
└── Learning Path Progress (% of prerequisites completed)
```

#### 4.2 Analytics API
```python
# /api/student/<id>/analytics/

{
    "learning_summary": {
        "weeks_active": 12,
        "total_questions": 156,
        "avg_questions_per_week": 13,
        "topics_explored": ["algebra", "geometry", "trigonometry"],
        "growth_rate": 0.15
    },
    "concept_mastery": {
        "strong": ["linear_equations", "basic_functions"],
        "intermediate": ["quadratic_equations", "coordinate_geometry"],
        "weak": ["logarithms", "trigonometric_identities"]
    },
    "recommendations_effectiveness": {
        "total_recommended": 24,
        "clicked": 18,
        "completed": 12,
        "engagement_rate": 0.75
    }
}
```

---

## 📊 Data Storage Strategy

### Database Design
```
Students → ChatbotConversations → ChatbotResponses
    ↓           ↓                       ↓
    └─→ LearnerProfile ←─────────────────┘
           ↓
    Extracted Topics/Concepts
           ↓
    Recommendations → CourseResources
```

### YAML Logging Enhancement
```yaml
# main/data/learner_interactions.yaml
# Extend student_searches.yaml with extracted topics

interactions:
  - student_id: "student-123"
    timestamp: "2026-03-11T14:30:00Z"
    question: "What is a derivative?"
    
    # NEW: Extracted metadata
    extracted_topics:
      - topic: "calculus"
        subtopic: "derivatives"
        difficulty: 2
        confidence: 0.92
    
    chatbot_response: "A derivative measures rate of change..."
    response_sources:
      - type: "course_material"
        id: 45
        engagement: true
    
    # Update to learner_profile
    profile_updates:
      - field: "topics_queried"
        value: {"calculus": 3}
      - field: "concepts_weak"
        action: "remove"
        value: "derivatives"
```

---

## 🔄 Real-Time Update Loop

```
Student asks question in forum
    ↓
Chatbot responds + logs interaction
    ↓
[NEW] Extract topic/concept
    ↓
[NEW] Update LearnerProfile (daily batch)
    ↓
[NEW] Generate new recommendations (weekly)
    ↓
Display in dashboard/forum widget
    ↓
Track engagement → feedback loop
```

---

## ✅ Implementation Checklist

### Phase 1: Data Extraction
- [ ] Create `LearnerProfile` model
- [ ] Create `Recommendation` model
- [ ] Build topic extraction utility
- [ ] Create concept taxonomy YAML
- [ ] Add migration files

### Phase 2: Engine
- [ ] Build `RecommendationEngine` class
- [ ] Implement matching algorithm
- [ ] Add gap identification logic
- [ ] Write scoring function
- [ ] Create recommendation ranking

### Phase 3: API & UI
- [ ] Create `/api/recommendations/` endpoint
- [ ] Add authentication & permissions
- [ ] Build recommendation widget component
- [ ] Add to student dashboard
- [ ] Style and integrate

### Phase 4: Analytics
- [ ] Create analytics API endpoint
- [ ] Build dashboard visualization
- [ ] Track engagement metrics
- [ ] Create admin reports

### Testing & Deployment
- [ ] Unit tests for extraction
- [ ] Integration tests for engine
- [ ] User acceptance testing
- [ ] Performance optimization
- [ ] Deploy to production

---

## 🚀 Quick Win: MVP (Weeks 1-3)

**Minimum Viable Product:**
1. Extract topics from chatbot questions
2. Track weak concepts per student
3. Simple material matching to weak concepts
4. Display top 3 recommendations in forum

**Scope:** 80% benefit with 20% effort

---

## 📈 Future Enhancements

1. **Spaced Repetition:** Remind students about weak concepts at optimal spacing
2. **Learning Paths:** Create sequences of materials for mastery
3. **Peer Learning:** "Students like you studied X next"
4. **Adaptive Difficulty:** Adjust recommendation difficulty based on success rate
5. **Prerequisite Enforcement:** Warn if missing prerequisites
6. **Skill Trees:** Gamified knowledge graph visualization
7. **A/B Testing:** Test different recommendation strategies

---

## 💡 Success Metrics

- **Engagement:** % of students clicking recommendations
- **Effectiveness:** % of recommendations leading to concept mastery
- **Retention:** Reduction in knowledge gaps over 4 weeks
- **Satisfaction:** Student feedback on recommendation relevance
- **Diversity:** % of students exploring new topics via recommendations

---

## 🙋 Questions for Product Team

1. What's the priority level? (MVP vs full implementation)
2. Which course/subject to start with?
3. Desired frequency of recommendations? (real-time vs weekly)
4. Should recommendations appear in forum or dedicated page?
5. Do we want to show "why" reasoning to students?

