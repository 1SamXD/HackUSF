#pip install transformers sentence-transformers faiss-cpu beautifulsoup4 requests

import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from transformers import pipeline

# === Step 1: Scrape the Website ===
def scrape_website(url):
    print(f"🔎 Scraping {url} ...")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

# Change this to whatever page you want
url = r"https://www.usf.edu/engineering/research/undergraduate-research.aspx"
scraped_text = scrape_website(url)

# Save to file
with open(r"C:\Users\samjo\OneDrive\Desktop\projects\usf_chatbot\compsci.txt", "w", encoding="utf-8") as f:
    f.write(scraped_text)
print("✅ Saved to website_data.txt")

# === Step 2: Load and Process Text ===
print("📚 Loading and splitting text...")
loader = TextLoader(r"C:\Users\samjo\OneDrive\Desktop\projects\usf_chatbot\compsci.txt", encoding="utf-8")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(documents)

# === Step 3: Embed Text ===
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = FAISS.from_documents(chunks, embedding)

# === Step 4: Load QA Model ===
print("🧠 Loading question-answering model...")
qa_pipeline = pipeline("question-answering", model="deepset/minilm-uncased-squad2")

# === Step 5: Ask Questions ===
print("\n💬 Chatbot ready! Ask questions about the website.")
print("Type 'exit' to quit.\n")

while True:
    query = input("You: ")
    if query.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break

    # Retrieve relevant docs
    docs = db.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in docs])

    # Get answer
    result = qa_pipeline(question=query, context=context)
    print("Bot:", result["answer"], "\n")
