import axios from 'axios';

const API_BASE_URL = '/api';

export const uploadPapers = async (files, userId) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('user_id', userId);
  
  const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const sendChatMessage = async (userPrompt, chatHistory, userId, sessionId = 'local_session') => {
  const response = await axios.post(`${API_BASE_URL}/chat`, {
    user_prompt: userPrompt,
    chat_history: chatHistory,
    user_id: userId,
    session_id: sessionId
  });
  return response.data;
};

export const getModelConfig = async () => {
  const response = await axios.get(`${API_BASE_URL}/model`);
  return response.data;
};
