from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from faiss_utils import vectorstore
from dotenv import load_dotenv
from logger import model_logger, error_logger, PerformanceTimer
import os
import time

load_dotenv()

model_logger.info("Initializing LangChain utilities")


def get_rag_chain(model="gemini-2.5-flash"):
    with PerformanceTimer(model_logger, f"get_rag_chain:{model}"):
        try:
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 6,
                    "fetch_k": 20,
                    "lambda_mult": 0.75
                }
            )

            if not model.startswith("gemini"):
                model = "gemini-2.5-flash"

            llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=os.getenv("GEMINI_KEY"),
                temperature=0.7,
                top_k=40,
                max_output_tokens=2048
            )

            contextualize_prompt = ChatPromptTemplate.from_messages([
                ("system", """Given chat history and a question, reformulate it to be standalone. 
                Consider both text and image contexts."""),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ])

            history_aware_retriever = create_history_aware_retriever(
                llm,
                retriever,
                contextualize_prompt
            )

            qa_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a technical expert analyzing documents. Use both text and image context.
                Text chunks may contain page numbers. Image summaries start with 'IMAGE:'. 
                Always cite sources using [page X] or [image X] notation."""),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                ("human", "Answer based on this context:\n{context}")
            ])

            question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
            retrieval_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

            return retrieval_chain

        except Exception as e:
            error_logger.error(f"Error creating RAG chain for model {model}: {str(e)}", exc_info=True)
            raise
