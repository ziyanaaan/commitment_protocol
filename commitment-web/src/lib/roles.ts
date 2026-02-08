/**
 * Role-based utilities for the Commitment Protocol.
 * Used to determine permissions and routing based on user role.
 */

export type Role = "client" | "freelancer" | "admin";

/**
 * Get the dashboard path for a given role.
 */
export function getDashboardPath(role: Role): string {
    if (role === "admin") return "/admin";
    return role === "client" ? "/dashboard/client" : "/dashboard/freelancer";
}

/**
 * Client-allowed actions by commitment status.
 */
const clientActions: Record<string, string[]> = {
    draft: ["fund"],
    funded: [],
    paid: [],
    locked: [],
    delivered: [],
    expired: [],
    settled: [],
};

/**
 * Freelancer-allowed actions by commitment status.
 */
const freelancerActions: Record<string, string[]> = {
    draft: [],
    funded: [],
    paid: ["lock"],
    locked: ["deliver"],
    delivered: [],
    expired: [],
    settled: [],
};

/**
 * Get allowed actions for a role and status combination.
 */
export function getActionsByRoleAndStatus(role: Role, status: string): string[] {
    if (role === "client") {
        return clientActions[status] || [];
    }
    return freelancerActions[status] || [];
}

/**
 * Check if a specific action is allowed for a role and status.
 */
export function canPerformAction(role: Role, status: string, action: string): boolean {
    const allowed = getActionsByRoleAndStatus(role, status);
    return allowed.includes(action);
}

/**
 * Get status message for a role - what the user should know about current state.
 */
export function getStatusMessage(role: Role, status: string): string {
    if (role === "client") {
        switch (status) {
            case "draft":
                return "Awaiting your payment to fund this commitment.";
            case "funded":
                return "Payment processing...";
            case "paid":
                return "Waiting for freelancer to lock the commitment.";
            case "locked":
                return "Work in progress. Freelancer is working on delivery.";
            case "delivered":
                return "Work delivered. Pending settlement.";
            case "settled":
                return "Commitment completed and settled.";
            case "expired":
                return "This commitment has expired.";
            default:
                return "";
        }
    } else {
        // freelancer
        switch (status) {
            case "draft":
                return "Waiting for client to fund this commitment.";
            case "funded":
                return "Client payment is being processed.";
            case "paid":
                return "Ready for you to lock and start working.";
            case "locked":
                return "Commitment locked. Complete the work and deliver.";
            case "delivered":
                return "Work delivered. Awaiting settlement.";
            case "settled":
                return "Commitment completed. Payout processed.";
            case "expired":
                return "This commitment has expired.";
            default:
                return "";
        }
    }
}
