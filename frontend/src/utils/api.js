// Use the Vite proxy in development
const API_BASE_URL = "/api";

// Helper function to handle API responses
const handleResponse = async(response) => {
    if (!response.ok) {
        try {
            const errorData = await response.json();
            throw new Error(errorData.detail || "API Error");
        } catch {
            // JSON parsing failed, use text instead
            const error = await response.text();
            throw new Error(error || "Unknown API Error");
        }
    }
    return response.json();
};

// Chat API
export const sendChatMessage = async(message, sessionId, model) => {
    try {
        console.log("Sending chat message:", { message, sessionId, model });

        // Ensure model is one of the supported models
        const supportedModels = ["gemini-2.0-flash", "gemini-2.0-flash"];
        const validModel = supportedModels.includes(model) ?
            model :
            "gemini-2.0-flash";

        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            mode: "cors",
            body: JSON.stringify({
                question: message,
                session_id: sessionId || null,
                model: validModel,
            }),
        });

        console.log("Response status:", response.status);

        if (!response.ok) {
            console.error("Response not OK:", response);
            const errorText = await response.text();
            console.error("Error text:", errorText);
            try {
                const errorData = JSON.parse(errorText);
                throw new Error(errorData.detail || "Failed to send message");
            } catch {
                // JSON parsing failed, use text instead
                throw new Error(errorText || "Failed to send message");
            }
        }

        const data = await response.json();
        console.log("Response data:", data);
        return data;
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
        const response = await fetch(`${API_BASE_URL}/documents`);
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

export const cleanupDocuments = async() => {
    try {
        const response = await fetch(`${API_BASE_URL}/cleanup-documents`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        });
        return handleResponse(response);
    } catch (error) {
        console.error("Cleanup Documents API Error:", error);
        throw error;
    }
};