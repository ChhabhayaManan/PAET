# accounts

Who the student is. Registration, the two-step login (password, then a one-time code by
email), access and refresh tokens, password reset, the one-click dev login, the student's
own profile, data-sharing consent and the peer comparison.

## Endpoints

| Router | Prefix | Endpoints |
|---|---|---|
| `router_auth.py` | `/api/v1/auth` | register, login, verify-otp, forgot/reset password, refresh, logout, me, dev-login |
| `router_users.py` | `/api/v1/users` | my profile (get/update), change password, consent, peer comparison, admin user list |
| `router_profile.py` | `/api/v1/profile` | `GET /mastery`, measured mastery per topic (read from `learner_model`) |

## Tables

- Writes: `users`, `otp_records`, `user_sessions`, `learning_profiles`
- Reads: `topic_mastery` (mastery endpoint), `code_submissions` / `code_evaluations`
  (profile stats), `onboarding_records` (profile)

`learning_profiles` rows are created here; their mirrored fields are kept up to date by
`learner_model`. `users.points`, `users.level` and `users.badges` are mirrors written by
`gamification`.

## Files

```
router_auth.py, router_users.py, router_profile.py   HTTP
service.py            AuthService: register, login, OTP, tokens, sessions
logic/user_service.py UserService: profile, consent, peer comparison
models.py             User, OTPRecord, LearningProfile, UserSession
schemas.py            request/response models (auth, user, profile)
```
