/**
 * Import function triggers from their respective submodules:
 *
 * const {onCall} = require("firebase-functions/v2/https");
 * const {onDocumentWritten} = require("firebase-functions/v2/firestore");
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

const {setGlobalOptions} = require("firebase-functions");
const {onRequest} = require("firebase-functions/https");
const logger = require("firebase-functions/logger");

// Enhanced logging utilities
const createLogger = (context = {}) => {
  const baseContext = {
    timestamp: new Date().toISOString(),
    service: "nedarim-callback",
    ...context,
  };

  return {
    info: (message, data = {}) => {
      logger.info(message, {
        ...baseContext,
        level: "INFO",
        ...data,
      });
    },
    warn: (message, data = {}) => {
      logger.warn(message, {
        ...baseContext,
        level: "WARN",
        ...data,
      });
    },
    error: (message, error = null, data = {}) => {
      const errorData = error ? {
        errorMessage: error.message,
        errorStack: error.stack,
        errorName: error.name,
        ...data,
      } : data;

      logger.error(message, {
        ...baseContext,
        level: "ERROR",
        ...errorData,
      });
    },
    debug: (message, data = {}) => {
      logger.info(message, {
        ...baseContext,
        level: "DEBUG",
        ...data,
      });
    },
  };
};

// Generate correlation ID for request tracking
const generateCorrelationId = () => {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Performance timing utility
const createTimer = (operation) => {
  const start = Date.now();
  return {
    end: (logFn) => {
      const duration = Date.now() - start;
      logFn(`Operation '${operation}' completed`, {duration: `${duration}ms`});
      return duration;
    },
  };
};

// For cost control, you can set the maximum number of containers that can be
// running at the same time. This helps mitigate the impact of unexpected
// traffic spikes by instead downgrading performance. This limit is a
// per-function limit. You can override the limit for each function using the
// `maxInstances` option in the function's options, e.g.
// `onRequest({ maxInstances: 5 }, (req, res) => { ... })`.
// NOTE: setGlobalOptions does not apply to functions using the v1 API. V1
// functions should each use functions.runWith({ maxInstances: 10 }) instead.
// In the v1 API, each function can only serve one request per container, so
// this will be the maximum concurrent request count.
setGlobalOptions({maxInstances: 10});

// Create and deploy your first functions
// https://firebase.google.com/docs/functions/get-started

// exports.helloWorld = onRequest((request, response) => {
//   logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });


const crypto = require("crypto");
const admin = require("firebase-admin");
const {onCall} = require("firebase-functions/v2/https");
const {onSchedule} = require("firebase-functions/v2/scheduler");
const functions = require("firebase-functions");

admin.initializeApp();

// Encryption key from env or Firebase config (32 bytes for AES-256)
const getEncryptionKey = () => {
  let key = process.env.ENCRYPTION_KEY;
  if (!key && typeof functions.config === "function") {
    const cfg = functions.config().nedarim;
    key = cfg && cfg.encryption_key;
  }
  if (key && String(key).length >= 32) {
    return Buffer.from(String(key).slice(0, 32), "utf8");
  }
  return null;
};

const ALGORITHM = "aes-256-cbc";
const IV_LENGTH = 16;

/**
 * Encrypt sensitive data. Uses AES-256-CBC if ENCRYPTION_KEY is configured,
 * otherwise falls back to base64 (logs warning).
 * @param {string|object} data - Data to encrypt (will be JSON stringified).
 * @return {string} Encrypted string (iv:data in base64, or plain base64).
 */
const encryptData = (data) => {
  const key = getEncryptionKey();
  if (key) {
    const iv = crypto.randomBytes(IV_LENGTH);
    const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
    const encrypted = Buffer.concat([
      cipher.update(JSON.stringify(data), "utf8"),
      cipher.final(),
    ]);
    return iv.toString("base64") + ":" + encrypted.toString("base64");
  }
  logger.warn("ENCRYPTION_KEY not configured — using base64 fallback");
  return Buffer.from(JSON.stringify(data)).toString("base64");
};

/**
 * Decrypt data. Tries AES-256-CBC first if key is configured,
 * otherwise treats input as base64. Use when reading encrypted org metadata.
 * @param {string} encrypted - Encrypted string from encryptData.
 * @return {string|object} Decrypted value (parsed from JSON).
 */
// eslint-disable-next-line no-unused-vars
const decryptData = (encrypted) => {
  const key = getEncryptionKey();
  if (key) {
    try {
      const [ivB64, dataB64] = encrypted.split(":");
      if (ivB64 && dataB64) {
        const iv = Buffer.from(ivB64, "base64");
        const data = Buffer.from(dataB64, "base64");
        const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
        return JSON.parse(
            decipher.update(data) + decipher.final("utf8"),
        );
      }
    } catch (e) {
      // Fall through to base64
    }
  }
  return JSON.parse(Buffer.from(encrypted, "base64").toString("utf8"));
};

/**
 * Nedarim Plus Callback Handler
 * Receives payment confirmation from Nedarim Plus
 */
exports.nedarimCallback = onRequest(async (req, res) => {
  const correlationId = generateCorrelationId();
  const log = createLogger({correlationId});
  const requestTimer = createTimer("nedarim-callback-request");

  // Declare variables at function scope for error handling
  let TransactionId;
  let Status;
  let purchaseId;
  let orgId;

  // Enhanced request logging
  log.info("Nedarim callback request received", {
    method: req.method,
    headers: {
      "user-agent": req.headers["user-agent"],
      "content-type": req.headers["content-type"],
      "content-length": req.headers["content-length"],
    },
    ip: req.ip,
    bodySize: JSON.stringify(req.body).length,
  });

  // Security logging for sensitive data (masked)
  const maskedBody = {
    ...req.body,
    CreditCardNumber: req.body.CreditCardNumber ? "****" : undefined,
  };
  log.debug("Request payload (masked)", {payload: maskedBody});

  try {
    // CALLBACK_SECRET: validate secret from query param or header if configured
    let callbackSecret = process.env.CALLBACK_SECRET;
    if (!callbackSecret && typeof functions.config === "function") {
      const cfg = functions.config().nedarim;
      callbackSecret = cfg && cfg.callback_secret;
    }
    if (callbackSecret) {
      const providedSecret = (req.query && req.query.secret) ||
          (req.headers && req.headers["x-callback-secret"]);
      if (providedSecret !== callbackSecret) {
        log.warn("Callback secret validation failed", {
          hasSecret: !!providedSecret,
        });
        return res.status(403).json({
          success: false,
          error: "Forbidden",
          correlationId,
        });
      }
    }

    // Nedarim Plus sends data via POST
    const paymentData = req.body || {};

    // Extract important fields
    const {
      Amount,
      CreditCardNumber,
      Param1, // purchaseId
      Param2, // orgId (MULTI-TENANCY)
      Message,
    } = paymentData;

    TransactionId = paymentData.TransactionId;
    Status = paymentData.Status;

    // Type validation: Amount must parse as number
    const amountNum = Amount != null ? Number(Amount) : NaN;
    if (Number.isNaN(amountNum) || amountNum < 0) {
      log.warn("Validation failed: Amount is not a valid number", {
        receivedAmount: Amount,
      });
      return res.status(400).json({
        success: false,
        error: "Invalid Amount",
        correlationId,
      });
    }

    // Param1 and Param2 must be non-empty strings
    if (typeof Param1 !== "string" || !Param1.trim()) {
      log.warn("Validation failed: Param1 must be a non-empty string", {
        receivedParam1: Param1,
      });
      return res.status(400).json({
        success: false,
        error: "Invalid Param1 (purchaseId)",
        correlationId,
      });
    }
    if (typeof Param2 !== "string" || !Param2.trim()) {
      log.warn("Validation failed: Param2 must be a non-empty string", {
        receivedParam2: Param2,
      });
      return res.status(400).json({
        success: false,
        error: "Invalid Param2 (orgId)",
        correlationId,
      });
    }

    log.info("Payment data extraction completed", {
      hasTransactionId: !!TransactionId,
      hasStatus: !!Status,
      hasAmount: !!Amount,
      hasCreditCard: !!CreditCardNumber,
      hasPurchaseId: !!Param1,
      hasOrgId: !!Param2,
      hasMessage: !!Message,
      statusValue: Status,
    });

    // Validate required fields
    if (!TransactionId || !Status) {
      const missingFields = [];
      if (!TransactionId) missingFields.push("TransactionId");
      if (!Status) missingFields.push("Status");

      log.error("Missing required fields", null, {
        missingFields,
        receivedFields: Object.keys(paymentData),
      });

      return res.status(400).json({
        success: false,
        error: "Missing required fields",
        missingFields,
        correlationId,
      });
    }

    // Parse purchaseId and orgId (already validated as non-empty strings)
    purchaseId = Param1.trim();
    orgId = Param2.trim();

    log.info("Payment data extracted successfully", {
      transactionId: TransactionId,
      status: Status,
      amount: Amount,
      purchaseId,
      orgId,
      hasCreditCard: !!CreditCardNumber,
      message: Message,
      rawParam1: Param1,
      rawParam2: Param2,
    });

    if (!purchaseId) {
      log.error("Missing purchaseId in Param1", null, {
        param1: Param1,
        param2: Param2,
        allParams: Object.keys(paymentData)
            .filter((key) => key.startsWith("Param")),
      });
      return res.status(400).json({
        success: false,
        error: "Missing purchaseId",
        correlationId,
      });
    }

    if (!orgId) {
      log.error("Missing orgId in Param2", null, {
        param1: Param1,
        param2: Param2,
        allParams: Object.keys(paymentData)
            .filter((key) => key.startsWith("Param")),
      });
      return res.status(400).json({
        success: false,
        error: "Missing orgId (multi-tenancy)",
        correlationId,
      });
    }

    // MULTI-TENANCY: Update purchase status in organization-specific path
    const purchaseRef = admin
        .database()
        .ref(`organizations/${orgId}/purchases/${purchaseId}`);

    const dbPath = `organizations/${orgId}/purchases/${purchaseId}`;
    log.info("Preparing database update", {
      path: dbPath,
      purchaseId,
      orgId,
      operation: "purchase-update",
    });

    // Sanitize: only store safe fields, never full raw payload
    const sanitizedRawResponse = {
      TransactionId,
      Status,
      Amount: amountNum,
      CreditCardNumber: CreditCardNumber ? "****" : undefined,
      Param1,
      Param2,
    };

    const updateData = {
      status: Status === "Error" ? "failed" : "completed",
      transactionId: TransactionId,
      amount: amountNum,
      creditCardNumber: CreditCardNumber || "****",
      message: Message || "",
      callbackReceivedAt: admin.database.ServerValue.TIMESTAMP,
      rawResponse: sanitizedRawResponse,
      correlationId,
      processedAt: new Date().toISOString(),
    };

    log.debug("Purchase update data prepared", {
      updateData: {
        ...updateData,
        rawResponse: "[REDACTED - see rawResponse field]",
      },
    });

    // Performance timing for database update
    const dbUpdateTimer = createTimer("purchase-database-update");
    await purchaseRef.update(updateData);
    dbUpdateTimer.end(log.info);

    log.info("Purchase status updated successfully", {
      purchaseId,
      orgId,
      status: updateData.status,
      transactionId: TransactionId,
    });

    // If successful, credit user account
    if (Status !== "Error") {
      log.info("Payment successful, initiating user crediting process", {
        status: Status,
        operation: "user-crediting",
      });

      // Performance timing for purchase retrieval
      const purchaseRetrievalTimer = createTimer("purchase-data-retrieval");
      const purchaseSnapshot = await purchaseRef.once("value");
      const purchase = purchaseSnapshot.val();
      purchaseRetrievalTimer.end(log.info);

      log.info("Purchase data retrieved for user crediting", {
        hasPurchase: !!purchase,
        hasUserId: !!(purchase && purchase.userId),
        purchaseId,
        userId: purchase && purchase.userId,
      });

      if (purchase && purchase.userId) {
        log.info("Starting user crediting process", {
          userId: purchase.userId,
          orgId,
          operation: "user-crediting",
        });

        // MULTI-TENANCY: Access user in organization-specific path
        const userRef = admin.database()
            .ref(`organizations/${orgId}/users/${purchase.userId}`);

        // Performance timing for user data retrieval
        const userRetrievalTimer = createTimer("user-data-retrieval");
        const userSnapshot = await userRef.once("value");
        const user = userSnapshot.val();
        userRetrievalTimer.end(log.info);

        log.info("User data retrieved for crediting", {
          hasUser: !!user,
          userId: purchase.userId,
          currentTime: (user && user.remainingTime) || 0,
          currentPrints: (user && user.printBalance) || 0,
        });

        if (user) {
          const currentTime = user.remainingTime || 0;
          const currentPrintBudget = user.printBalance || 0;
          const addingMinutes = purchase.minutes || 0;
          const addingPrintBudget = purchase.printBudget || 0;
          const validityDays = purchase.validityDays || 0;
          const newTime = currentTime + (addingMinutes * 60);
          const newPrintBudget = currentPrintBudget + addingPrintBudget;

          log.info("Calculating user credit amounts", {
            currentTime,
            addingMinutes,
            newTime,
            currentPrintBudget,
            addingPrintBudget,
            newPrintBudget,
            validityDays,
            userId: purchase.userId,
          });

          // Calculate expiration date if package has validity
          const updatePayload = {
            remainingTime: newTime,
            printBalance: newPrintBudget,
            updatedAt: new Date().toISOString(),
            lastCreditedAt: new Date().toISOString(),
            lastCreditedBy: "nedarim-callback",
            correlationId,
          };

          // Set time expiration if package has validityDays
          if (validityDays > 0) {
            const expiresAt = new Date();
            expiresAt.setDate(expiresAt.getDate() + validityDays);
            updatePayload.timeExpiresAt = expiresAt.toISOString();
            log.info("Setting time expiration", {
              validityDays,
              expiresAt: updatePayload.timeExpiresAt,
            });
          }

          // Performance timing for user update
          const userUpdateTimer = createTimer("user-crediting-update");
          await userRef.update(updatePayload);
          userUpdateTimer.end(log.info);

          log.info("User credited successfully", {
            userId: purchase.userId,
            orgId,
            timeAdded: addingMinutes,
            printBudgetAdded: addingPrintBudget,
            newTime,
            newPrintBudget,
          });
        } else {
          log.error("User not found in database", null, {
            userId: purchase.userId,
            orgId,
            userPath: `organizations/${orgId}/users/${purchase.userId}`,
          });
        }
      } else {
        log.error("Purchase missing userId or purchase not found", null, {
          hasPurchase: !!purchase,
          hasUserId: !!(purchase && purchase.userId),
          purchaseId,
          orgId,
        });
      }
    } else {
      log.info("Payment failed, skipping user crediting", {
        status: Status,
        reason: "payment-error",
      });
    }

    // Performance timing for entire request
    requestTimer.end(log.info);

    // Respond to Nedarim Plus
    const response = {
      success: true,
      message: "Callback processed successfully",
      correlationId,
      processedAt: new Date().toISOString(),
    };

    log.info("Callback processing completed successfully", {
      transactionId: TransactionId,
      status: Status,
      purchaseId,
      orgId,
      responseCode: 200,
    });

    res.status(200).json(response);
  } catch (error) {
    // Enhanced error logging with full context
    log.error("Error processing callback", error, {
      transactionId: TransactionId || "unknown",
      status: Status || "unknown",
      purchaseId: purchaseId || "unknown",
      orgId: orgId || "unknown",
      errorPhase: "callback-processing",
      requestBody: maskedBody,
    });

    const errorResponse = {
      success: false,
      error: error.message,
      correlationId,
      timestamp: new Date().toISOString(),
    };

    log.error("Sending error response", null, {
      responseCode: 500,
      errorResponse,
    });

    res.status(500).json(errorResponse);
  }
});

/**
 * Convert phone number to email format for Firebase Auth
 * Same logic as desktop client for consistency
 * @param {string} phone - Phone number (e.g., "0501234567")
 * @return {string} Email format (e.g., "0501234567@sionyx.app")
 */
const phoneToEmail = (phone) => {
  // Remove all non-digit characters
  const cleanPhone = phone.replace(/\D/g, "");
  return `${cleanPhone}@sionyx.app`;
};

/**
 * Reset User Password Function
 * Allows organization admin to reset a user's password
 * Called from web admin dashboard
 */
exports.resetUserPassword = onCall(async (request) => {
  const correlationId = generateCorrelationId();
  const log = createLogger({
    correlationId,
    service: "reset-user-password",
  });

  log.info("Password reset request received", {
    hasData: !!request.data,
    hasAuth: !!request.auth,
  });

  try {
    // Verify caller is authenticated
    if (!request.auth) {
      throw new functions.https.HttpsError(
          "unauthenticated",
          "Must be authenticated to reset passwords",
      );
    }

    const callerUid = request.auth.uid;
    const {orgId, userId, newPassword} = request.data;

    // Validate required fields
    if (!orgId || !userId || !newPassword) {
      throw new functions.https.HttpsError(
          "invalid-argument",
          "Missing required fields: orgId, userId, newPassword",
      );
    }

    // Validate password length
    if (newPassword.length < 6) {
      throw new functions.https.HttpsError(
          "invalid-argument",
          "הסיסמה חייבת להכיל לפחות 6 תווים",
      );
    }

    log.info("Validating caller permissions", {
      callerUid,
      orgId,
      targetUserId: userId,
    });

    // Verify caller is admin of the organization
    const callerRef = admin.database()
        .ref(`organizations/${orgId}/users/${callerUid}`);
    const callerSnapshot = await callerRef.once("value");

    if (!callerSnapshot.exists()) {
      log.warn("Caller not found in organization", {callerUid, orgId});
      throw new functions.https.HttpsError(
          "permission-denied",
          "You are not a member of this organization",
      );
    }

    const callerData = callerSnapshot.val();
    if (!callerData.isAdmin) {
      log.warn("Caller is not an admin", {callerUid, orgId});
      throw new functions.https.HttpsError(
          "permission-denied",
          "רק מנהלים יכולים לאפס סיסמאות",
      );
    }

    // Verify target user exists in organization
    const targetUserRef = admin.database()
        .ref(`organizations/${orgId}/users/${userId}`);
    const targetUserSnapshot = await targetUserRef.once("value");

    if (!targetUserSnapshot.exists()) {
      log.warn("Target user not found", {userId, orgId});
      throw new functions.https.HttpsError(
          "not-found",
          "המשתמש לא נמצא",
      );
    }

    const targetUserData = targetUserSnapshot.val();

    log.info("Resetting password for user", {
      targetUserId: userId,
      targetUserPhone: targetUserData.phoneNumber,
      callerUid,
    });

    // Reset the password using Firebase Admin SDK
    await admin.auth().updateUser(userId, {
      password: newPassword,
    });

    // Update user record with password reset timestamp
    await targetUserRef.update({
      passwordResetAt: new Date().toISOString(),
      passwordResetBy: callerUid,
      updatedAt: new Date().toISOString(),
    });

    log.info("Password reset successful", {
      targetUserId: userId,
      callerUid,
      correlationId,
    });

    return {
      success: true,
      message: "הסיסמה אופסה בהצלחה",
      correlationId,
    };
  } catch (error) {
    log.error("Error resetting password", error, {
      correlationId,
    });

    // Re-throw HttpsError as-is
    if (error instanceof functions.https.HttpsError) {
      throw error;
    }

    // Handle specific Firebase Auth errors
    if (error.code === "auth/user-not-found") {
      throw new functions.https.HttpsError(
          "not-found",
          "המשתמש לא נמצא במערכת האימות",
      );
    }

    throw new functions.https.HttpsError(
        "internal",
        "שגיאה באיפוס הסיסמה: " + error.message,
    );
  }
});

/**
 * Organization Registration Function
 * Handles secure registration of new organizations with NEDARIM credentials
 * AND creates the first admin user for the organization
 */
exports.registerOrganization = onCall(async (request) => {
  const correlationId = generateCorrelationId();
  const log = createLogger({
    correlationId,
    service: "organization-registration",
  });
  const requestTimer = createTimer("organization-registration-request");

  log.info("Organization registration request received", {
    hasData: !!request.data,
    dataKeys: request.data ? Object.keys(request.data) : [],
  });

  try {
    const {
      organizationName,
      nedarimMosadId,
      nedarimApiValid,
      // Admin user fields
      adminPhone,
      adminPassword,
      adminFirstName,
      adminLastName,
      adminEmail,
    } = request.data;

    // Minimal safety check - UI handles detailed validation
    if (!organizationName || !nedarimMosadId || !nedarimApiValid ||
        !adminPhone || !adminPassword || !adminFirstName || !adminLastName) {
      throw new functions.https.HttpsError(
          "invalid-argument",
          "חסרים שדות חובה",
      );
    }

    const cleanOrgName = organizationName.trim();
    const cleanMosadId = nedarimMosadId.trim();
    const cleanApiValid = nedarimApiValid.trim();
    const cleanAdminPhone = adminPhone.replace(/\D/g, "");

    log.info("Processing registration", {
      orgNameLength: cleanOrgName.length,
      hasAdminPhone: !!cleanAdminPhone,
    });

    // Use organization name as ID (normalized)
    const orgId = cleanOrgName.toLowerCase()
        .replace(/[^a-z0-9\u0590-\u05FF]/g, "") // Keep letters, numbers, Hebrew
        .replace(/\s+/g, ""); // Remove spaces

    // Validate orgId is not empty after normalization
    if (!orgId || orgId.length < 2) {
      throw new functions.https.HttpsError(
          "invalid-argument",
          "Organization name must contain valid characters",
      );
    }

    // Check for duplicate organization IDs
    const orgsRef = admin.database().ref("organizations");
    const orgsSnapshot = await orgsRef.once("value");

    if (orgsSnapshot.exists()) {
      const organizations = orgsSnapshot.val();

      // Check if orgId already exists
      if (organizations[orgId]) {
        log.warn("Organization ID already exists", {
          orgId,
          orgName: cleanOrgName,
        });

        throw new functions.https.HttpsError(
            "already-exists",
            "Organization name already exists",
        );
      }
    }

    log.info("Organization ID generated from name", {
      orgId,
      orgName: cleanOrgName,
    });

    // Step 1: Create admin user in Firebase Auth
    const adminFirebaseEmail = phoneToEmail(cleanAdminPhone);
    log.info("Creating admin user in Firebase Auth", {
      email: adminFirebaseEmail,
      phone: cleanAdminPhone,
    });

    let adminUid;
    try {
      const userRecord = await admin.auth().createUser({
        email: adminFirebaseEmail,
        password: adminPassword,
        displayName: `${adminFirstName} ${adminLastName}`,
      });
      adminUid = userRecord.uid;
      log.info("Admin user created in Firebase Auth", {uid: adminUid});
    } catch (authError) {
      log.error("Failed to create admin user in Firebase Auth", authError);

      // Handle specific Firebase Auth errors
      if (authError.code === "auth/email-already-exists") {
        throw new functions.https.HttpsError(
            "already-exists",
            "מספר הטלפון כבר רשום במערכת",
        );
      }

      throw new functions.https.HttpsError(
          "internal",
          "Failed to create admin user: " + authError.message,
      );
    }

    // Step 2: Prepare and save organization metadata
    const metadata = {
      name: cleanOrgName,
      nedarim_mosad_id: encryptData(cleanMosadId),
      nedarim_api_valid: encryptData(cleanApiValid),
      created_at: new Date().toISOString(),
      status: "active",
      created_by: "public-registration",
      admin_uid: adminUid,
      // Admin contact for password reset flow
      admin_phone: cleanAdminPhone,
      admin_email: adminEmail ? adminEmail.trim() : "",
      correlation_id: correlationId,
    };

    // Save to Firebase using correct hierarchy: organizations/{orgId}/metadata
    const orgRef = admin.database().ref(`organizations/${orgId}/metadata`);
    await orgRef.set(metadata);

    log.info("Organization metadata saved", {
      orgId,
      orgName: cleanOrgName,
      created_at: metadata.created_at,
    });

    // Step 3: Create admin user data in organization's users collection
    const adminUserData = {
      firstName: adminFirstName.trim(),
      lastName: adminLastName.trim(),
      phoneNumber: cleanAdminPhone,
      email: adminEmail ? adminEmail.trim() : "",
      remainingTime: 0, // Admins don't need time balance for admin dashboard
      printBalance: 0.0,
      // Active session is managed by sionyx-kiosk only
      isSessionActive: false,
      isAdmin: true, // This user is the organization admin
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      createdBy: "organization-registration",
      correlation_id: correlationId,
    };

    // Save admin user to organizations/{orgId}/users/{adminUid}
    const adminUserRef = admin.database()
        .ref(`organizations/${orgId}/users/${adminUid}`);
    await adminUserRef.set(adminUserData);

    log.info("Admin user data saved to organization", {
      orgId,
      adminUid,
      adminPhone: cleanAdminPhone,
      isAdmin: true,
    });

    // Performance timing for entire request
    requestTimer.end(log.info);

    return {
      success: true,
      orgId,
      adminUid,
      message: "Organization and admin user registered successfully",
      correlationId,
    };
  } catch (error) {
    // Enhanced error logging with full context
    log.error("Error registering organization", error, {
      errorPhase: "organization-registration",
      hasData: !!request.data,
      dataKeys: request.data ? Object.keys(request.data) : [],
    });

    // Re-throw HttpsError as-is
    if (error instanceof functions.https.HttpsError) {
      throw error;
    }

    // Convert other errors to HttpsError
    throw new functions.https.HttpsError(
        "internal",
        "Failed to register organization: " + error.message,
    );
  }
});

// ─── Inactive User Cleanup ─────────────────────────────────────────

const INACTIVE_DAYS_NEVER_PURCHASED = 7;

/**
 * Core cleanup logic shared by scheduled and manual triggers.
 * Deletes users who never purchased and registered 7+ days ago.
 * Never deletes admins.
 * @param {string|null} singleOrgId - If provided, only clean this org.
 * @return {object} Summary of cleanup results.
 */
const runCleanup = async (singleOrgId = null) => {
  const log = createLogger({service: "user-cleanup"});
  const timer = createTimer("user-cleanup");
  const msPerDay = 24 * 60 * 60 * 1000;
  const cutoff = Date.now() -
      (INACTIVE_DAYS_NEVER_PURCHASED * msPerDay);
  const summary = {orgs: 0, deleted: 0, skipped: 0, errors: 0};

  let orgsSnapshot;
  if (singleOrgId) {
    const orgRef = admin.database().ref(`organizations/${singleOrgId}`);
    const snap = await orgRef.once("value");
    if (!snap.exists()) {
      log.warn("Organization not found", {orgId: singleOrgId});
      return summary;
    }
    orgsSnapshot = {val: () => ({[singleOrgId]: snap.val()})};
  } else {
    orgsSnapshot = await admin.database().ref("organizations").once("value");
    const noData = !orgsSnapshot.exists ||
        (typeof orgsSnapshot.exists === "function" &&
        !orgsSnapshot.exists());
    if (noData) {
      log.info("No organizations found");
      return summary;
    }
  }

  const organizations = orgsSnapshot.val();

  for (const [orgId, orgData] of Object.entries(organizations)) {
    if (!orgData || !orgData.users) continue;
    summary.orgs++;

    const users = orgData.users || {};
    const purchases = orgData.purchases || {};

    // Build set of userIds that have at least one purchase
    const usersWithPurchases = new Set();
    for (const purchase of Object.values(purchases)) {
      if (purchase.userId) {
        usersWithPurchases.add(purchase.userId);
      }
    }

    for (const [userId, userData] of Object.entries(users)) {
      // Never delete admins
      if (userData.isAdmin) {
        summary.skipped++;
        continue;
      }

      // Keep users who ever purchased
      if (usersWithPurchases.has(userId)) {
        summary.skipped++;
        continue;
      }

      // Keep users registered less than 7 days ago
      const createdAt = userData.createdAt ?
          new Date(userData.createdAt).getTime() : 0;
      if (createdAt > cutoff) {
        summary.skipped++;
        continue;
      }

      // This user should be deleted
      try {
        log.info("Deleting inactive user", {orgId, userId});

        // 1. Delete user's messages
        if (orgData.messages) {
          const batch = {};
          for (const [msgId, msg] of Object.entries(orgData.messages)) {
            if (msg.toUserId === userId) {
              batch[`organizations/${orgId}/messages/${msgId}`] = null;
            }
          }
          if (Object.keys(batch).length > 0) {
            await admin.database().ref().update(batch);
          }
        }

        // 2. Clear computer association
        if (userData.currentComputerId && orgData.computers) {
          const comp = orgData.computers[userData.currentComputerId];
          if (comp && comp.currentUserId === userId) {
            const cId = userData.currentComputerId;
            const cPath =
                `organizations/${orgId}/computers/${cId}`;
            await admin.database().ref(cPath)
                .update({
                  currentUserId: null,
                  isActive: false,
                });
          }
        }

        // 3. Delete RTDB user record
        await admin.database()
            .ref(`organizations/${orgId}/users/${userId}`)
            .remove();

        // 4. Delete Firebase Auth account
        try {
          await admin.auth().deleteUser(userId);
        } catch (authErr) {
          if (authErr.code !== "auth/user-not-found") {
            log.warn("Failed to delete auth account", {
              userId, error: authErr.message,
            });
          }
        }

        summary.deleted++;
      } catch (err) {
        log.error("Error deleting user", err, {orgId, userId});
        summary.errors++;
      }
    }
  }

  timer.end(log.info);
  log.info("Cleanup complete", summary);
  return summary;
};

/**
 * Scheduled cleanup: runs every Saturday night at 3 AM Israel time.
 */
exports.cleanupInactiveUsers = onSchedule({
  schedule: "0 3 * * 0",
  timeZone: "Asia/Jerusalem",
  maxInstances: 1,
}, async () => {
  const log = createLogger({service: "scheduled-cleanup"});
  log.info("Starting scheduled inactive user cleanup");
  const summary = await runCleanup();
  log.info("Scheduled cleanup finished", summary);
});

/**
 * Delete a single user: callable from web admin.
 * Removes user record, messages, computer association, and auth account.
 */
exports.deleteUser = onCall(async (request) => {
  const correlationId = generateCorrelationId();
  const log = createLogger({correlationId, service: "delete-user"});

  if (!request.auth) {
    throw new functions.https.HttpsError(
        "unauthenticated", "Must be authenticated",
    );
  }

  const {orgId, userId} = request.data || {};
  if (!orgId || !userId) {
    throw new functions.https.HttpsError(
        "invalid-argument", "Missing orgId or userId",
    );
  }

  // Verify caller is admin
  const callerRef = admin.database()
      .ref(`organizations/${orgId}/users/${request.auth.uid}`);
  const callerSnap = await callerRef.once("value");
  if (!callerSnap.exists() || !callerSnap.val().isAdmin) {
    throw new functions.https.HttpsError(
        "permission-denied", "רק מנהלים יכולים למחוק משתמשים",
    );
  }

  // Cannot delete yourself
  if (userId === request.auth.uid) {
    throw new functions.https.HttpsError(
        "failed-precondition", "לא ניתן למחוק את עצמך",
    );
  }

  // Check target user exists
  const userRef = admin.database()
      .ref(`organizations/${orgId}/users/${userId}`);
  const userSnap = await userRef.once("value");
  if (!userSnap.exists()) {
    throw new functions.https.HttpsError("not-found", "המשתמש לא נמצא");
  }

  const userData = userSnap.val();

  // Prevent deleting other admins
  if (userData.isAdmin) {
    throw new functions.https.HttpsError(
        "failed-precondition", "לא ניתן למחוק משתמש מנהל",
    );
  }

  log.info("Deleting user", {orgId, userId, callerUid: request.auth.uid});

  // 1. Delete messages
  const messagesSnap = await admin.database()
      .ref(`organizations/${orgId}/messages`).once("value");
  if (messagesSnap.exists()) {
    const batch = {};
    for (const [msgId, msg] of Object.entries(messagesSnap.val())) {
      if (msg.toUserId === userId) {
        batch[`organizations/${orgId}/messages/${msgId}`] = null;
      }
    }
    if (Object.keys(batch).length > 0) {
      await admin.database().ref().update(batch);
    }
  }

  // 2. Clear computer association
  if (userData.currentComputerId) {
    const compRef = admin.database()
        .ref(`organizations/${orgId}/computers/${userData.currentComputerId}`);
    const compSnap = await compRef.once("value");
    if (compSnap.exists() && compSnap.val().currentUserId === userId) {
      await compRef.update({currentUserId: null, isActive: false});
    }
  }

  // 3. Delete user record
  await userRef.remove();

  // 4. Delete auth account
  try {
    await admin.auth().deleteUser(userId);
  } catch (authErr) {
    if (authErr.code !== "auth/user-not-found") {
      log.warn("Failed to delete auth account", {
        userId, error: authErr.message,
      });
    }
  }

  log.info("User deleted successfully", {orgId, userId});
  return {success: true, message: "המשתמש נמחק בהצלחה", correlationId};
});
