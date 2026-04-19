<h2>Tech Stack:</h2>

AI Tools:   Ollama(Claude Code alternate), Github Copilot
Storage:    Can shift to another DB like SQLite or some other if large records
  ┌──────────────┬──────────────────────────┬───────────────────────────────────────┐
  │   Storage    │         Used For         │               Why JSON                │
  ├──────────────┼──────────────────────────┼───────────────────────────────────────┤                                                                  
  │ Raw HTML     │ Archive original filings │ raw data, never modify                │
  ├──────────────┼──────────────────────────┼───────────────────────────────────────┤                                                                  
  │ Chunks JSON  │ Structured SEC text      │ Easy to read, debug, portable         │
  ├──────────────┼──────────────────────────┼───────────────────────────────────────┤                                                                  
  │ FAISS index  │ Vector search            │ Binary format, fast similarity search │
  ├──────────────┼──────────────────────────┼───────────────────────────────────────┤                                                                  
 


  ┌─────────────┬───────────────────┬────────────────────────────────────────────────────────────┐
  │    Tool     │      Purpose      │                            Why                             │
  ├─────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
  │ WhatsApp    │ User interface    │ Everyone has it, no app install needed                     │
  ├─────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
  │ Twilio      │ WhatsApp API      │ Connects WhatsApp to server                           
  ├─────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
  │ ngrok       │ Tunnel            │ Exposes local server to internet 
  ├─────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
  │ FastAPI     │ Web server        │ Receives webhook calls from Twilio                         │
  │ Uvicorn     │ Runs FastAPI 
  ├─────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
  │ LangChain   │ LLM orchestration │ Chains prompts + retrieval + LLM together                  │
  ├─────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
  │ Groq        │ LLM               │ Llama 3.3 70B - fast, free, no OpenAI cost                 │
  ├─────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
  │ FAISS       │ Vector search DB  │ Finds relevant SEC filing chunks fast                      │
  ├─────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
  │ HuggingFace │ Embeddings        │ all-MiniLM-L6-v2 - Converts text to vectors                │
  ├─────────────┼───────────────────┼────────────────────────────────────────────────────────────┤
  │ SEC EDGAR   │ Data source       │ Free SEC filings - no API key needed                       │
  └─────────────┴───────────────────┴────────────────────────────────────────────────────────────┘ 

<h2>ARCHITECTURE</h2>
                                                                                   
                                                                                                                                                                          
                                ┌─────────┐                                                                                                                               
                                │ WHATSAPP│
                                │  USER   │
                                └────┬────┘
                                     │ send message                                                                                                                       
                                ┌────▼────┐
                                │ TWILIO  │                                                                                                                               
                                │ WEBHOOK │
                                └────┬────┘
                                     │ HTTPS
                                ┌────▼────┐                                                                                                                               
                                │ NGROK   │
                                │ :5000   │                                                                                                                               
                                └────┬────┘
                                     │ proxy
                                ┌────▼────┐
                                │ UVICORN │                                                                                                                               
                                │ :5000   │
                                └────┬────┘                                                                                                                               
                                     │
                           ┌─────────┼─────────┐
                           │                   │
                     ┌─────▼─────┐       ┌─────▼─────┐                                                                                                                    
                     │   MENU    │       │   QUERY   │
                     │  HANDLER  │       │  HANDLER  │                                                                                                                    
                     │  (1-5)    │       │     │                                                                                                                    
                     └─────┬─────┘       └─────┬─────┘
                           │                   │                                                                                                                          
                           └─────────┬─────────┘
                                     │                                                                                                                                    
                            ┌────────▼────────┐
                            │    LANGCHAIN 
                               ORCHESTRATOR                                                                                                                                  
                            │  (ticker/year   │
                            │   extraction)   │                                                                                                                           
                            └────────┬────────┘
                                     │                                                                                                                                    
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │                                                                                                             
         ┌──────▼──────┐       ┌──────▼──────┐       ┌──────▼──────┐
         │   GROQ      │       │   GROQ      │       │   GROQ       │                                                                                                     
         │   Llama     │       │   Llama     │       │   Llama      │
         │   3.3 70B   │       │   3.3 70B   │       │   3.3 70B    │                                                                                                     
         │             │       │             │       │              │                                                                                                     
         │ (risk_chain)│       │(financials) │       │(valuation)   │                                                                                                     
         └──────┬──────┘       └──────┬──────┘       └──────┬──────┘                                                                                                      
                │                     │                     │
                │            ┌─────────┴─────────┐          │                                                                                                             
                │            │                   │          │                                                                                                             
         ┌──────▼──────┐ ┌───▼────┐       ┌──────▼──────┐   │
         │   FAISS     │ │  JSON  │       │   FAISS     │   │                                                                                                             
         │   (risk)    │ │(metric)│       │   (mda)     │   │
         └─────────────┘ │        │       └─────────────┘   │                                                                                                             
                         └────────┘                                   

                
                                                           
