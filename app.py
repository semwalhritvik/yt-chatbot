from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpointEmbeddings, HuggingFaceEndpoint, ChatHuggingFace
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

# Indexing (Document Ingestion)
video_id = "0h8vAGCiRX0"
try:
    transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=['en'])
    transcript = " ".join(chunk["text"] for chunk in transcript_list.to_raw_data())
    #print(transcript)

except TranscriptsDisabled:
    print("Captions not available for this video.")

# Splitter
splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)
chunks = splitter.create_documents([transcript])

print(len(chunks))

model = "sentence-transformers/all-mpnet-base-v2"
embeddings = HuggingFaceEndpointEmbeddings(
    model=model,
    task="feature-extraction"
)

vector_store = FAISS.from_documents(chunks, embeddings)

#print(vector_store.index_to_docstore_id)

# Retrieval
retriever = vector_store.as_retriever(search_type = "similarity", search_kwargs = {"k":2})
#print(retriever.invoke("What is the lack table made of?"))

# Augmentation
prompt = PromptTemplate(
    template = """
You are a helpful assistant.
Answer ONLY from the provided context.
If the context  is insufficient, just say you dont know.

{context}
Question: {question}
""", input_variables=['context', 'question']
)

question = "What is the lack table made of?"
retrieved_docs = retriever.invoke(question)

context_text = " ".join(docs.page_content for docs in retrieved_docs)

final_prompt = prompt.invoke({"context": context_text, "question": question})
#print(final_prompt)

# Generation
llm = HuggingFaceEndpoint(
    repo_id= "deepseek-ai/DeepSeek-V3.2",
    task= "text-generation"
)

model = ChatHuggingFace(llm = llm)
print(model.invoke(final_prompt))

