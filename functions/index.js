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


const admin = require("firebase-admin");

admin.initializeApp();

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
    // Nedarim Plus sends data via POST
    const paymentData = req.body;

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

    // Parse purchaseId and orgId
    purchaseId = Param1;
    orgId = Param2;

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

    const updateData = {
      status: Status === "Error" ? "failed" : "completed",
      transactionId: TransactionId,
      amount: Amount,
      creditCardNumber: CreditCardNumber || "****",
      message: Message || "",
      callbackReceivedAt: admin.database.ServerValue.TIMESTAMP,
      rawResponse: paymentData,
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
          currentPrints: (user && user.remainingPrints) || 0,
        });

        if (user) {
          const currentTime = user.remainingTime || 0;
          const currentPrints = user.remainingPrints || 0;
          const addingMinutes = purchase.minutes || 0;
          const addingPrints = purchase.prints || 0;
          const newTime = currentTime + (addingMinutes * 60);
          const newPrints = currentPrints + addingPrints;

          log.info("Calculating user credit amounts", {
            currentTime,
            addingMinutes,
            newTime,
            currentPrints,
            addingPrints,
            newPrints,
            userId: purchase.userId,
          });

          // Performance timing for user update
          const userUpdateTimer = createTimer("user-crediting-update");
          await userRef.update({
            remainingTime: newTime,
            remainingPrints: newPrints,
            updatedAt: new Date().toISOString(),
            lastCreditedAt: new Date().toISOString(),
            lastCreditedBy: "nedarim-callback",
            correlationId,
          });
          userUpdateTimer.end(log.info);

          log.info("User credited successfully", {
            userId: purchase.userId,
            orgId,
            timeAdded: addingMinutes,
            printsAdded: addingPrints,
            newTime,
            newPrints,
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
