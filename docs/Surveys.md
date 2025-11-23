# Surveys: Architecture, APIs, and Data Model

This document explains how the survey system in `main` works: models, flows, request/response contracts, validation rules (including how fieldless questions are skipped), scoring, analytics, and how to exercise the APIs locally.

## Data Model

- `CustomUserSurvey` — top‑level survey definition, created by admins.
  - `title`, `description`, `intro_text`, `outro_text`, `consent_text`
  - `is_active`: governs whether it can be prompted/answered.
  - `require_consent`: if true, the participant must consent before submitting.
  - `target_roles`: list of allowed roles; empty list means open to any authenticated non‑admin role.
  - `display_rules`: JSON used for reminder cadence; `remind_after_hours` is read in `api_survey_next`.
  - `created_by`: admin user reference.
- `CustomUserSurveyQuestion`
  - `order`: 1‑based order within survey (kept gapless on writes/deletes).
  - `qtype`: one of `short-text`, `long-text`, `single-choice`, `multi-choice`, `rating`, `number`, `scale`, `info`.
  - `prompt`, `help_text`
  - `is_required`: whether a value is required (ignored for non‑answerable questions, see below).
  - `is_scored`, `max_score`, `chart_type`
  - `config`: JSON for options or widget config. For choice types: `{"options":[{"value":"a","label":"Option A","score":10}, ...]}`.
- `CustomUserSurveyParticipant`
  - `status`: `pending`, `consented`, `dismissed`, `declined`, `completed`
  - `consented_at`, `dismissed_at`, `last_prompted_at`
  - Unique per `(survey, user)`.
- `CustomUserSurveyResponse`
  - One‑to‑one with participant.
  - `answers`: JSON keyed by question id (string).
  - `score_summary`: totals plus per‑question entries (scores and optional chart payloads).

## Key Views / APIs

All survey endpoints live in `main.views.surveys`.

Admin (login + admin role required):
- `GET /api/surveys/` (`api_surveys_collection`): list all surveys.
- `POST /api/surveys/`: create a survey. Body fields: `title` (required), `description`, `introText`, `outroText`, `consentText`, `isActive`, `requireConsent`, `targetRoles`, `displayRules`.
- `GET /api/surveys/<id>/` (`api_survey_detail`): fetch survey with questions.
- `PATCH /api/surveys/<id>/`: update fields above plus `isActive`, `targetRoles`.
- `DELETE /api/surveys/<id>/`: delete survey.
- `GET /api/surveys/<id>/questions/` (`api_survey_questions`): list questions.
- `POST /api/surveys/<id>/questions/`: create a question. Body fields: `type`/`qtype`, `prompt`, `helpText`, `isRequired`, `isScored`, `maxScore`, `chartType`, `order` (optional), `config` (JSON).
- `GET /api/surveys/<id>/questions/<qid>/` (`api_survey_question_detail`): fetch one question.
- `PATCH /api/surveys/<id>/questions/<qid>/`: update any fields above; can also reorder via `order` (1‑based, gapless normalization).
- `DELETE /api/surveys/<id>/questions/<qid>/`: delete and renumber remaining questions.
- `GET /api/surveys/<id>/analytics/` (`api_survey_analytics`): aggregate charts/data from responses.

User (login required, non‑admin):
- `GET /api/surveys/next/` (`api_survey_next`): returns the next available survey and participant record, considering `target_roles`, `display_rules`, reminder windows, and prior completion.
- `POST /api/surveys/<id>/participation/` (`api_survey_participation`): actions `consent`, `dismiss`/`later`, `decline`. Updates participant state and timestamps.
- `POST /api/surveys/<id>/responses/` (`api_survey_responses`): submit answers; returns participant, survey meta, and score summary. If already completed, returns the existing summary.

Pages:
- `survey_builder` view renders `SurveyBuilder.html` (admin only).
- `survey_analytics_dashboard` renders `SurveyAnalytics.html` (admin only).

## Question Types and Config

- `short-text`, `long-text`: free text; stored as strings.
- `single-choice`: `config.options` array required. Each option dict: `value` (string, required), `label`/`text` (display), `score` (numeric).
- `multi-choice`: same shape as single choice; answers stored as list of selected `value` strings.
- `rating`, `number`, `scale`: numeric inputs; accepted as float; validated for numeric coercion.
- `info`: informational block; non‑answerable.

### Fieldless / Non‑answerable handling
- Questions marked `info` are skipped during validation.
- Choice questions (`single-choice`, `multi-choice`) with **no options** are treated as non‑answerable and skipped. They no longer block submission even if `is_required=True`.

## Validation Rules (api_survey_responses)

- `answers` must be an object keyed by question id (string).
- Required questions must have a value unless non‑answerable (info or choice with no options).
- Choice types validate that selected values exist in the configured options.
- Multi‑choice requires at least one valid option when required.
- Numeric types require numeric coercion; otherwise return `400` with `details`.
- On validation errors, response: `{"error": "Validation error", "details": {...}}` with `400`.

## Scoring

- Only `is_scored=True` questions are included in totals.
- `max_score`: if provided (>0), caps the score; otherwise derived:
  - single choice: max of option scores
  - multi-choice: sum of positive option scores
  - numeric types: defaults to `100.0` when scored
- For choice questions, option `score` values are used. For numeric/rating/scale, submitted numeric value is used (clamped to `max_score`).
- `score_summary` shape:
  ```json
  {
    "questions": [{"id": 12, "score": 8, "maxScore": 10, "chart": {...}}],
    "totalScore": 18,
    "totalPossible": 20,
    "percentage": 90.0
  }
  ```
- If `chart_type` is set and the question is scored, an individual chart payload is embedded per question.

## Targeting and Display

- `CustomUserSurvey.allows_role(role)` checks role against `target_roles`; admins always bypass checks in admin endpoints, but are not auto‑prompted in `api_survey_next`.
- `api_survey_next` filters active surveys, ensures role is allowed, ensures the participant is not completed, respects dismissal cooldown via `display_rules.remind_after_hours` (default 24h), and marks `last_prompted_at`.

## Participant Flow

1) `api_survey_next` returns a pending survey (or `survey: null`).
2) User POSTs `participation` with `action=consent` to move to `consented`.
3) User POSTs `responses` with `answers` to complete; participant status becomes `completed`. If already completed, the API returns the stored response/score.
4) User can `dismiss`/`later` to snooze or `decline` to stop being prompted.

## Error Semantics

- `403 Forbidden` for role violations or non‑admin access to admin endpoints.
- `400` for payload/validation errors (JSON decode, unsupported question type, invalid config, invalid answers).
- `204` on successful deletes (survey or question).

## Testing

- Unit/integration tests live under `main/tests/`:
  - `test_smoke.py`: basic page/API availability
  - `test_surveys.py`: regression for fieldless required questions being skipped
  - `test_surveys` can be extended for more cases (see below).
- Running (Postgres): drop stale test DB if needed, then `python manage.py test main.tests.test_surveys --noinput`.
- To avoid touching Postgres, create a test settings module that points `DATABASES['default']` to SQLite (`':memory:'`) and run with `--settings`.

### Suggested Additional Test Cases
- Create/update question ordering and ensure gapless renumbering after deletions.
- Validate required multi-choice without options is skipped (non‑answerable) and with options requires at least one selection.
- Scoring paths: numeric coercion, option scoring aggregation, percentage calculation when `total_possible` is zero.
- `api_survey_next` reminder window logic with `dismissed_at` and `display_rules.remind_after_hours`.

## Admin UX Notes

- Survey Builder consumes the same APIs above; ensure `chartType` and `options` are populated for choice questions to avoid “fieldless” skips.
- For non-interactive text blocks, use `qtype="info"`; these will render but not require answers.

## Quick Payload Examples

- Create survey:
  ```json
  {
    "title": "Index Survey",
    "description": "Helps improve the home experience",
    "isActive": true,
    "requireConsent": true,
    "targetRoles": ["student"],
    "displayRules": {"remind_after_hours": 48}
  }
  ```
- Add single-choice question:
  ```json
  {
    "qtype": "single-choice",
    "prompt": "How likely are you to recommend us?",
    "isRequired": true,
    "isScored": true,
    "maxScore": 10,
    "chartType": "pie",
    "order": 1,
    "config": {
      "options": [
        {"value": "0-6", "label": "0-6", "score": 2},
        {"value": "7-8", "label": "7-8", "score": 7},
        {"value": "9-10", "label": "9-10", "score": 10}
      ]
    }
  }
  ```
- Submit responses:
  ```json
  {
    "answers": {
      "12": "9-10",
      "13": ["engaging", "clear"],
      "14": 8.5
    }
  }
  ```

## Maintenance Tips

- Keep `config.options` populated for choice types; empty options will now be skipped but degrade survey usefulness.
- When changing question orders, the view normalizes to gapless sequences to avoid duplicate orders.
- Ensure `chart_type` is set only for scored questions to get per-question charts in analytics.
- For reminder cadence, set `displayRules.remind_after_hours` to control how soon dismissed users are re-prompted.
