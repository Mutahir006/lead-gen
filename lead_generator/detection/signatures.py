"""
Known vendor signatures to look for in page HTML/scripts.
This list is the part YOU maintain over time — new AI voice/chatbot vendors
launch constantly, and this is a plain data file, not something LangChain
or an LLM should be guessing at. Add to it as you discover new vendors.

Each value is a list of substrings — if any appear in the raw page source
(script src, div id, inline script text), we count it as a match.
"""

CHATBOT_SIGNATURES = {
    "Intercom": ["widget.intercom.io", "intercomSettings"],
    "Drift": ["js.driftt.com", "drift.load"],
    "Tidio": ["code.tidio.co"],
    "Crisp": ["client.crisp.chat"],
    "Tawk.to": ["embed.tawk.to"],
    "HubSpot Chat": ["js.hs-scripts.com", "hubspot-messages-iframe"],
    "ManyChat": ["widget.manychat.com"],
    "Chatbase": ["chatbase.co"],
    "Zendesk Chat": ["static.zdassets.com"],
}

AI_VOICE_SIGNATURES = {
    "Vapi": ["vapi.ai", "vapi-widget"],
    "Bland.ai": ["bland.ai"],
    "Retell AI": ["retellai.com", "retell-widget"],
    "Synthflow": ["synthflow.ai"],
    "Smith.ai": ["smith.ai"],
    "Goodcall": ["goodcall.com"],
    "PolyAI": ["poly.ai"],
    "Voiceflow": ["voiceflow.com", "vf-widget"],
}

ALL_SIGNATURES = {**CHATBOT_SIGNATURES, **AI_VOICE_SIGNATURES}
