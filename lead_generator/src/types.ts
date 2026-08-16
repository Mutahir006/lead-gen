export interface Lead {
  business_name: string;
  category: string;
  address: string;
  city: string;
  postcode: string;
  website: string;
  phone: string;
  website_status: "FOUND" | "NOT_FOUND" | "UNCERTAIN";
  ai_tool_status: "DETECTED" | "NOT_DETECTED" | "NOT_APPLICABLE" | "UNCERTAIN";
  ai_tool_vendor: string | null;
  lead_score: number;
  lead_status: "HOT" | "WARM" | "COLD";
  source: string;
}

export interface GenerateRequest {
  city: string;
  category: string;
  country: string;
  max_results: number;
  no_website_only: boolean;
}

export interface GenerateResponse {
  leads: Lead[];
  log: string[];
}
