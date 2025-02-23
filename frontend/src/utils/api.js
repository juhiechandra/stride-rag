const API_BASE_URL = "http://localhost:8000"; // FastAPI default port, not the frontend port (5173)

// Helper function to handle API responses
const handleResponse = async(response) => {
    if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
    }
    return response.json();
};

// Chat API
export const sendChatMessage = async(message, sessionId, model) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                question: message,
                session_id: sessionId || null,
                model: model || "gpt-4o", // default to gpt-4oif not specified
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Server error:", errorData); // Log the error details
            throw new Error(errorData.detail || "Failed to send message");
        }

        return await response.json();
    } catch (error) {
        console.error("Error sending message:", error);
        throw error;
    }
};

// Document APIs
export const uploadDocument = async(formData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/upload-doc`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Upload failed");
        }

        return await response.json();
    } catch (error) {
        console.error("Error uploading document:", error);
        throw error;
    }
};

export const listDocuments = async() => {
    try {
        const response = await fetch(`${API_BASE_URL}/list-docs`);
        return handleResponse(response);
    } catch (error) {
        console.error("List Documents API Error:", error);
        throw error;
    }
};

export const deleteDocument = async(fileId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/delete-doc`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                file_id: fileId,
            }),
        });
        return handleResponse(response);
    } catch (error) {
        console.error("Delete API Error:", error);
        throw error;
    }
};