import { useState, FormEvent } from "react";
import type { Lead, GenerateRequest, GenerateResponse } from "./types";

const statusColor: Record<Lead["lead_status"], string> = {
  HOT: "text-red-400",
  WARM: "text-amber-400",
  COLD: "text-zinc-500",
};

export default function App() {
  const [form, setForm] = useState<GenerateRequest>({
    city: "",
    category: "",
    country: "UK",
    max_results: 10,
    no_website_only: false,
  });
  const [leads, setLeads] = useState<Lead[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Request failed (${res.status})`);
      }

      const data: GenerateResponse = await res.json();
      setLeads(data.leads);
      setLog(data.log || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-5 py-10">
      <h1 className="text-xl font-semibold">Rowentrix Lead Generator</h1>
      <p className="text-zinc-400 text-sm mb-6">
        UK business leads — no-website + no-AI-tool filtering
      </p>

      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-2 gap-3 bg-[#15181c] border border-[#23262b] rounded-xl p-5"
      >
        <div>
          <label className="text-xs text-zinc-400 block mb-1">City</label>
          <input
            required
            value={form.city}
            onChange={(e) => setForm({ ...form, city: e.target.value })}
            placeholder="Birmingham"
            className="w-full px-3 py-2 rounded-md bg-[#0f1114] border border-[#2c2f35] text-sm outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="text-xs text-zinc-400 block mb-1">Category</label>
          <input
            required
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            placeholder="care home"
            className="w-full px-3 py-2 rounded-md bg-[#0f1114] border border-[#2c2f35] text-sm outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="text-xs text-zinc-400 block mb-1">Max results</label>
          <input
            type="number"
            min={1}
            max={20}
            value={form.max_results}
            onChange={(e) => setForm({ ...form, max_results: Number(e.target.value) })}
            className="w-full px-3 py-2 rounded-md bg-[#0f1114] border border-[#2c2f35] text-sm outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="text-xs text-zinc-400 block mb-1">Country</label>
          <input
            value={form.country}
            onChange={(e) => setForm({ ...form, country: e.target.value })}
            className="w-full px-3 py-2 rounded-md bg-[#0f1114] border border-[#2c2f35] text-sm outline-none focus:border-blue-500"
          />
        </div>

        <div className="col-span-2 flex items-center gap-2">
          <input
            type="checkbox"
            id="no_website_only"
            checked={form.no_website_only}
            onChange={(e) => setForm({ ...form, no_website_only: e.target.checked })}
          />
          <label htmlFor="no_website_only" className="text-sm">
            No website only
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="col-span-2 py-2 rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-60 font-medium text-sm transition"
        >
          {loading ? "Searching..." : "Find Leads"}
        </button>
      </form>

      {error && <p className="text-red-400 text-sm mt-3">{error}</p>}

      <div className="flex justify-between items-center mt-6">
        <span className="text-sm text-zinc-400">
          {leads.length > 0 ? `${leads.length} lead(s)` : ""}
        </span>
        <a href="/api/export" className="text-sm text-blue-400 hover:underline">
          Export CSV
        </a>
      </div>

      {leads.length > 0 && (
        <table className="w-full text-sm mt-3 border-collapse">
          <thead>
            <tr className="text-zinc-400 text-left border-b border-[#23262b]">
              <th className="py-2 pr-2">Business</th>
              <th className="py-2 pr-2">Category</th>
              <th className="py-2 pr-2">City</th>
              <th className="py-2 pr-2">Phone</th>
              <th className="py-2 pr-2">Website</th>
              <th className="py-2 pr-2">AI Tool</th>
              <th className="py-2 pr-2">Score</th>
              <th className="py-2 pr-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead, i) => (
              <tr key={i} className="border-b border-[#23262b]">
                <td className="py-2 pr-2">{lead.business_name}</td>
                <td className="py-2 pr-2">{lead.category}</td>
                <td className="py-2 pr-2">{lead.city}</td>
                <td className="py-2 pr-2">{lead.phone || "—"}</td>
                <td className="py-2 pr-2">{lead.website_status}</td>
                <td className="py-2 pr-2">
                  {lead.ai_tool_status}
                  {lead.ai_tool_vendor ? ` (${lead.ai_tool_vendor})` : ""}
                </td>
                <td className="py-2 pr-2">{lead.lead_score}</td>
                <td className={`py-2 pr-2 font-semibold ${statusColor[lead.lead_status]}`}>
                  {lead.lead_status}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {log.length > 0 && (
        <pre className="text-xs text-zinc-500 mt-4 whitespace-pre-wrap">{log.join("\n")}</pre>
      )}
    </div>
  );
}
