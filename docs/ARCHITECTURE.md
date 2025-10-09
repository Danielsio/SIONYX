# SIONYX Architecture

## Multi-Tenant Design

SIONYX uses a **multi-tenant architecture** where a single Firebase project serves multiple organizations with complete data isolation.

## Database Structure

```
Firebase Realtime Database (ONE PROJECT)
│
├── config/
│   └── superAdminUid: "abc123..."       # Super admin UID
│
└── organizations/
    ├── tech-lab/                        # Organization 1
    │   ├── metadata/
    │   │   ├── name: "Tech Lab"
    │   │   ├── createdAt: "2024-..."
    │   │   └── status: "active"
    │   ├── users/
    │   │   ├── user1/
    │   │   │   ├── firstName: "John"
    │   │   │   ├── remainingTime: 3600
    │   │   │   └── isAdmin: true
    │   │   └── user2/
    │   ├── packages/
    │   │   ├── pkg1/
    │   │   │   ├── name: "Quick Session"
    │   │   │   ├── price: 25
    │   │   │   └── minutes: 30
    │   │   └── pkg2/
    │   ├── sessions/
    │   │   └── session1/
    │   └── purchases/
    │       └── purchase1/
    │
    ├── school123/                       # Organization 2
    │   ├── metadata/
    │   ├── users/
    │   ├── packages/
    │   ├── sessions/
    │   └── purchases/
    │
    └── mycompany/                       # Organization 3
        ├── metadata/
        ├── users/
        ├── packages/
        ├── sessions/
        └── purchases/
```

## Data Isolation

### How It Works

1. **Organization ID in .env**
   ```bash
   ORG_ID=tech-lab
   ```

2. **Firebase Client Prefixing**
   - All database operations automatically prefix with `organizations/{ORG_ID}/`
   - Example: Reading users → `GET /organizations/tech-lab/users`

3. **Security Rules**
   ```javascript
   {
     "rules": {
       "organizations": {
         "$orgId": {
           "users": {
             ".read": "auth != null",
             "$userId": {
               ".write": "$userId === auth.uid || 
                         root.child('organizations').child($orgId)
                         .child('users').child(auth.uid)
                         .child('isAdmin').val() === true"
             }
           }
         }
       }
     }
   }
   ```

## Components

### Desktop Application (Python/PyQt6)

```
┌─────────────────────────────────┐
│     SIONYX Desktop App          │
│  (Python 3.10+, PyQt6)          │
├─────────────────────────────────┤
│  • Auth Window                  │
│  • Main Window (Dashboard)      │
│  • Package Selection            │
│  • Floating Timer               │
│  • Payment Dialog (Nedarim)     │
└──────────────┬──────────────────┘
               │
               │ HTTPS REST API
               ▼
┌─────────────────────────────────┐
│   Firebase Client               │
│   (requests library)            │
├─────────────────────────────────┤
│  • JWT Token Management         │
│  • Auto-retry Logic             │
│  • Organization Path Prefixing  │
│  • Offline Queue                │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   Firebase Backend              │
│   (Single Project)              │
├─────────────────────────────────┤
│  • Authentication               │
│  • Realtime Database            │
│  • Cloud Functions              │
│  • Security Rules               │
└─────────────────────────────────┘
```

### Admin Dashboard (React/Vite)

```
┌─────────────────────────────────┐
│   Admin Dashboard               │
│   (React + Vite)                │
├─────────────────────────────────┤
│  • Login Page                   │
│  • Overview (Stats)             │
│  • Users Management             │
│  • Packages Management          │
└──────────────┬──────────────────┘
               │
               │ Firebase SDK
               ▼
┌─────────────────────────────────┐
│   Firebase Backend              │
│   (Same Project)                │
└─────────────────────────────────┘
```

## Authentication Flow

### User Authentication

```
1. User enters phone number (e.g., 0501234567)
   ↓
2. App converts to email: 0501234567@sionyx.app
   ↓
3. Firebase Authentication verifies credentials
   ↓
4. Returns JWT token + UID
   ↓
5. App reads user data from: organizations/{ORG_ID}/users/{UID}
   ↓
6. Load user dashboard
```

### Admin Authentication

```
1. Admin logs in with phone + password
   ↓
2. Check: organizations/{ORG_ID}/users/{UID}/isAdmin === true
   ↓
3. If admin: Grant admin dashboard access
   If not: Regular user access only
```

### Super Admin

```
1. Super admin UID stored in: /config/superAdminUid
   ↓
2. Super admin can:
   • Create new organizations
   • Access all organizations' data
   • Manage super admin settings
   ↓
3. Security rules check: auth.uid === root.child('config/superAdminUid').val()
```

## Session Management

```
┌──────────────┐
│  User Clicks │
│ "Start Work" │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────┐
│ Create Session              │
│ organizations/{ORG_ID}/     │
│   sessions/{SESSION_ID}     │
│   {                         │
│     userId: "abc",          │
│     startTime: 1234567890,  │
│     remainingSeconds: 3600, │
│     status: "active"        │
│   }                         │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Show Floating Timer         │
│ (Minimize main window)      │
└──────┬──────────────────────┘
       │
       │ Every 10 seconds
       ▼
┌─────────────────────────────┐
│ Sync to Firebase            │
│ Update remainingSeconds     │
└──────┬──────────────────────┘
       │
       │ Time expires
       ▼
┌─────────────────────────────┐
│ End Session                 │
│ Update user's remainingTime │
│ Show summary                │
└─────────────────────────────┘
```

## Payment Flow (Nedarim Plus)

```
┌──────────────┐
│ User Selects │
│   Package    │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────┐
│ Open Payment Dialog         │
│ (QWebEngineView + HTML)     │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ User Fills Payment Form     │
│ (Name, Address, etc.)       │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Create Pending Purchase     │
│ organizations/{ORG_ID}/     │
│   purchases/{PURCHASE_ID}   │
│   {                         │
│     status: "pending",      │
│     amount: 40,             │
│     packageId: "pkg123"     │
│   }                         │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Send to Nedarim iframe      │
│ (With PURCHASE_ID + ORG_ID) │
└──────┬──────────────────────┘
       │
       │ User completes payment
       ▼
┌─────────────────────────────┐
│ Nedarim Plus Callback       │
│ → Firebase Cloud Function   │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Update Purchase Status      │
│ Add time to user account    │
│ status: "completed"         │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Notify Desktop App          │
│ Show success message        │
└─────────────────────────────┘
```

## Multi-Organization Benefits

### Cost Efficiency
- **Single Firebase project** → One subscription
- **Shared infrastructure** → Lower per-org costs
- **Centralized management** → Easier maintenance

### Scalability
- Add new organizations without new Firebase projects
- All organizations benefit from infrastructure improvements
- Easier to implement cross-organization features (if needed)

### Data Isolation
- **Complete separation** via database paths
- **Security rules** enforce organization boundaries
- **No cross-org data leaks** possible

### Management
- **One admin dashboard** can manage all organizations
- **Super admin** has overview of entire system
- **Per-org admins** manage only their organization

## Environment Configuration

### Organization 1 (.env.tech-lab)
```bash
ORG_ID=tech-lab
FIREBASE_API_KEY=AIzaSy...       # SAME
FIREBASE_DATABASE_URL=https://... # SAME
FIREBASE_PROJECT_ID=my-project   # SAME
```

### Organization 2 (.env.school123)
```bash
ORG_ID=school123                  # DIFFERENT
FIREBASE_API_KEY=AIzaSy...       # SAME
FIREBASE_DATABASE_URL=https://... # SAME
FIREBASE_PROJECT_ID=my-project   # SAME
```

### Organization 3 (.env.mycompany)
```bash
ORG_ID=mycompany                  # DIFFERENT
FIREBASE_API_KEY=AIzaSy...       # SAME
FIREBASE_DATABASE_URL=https://... # SAME
FIREBASE_PROJECT_ID=my-project   # SAME
```

## Security Considerations

### Data Isolation
- ✅ Organization data stored under separate paths
- ✅ Security rules enforce access boundaries
- ✅ JWT tokens include user UID but not organization context
- ✅ App prefixes all database paths with ORG_ID

### Access Control
- **Regular Users**: Can only access their own data within their organization
- **Organization Admins**: Can manage users and packages in their organization
- **Super Admin**: Can access all organizations (for setup and troubleshooting)

### Payment Security
- Payment credentials (Nedarim) stored in local .env only
- Purchase IDs include organization context
- Firebase Cloud Function validates organization before processing

## Technology Stack

### Desktop Application
- **Python 3.10+**: Core language
- **PyQt6**: GUI framework
- **requests**: HTTP client for Firebase REST API
- **cryptography**: Local data encryption
- **python-dotenv**: Environment variable management

### Admin Dashboard
- **React**: UI framework
- **Vite**: Build tool
- **Firebase SDK**: Direct Firebase integration
- **Zustand**: State management

### Backend
- **Firebase Authentication**: User authentication
- **Firebase Realtime Database**: Data storage
- **Firebase Cloud Functions**: Server-side logic (Node.js)
- **Firebase Security Rules**: Access control

### Payment
- **Nedarim Plus**: Payment gateway
- **QWebEngineView**: Embedded browser for payment form
- **postMessage API**: JavaScript-Python communication

## Deployment Scenarios

### Scenario 1: Multiple Physical Locations
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Tech Lab       │     │  School Lab     │     │  Company Office │
│  (Desktop PC)   │     │  (Desktop PC)   │     │  (Desktop PC)   │
│  ORG_ID:        │     │  ORG_ID:        │     │  ORG_ID:        │
│  tech-lab       │     │  school123      │     │  mycompany      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Firebase       │
                        │  (ONE Project)  │
                        └─────────────────┘
```

### Scenario 2: Development/Testing
```
Developer Machine
├── .env.dev → ORG_ID=dev-test
├── .env.staging → ORG_ID=staging-test
└── .env.production → ORG_ID=production-org

$ python launch_org.py dev-test        # Test with dev data
$ python launch_org.py staging-test    # Test with staging
$ python launch_org.py production-org  # Use production
```

## Future Considerations

### Potential Enhancements
- Organization-level settings and customization
- Cross-organization reporting for super admin
- Organization branding (logos, colors) in desktop app
- Usage-based billing per organization
- Organization backup and export tools

### Scalability
- Current architecture supports hundreds of organizations
- For thousands: Consider sharding by region or industry
- Firebase Realtime Database scales to millions of concurrent connections
- Cloud Functions can handle high request volumes with auto-scaling

---

For installation instructions, see [INSTALLATION.md](INSTALLATION.md)
For API documentation, see [API.md](API.md)


