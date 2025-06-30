import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import styled from "styled-components";
import { Send } from "react-feather";
import { sendMessage } from "../utils/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const Container = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  height: calc(100vh - 4rem);
  display: flex;
  flex-direction: column;
  background: white;
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e9ecef;
`;

const Title = styled.h1`
  color: #2c3e50;
  margin-bottom: 1rem;
  font-weight: 600;
`;

const BackButton = styled(Link)`
  display: inline-block;
  background: #6c757d;
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  transition: all 0.3s ease;

  &:hover {
    background: #545b62;
    transform: translateY(-1px);
  }
`;

const ChatMessages = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 1rem;
  border: 1px solid #e9ecef;
  max-height: 60vh;
`;

const MessageWrapper = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  align-items: flex-start;
`;

const Avatar = styled.div`
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: ${props => props.isUser ? '#007bff' : '#28a745'};
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.8rem;
  flex-shrink: 0;
`;

const MessageContent = styled.div`
  background: ${props => props.isUser ? '#007bff' : 'white'};
  color: ${props => props.isUser ? 'white' : '#2c3e50'};
  padding: 1rem 1.5rem;
  border-radius: 18px;
  max-width: 70%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: ${props => props.isUser ? 'none' : '1px solid #e9ecef'};

  p {
    margin: 0;
    line-height: 1.6;
  }

  code {
    background: ${props => props.isUser ? 'rgba(255,255,255,0.2)' : '#f8f9fa'};
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: "Monaco", "Menlo", monospace;
    font-size: 0.9em;
  }

  pre {
    background: ${props => props.isUser ? 'rgba(255,255,255,0.1)' : '#f8f9fa'};
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    margin: 0.5rem 0;
  }
`;

const ChatInput = styled.div`
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 25px;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
`;

const InputForm = styled.form`
  display: flex;
  width: 100%;
  align-items: center;
`;

const Input = styled.input`
  flex: 1;
  padding: 1rem 1.5rem;
  border: none;
  background: transparent;
  color: #2c3e50;
  font-size: 1rem;
  outline: none;

  &::placeholder {
    color: #6c757d;
  }
`;

const SendButton = styled.button`
  background: #007bff;
  color: white;
  border: none;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    background: #0056b3;
    transform: scale(1.05);
  }

  &:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
`;

const LoadingMessage = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const LoadingDots = styled.div`
  display: flex;
  gap: 0.3rem;
  
  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #007bff;
    animation: loading 1.4s infinite ease-in-out both;

    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
    &:nth-child(3) { animation-delay: 0s; }
  }

  @keyframes loading {
    0%, 80%, 100% {
      transform: scale(0);
    } 40% {
      transform: scale(1);
    }
  }
`;

const EmptyState = styled.div`
  text-align: center;
  color: #6c757d;
  padding: 3rem 1rem;

  h3 {
    color: #2c3e50;
    margin-bottom: 1rem;
  }
`;

const ClearButton = styled.button`
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  margin-left: 1rem;
  transition: all 0.3s ease;

  &:hover {
    background: #c82333;
    transform: translateY(-1px);
  }
`;

const ChatPage = () => {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const newMessage = { role: "user", content: message };
    setMessages(prev => [...prev, newMessage]);
    setMessage("");
    setIsLoading(true);

    try {
      const sessionId = `session_${Date.now()}`;
      
      const response = await sendMessage(message, sessionId, "gemini-2.5-flash");

      if (response && response.answer) {
        setMessages(prev => [
          ...prev,
          { role: "assistant", content: response.answer }
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          {
            role: "assistant",
            content: "I received an unexpected response. Please try again."
          }
        ]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${error.message || "Something went wrong. Please try again."}`
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <Container>
      <Header>
        <BackButton to="/">← Back to Home</BackButton>
        <Title>Chat with Documents</Title>
        {messages.length > 0 && (
          <ClearButton onClick={clearChat}>Clear Chat</ClearButton>
        )}
      </Header>

      <ChatMessages>
        {messages.length === 0 ? (
          <EmptyState>
            <h3>Start a conversation</h3>
            <p>Upload a document and ask questions about its content.</p>
          </EmptyState>
        ) : (
          messages.map((msg, index) => (
            <MessageWrapper key={index}>
              <Avatar isUser={msg.role === "user"}>
                {msg.role === "user" ? "You" : "AI"}
              </Avatar>
              <MessageContent isUser={msg.role === "user"}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.content}
                </ReactMarkdown>
              </MessageContent>
            </MessageWrapper>
          ))
        )}
        
        {isLoading && (
          <LoadingMessage>
            <Avatar>AI</Avatar>
            <div>
              <div>Thinking...</div>
              <LoadingDots>
                <span></span>
                <span></span>
                <span></span>
              </LoadingDots>
            </div>
          </LoadingMessage>
        )}
      </ChatMessages>

      <ChatInput>
        <InputForm onSubmit={handleSendMessage}>
          <Input
            type="text"
            placeholder="Ask a question about your documents..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={isLoading}
          />
          <SendButton type="submit" disabled={isLoading || !message.trim()}>
            <Send size={20} />
          </SendButton>
        </InputForm>
      </ChatInput>
    </Container>
  );
};

export default ChatPage;
