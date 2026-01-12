"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function Home() {
  const [id, setId] = useState("");
  const router = useRouter();

  return (
    <main>
      <h1>Commitment Protocol</h1>

      <button onClick={() => router.push("/commitments/new")}>
        Create Commitment
      </button>

      <hr />

      <input
        placeholder="Commitment ID"
        value={id}
        onChange={(e) => setId(e.target.value)}
      />
      <button onClick={() => router.push(`/commitments/${id}`)}>
        Open
      </button>
    </main>
  );
}
