# SIONYX Admin Dashboard

A modern, responsive admin dashboard for managing SIONYX organizations, users, and packages.

## Features

- 🔐 **Secure Authentication** - Firebase-based admin login
- 📊 **Overview Dashboard** - Real-time statistics and analytics
- 👥 **User Management** - View and manage organization users
- 📦 **Package Management** - Full CRUD operations for packages
- 🎨 **Modern UI** - Built with Ant Design components
- 📱 **Responsive** - Works on desktop, tablet, and mobile

## Tech Stack

- **React 19** - UI library
- **Vite** - Build tool and dev server
- **Firebase** - Authentication and Realtime Database
- **Ant Design** - UI component library
- **Zustand** - State management
- **React Router** - Navigation
- **Axios** - HTTP client
- **Day.js** - Date formatting

## Setup

### 1. Install Dependencies

```bash
cd admin-dashboard
npm install
```

### 2. Configure Environment

Create a `.env` file in the `admin-dashboard` directory:

```env
VITE_FIREBASE_API_KEY=your_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abcdef
```

### 3. Create Admin Users

You need to create admin users in Firebase before you can log in. See the `scripts/seed-admin.js` file for a seeding script, or manually create admins using the Firebase Console.

**Admin Data Structure:**
```javascript
organizations/{orgId}/admins/{adminId}
{
  email: "admin@example.com",
  displayName: "Admin Name",
  orgId: "your-org-id",
  role: "admin",
  createdAt: "2025-10-08T12:00:00.000Z",
  lastLogin: null
}

// Also create a mapping for quick lookup:
adminMappings/{adminId}
{
  orgId: "your-org-id"
}
```

### 4. Run Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Preview Production Build

```bash
npm run preview
```

## Project Structure

```
admin-dashboard/
├── src/
│   ├── components/          # Reusable components
│   │   ├── MainLayout.jsx   # Main layout with sidebar
│   │   └── ProtectedRoute.jsx  # Route guard
│   ├── config/
│   │   └── firebase.js      # Firebase configuration
│   ├── pages/               # Page components
│   │   ├── LoginPage.jsx
│   │   ├── OverviewPage.jsx
│   │   ├── UsersPage.jsx
│   │   └── PackagesPage.jsx
│   ├── services/            # API services
│   │   ├── authService.js
│   │   ├── organizationService.js
│   │   ├── userService.js
│   │   └── packageService.js
│   ├── store/               # State management
│   │   ├── authStore.js
│   │   └── dataStore.js
│   ├── App.jsx              # Main app component
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── public/                  # Static assets
├── .env                     # Environment variables
├── package.json
└── vite.config.js
```

## Features in Detail

### Authentication

- Admins log in with email/password
- Firebase Authentication handles auth
- Admin data stored in Realtime Database
- Protected routes require authentication
- Auto-logout on session expiry

### Overview Dashboard

- Total users count
- Total packages count
- Total purchases count
- Revenue statistics
- Time statistics
- Quick averages and metrics

### Users Management

- List all users in organization
- Search and filter users
- View user details
- See user purchase history
- View remaining time and prints
- Sort by various criteria

### Package Management

- List all packages
- Create new packages
- Edit existing packages
- Delete packages
- View package details
- Calculate discounted prices
- Sort and filter packages

## Data Design

The dashboard uses Firebase Realtime Database with the following structure:

```
organizations/
  └── {orgId}/
      ├── admins/
      │   └── {adminId}/
      │       ├── email
      │       ├── displayName
      │       ├── orgId
      │       ├── role
      │       └── lastLogin
      ├── users/
      │   └── {userId}/
      │       ├── firstName
      │       ├── lastName
      │       ├── phoneNumber
      │       ├── email
      │       ├── remainingTime
      │       ├── remainingPrints
      │       └── isActive
      ├── packages/
      │   └── {packageId}/
      │       ├── name
      │       ├── description
      │       ├── price
      │       ├── discountPercent
      │       ├── timeMinutes
      │       └── prints
      └── purchases/
          └── {purchaseId}/
              ├── userId
              ├── packageId
              ├── status
              └── ...

adminMappings/
  └── {adminId}/
      └── orgId
```

## Security

- Firebase Authentication for admin login
- Protected routes using React Router
- Organization data isolation
- Admin-only access to dashboard
- Secure environment variables

## Troubleshooting

### "Organization not found" Error

Make sure:
1. Admin user exists in Firebase Auth
2. Admin data exists in `organizations/{orgId}/admins/{adminId}`
3. Admin mapping exists in `adminMappings/{adminId}`

### Cannot login

1. Check Firebase credentials in `.env`
2. Verify admin email/password in Firebase Console
3. Check browser console for errors
4. Ensure Firebase Realtime Database rules allow read/write

### Data not loading

1. Check Firebase Realtime Database rules
2. Verify organization ID is correct
3. Check network tab for failed requests
4. Look for CORS issues

## Support

For issues or questions, refer to:
- `docs/ADMIN_DATA_DESIGN.md` - Data structure documentation
- `docs/MULTI_TENANCY_GUIDE.md` - Multi-tenancy setup
- Firebase Console - Database and Auth debugging

## License

Proprietary - SIONYX

