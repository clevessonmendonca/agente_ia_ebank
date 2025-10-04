// web_interface/src/services/api.jsx (correção final)
import axios from 'axios';

// Verificar a URL base correta com base no router.py e nas configurações do FastAPI
// Usando path relativo completo para garantir compatibilidade
const API_BASE_URL = '/api/v1';

// Função para buscar o fluxo atual
export const fetchFlow = async () => {
    try {
        // Endpoint correto baseado no flow_manager.py (GET /api/flow)
        const response = await axios.get(`${API_BASE_URL}/flow-manager/api/flow`);
        console.log('Fetch flow response:', response.data);
        return response.data;
    } catch (error) {
        console.error('Erro ao buscar o fluxo:', error);
        
        // Log detalhado para ajudar na depuração
        if (error.response) {
            console.error('Status do erro:', error.response.status);
            console.error('Dados da resposta:', error.response.data);
            console.error('Cabeçalhos:', error.response.headers);
        } else if (error.request) {
            console.error('Requisição sem resposta:', error.request);
        } else {
            console.error('Erro na configuração da requisição:', error.message);
        }
        
        throw error;
    }
};

// Função para salvar o fluxo
export const saveFlow = async (flowData) => {
    try {
        console.log('Saving flow data:', flowData);
        const response = await axios.post(`${API_BASE_URL}/flow-manager/api/flow`, flowData);
        return response.data;
    } catch (error) {
        console.error('Erro ao salvar o fluxo:', error);
        if (error.response) {
            console.error('Status do erro:', error.response.status);
            console.error('Dados da resposta:', error.response.data);
        }
        throw error;
    }
};

// Função para validar o fluxo
export const validateFlow = async (flowData) => {
    try {
        const response = await axios.post(
            `${API_BASE_URL}/flow-manager/api/flow/validate`,
            flowData
        );
        return response.data;
    } catch (error) {
        console.error('Erro ao validar o fluxo:', error);
        if (error.response && error.response.data) {
            throw new Error(
                error.response.data.error || 'Erro de validação desconhecido'
            );
        }
        throw error;
    }
};

// Função para importar o fluxo a partir de um arquivo
export const importFlow = async (file) => {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post(
            `${API_BASE_URL}/flow-manager/api/flow/import`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data;
    } catch (error) {
        console.error('Erro ao importar o fluxo:', error);
        throw error;
    }
};

// Função para exportar o fluxo atual
export const exportFlow = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/flow-manager/api/flow/export`);
        return response.data;
    } catch (error) {
        console.error('Erro ao exportar o fluxo:', error);
        throw error;
    }
};