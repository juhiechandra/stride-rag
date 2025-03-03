from langchain.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List
from langchain_core.documents import Document
import os
from chroma_utils import vectorstore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from typing import List
from langchain_core.documents import Document
import os
from chroma_utils import vectorstore
from dotenv import load_dotenv
import openai
from datetime import datetime

# Enhanced retriever configuration
retriever = vectorstore.as_retriever(
    search_type="mmr",  # Use MMR for diversity in results
    search_kwargs={
        "k": 4,  # Increased from 2 to 4 for better context
        "fetch_k": 20,  # Fetch more documents initially
        "lambda_mult": 0.7,  # Diversity factor for MMR
    }
)

output_parser = StrOutputParser()

system_prompt = """
You are a seasoned security expert with a deep understanding of various security domains, including web application security (OWASP Top 10), mobile security, CWEs by MITRE and general security best practices.

Your output should always follow this format:
COMPONENT | ALL ATTACK VECTORS | ALL OWASP MAPPING

Each component should have up to five attack vectors, and each attack vector should be mapped to relevant OWASP Top 10 categories.
"""

role = """
Map each attack vector to its all possible owasp top 10.

INPUT: PDF UPLOADED and List of components
OUTPUT: COMPONENT | ALL ATTACK VECTORS | ALL OWASP MAPPING

First Column: Take a sub component from the whole architecture 
Second Column: Do threat analysis, see at must Five attack vectors for one component, mention these five attack vectors in a column to side of this component
Third Column: Now in the third column, map all the five attack vectors to its OWASP Top10 

List of all possible attack vectors for any PRD uploaded by user: 

Input Validation and Injection:
- SQL injection
- Cross site scripting (XSS)
- Injection Attacks
- Input validation and injection attacks
- Vulnerability to Injection Attacks in the Repository

Access Control:
- Access Control Issues
- Access control bypass
- Lack of access control to stored data (both read and write access)

Authentication:
- Authentication Issues
- Hardcoded credentials
- User enumeration
- Authentication Mechanism and Bypass
- Account Lockout
- Password bruteforce
- OTP bruteforce
- Race Condition
- Weak Password policy
- Lack of 2FA
- Username Enumeration
- Business logic bugs on authentication page
- Weak session management and algorithm
- Too Long Session expiry
- No session termination in case of activity or logout
- Lack of device fingerprinting
- Lack of Root and Emulator Detection
- Lack of authentication
- Weak MPIN Mechanisms

Financial Transactions:
- Flaw in business logic
- Insecure storage of payment related data
- Negative number acceptance
- Payment bypass
- Lack of server side validation on payment transactions
- Improper business logic for international currencies
- Hardcoded Sensitive keys (payment gateway)
- Response manipulation
- No check on higher transaction value
- Non validation of receiver's account
- Race condition bypass
- Lack of 2FA on payments
- Insufficient Transaction Authorization
- Regulatory Compliance issues
- Inadequate supply chain vulnerability
- Insufficient Binary Protection
- Incorrect Payee transactions
- Man in the Middle Attacks

Mobile Banking Apps:
- Inadequate linking with bank account
- Lack of customer bank account verification
- Lack of device binding
- Improper supply chain (app modification for redirection)
- OTP validation bypass
- Business Logic bypass
- Task Hijacking
- Sensitive Information in Device Log
- Insecure Communication
- Lack of Obfuscation on Code
- Lack of SSL Pinning
- SMS hijacking and tampering (including SIM cloning)

QR Code Payments:
- QR code hijacking
- No verification for new account transfers
- No checks on higher payments
- Negative money transfer
- Direct API call to initiate payment without source account balance check

International Transactions:
- Lack of 2FA for international cards
- Weak business logic in card creation (guessable bins)
- Lack of syncing between credit and debit cards

Third party Service Providers and Apps:
- Lack of Visibility into Third party Service Providers' Security Practices
- Use of Outdated Libraries or Insecure Coding Practices in Third party Apps
- Lack of Visibility into Third party Apps' Security Practices and Data Handling Procedures
- App impersonification and malicious supply chain
- Data Breach (Third party providers)
- Insufficient Binary Protection
- Outdated Libraries
- Misconfigurations

Data Handling and Storage:
- Data storage (sensitive and PII) in plain text
- Inadequate Encryption of Sensitive Data at Rest
- Data Breach and Exposure
- Inadequate supply chain vulnerability
- Lack of Data Backup and Recovery Mechanisms
- Sync Issues

Session Management:
- No session termination in case of activity or logout

Rate Limiting and CAPTCHA:
- Rate Limit Issue on user creation
- Bypass Rate Limit and CAPTCHA

Repository and Logs:
- Hardcoded sensitive information
- Lack of mobile/email validation
- Credentials Over Unencrypted Channel

SOME EXAMPLES:

Component | Attack vectors | OWASP Mapping
User Interfaces | 1. Access Control Issues 2. Input validation or Injection 3. Authentication issues 4. Hardcoded credentials | A1: Broken Access Control A3: Injection A7: Identification and Authentication Failures

User Registration | 1. Account takeover by changing existing user data 2. Credentials Over Unencrypted Channel 3. Lack of device binding with phone number making it easier for attackers to create multiple accounts or take over existing ones 4. User enumeration 5. Lack of mobile/email validation | A1: Broken Access Control A2: Cryptographic Failures A4: Insecure Design A7: Identification and Authentication Failures
"""

# Enhanced system prompt for better context preservation
contextualize_q_system_prompt = """
You are an advanced security context analyzer with expertise in maintaining conversation coherence and security context. Your role is to:

1. ANALYZE the chat history comprehensively, focusing on:
   - Previously mentioned security components and systems
   - Specific attack vectors or vulnerabilities discussed
   - Technical requirements and constraints mentioned
   - Security standards and compliance requirements
   - Any specific examples or use cases provided

2. PROCESS the latest user question by:
   - Identifying references to previous context
   - Detecting implicit security assumptions
   - Understanding the security domain being discussed
   - Recognizing any specific technical terms or concepts

3. REFORMULATE the question to:
   - Explicitly include all relevant context from chat history
   - Maintain technical accuracy and security focus
   - Preserve specific component names and security concepts
   - Include relevant constraints and requirements
   - Reference specific standards or frameworks mentioned
   - Maintain continuity with previous security discussions

4. ENSURE the reformulated question:
   - Is completely standalone and self-contained
   - Maintains all security-relevant details
   - Preserves the original intent and scope
   - Includes all necessary technical context
   - References specific components or systems

Example Transformations:
[History]: "We discussed SQL injection vulnerabilities in the login system."
[User]: "What about XSS?"
[Output]: "What are the potential Cross-Site Scripting (XSS) vulnerabilities in the login system, and how do they relate to the previously discussed SQL injection attack vectors?"

[History]: "The system uses JWT for authentication."
[User]: "Are there any security risks?"
[Output]: "What are the specific security risks and potential vulnerabilities associated with the JWT-based authentication implementation in the system, including token handling, validation, and expiration mechanisms?"

Remember: Do NOT answer the question - only reformulate it to include full context.
"""

# Enhanced QA prompt template
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("system", """
    Previous Context Summary:
    {context}
    
    Focus on:
    1. Maintaining consistency with previous security discussions
    2. Incorporating relevant details from provided context
    3. Ensuring comprehensive security analysis
    4. Mapping to specific OWASP categories
    5. Providing actionable security insights
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", role + "\n\nSpecific Security Question: {input}")
])

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# Add a custom reranking function


def rerank_documents(documents: List[Document], query: str) -> List[Document]:
    """
    Rerank documents based on relevance to query and metadata
    """
    # Add scoring based on metadata and content relevance
    scored_docs = []
    for doc in documents:
        score = 0
        # Boost score for more recent documents
        if 'timestamp' in doc.metadata:
            time_diff = datetime.now() - \
                datetime.fromisoformat(doc.metadata['timestamp'])
            score += 1 / (1 + time_diff.days)

        # Boost score for title/header matches
        if query.lower() in doc.page_content.lower()[:100]:
            score += 2

        # Boost score for security-related content
        security_terms = ['vulnerability',
                          'attack', 'security', 'risk', 'threat']
        score += sum(term in doc.page_content.lower()
                     for term in security_terms)

        scored_docs.append((doc, score))

    # Sort by score and return documents
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored_docs]


def get_rag_chain(model="gpt-4o-mini"):
    llm = ChatOpenAI(model=model)

    # Enhanced retriever with reranking
    def enhanced_retriever(query, chat_history):
        # Get initial documents
        docs = retriever.get_relevant_documents(query)
        # Rerank documents
        reranked_docs = rerank_documents(docs, query)
        return reranked_docs

    history_aware_retriever = create_history_aware_retriever(
        llm,
        enhanced_retriever,
        contextualize_q_prompt
    )

    # 3. Create QA chain
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # 4. Combine retriever and QA chain
    rag_chain = create_retrieval_chain(
        history_aware_retriever, question_answer_chain)
    return rag_chain
