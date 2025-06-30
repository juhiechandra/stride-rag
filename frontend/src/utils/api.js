// Use the Vite proxy in development
const API_BASE_URL = "http://localhost:8000";

// Supported models configuration
const supportedModels = ["gemini-2.5-flash"];
const defaultModel = localStorage.getItem("selectedModel") || "gemini-2.5-flash";

// Helper function to handle API responses
const handleApiResponse = async (response) => {
    if (!response.ok) {
        const errorData = await response.text();
        let errorMessage;
        try {
            const parsedError = JSON.parse(errorData);
            errorMessage = parsedError.message || parsedError.detail || `HTTP ${response.status}`;
        } catch {
            errorMessage = errorData || `HTTP ${response.status}`;
        }
        throw new Error(errorMessage);
    }
    return response.json();
};

// Upload a document
export const uploadDocument = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/upload-doc`, {
        method: "POST",
        body: formData,
    });

    return handleApiResponse(response);
};

// Send a chat message
export const sendMessage = async (message, sessionId = null, model = defaultModel) => {
    try {
        // Ensure model is one of the supported models
        const validModel = supportedModels.includes(model) ? model : defaultModel;

        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                question: message,
                session_id: sessionId,
                model: validModel,
            }),
        });

        return handleApiResponse(response);
    } catch (error) {
        console.error("Error sending message:", error);
        throw error;
    }
};

// List all documents
export const listDocuments = async () => {
    const response = await fetch(`${API_BASE_URL}/documents`);
    return handleApiResponse(response);
};

// Delete a document
export const deleteDocument = async (fileId) => {
    const response = await fetch(`${API_BASE_URL}/delete-doc`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ file_id: fileId }),
    });

    return handleApiResponse(response);
};

// Clean up all documents
export const cleanupDocuments = async () => {
    const response = await fetch(`${API_BASE_URL}/cleanup-documents`, {
        method: "POST",
    });

    return handleApiResponse(response);
};

export { supportedModels, defaultModel };