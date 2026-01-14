"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function NewCommitmentPage() {
  const router = useRouter();

  const [freelancerId, setFreelancerId] = useState(2);
  const [amount, setAmount] = useState(1000);
  const [deadline, setDeadline] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function create() {
    setLoading(true);
    setError(null);

    try {
      const res = await api<any>("/commitments", {
        method: "POST",
        body: JSON.stringify({
          client_id: 1,               // temporary
          freelancer_id: freelancerId,
          amount,
          deadline: new Date(deadline).toISOString(),
          decay_curve: "linear",      // default for now
        }),
      });

      router.push(`/commitments/${res.id}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>Create Commitment</h1>

      <label>
        Freelancer ID
        <input
          type="number"
          value={freelancerId}
          onChange={(e) => setFreelancerId(+e.target.value)}
        />
      </label>

      <label>
        Amount
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(+e.target.value)}
        />
      </label>

      <label>
        Deadline
        <input
          type="datetime-local"
          value={deadline}
          onChange={(e) => setDeadline(e.target.value)}
        />
      </label>

      <button onClick={create} disabled={loading}>
        Create
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}
    </main>
  );
}
