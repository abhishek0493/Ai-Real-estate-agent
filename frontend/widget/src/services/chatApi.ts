/** Chat API client — sends messages to the backend. */

export interface ChatResponse {
  assistant_message: string;
  lead_id: string;
  current_status: string;
  tool_executed?: string;
  error?: string;
}

let _apiBase = "http://localhost:8000/api/v1";
let _tenantKey = "";

export function configure(apiBase: string, tenantKey: string) {
  _apiBase = apiBase;
  _tenantKey = tenantKey;
}

export async function sendMessage(
  message: string,
  leadId?: string
): Promise<ChatResponse> {
  const body: Record<string, string> = { message };
  if (leadId) body.lead_id = leadId;

  const res = await fetch(`${_apiBase}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-Key": _tenantKey,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}
