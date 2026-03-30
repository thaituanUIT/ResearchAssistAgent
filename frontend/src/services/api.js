import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const uploadPapers = async (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const sendChatMessage = async (userPrompt, chatHistory, workingDocument, synthesis) => {
  const response = await axios.post(`${API_BASE_URL}/chat`, {
    user_prompt: userPrompt,
    chat_history: chatHistory,
    working_document: workingDocument,
    synthesis: synthesis
  });
  return response.data;
};
