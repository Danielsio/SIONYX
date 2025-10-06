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
  // Log incoming request
  logger.info("Nedarim callback received:", req.body);

  try {
    // Nedarim Plus sends data via POST
    const paymentData = req.body;

    // Extract important fields
    const {
      TransactionId,
      Status,
      Amount,
      CreditCardNumber,
      Param1, // We'll use this to store purchaseId
      Message,
    } = paymentData;

    // Validate required fields
    if (!TransactionId || !Status) {
      logger.error("Missing required fields");
      return res.status(400).json({
        success: false,
        error: "Missing required fields",
      });
    }

    // Parse purchaseId from Param1
    const purchaseId = Param1;

    if (!purchaseId) {
      logger.error("Missing purchaseId in Param1");
      return res.status(400).json({
        success: false,
        error: "Missing purchaseId",
      });
    }

    // Update purchase status in Firebase
    const purchaseRef = admin
        .database()
        .ref(`purchases/${purchaseId}`);

    const updateData = {
      status: Status === "Error" ? "failed" : "completed",
      transactionId: TransactionId,
      amount: Amount,
      creditCardNumber: CreditCardNumber || "****",
      message: Message || "",
      callbackReceivedAt: admin.database.ServerValue.TIMESTAMP,
      rawResponse: paymentData,
    };

    await purchaseRef.update(updateData);

    logger.log(`Purchase ${purchaseId} updated: ${updateData.status}`);

    // If successful, credit user account
    if (Status !== "Error") {
      const purchaseSnapshot = await purchaseRef.once("value");
      const purchase = purchaseSnapshot.val();

      if (purchase && purchase.userId) {
        const userRef = admin.database().ref(`users/${purchase.userId}`);
        const userSnapshot = await userRef.once("value");
        const user = userSnapshot.val();

        if (user) {
          const newTime = (user.remainingTime || 0) +
            (purchase.minutes || 0) * 60;
          const newPrints = (user.remainingPrints || 0) +
            (purchase.prints || 0);

          await userRef.update({
            remainingTime: newTime,
            remainingPrints: newPrints,
            updatedAt: new Date().toISOString(),
          });

          logger.log(`User ${purchase.userId} credited successfully`);
        }
      }
    }

    // Respond to Nedarim Plus
    res.status(200).json({
      success: true,
      message: "Callback processed successfully",
    });
  } catch (error) {
    logger.error("Error processing callback:", error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});
