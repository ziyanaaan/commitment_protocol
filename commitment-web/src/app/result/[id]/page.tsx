"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ResultPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api(`/settlements/by-commitment/${id}`)
      .then(setData)
      .catch(e => setErr(e.message));
  }, [id]);

  if (err) return <p>{err}</p>;
  if (!data) return <p>Loading…</p>;

  return (
    <main>
      <h1>Settlement for Commitment #{id}</h1>
      <p><b>Payout:</b> ₹{data.payout_amount}</p>
      <p><b>Refund:</b> ₹{data.refund_amount}</p>
      <p><b>Decay:</b> {data.decay_applied}</p>
      <p><b>Time:</b> {new Date(data.created_at).toLocaleString()}</p>
    </main>
  );
}
