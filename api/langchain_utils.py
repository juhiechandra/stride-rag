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
    """
    Create a RAG chain with the specified model using simple vector search.

    Args:
        model (str): The model to use for the RAG chain.

    Returns:
        A LangChain retrieval chain.
    """
    with PerformanceTimer(model_logger, f"get_rag_chain:{model}"):
        try:
            # Configure vector retriever with MMR search
            model_logger.info(f"Configuring vector retriever for model: {model}")
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 6,
                    "fetch_k": 20,
                    "lambda_mult": 0.75
                }
            )
            model_logger.info("Vector retriever configured with MMR search")

            # Initialize LLM - ONLY USE GEMINI MODELS
            # Force model to be a Gemini model
            if not model.startswith("gemini"):
                model_logger.warning(
                    f"Non-Gemini model requested: {model}, forcing to gemini-2.5-flash")
                model = "gemini-2.5-flash"

            model_logger.info(f"Using Gemini model: {model}")
            llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=os.getenv("GEMINI_KEY"),
                temperature=0.7,
                top_k=40,
                max_output_tokens=2048
            )

            # Contextualization prompt
            model_logger.info("Creating contextualization prompt")
            contextualize_prompt = ChatPromptTemplate.from_messages([
                ("system", """Given chat history and a question, reformulate it to be standalone. 
                Consider both text and image contexts."""),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ])

            model_logger.info("Creating history-aware retriever")
            history_aware_retriever = create_history_aware_retriever(
                llm,
                retriever,
                contextualize_prompt
            )

            # QA prompt
            model_logger.info("Creating QA prompt")
            qa_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a technical expert analyzing documents. Use both text and image context.
                Text chunks may contain page numbers. Image summaries start with 'IMAGE:'. 
                Always cite sources using [page X] or [image X] notation."""),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                ("human", "Answer based on this context:\n{context}")
            ])

            # Assemble full chain
            model_logger.info("Creating question-answer chain")
            question_answer_chain = create_stuff_documents_chain(
                llm, qa_prompt)

            model_logger.info("Creating retrieval chain")
            retrieval_chain = create_retrieval_chain(
                history_aware_retriever, question_answer_chain
            )

            model_logger.info(
                f"RAG chain created successfully for model: {model}")
            return retrieval_chain

        except Exception as e:
            error_msg = f"Error creating RAG chain for model {model}: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            raise
