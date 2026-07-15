# Development Guide

## Project Structure

```
/
├── backend/                    # FastAPI backend
│   ├── config.py              # Configuration management
│   ├── database.py            # Neo4j connection
│   ├── main.py                # FastAPI app entry point
│   ├── models.py              # Pydantic models
│   ├── mock_data.py           # Sample company data
│   ├── test_ingestion.py      # Test script for ingestion
│   ├── requirements.txt       # Python dependencies
│   ├── routers/               # API route handlers
│   │   ├── ingest.py         # Data ingestion endpoints
│   │   ├── librarian.py      # GraphRAG query endpoints
│   │   └── boardroom.py      # Multi-agent debate endpoints
│   └── services/              # Business logic
│       ├── ingestion_service.py    # Knowledge Graph ingestion
│       ├── librarian_service.py    # GraphRAG queries
│       └── boardroom_service.py    # LangGraph debate system
│
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js app directory
│   │   │   ├── layout.tsx    # Root layout
│   │   │   ├── page.tsx      # Main page with tabs
│   │   │   └── globals.css   # Global styles
│   │   ├── components/        # React components
│   │   │   ├── LibrarianTab.tsx   # Librarian interface
│   │   │   └── BoardroomTab.tsx   # Boardroom interface
│   │   └── lib/
│   │       └── api.ts         # API client
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── next.config.js
│
├── .env.example               # Environment variables template
├── .gitignore
├── setup.sh                   # Setup script
└── README.md
```

## Architecture Overview

### Backend Architecture

#### 1. Data Ingestion Pipeline
- **Input**: Raw text documents
- **Process**:
  1. Text chunking using `TokenTextSplitter`
  2. Entity extraction using Gemini LLM
  3. Graph document creation via `LLMGraphTransformer`
  4. Loading into Neo4j AuraDB
- **Output**: Populated Knowledge Graph

#### 2. The Librarian (GraphRAG)
- **Purpose**: Factual query answering
- **Components**:
  - `GraphCypherQAChain`: Converts natural language to Cypher
  - Neo4j query execution
  - Answer synthesis using Gemini
- **Flow**: Question → Cypher Generation → Graph Query → Answer Synthesis

#### 3. The Boardroom (Multi-Agent System)
- **Purpose**: Idea evaluation through debate
- **Architecture**: LangGraph state machine
- **Agents**:
  1. **Supervisor**: Analyzes idea, identifies data requirements
  2. **Retrieval**: Queries Neo4j for relevant context
  3. **Strategist**: Argues FOR the idea
  4. **Risk Analyst**: Argues AGAINST the idea
  5. **Synthesizer**: Creates executive summary
- **Flow**: 
  ```
  Idea → Supervisor → Retrieval → [Strategist ↔ Risk Analyst] × N → Synthesizer → Verdict
  ```

### Frontend Architecture

#### Component Hierarchy
```
App (page.tsx)
├── LibrarianTab
│   ├── Query Form
│   ├── Answer Display
│   └── Sources Display
└── BoardroomTab
    ├── Idea Form
    ├── Debate Transcript
    ├── Final Verdict
    └── Data Sources
```

## Development Workflow

### 1. Initial Setup
```bash
# Run the setup script
chmod +x setup.sh
./setup.sh

# Or manually:
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Configuration
Edit `.env` with your credentials:
```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
GEMINI_API_KEY=your-api-key
```

### 3. Testing Ingestion
```bash
cd backend
source venv/bin/activate
python test_ingestion.py
```

### 4. Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access**: http://localhost:3000

## API Endpoints

### Ingestion
- `POST /api/ingest/` - Ingest text into Knowledge Graph
- `GET /api/ingest/status` - Get graph statistics
- `DELETE /api/ingest/clear` - Clear all data

### Librarian
- `POST /api/librarian/query` - Query the Knowledge Graph

### Boardroom
- `POST /api/boardroom/debate` - Start a debate
- `POST /api/boardroom/debate/stream` - Stream debate (SSE)

### Health
- `GET /` - Basic health check
- `GET /health` - Detailed health check

## Knowledge Graph Schema

### Node Types
- **Employee**: `{name, role, department}`
- **Project**: `{name, status, description}`
- **Department**: `{name, budget}`
- **Client**: `{name, industry}`
- **OKR**: `{name, description, status}`
- **Budget**: `{amount, allocated_to}`

### Relationship Types
- `WORKS_ON`: Employee → Project
- `MANAGES`: Employee → Project/Department
- `FOCUSED_ON`: Project → OKR
- `REPORTS_TO`: Employee → Employee
- `ALLOCATED_TO`: Budget → Project/Department
- `DEPENDS_ON`: Project → Project
- `SERVES`: Project → Client

## Debugging Tips

### Backend Issues
1. **Neo4j Connection Failed**
   - Verify credentials in `.env`
   - Check Neo4j AuraDB instance is running
   - Test connection: `python -c "from database import neo4j_connection; print(neo4j_connection.verify_connectivity())"`

2. **Gemini API Errors**
   - Verify API key is valid
   - Check API quota/limits
   - Review error messages in terminal

3. **Import Errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

### Frontend Issues
1. **Module Not Found**
   - Delete `node_modules` and `.next`
   - Run `npm install` again

2. **API Connection Failed**
   - Verify backend is running on port 8000
   - Check CORS settings in `backend/config.py`
   - Verify `NEXT_PUBLIC_API_URL` in frontend

## Testing Scenarios

### Test 1: Librarian Queries
```
Query: "Who is working on Project Alpha?"
Expected: List of employees (Emily Rodriguez, John Martinez)

Query: "What is the status of Project Beta?"
Expected: "Failing due to budget constraints"

Query: "What is the budget for the Engineering Department?"
Expected: "$2.5 million"
```

### Test 2: Boardroom Debates
```
Idea: "We should allocate more budget to Project Alpha"
Expected Strategist Arguments:
- Project Alpha is 60% complete
- Serves enterprise client HealthCorp
- Focused on key OKR

Expected Risk Analyst Arguments:
- Total budget already allocated
- Finance Department concerns
- Historical project failures (Project Delta)
```

## Performance Optimization

### Backend
- Use connection pooling for Neo4j
- Cache frequently accessed graph patterns
- Implement query result caching
- Use async/await for concurrent operations

### Frontend
- Implement React.memo for expensive components
- Use React Query for API state management
- Add loading skeletons
- Implement virtual scrolling for long transcripts

## Security Considerations

1. **API Keys**: Never commit `.env` to version control
2. **Input Validation**: All user inputs are validated via Pydantic
3. **CORS**: Configure allowed origins in production
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Neo4j Injection**: Use parameterized queries (handled by LangChain)

## Deployment

### Backend (Example: Railway/Render)
1. Set environment variables
2. Use `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Configure health check endpoint

### Frontend (Example: Vercel)
1. Connect GitHub repository
2. Set `NEXT_PUBLIC_API_URL` environment variable
3. Deploy automatically on push

## Future Enhancements

1. **Authentication**: Add user authentication and authorization
2. **Real-time Updates**: WebSocket support for live debate streaming
3. **Graph Visualization**: Interactive Neo4j graph visualization
4. **Export**: Export debate transcripts as PDF/Markdown
5. **History**: Store and retrieve past queries and debates
6. **Multi-tenancy**: Support multiple organizations
7. **Advanced Analytics**: Dashboard with graph statistics
8. **File Upload**: Support PDF/DOCX ingestion
9. **Custom Ontology**: Allow users to define custom node/relationship types
10. **Agent Customization**: Configure agent personalities and debate styles