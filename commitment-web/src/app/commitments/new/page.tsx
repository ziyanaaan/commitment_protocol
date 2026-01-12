"use client";

import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NewCommitment() {
  const router = useRouter();
  const [amount, setAmount] = useState(1000);

  async function create() {
    const c = await api<any>("/commitments", {
      method: "POST",
      body: JSON.stringify({
        client_id: 1,
        freelancer_id: 2,
        amount,
        decay_curve: "linear",
        deadline: new Date(Date.now() + 86400000),
      }),
    });

    router.push(`/commitments/${c.id}`);
  }

  return (
    <main>
      <h2>New Commitment</h2>
      <input
        type="number"
        value={amount}
        onChange={(e) => setAmount(+e.target.value)}
      />
      <button onClick={create}>Create</button>
    </main>
  );
}
