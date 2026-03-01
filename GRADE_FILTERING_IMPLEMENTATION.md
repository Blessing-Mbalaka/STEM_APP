# Grade-Based Role Parameter & Filtering Implementation Plan

## Overview
This document outlines the steps to implement grade as a role parameter in the STEM Application and create a new `GradeFiltering` model to manage grade-based content filtering.

---

## Phase 1: Database Model Updates

### Step 1.1: Update CustomUser Model
**File:** `main/models/user.py`

- Add a `grade` field to the `CustomUser` model as a choice field (not just in Profile)
- Create a `GRADE_CHOICES` constant with valid grade levels (e.g., 9, 10, 11, 12, or K-12 equivalents)
- Example:
  ```python
  GRADE_CHOICES = [
      ('9', 'Grade 9'),
      ('10', 'Grade 10'),
      ('11', 'Grade 11'),
      ('12', 'Grade 12'),
  ]
  ```
- Add field: `grade = models.CharField(max_length=10, choices=GRADE_CHOICES, blank=True, default="")`

### Step 1.2: Create GradeFiltering Model
**File:** `main/models/resource.py` or create new file `main/models/grade_filtering.py`

Create a new model to manage grade-based content filtering:

```python
class GradeFiltering(models.Model):
    resource = models.OneToOneField(CourseResource, on_delete=models.CASCADE, related_name='grade_filter')
    min_grade = models.CharField(max_length=10, choices=GRADE_CHOICES)
    max_grade = models.CharField(max_length=10, choices=GRADE_CHOICES)
    allow_above_max = models.BooleanField(default=False)  # Allow students above max_grade to access
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Grade Filter"
        verbose_name_plural = "Grade Filters"
    
    def is_accessible_by_user(self, user):
        """Check if a user's grade falls within the filter range"""
        user_grade = user.grade
        # Convert grades to integers for comparison
        # Handle logic for allow_above_max
        pass
    
    def __str__(self):
        return f"Grades {self.min_grade}-{self.max_grade} for {self.resource.title}"
```

---

## Phase 2: Database Migrations

### Step 2.1: Create Migration for CustomUser Grade Field
- Run: `python manage.py makemigrations main`
- Review the migration file to ensure the `grade` field is created with proper defaults
- Run: `python manage.py migrate`

### Step 2.2: Create Migration for GradeFiltering Model
- Run: `python manage.py makemigrations main` again
- Review migration for the new `GradeFiltering` model
- Run: `python manage.py migrate`

---

## Phase 3: Admin Interface Updates

### Step 3.1: Update Django Admin
**File:** `main/admin.py`

- Update `CustomUserAdmin` to include the `grade` field in display and form
- Create `GradeFilteringAdmin` class with inline editing within resource details
- Add to admin site:
  ```python
  admin.site.register(GradeFiltering, GradeFilteringAdmin)
  ```
- Make sure grade filtering configuration is accessible when editing CourseResource

---

## Phase 4: Views & Filtering Logic

### Step 4.1: Create Grade Filtering Utility Functions
**File:** `main/utils/grade_filtering.py` (new file)

- Create utility functions:
  - `get_accessible_resources_for_user(user)`: Returns QuerySet of resources accessible to user's grade
  - `filter_resources_by_grade(queryset, user)`: Filters QuerySet by user's grade
  - `grade_is_in_range(user_grade, min_grade, max_grade)`: Validation logic

### Step 4.2: Update View Functions
**Files:** `main/views/*.py`

- Update views that list or retrieve CourseResources to apply grade filtering
- Apply filtering in:
  - Course detail views
  - Resource list endpoints
  - Search functionality
  - API endpoints (if applicable)
- Ensure unauthorized access returns appropriate response (403 or filtered out from results)

---

## Phase 5: Role-Based Access Control (RBAC) Integration

### Step 5.1: Update Role System
**File:** `main/models/user.py` and relevant middleware/decorators

- Define role constants or choices:
  ```python
  ROLE_CHOICES = [
      ('student', 'Student'),
      ('tutor', 'Tutor'),
      ('admin', 'Admin'),
      ('teacher', 'Teacher'),
  ]
  ```
- Consider if `grade` should be a separate parameter or integrated into role definition
- If `is_tutor` boolean is kept, determine how grades apply (do tutors have grades?)

### Step 5.2: Create Role-Grade Mapping
**File:** `main/utils/role_mapping.py` (new file)

- Define which roles can see/access grade filters
- Define default grade access for different roles
- Create helpers:
  - `get_user_grade_level(user)`: Retrieve user's grade
  - `check_grade_permission(user, resource)`: Permission checker

---

## Phase 6: Forms & User Interface

### Step 6.1: Update User Forms
**File:** `main/forms.py`

- Update registration form to include `grade` selection
- Update profile edit form to allow grade change
- Add validation for grade field

### Step 6.2: Create Grade Filter Admin Form
- Create form for managing grade filters on resources
- Include fields:
  - `min_grade` (dropdown)
  - `max_grade` (dropdown)
  - `allow_above_max` (checkbox)
- Add validation to ensure `min_grade <= max_grade`

### Step 6.3: Update Templates
**File:** `main/templates/`

- Update registration template to show grade selector
- Update profile page to show/edit grade
- Update admin pages to show grade filtering options
- Add informational text if resource requires specific grade level

---

## Phase 7: API & Serializers (if applicable)

### Step 7.1: Update Serializers
**File:** `main/serializers/` (if using DRF)

- Add `grade` field to `CustomUserSerializer`
- Create `GradeFilteringSerializer`
- Update resource serializers to include grade filter info

### Step 7.2: Update API Views
- Add filtering logic to API endpoints
- Add query parameter support for grade filtering (for admins)
- Return appropriate error responses for unauthorized grade access

---

## Phase 8: Testing

### Step 8.1: Unit Tests
**File:** `main/tests/test_grade_filtering.py` (new file)

- Test `GradeFiltering.is_accessible_by_user()` method
- Test grade comparison logic
- Test `allow_above_max` flag behavior
- Test grade validation

### Step 8.2: Integration Tests
- Test that resources with grade filters appear/disappear based on user grade
- Test access restrictions (403 responses)
- Test admin ability to set grade filters
- Test grade field in user registration and profile

### Step 8.3: Manual Testing Checklist
- [ ] Create test users with different grades
- [ ] Create resources with various grade filters
- [ ] Verify resource visibility by grade
- [ ] Test `allow_above_max` scenarios
- [ ] Test admin interface functionality
- [ ] Test registration form grade selection

---

## Phase 9: Documentation & Deployment

### Step 9.1: Code Documentation
- Add docstrings to all new model methods
- Document `GradeFiltering.is_accessible_by_user()` behavior
- Create developer guide for grade-based filtering queries

### Step 9.2: Update Requirements
- Ensure no new dependencies are needed (using built-in Django features)
- Update `requirements.txt` if necessary

### Step 9.3: Deployment Steps
- Backup database before migration
- Run migrations in staging environment first
- Test all grade filtering functionality in staging
- Deploy to production
- Monitor for any issues

---

## Phase 10: Additional Considerations

### Step 10.1: Performance Optimization
- Add database indexes on `grade` field for filtering queries
- Consider caching grade-accessible resources if there are many resources

### Step 10.2: Reporting & Analytics
- Create admin reports showing resource access by grade
- Track which grade levels use which resources

### Step 10.3: Future Enhancements
- Support for grade ranges (e.g., "Grades 9-10")
- Individual resource recommendations based on grade
- Adaptive difficulty levels based on grade
- Grade progression tracking

---

## Summary of Files to Modify/Create

### Modify:
- `main/models/user.py` - Add grade field to CustomUser
- `main/admin.py` - Register GradeFiltering, update CustomUserAdmin
- `main/forms.py` - Add grade field to forms
- `main/views/*.py` - Apply grade filtering to views
- Templates for registration and profile pages

### Create:
- `main/models/grade_filtering.py` - New GradeFiltering model
- `main/utils/grade_filtering.py` - Utility functions
- `main/utils/role_mapping.py` - Role-grade mapping logic
- `main/tests/test_grade_filtering.py` - Unit and integration tests
- Database migrations (auto-generated)

---

## Implementation Timeline
1. **Phase 1-2:** Model creation and migrations (1-2 days)
2. **Phase 3:** Admin interface (1 day)
3. **Phase 4-5:** Views and role integration (2-3 days)
4. **Phase 6:** Forms and UI updates (2 days)
5. **Phase 7:** API updates (1-2 days)
6. **Phase 8:** Testing (2-3 days)
7. **Phase 9:** Documentation and deployment (1-2 days)

**Total Estimated Time:** 1-2 weeks
