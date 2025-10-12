import { ref, update, get, set } from 'firebase/database';
import { database } from '../config/firebase';
import { PURCHASE_STATUS } from '../constants/purchaseStatus';

/**
 * Nedarim Plus Callback Service
 * Handles payment confirmation callbacks and updates the database
 * This replaces the Firebase function with a React-based endpoint
 */
export class CallbackService {
  /**
   * Process Nedarim Plus payment callback
   * @param {Object} paymentData - Payment data from Nedarim Plus
   * @returns {Promise<Object>} - Result of the operation
   */
  static async processCallback(paymentData) {
    try {
      console.log("Nedarim callback received:", paymentData);

      // Extract important fields
      const {
        TransactionId,
        Status,
        Amount,
        CreditCardNumber,
        Param1, // purchaseId
        Param2, // orgId (MULTI-TENANCY)
        Message,
      } = paymentData;

      // Validate required fields
      if (!TransactionId || !Status) {
        console.error("Missing required fields");
        return {
          success: false,
          error: "Missing required fields",
        };
      }

      // Parse purchaseId and orgId
      const purchaseId = Param1;
      const orgId = Param2;

      if (!purchaseId) {
        console.error("Missing purchaseId in Param1");
        return {
          success: false,
          error: "Missing purchaseId",
        };
      }

      if (!orgId) {
        console.error("Missing orgId in Param2");
        return {
          success: false,
          error: "Missing orgId (multi-tenancy)",
        };
      }

      // MULTI-TENANCY: Update purchase status in organization-specific path
      const purchaseRef = ref(database, `organizations/${orgId}/purchases/${purchaseId}`);

      const updateData = {
        status: CallbackService.getStatusFromNedarim(Status),
        transactionId: TransactionId,
        amount: Amount,
        creditCardNumber: CreditCardNumber || "****",
        message: Message || "",
        callbackReceivedAt: new Date().toISOString(),
        rawResponse: paymentData,
      };

      await update(purchaseRef, updateData);

      console.log(`Purchase ${purchaseId} updated: ${updateData.status}`);

      // If successful, credit user account
      if (Status !== "Error") {
        const purchaseSnapshot = await get(purchaseRef);
        const purchase = purchaseSnapshot.val();

        if (purchase && purchase.userId) {
          // MULTI-TENANCY: Access user in organization-specific path
          const userRef = ref(database, `organizations/${orgId}/users/${purchase.userId}`);
          const userSnapshot = await get(userRef);
          const user = userSnapshot.val();

          if (user) {
            const newTime = (user.remainingTime || 0) +
              (purchase.minutes || 0) * 60;
            const newPrints = (user.remainingPrints || 0) +
              (purchase.prints || 0);

            await update(userRef, {
              remainingTime: newTime,
              remainingPrints: newPrints,
              updatedAt: new Date().toISOString(),
            });

            console.log(`User ${purchase.userId} credited successfully`);
          }
        }
      }

      return {
        success: true,
        message: "Callback processed successfully",
      };
    } catch (error) {
      console.error("Error processing callback:", error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Validate callback request (basic security check)
   * @param {Object} requestData - Request data to validate
   * @returns {boolean} - Whether the request is valid
   */
  static validateCallbackRequest(requestData) {
    // Basic validation - you can add more security checks here
    // like checking for specific headers, IP whitelist, etc.
    return requestData && 
           typeof requestData === 'object' && 
           requestData.TransactionId && 
           requestData.Status;
  }

  /**
   * Get the appropriate status value based on Nedarim response
   * @param {string} nedarimStatus - Status from Nedarim Plus
   * @returns {string} - Standardized status value
   */
  static getStatusFromNedarim(nedarimStatus) {
    return nedarimStatus === "Error" ? PURCHASE_STATUS.FAILED : PURCHASE_STATUS.COMPLETED;
  }
}
