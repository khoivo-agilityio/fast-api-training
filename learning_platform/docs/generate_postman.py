"""Generate combined Postman collection (Phase 0-5) with camelCase env vars."""
import json, pathlib

BASE = pathlib.Path(__file__).parent
OUT_COL = BASE / "postman_collection_all.json"
OUT_ENV = BASE / "postman_environment_all.json"

B = "{{baseUrl}}"
ADM = "Bearer {{adminAccessToken}}"
INS = "Bearer {{instructorAccessToken}}"
STU = "Bearer {{studentAccessToken}}"
CT  = {"key": "Content-Type", "value": "application/json"}

def req(method, url, headers=None, body_raw=None):
    r = {"method": method, "header": headers or []}
    if isinstance(url, str):
        r["url"] = url
    else:
        r["url"] = url
    if body_raw:
        r["body"] = {"mode": "raw", "raw": body_raw}
    return r

def test(*lines):
    return [{"listen": "test", "script": {"exec": list(lines)}}]

def item(name, request, events):
    return {"name": name, "request": request, "event": events}

# ── 0 Health ──────────────────────────────────────────────────────────────────
health = {
    "name": "0 — Health Check",
    "item": [
        item("GET /health",
             req("GET", "http://localhost:8001/health"),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "pm.test('healthy',()=>pm.expect(pm.response.json().status).to.eql('healthy'));"))
    ]
}

# ── 1 Auth ────────────────────────────────────────────────────────────────────
def auth_post(name, body_raw, capture=None, expect=201):
    evts = [f"pm.test('Status {expect}',()=>pm.response.to.have.status({expect}));"]
    if capture:
        evts += [f"const j=pm.response.json();"] + [f"pm.collectionVariables.set('{k}',j.{v});" for k,v in capture]
    return item(name, req("POST", f"{B}/auth/register" if "Register" in name else f"{B}/auth/login" if "Login" in name else f"{B}/auth/refresh" if "Refresh" in name else f"{B}/auth/logout", [CT], body_raw), test(*evts))

auth_folder = {
    "name": "1 — Auth",
    "item": [
        item("Register Admin",
             req("POST", f"{B}/auth/register", [CT], '{"email":"admin@example.com","password":"AdminPass1!","display_name":"Admin User"}'),
             test("pm.test('Status 201',()=>pm.response.to.have.status(201));",
                  "pm.collectionVariables.set('adminAccessToken',pm.response.json().access_token);")),
        item("Register Instructor",
             req("POST", f"{B}/auth/register", [CT], '{"email":"instructor@example.com","password":"InstrPass1!","display_name":"Jane Instructor"}'),
             test("pm.test('Status 201',()=>pm.response.to.have.status(201));",
                  "const j=pm.response.json();",
                  "pm.collectionVariables.set('instructorAccessToken',j.access_token);",
                  "pm.collectionVariables.set('instructorRefreshToken',j.refresh_token);")),
        item("Register Student",
             req("POST", f"{B}/auth/register", [CT], '{"email":"student@example.com","password":"StudPass1!","display_name":"Bob Student"}'),
             test("pm.test('Status 201',()=>pm.response.to.have.status(201));",
                  "const j=pm.response.json();",
                  "pm.collectionVariables.set('studentAccessToken',j.access_token);",
                  "pm.collectionVariables.set('studentRefreshToken',j.refresh_token);")),
        item("Register — Duplicate Email (expect 409)",
             req("POST", f"{B}/auth/register", [CT], '{"email":"student@example.com","password":"StudPass1!","display_name":"Dup"}'),
             test("pm.test('Status 409',()=>pm.response.to.have.status(409));")),
        item("Login — Instructor",
             req("POST", f"{B}/auth/login", [CT], '{"email":"instructor@example.com","password":"InstrPass1!"}'),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "const j=pm.response.json();",
                  "pm.collectionVariables.set('instructorAccessToken',j.access_token);",
                  "pm.collectionVariables.set('instructorRefreshToken',j.refresh_token);")),
        item("Login — Wrong Password (expect 401)",
             req("POST", f"{B}/auth/login", [CT], '{"email":"instructor@example.com","password":"WrongPass!"}'),
             test("pm.test('Status 401',()=>pm.response.to.have.status(401));")),
        item("Refresh Token — Instructor",
             req("POST", f"{B}/auth/refresh", [CT], '{"refresh_token":"{{instructorRefreshToken}}"}'),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "const j=pm.response.json();",
                  "pm.collectionVariables.set('instructorAccessToken',j.access_token);",
                  "pm.collectionVariables.set('instructorRefreshToken',j.refresh_token);")),
        item("Logout — Student",
             req("POST", f"{B}/auth/logout", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));")),
        item("Use Token After Logout (expect 401)",
             req("GET", f"{B}/users/me", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 401',()=>pm.response.to.have.status(401));")),
        item("Re-Login Student (restore token)",
             req("POST", f"{B}/auth/login", [CT], '{"email":"student@example.com","password":"StudPass1!"}'),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "const j=pm.response.json();",
                  "pm.collectionVariables.set('studentAccessToken',j.access_token);",
                  "pm.collectionVariables.set('studentRefreshToken',j.refresh_token);")),
    ]
}

# ── 2 Users ───────────────────────────────────────────────────────────────────
users_folder = {
    "name": "2 — Users",
    "item": [
        item("GET /users/me — Instructor",
             req("GET", f"{B}/users/me", [{"key":"Authorization","value":INS}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "pm.test('Has email',()=>pm.expect(pm.response.json()).to.have.property('email'));")),
        item("PATCH /users/me — Update display_name",
             req("PATCH", f"{B}/users/me", [{"key":"Authorization","value":INS},CT], '{"display_name":"Jane Updated"}'),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "pm.test('Name updated',()=>pm.expect(pm.response.json().display_name).to.eql('Jane Updated'));")),
        item("GET /users/me — No Token (expect 401)",
             req("GET", f"{B}/users/me"),
             test("pm.test('Status 401',()=>pm.response.to.have.status(401));")),
    ]
}

# ── 3 Courses ─────────────────────────────────────────────────────────────────
courses_folder = {
    "name": "3 — Courses",
    "item": [
        item("POST /courses — Instructor creates course",
             req("POST", f"{B}/courses", [{"key":"Authorization","value":INS},CT],
                 '{"title":"Python Fundamentals","description":"Learn Python from scratch."}'),
             test("pm.test('Status 201',()=>pm.response.to.have.status(201));",
                  "pm.collectionVariables.set('courseId',pm.response.json().id);")),
        item("POST /courses — Student forbidden (expect 403)",
             req("POST", f"{B}/courses", [{"key":"Authorization","value":STU},CT], '{"title":"Hack"}'),
             test("pm.test('Status 403',()=>pm.response.to.have.status(403));")),
        item("GET /courses — List all",
             req("GET", {"raw":f"{B}/courses?limit=20&offset=0","query":[{"key":"limit","value":"20"},{"key":"offset","value":"0"}]},
                 [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "pm.test('Has items',()=>pm.expect(pm.response.json()).to.have.property('items'));")),
        item("GET /courses?search=Python — Filtered",
             req("GET", {"raw":f"{B}/courses?search=Python","query":[{"key":"search","value":"Python"}]},
                 [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "pm.test('Results found',()=>pm.expect(pm.response.json().total).to.be.above(0));")),
        item("GET /courses/{id}",
             req("GET", f"{B}/courses/{{courseId}}", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "pm.test('Correct id',()=>pm.expect(pm.response.json().id).to.eql(pm.collectionVariables.get('courseId')));")),
        item("GET /courses/{id} — Not found (expect 404)",
             req("GET", f"{B}/courses/00000000-0000-0000-0000-000000000000", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 404',()=>pm.response.to.have.status(404));")),
        item("PATCH /courses/{id} — Instructor updates",
             req("PATCH", f"{B}/courses/{{courseId}}", [{"key":"Authorization","value":INS},CT],
                 '{"description":"Updated description."}'),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));")),
        item("POST /courses/{id}/enroll — Student enrolls",
             req("POST", f"{B}/courses/{{courseId}}/enroll", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 201',()=>pm.response.to.have.status(201));")),
        item("POST /courses/{id}/enroll — Duplicate (expect 409)",
             req("POST", f"{B}/courses/{{courseId}}/enroll", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 409',()=>pm.response.to.have.status(409));")),
        item("DELETE /courses/{id} — Student forbidden (expect 403)",
             req("DELETE", f"{B}/courses/{{courseId}}", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 403',()=>pm.response.to.have.status(403));")),
    ]
}

# ── 4 Lessons ─────────────────────────────────────────────────────────────────
lessons_folder = {
    "name": "4 — Lessons",
    "item": [
        item("POST /courses/{id}/lessons — Lesson 1",
             req("POST", f"{B}/courses/{{courseId}}/lessons", [{"key":"Authorization","value":INS},CT],
                 '{"title":"Lesson 1: Variables","content":"Variables in Python.","order":1}'),
             test("pm.test('Status 201',()=>pm.response.to.have.status(201));",
                  "pm.collectionVariables.set('lessonId',pm.response.json().id);")),
        item("POST /courses/{id}/lessons — Lesson 2",
             req("POST", f"{B}/courses/{{courseId}}/lessons", [{"key":"Authorization","value":INS},CT],
                 '{"title":"Lesson 2: Functions","content":"Functions let you reuse code.","order":2}'),
             test("pm.test('Status 201',()=>pm.response.to.have.status(201));",
                  "pm.collectionVariables.set('lesson2Id',pm.response.json().id);")),
        item("POST /courses/{id}/lessons — Student forbidden (expect 403)",
             req("POST", f"{B}/courses/{{courseId}}/lessons", [{"key":"Authorization","value":STU},CT],
                 '{"title":"Hack","content":"...","order":99}'),
             test("pm.test('Status 403',()=>pm.response.to.have.status(403));")),
        item("GET /courses/{id}/lessons — List",
             req("GET", f"{B}/courses/{{courseId}}/lessons", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "pm.test('Is array',()=>pm.expect(pm.response.json()).to.be.an('array'));")),
        item("GET /lessons/{id} — Student enrolled",
             req("GET", f"{B}/lessons/{{lessonId}}", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "pm.test('Correct id',()=>pm.expect(pm.response.json().id).to.eql(pm.collectionVariables.get('lessonId')));")),
        item("GET /lessons/{id} — Not found (expect 404)",
             req("GET", f"{B}/lessons/00000000-0000-0000-0000-000000000000", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 404',()=>pm.response.to.have.status(404));")),
        item("PATCH /lessons/{id} — Instructor updates",
             req("PATCH", f"{B}/lessons/{{lessonId}}", [{"key":"Authorization","value":INS},CT],
                 '{"title":"Lesson 1: Variables & Types","timeline":"20 min"}'),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));")),
        item("PATCH /lessons/{id} — Student forbidden (expect 403)",
             req("PATCH", f"{B}/lessons/{{lessonId}}", [{"key":"Authorization","value":STU},CT],
                 '{"title":"Hacked"}'),
             test("pm.test('Status 403',()=>pm.response.to.have.status(403));")),
    ]
}

# ── 5 Progress ────────────────────────────────────────────────────────────────
progress_folder = {
    "name": "5 — Progress Tracking (Phase 4)",
    "item": [
        item("GET /lessons/{id} — View lesson 1 (triggers touch → completed)",
             req("GET", f"{B}/lessons/{{lessonId}}", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));")),
        item("GET /lessons/{id} — View again (idempotent)",
             req("GET", f"{B}/lessons/{{lessonId}}", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200 idempotent',()=>pm.response.to.have.status(200));")),
        item("GET /courses/{id}/progress — 1/2 lessons (50%)",
             req("GET", f"{B}/courses/{{courseId}}/progress", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "const j=pm.response.json();",
                  "pm.test('total_lessons 2',()=>pm.expect(j.total_lessons).to.eql(2));",
                  "pm.test('completed_lessons 1',()=>pm.expect(j.completed_lessons).to.eql(1));",
                  "pm.test('percent 50',()=>pm.expect(j.percent_complete).to.eql(50));",
                  "pm.test('not complete',()=>pm.expect(j.is_complete).to.eql(false));")),
        item("GET /lessons/{id} — View lesson 2 (completes it)",
             req("GET", f"{B}/lessons/{{lesson2Id}}", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));")),
        item("GET /courses/{id}/progress — 2/2 lessons (100%)",
             req("GET", f"{B}/courses/{{courseId}}/progress", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "const j=pm.response.json();",
                  "pm.test('percent 100',()=>pm.expect(j.percent_complete).to.eql(100));",
                  "pm.test('is_complete true',()=>pm.expect(j.is_complete).to.eql(true));")),
        item("GET /progress — All enrolled courses",
             req("GET", f"{B}/progress", [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                  "pm.test('Is array',()=>pm.expect(pm.response.json()).to.be.an('array'));",
                  "pm.test('Has entries',()=>pm.expect(pm.response.json().length).to.be.above(0));")),
        item("GET /courses/{id}/progress — No auth (expect 401)",
             req("GET", f"{B}/courses/{{courseId}}/progress"),
             test("pm.test('Status 401',()=>pm.response.to.have.status(401));")),
        item("GET /courses/unknown/progress — Not found (expect 404)",
             req("GET", f"{B}/courses/00000000-0000-0000-0000-000000000099/progress",
                 [{"key":"Authorization","value":STU}]),
             test("pm.test('Status 404',()=>pm.response.to.have.status(404));")),
    ]
}

# ── 6 Admin ───────────────────────────────────────────────────────────────────
admin_folder = {
    "name": "6 — Admin REST API (Phase 5)",
    "item": [
        {
            "name": "6.1 Users",
            "item": [
                item("GET /admin/users — List all",
                     req("GET", {"raw":f"{B}/admin/users?limit=20&offset=0","query":[{"key":"limit","value":"20"},{"key":"offset","value":"0"}]},
                         [{"key":"Authorization","value":ADM}]),
                     test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                          "const j=pm.response.json();",
                          "pm.test('Is array',()=>pm.expect(j).to.be.an('array'));",
                          "if(j.length>0){pm.collectionVariables.set('targetUserId',j[0].id);}")),
                item("GET /admin/users — Student forbidden (expect 401)",
                     req("GET", f"{B}/admin/users", [{"key":"Authorization","value":STU}]),
                     test("pm.test('Status 401',()=>pm.response.to.have.status(401));")),
                item("GET /admin/users — No auth (expect 401)",
                     req("GET", f"{B}/admin/users"),
                     test("pm.test('Status 401',()=>pm.response.to.have.status(401));")),
                item("GET /admin/users/{id}",
                     req("GET", f"{B}/admin/users/{{targetUserId}}", [{"key":"Authorization","value":ADM}]),
                     test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                          "pm.test('Has role',()=>pm.expect(pm.response.json()).to.have.property('role'));")),
                item("GET /admin/users/{id} — Not found (expect 404)",
                     req("GET", f"{B}/admin/users/00000000-0000-0000-0000-000000000000",
                         [{"key":"Authorization","value":ADM}]),
                     test("pm.test('Status 404',()=>pm.response.to.have.status(404));")),
                item("PATCH /admin/users/{id} — Update any user",
                     req("PATCH", f"{B}/admin/users/{{targetUserId}}",
                         [{"key":"Authorization","value":ADM},CT], '{"display_name":"Admin Updated"}'),
                     test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                          "pm.test('Updated',()=>pm.expect(pm.response.json().display_name).to.eql('Admin Updated'));")),
            ]
        },
        {
            "name": "6.2 Courses",
            "item": [
                item("GET /admin/courses — List all",
                     req("GET", {"raw":f"{B}/admin/courses?limit=20&offset=0","query":[{"key":"limit","value":"20"},{"key":"offset","value":"0"}]},
                         [{"key":"Authorization","value":ADM}]),
                     test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                          "pm.test('Is array',()=>pm.expect(pm.response.json()).to.be.an('array'));")),
                item("GET /admin/courses/{id}",
                     req("GET", f"{B}/admin/courses/{{courseId}}", [{"key":"Authorization","value":ADM}]),
                     test("pm.test('Status 200',()=>pm.response.to.have.status(200));")),
                item("PATCH /admin/courses/{id} — Bypass ownership",
                     req("PATCH", f"{B}/admin/courses/{{courseId}}",
                         [{"key":"Authorization","value":ADM},CT], '{"description":"Updated by admin."}'),
                     test("pm.test('Status 200',()=>pm.response.to.have.status(200));")),
            ]
        },
        {
            "name": "6.3 Submissions & Progress",
            "item": [
                item("GET /admin/submissions",
                     req("GET", {"raw":f"{B}/admin/submissions?limit=20&offset=0","query":[{"key":"limit","value":"20"},{"key":"offset","value":"0"}]},
                         [{"key":"Authorization","value":ADM}]),
                     test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                          "pm.test('Is array',()=>pm.expect(pm.response.json()).to.be.an('array'));")),
                item("GET /admin/progress",
                     req("GET", {"raw":f"{B}/admin/progress?limit=20&offset=0","query":[{"key":"limit","value":"20"},{"key":"offset","value":"0"}]},
                         [{"key":"Authorization","value":ADM}]),
                     test("pm.test('Status 200',()=>pm.response.to.have.status(200));",
                          "pm.test('Is array',()=>pm.expect(pm.response.json()).to.be.an('array'));")),
            ]
        },
        {
            "name": "6.4 Cleanup",
            "item": [
                item("DELETE /admin/courses/{id}",
                     req("DELETE", f"{B}/admin/courses/{{courseId}}", [{"key":"Authorization","value":ADM}]),
                     test("pm.test('Status 204',()=>pm.response.to.have.status(204));")),
                item("GET /courses/{id} — After delete (expect 404)",
                     req("GET", f"{B}/courses/{{courseId}}", [{"key":"Authorization","value":ADM}]),
                     test("pm.test('Status 404',()=>pm.response.to.have.status(404));")),
            ]
        },
    ]
}

# ── Combine ───────────────────────────────────────────────────────────────────
collection = {
    "info": {
        "name": "Learning Platform — Phase 0-5 (All)",
        "description": "Complete test suite: Auth, Users, Courses, Lessons, Progress, Admin.\nRun folders in order 0→6. Base URL: http://localhost:8001",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl",                 "value": "http://localhost:8001/api/v1"},
        {"key": "adminAccessToken",        "value": ""},
        {"key": "instructorAccessToken",   "value": ""},
        {"key": "instructorRefreshToken",  "value": ""},
        {"key": "studentAccessToken",      "value": ""},
        {"key": "studentRefreshToken",     "value": ""},
        {"key": "courseId",                "value": ""},
        {"key": "lessonId",                "value": ""},
        {"key": "lesson2Id",               "value": ""},
        {"key": "targetUserId",            "value": ""},
    ],
    "item": [health, auth_folder, users_folder, courses_folder,
             lessons_folder, progress_folder, admin_folder]
}

environment = {
    "id": "learning-platform-local-all",
    "name": "Learning Platform — Local (Phase 0-5)",
    "values": [
        {"key": "baseUrl",               "value": "http://localhost:8001/api/v1", "type": "default",  "enabled": True},
        {"key": "adminEmail",            "value": "admin@example.com",            "type": "default",  "enabled": True},
        {"key": "adminPassword",         "value": "AdminPass1!",                  "type": "default",  "enabled": True},
        {"key": "adminAccessToken",      "value": "",                             "type": "secret",   "enabled": True},
        {"key": "instructorEmail",       "value": "instructor@example.com",       "type": "default",  "enabled": True},
        {"key": "instructorPassword",    "value": "InstrPass1!",                  "type": "default",  "enabled": True},
        {"key": "instructorAccessToken", "value": "",                             "type": "secret",   "enabled": True},
        {"key": "instructorRefreshToken","value": "",                             "type": "secret",   "enabled": True},
        {"key": "studentEmail",          "value": "student@example.com",          "type": "default",  "enabled": True},
        {"key": "studentPassword",       "value": "StudPass1!",                   "type": "default",  "enabled": True},
        {"key": "studentAccessToken",    "value": "",                             "type": "secret",   "enabled": True},
        {"key": "studentRefreshToken",   "value": "",                             "type": "secret",   "enabled": True},
        {"key": "courseId",              "value": "",                             "type": "default",  "enabled": True},
        {"key": "lessonId",              "value": "",                             "type": "default",  "enabled": True},
        {"key": "lesson2Id",             "value": "",                             "type": "default",  "enabled": True},
        {"key": "targetUserId",          "value": "",                             "type": "default",  "enabled": True},
    ],
    "_postman_variable_scope": "environment",
    "description": (
        "Environment for Learning Platform Phase 0-5.\n\n"
        "Usage:\n"
        "1. Import: Environments → Import\n"
        "2. Select 'Learning Platform — Local (Phase 0-5)'\n"
        "3. Run folder 1-Auth first — tokens auto-populate\n"
        "4. courseId, lessonId, etc. auto-set after creation\n\n"
        "Prerequisites:\n"
        "- Server: cd learning_platform && uv run uvicorn src.main:app --port 8001 --reload\n"
        "- Admin role: UPDATE users SET role='admin' WHERE email='admin@example.com';"
    )
}

OUT_COL.write_text(json.dumps(collection, indent=2))
OUT_ENV.write_text(json.dumps(environment, indent=2))
print(f"✓ {OUT_COL}")
print(f"✓ {OUT_ENV}")
