"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { actionsByStatus } from "@/lib/status";

type Commitment = {
  id: number;
  status: string;
  amount: number;
  deadline: string;
};

type Payment = {
  status: string;
};

export default function CommitmentPage() {
  const { id } = useParams<{ id: string }>();
  const [commitment, setCommitment] = useState<Commitment | null>(null);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    try {
      const c = await api<Commitment>(`/commitments/${id}`);
      setCommitment(c);

      try {
        const p = await api<Payment>(`/payments/${id}`);
        setPayment(p);
      } catch {
        setPayment(null);
      }
    } catch (e: any) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  async function action(path: string) {
    setLoading(true);
    setError(null);
    try {
      await api(path, { method: "POST" });
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (error) {
    return <p style={{ color: "red" }}>{error}</p>;
  }

  if (!commitment) {
    return <p>Loading…</p>;
  }

  const allowed = actionsByStatus[commitment.status] || [];
async function pay() {
  if (!commitment) return;

  // Step 1: fund (create Razorpay order)
  const res = await api<any>(`/commitments/${id}/fund`, {
    method: "POST",
  });

  const options = {
    key: res.razorpay_key,
    amount: res.amount,
    currency: res.currency,
    order_id: res.order_id,
    name: "Commitment Protocol",
    description: `Commitment #${id}`,
    handler: async function (response: any) {
      // Step 2: verify payment
      await api("/payments/verify", {
        method: "POST",
        body: JSON.stringify({
          razorpay_order_id: response.razorpay_order_id,
          razorpay_payment_id: response.razorpay_payment_id,
          razorpay_signature: response.razorpay_signature,
        }),
      });

      // reload state
      await load();
    },
  };

  const rzp = new (window as any).Razorpay(options);
  rzp.open();
}

  return (
    <main style={{ padding: 20 }}>
      <h1>Commitment #{commitment.id}</h1>

      <p><b>Status:</b> {commitment.status}</p>
      <p><b>Amount:</b> ₹{commitment.amount}</p>
      <p><b>Deadline:</b> {new Date(commitment.deadline).toLocaleString()}</p>

      <p>
        <b>Payment:</b>{" "}
        {payment ? payment.status : "not created"}
      </p>

      <hr />

      {allowed.includes("fund") && (
        <button onClick={pay}>
             Pay
        </button>
      )}


      {allowed.includes("lock") && (
        <button onClick={() => action(`/commitments/${id}/lock`)}>
          Lock
        </button>
      )}

      {allowed.includes("deliver") && (
        <button onClick={() => action(`/commitments/${id}/deliver`)}>
          Deliver
        </button>
      )}
      {commitment.status === "settled" && (
        <div style={{ marginTop: 16 }}>
          <a href={`/result/${id}`}>
            View Settlement Result
          </a>
        </div>
      )}


      {loading && <p>Processing…</p>}
    </main>
  );
}
