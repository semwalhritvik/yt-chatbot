"""
YouTube RAG Chatbot Backend

This Flask application serves as the backend for the YouTube RAG Chatbot.
It handles:
1. Fetching YouTube transcripts using `youtube_transcript_api`.
2. Vectorizing text chunks using `FAISS` and `HuggingFaceEndpointEmbeddings`.
3. Performing RAG (Retrieval-Augmented Generation) using `DeepSeek-V3.2`.
4. Serving a REST API for the Chrome Extension.
"""

import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpointEmbeddings, HuggingFaceEndpoint, ChatHuggingFace
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS for Chrome Extension access
CORS(app)

# --- Global Configuration ---

# Embedding Model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
embeddings = HuggingFaceEndpointEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    task="feature-extraction"
)

# Text Splitter
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# LLM Setup
llm = HuggingFaceEndpoint(
    repo_id="deepseek-ai/DeepSeek-V3.2",
    task="text-generation"
)
chat_model = ChatHuggingFace(llm=llm)

# Prompt Template
prompt = PromptTemplate(
    template="""
You are a helpful assistant.
Answer ONLY from the provided context.
If the context is insufficient, just say you don't know.

{context}
Question: {question}
""", 
    input_variables=['context', 'question']
)

# In-memory cache for vector stores: {video_id: vector_store}
# Note: In production, consider using a persistent vector DB (e.g., Pinecone, Chroma).
vector_store_cache = {}

def get_or_create_vector_store(video_id):
    """
    Retrieves a vector store from cache or creates a new one by fetching
    the video transcript and embedding it.
    """
    if video_id in vector_store_cache:
        return vector_store_cache[video_id]
    
    try:
        # Fetch transcript, prioritizing US English but falling back to generic English
        transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=['en-US', 'en'])
        
        # Convert fetched object to a list of dictionaries
        transcript_data = transcript_list.to_raw_data()
        
        # Combine all text segments
        transcript = " ".join(chunk["text"] for chunk in transcript_data)
        
        # Create text chunks
        chunks = splitter.create_documents([transcript])
        if not chunks:
            print(f"No text chunks created for video {video_id}")
            return None
            
        # Create Vector Store
        vector_store = FAISS.from_documents(chunks, embeddings)
        vector_store_cache[video_id] = vector_store
        return vector_store
        
    except TranscriptsDisabled:
        print(f"Captions not available for video {video_id}")
        return None
    except Exception as e:
        print(f"Error processing video {video_id}: {e}")
        traceback.print_exc()
        return None

def format_docs(retrieved_docs):
    """Helper to join retrieved document content."""
    return " ".join(doc.page_content for doc in retrieved_docs)

@app.route('/chat', methods=['POST'])
def chat():
    """
    API Endpoint to handle chat queries.
    Expects JSON: { "video_id": "...", "question": "..." }
    """
    data = request.json
    video_id = data.get('video_id')
    question = data.get('question')

    if not video_id or not question:
        return jsonify({"error": "Missing video_id or question"}), 400

    vector_store = get_or_create_vector_store(video_id)
    
    if not vector_store:
        return jsonify({"error": "Could not process video transcript (e.g. no captions available)."}), 404

    # Setup Retrieval Chain
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})

    parallel_chain = RunnableParallel(
        {
            'context': retriever | RunnableLambda(format_docs),
            'question': RunnablePassthrough()
        }
    )

    main_chain = parallel_chain | prompt | chat_model | StrOutputParser()

    try:
        answer = main_chain.invoke(question)
        return jsonify({"answer": answer})
    except Exception as e:
        print(f"Error generating answer: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask Server on port 5000...")
    app.run(debug=True, port=5000)
