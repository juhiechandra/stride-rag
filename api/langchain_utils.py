"""
AI Model Setup and Question Answering

This module sets up the AI models that answer questions about documents.
It handles:

1. Setting up Gemini models for question answering (ONLY Gemini is used for RAG)
2. Creating the question answering system
3. Including conversation history for context
4. Finding relevant information in documents
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from chroma_utils import vectorstore
from dotenv import load_dotenv
from logger import model_logger, error_logger, PerformanceTimer, log_token_usage, app_logger
import os

# Load API keys from .env file
load_dotenv()

app_logger.info("Setting up Gemini AI models for RAG")


def get_rag_chain(model="gemini-2.0-flash"):
    """
    Create a system that answers questions based on document content using ONLY Gemini models.

    This function:
    1. Sets up a search system to find relevant document parts
    2. Configures the Gemini AI model
    3. Creates a system that understands conversation history
    4. Returns a complete question-answering system

    Args:
        model (str): Which Gemini model to use (e.g., "gemini-2.0-flash" or "gemini-2.0-pro")

    Returns:
        A complete question-answering system using Gemini
    """
    with PerformanceTimer(app_logger, f"setup_qa_system:{model}"):
        try:
            # Ensure we're using a Gemini model
            if not model.startswith("gemini"):
                original_model = model
                model = "gemini-2.0-flash"  # Default to Gemini Flash
                app_logger.warning(
                    f"Non-Gemini model requested ({original_model}). Defaulting to {model} for RAG.")

            # Set up the document search system
            app_logger.info(f"Setting up search for Gemini model: {model}")
            retriever = vectorstore.as_retriever(
                search_type="mmr",  # Use Maximum Marginal Relevance for diverse results
                search_kwargs={
                    "k": 6,         # Return 6 results
                    "fetch_k": 20,  # Consider top 20 results first
                    "lambda_mult": 0.75  # Balance between relevance and diversity
                }
            )
            app_logger.info("Search system ready")

            # Set up the Gemini model
            app_logger.info(f"Setting up Gemini model: {model}")
            llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=os.getenv("GEMINI_API_KEY"),
                temperature=0.7,     # Some creativity in responses
                top_k=40,            # Consider top 40 tokens when generating text
                max_output_tokens=2048  # Maximum response length
            )

            # Create a system that understands conversation context
            app_logger.info(
                "Setting up conversation understanding with Gemini")
            contextualize_prompt = ChatPromptTemplate.from_messages([
                ("system", """Look at the chat history and the new question. 
                Rewrite the question to include any important context from the history.
                Consider both text and image information."""),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ])

            # Create a search system that uses conversation history
            app_logger.info("Setting up history-aware search")
            history_aware_retriever = create_history_aware_retriever(
                llm,
                retriever,
                contextualize_prompt
            )

            # Create the template for how the AI should answer questions
            app_logger.info("Setting up answer format for Gemini")
            qa_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful assistant analyzing documents. Use both text and images to answer.
                When information comes from a specific page, mention it like [page 5].
                When information comes from an image, mention it like [image 2].
                Be accurate and cite your sources."""),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                ("human", "Here's information to help answer:\n{context}")
            ])

            # Put everything together
            app_logger.info("Creating final answer system with Gemini")
            question_answer_chain = create_stuff_documents_chain(
                llm, qa_prompt)

            app_logger.info("Connecting search and answer systems")
            retrieval_chain = create_retrieval_chain(
                history_aware_retriever, question_answer_chain)

            app_logger.info(
                f"Question answering system ready using Gemini model: {model}")
            return retrieval_chain

        except Exception as e:
            error_msg = f"Error setting up Gemini question answering system with {model}: {str(e)}"
            model_logger.error(error_msg)
            error_logger.error(error_msg, exc_info=True)
            raise


def estimate_gemini_tokens(result, model_name, operation_type="chat"):
    """
    Estimate and log token usage for Gemini models.

    Args:
        result: The result from the Gemini model
        model_name: The name of the Gemini model used
        operation_type: The type of operation (default: "chat")
    """
    try:
        # For Gemini, we need to estimate tokens since they're not directly provided
        # Rough estimate: 4 characters per token for English text
        if "answer" in result:
            output_text = result["answer"]
            input_text = result.get("input", "")

            # Estimate tokens
            input_tokens = len(input_text) // 4
            output_tokens = len(output_text) // 4
            total_tokens = input_tokens + output_tokens

            # Log the estimated token usage
            log_token_usage(model_name, operation_type,
                            input_tokens, output_tokens, total_tokens)
            app_logger.info(
                f"Estimated token usage for {model_name}: {total_tokens} tokens (input: {input_tokens}, output: {output_tokens})")
    except Exception as e:
        error_logger.error(f"Error estimating token usage: {str(e)}")
