<h2>What is this:</h2>

MVP: A RAG-powered analyst trapped inside WhatsApp, extracting risks, EBITDA drivers, and value creation ideas from SEC filings.


<h2>Tech Stack:</h2>

AI Tools:   Ollama(Claude Code alternate), Github Copilot

Storage:    In the future, another SQL DB for can be used for scalability


| Storage       | Used For                  | Why JSON / Format                     |
|---------------|---------------------------|--------------------------------------|
| Raw HTML      | Archive original filings  | Raw data, never modify               |
| Chunks JSON   | Structured SEC text       | Easy to read, debug, portable        |
| FAISS Index   | Vector search             | Binary format, fast similarity search|                                                       
 



  | Tool         | Purpose           | Why                                                                 |
|--------------|------------------|----------------------------------------------------------------------|
| WhatsApp     | User interface   | Everyone has it, no app install needed                              |
| Twilio       | WhatsApp API     | Connects WhatsApp to backend                                        |
| ngrok        | Tunnel           | Exposes local server to internet                                    |
| FastAPI      | Web server       | Receives webhook calls from Twilio                                  |
| Uvicorn      | ASGI server      | Runs FastAPI efficiently                                            |
| LangChain    | LLM orchestration| Chains retrieval + prompts + LLM                                    |
| Groq         | LLM              | Llama 3 (fast, low latency, cost-effective)                         |
| FAISS        | Vector DB        | Fast similarity search for SEC chunks                               |
| HuggingFace  | Embeddings       | Converts text to vectors (e.g., all-MiniLM-L6-v2)                   |
| SEC EDGAR    | Data source      | Free SEC filings                              |


<h2>ARCHITECTURE</h2>

<img width="776" height="2180" alt="mermaid-diagram (1)" src="https://github.com/user-attachments/assets/eca0a3c8-f516-4d16-873f-584cb90b6b4b" />

<h2>DEMO</h2>:

<img width="776" height="2180" alt="video" src="https://github.com/devsarahgeo/Chatbot-to-chat-with-Documents/blob/main/demo_chatbot.mp4" />







                
                                                           
