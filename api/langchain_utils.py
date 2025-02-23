
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

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

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

# Set up prompts and chains
contextualize_q_system_prompt = """
You are a security context analyzer specializing in converting contextual security questions into detailed standalone queries. Your task is to:

1. ANALYZE the chat history and the latest user question carefully
2. IDENTIFY all relevant security components, attack vectors, or OWASP categories mentioned in the conversation
3. REFORMULATE the question into a detailed standalone query that:
   - Preserves all specific security contexts from the chat history
   - Includes relevant component names, security features, or attack vectors previously discussed
   - Maintains any specific OWASP categories or security standards mentioned
   - Expands pronouns (it, they, these, etc.) with their full references
   - Adds critical context that would be needed for a complete security analysis

Rules:
- Do NOT answer the question, only reformulate it
- If the question is already standalone and specific, return it as is
- Always maintain the security-focused nature of the question
- Preserve any specific technical terms or security concepts mentioned

Examples:
[Previous]: "Let's analyze the OAuth implementation in the login system"
[User]: "What vulnerabilities should I check for?"
[Output]: "What are the potential vulnerabilities and security risks in the OAuth implementation of the login system?"

[Previous]: "The mobile app uses biometric authentication"
[User]: "Are there any issues with this approach?"
[Output]: "What are the security vulnerabilities and potential attack vectors associated with biometric authentication implementation in the mobile app?"

[Previous]: "The payment gateway integrates with third-party providers"
[User]: "How can these be exploited?"
[Output]: "What are the potential security exploits and attack vectors for the third-party payment gateway integrations in the payment system?"
"""
#     "Given a chat history and the latest user question "
#     "which might reference context in the chat history, "
#     "formulate a standalone question which can be understood "
#     "without the chat history. Do NOT answer the question, "
#     "just reformulate it if needed and otherwise return it as is."
# )


contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", role + "\n\nUser Question: {input}")
])


def get_rag_chain(model="gpt-4o-mini"):
    # 1. Initialize the LLM
    llm = ChatOpenAI(model=model)

    # 2. Create history-aware retriever
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt)

    # 3. Create QA chain
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # 4. Combine retriever and QA chain
    rag_chain = create_retrieval_chain(
        history_aware_retriever, question_answer_chain)
    return rag_chain
