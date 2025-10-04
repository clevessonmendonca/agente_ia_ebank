import React, { useState } from 'react';
import {
    Box,
    Button,
    ButtonGroup,
    Tooltip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    DialogContentText,
    TextField,
    IconButton,
    Menu,
    MenuItem,
    Typography,
    CircularProgress,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import UploadIcon from '@mui/icons-material/Upload';
import DownloadIcon from '@mui/icons-material/Download';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { exportFlow, importFlow } from '../services/api';
import { generateUniqueMenuId } from '../utils/flowUtils';

const FlowToolbar = ({
    flowData,
    setFlowData,
    onSave,
    onReload,
    onAddMenu,
    onImportFlow, // Already defined prop
    saving,
    loading,
}) => {
    const [exportOpen, setExportOpen] = useState(false);
    const [exportData, setExportData] = useState('');
    const [importOpen, setImportOpen] = useState(false);
    const [importData, setImportData] = useState('');
    const [importError, setImportError] = useState('');
    const [fileInput, setFileInput] = useState(null);
    const [menuDialogOpen, setMenuDialogOpen] = useState(false);
    const [newMenuName, setNewMenuName] = useState('');
    const [menuAnchorEl, setMenuAnchorEl] = useState(null);
    const [exportLoading, setExportLoading] = useState(false);
    const [importLoading, setImportLoading] = useState(false);
    // New state for save confirmation dialog
    const [saveConfirmOpen, setSaveConfirmOpen] = useState(false);

    const handleExport = async () => {
        try {
            setExportLoading(true);
            // Opção 1: Exportar o fluxo atual em memória
            const jsonData = JSON.stringify(flowData, null, 2);
            setExportData(jsonData);

            // Opção 2: Obter o fluxo mais recente do servidor
            // const data = await exportFlow();
            // setExportData(JSON.stringify(data, null, 2));

            setExportOpen(true);
        } catch (error) {
            console.error('Erro ao exportar fluxo:', error);
            alert('Erro ao exportar o fluxo');
        } finally {
            setExportLoading(false);
        }
    };

    const handleDownloadJson = () => {
        const dataStr =
            'data:text/json;charset=utf-8,' + encodeURIComponent(exportData);
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute('href', dataStr);
        downloadAnchorNode.setAttribute('download', 'flow_export.json');
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    const handleImportClick = () => {
        setImportData('');
        setImportError('');
        setImportOpen(true);
    };

    const handleImportTextChange = (e) => {
        setImportData(e.target.value);
        setImportError('');
    };

    const handleImportJson = async () => {
        try {
            setImportLoading(true);
            let jsonData;
    
            try {
                jsonData = JSON.parse(importData);
            } catch (error) {
                setImportError('JSON inválido. Verifique a formatação.');
                setImportLoading(false);
                return;
            }
    
            if (!jsonData.menus) {
                setImportError(
                    'O JSON não possui o formato correto. Deve conter um objeto "menus".'
                );
                setImportLoading(false);
                return;
            }
    
            // Update flowData state and regenerate graph via callback
            if (onImportFlow) {
                onImportFlow(jsonData);
            }
            
            // Close the import dialog
            setImportOpen(false);
            
            // Ask if user wants to save to server
            setSaveConfirmOpen(true);
        } catch (error) {
            console.error('Erro ao importar fluxo:', error);
            setImportError('Erro ao processar o JSON importado.');
        } finally {
            setImportLoading(false);
        }
    };

    const handleImportFile = (e) => {
        const file = e.target.files[0];
        if (!file) return;
    
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                setImportData(event.target.result);
                
                // Try to parse JSON to provide immediate feedback
                try {
                    const jsonData = JSON.parse(event.target.result);
                    if (!jsonData.menus) {
                        setImportError('O arquivo não contém um fluxo de conversa válido');
                    } else {
                        setImportError(''); // Clear any previous errors
                    }
                } catch (parseError) {
                    setImportError('O arquivo não é um JSON válido');
                }
            } catch (error) {
                setImportError('Erro ao ler o arquivo.');
            }
        };
        reader.readAsText(file);
    };

    const handleAddMenuClick = () => {
        setNewMenuName('');
        setMenuDialogOpen(true);
    };

    const handleAddMenu = () => {
        if (!newMenuName.trim()) return;

        // Gerar ID baseado no nome
        const baseId = newMenuName
            .trim()
            .toLowerCase()
            .replace(/\s+/g, '_')
            .replace(/[^a-z0-9_]/g, '');

        const menuId = generateUniqueMenuId(flowData.menus, baseId);

        const newMenu = {
            title: newMenuName,
            content: `Conteúdo do menu ${newMenuName}`,
            options: {
                menu_type: 'text',
            },
            extra_actions: [],
        };

        const updatedFlowData = {
            ...flowData,
            menus: {
                ...flowData.menus,
                [menuId]: newMenu,
            },
        };

        setFlowData(updatedFlowData);
        setMenuDialogOpen(false);

        // Chamar função para adicionar novo menu ao fluxo visual
        if (onAddMenu) {
            onAddMenu(menuId, newMenu);
        }
    };

    const handleMenuOpen = (event) => {
        setMenuAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setMenuAnchorEl(null);
    };

    return (
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
            <ButtonGroup variant="outlined" size="small">
                <Tooltip title="Adicionar novo menu">
                    <Button
                        startIcon={<AddIcon />}
                        onClick={handleAddMenuClick}
                    >
                        Novo Menu
                    </Button>
                </Tooltip>
                <Tooltip title="Recarregar fluxo">
                    <Button
                        color="primary"
                        onClick={onReload}
                        disabled={loading}
                    >
                        {loading ? (
                            <CircularProgress size={20} />
                        ) : (
                            <RefreshIcon />
                        )}
                    </Button>
                </Tooltip>
            </ButtonGroup>

            <ButtonGroup variant="outlined" size="small">
                <Tooltip title="Salvar fluxo">
                    <Button
                        color="success"
                        onClick={onSave}
                        disabled={saving}
                        startIcon={
                            saving ? (
                                <CircularProgress size={20} />
                            ) : (
                                <SaveIcon />
                            )
                        }
                    >
                        Salvar
                    </Button>
                </Tooltip>
                <Tooltip title="Mais opções">
                    <IconButton onClick={handleMenuOpen}>
                        <MoreVertIcon />
                    </IconButton>
                </Tooltip>
            </ButtonGroup>

            {/* Menu de opções adicionais */}
            <Menu
                anchorEl={menuAnchorEl}
                open={Boolean(menuAnchorEl)}
                onClose={handleMenuClose}
            >
                <MenuItem
                    onClick={() => {
                        handleMenuClose();
                        handleExport();
                    }}
                >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <DownloadIcon fontSize="small" sx={{ mr: 1 }} />
                        <Typography variant="body2">Exportar JSON</Typography>
                    </Box>
                </MenuItem>
                <MenuItem
                    onClick={() => {
                        handleMenuClose();
                        handleImportClick();
                    }}
                >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <UploadIcon fontSize="small" sx={{ mr: 1 }} />
                        <Typography variant="body2">Importar JSON</Typography>
                    </Box>
                </MenuItem>
            </Menu>

            {/* Dialog para exportar JSON */}
            <Dialog
                open={exportOpen}
                onClose={() => setExportOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>Exportar Fluxo (JSON)</DialogTitle>
                <DialogContent>
                    {exportLoading ? (
                        <Box
                            sx={{
                                display: 'flex',
                                justifyContent: 'center',
                                p: 3,
                            }}
                        >
                            <CircularProgress />
                        </Box>
                    ) : (
                        <TextField
                            fullWidth
                            multiline
                            rows={20}
                            value={exportData}
                            variant="outlined"
                            margin="dense"
                            InputProps={{ readOnly: true }}
                        />
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setExportOpen(false)}>Fechar</Button>
                    <Button
                        onClick={handleDownloadJson}
                        color="primary"
                        disabled={exportLoading}
                    >
                        Download JSON
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Dialog para importar JSON */}
            <Dialog
                open={importOpen}
                onClose={() => setImportOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>Importar Fluxo (JSON)</DialogTitle>
                <DialogContent>
                    <Box sx={{ mb: 2 }}>
                        <Button
                            variant="outlined"
                            component="label"
                            startIcon={<UploadIcon />}
                        >
                            Selecionar Arquivo
                            <input
                                type="file"
                                accept=".json"
                                hidden
                                onChange={handleImportFile}
                                ref={setFileInput}
                            />
                        </Button>
                    </Box>
                    <TextField
                        fullWidth
                        multiline
                        rows={15}
                        value={importData}
                        onChange={handleImportTextChange}
                        placeholder="Cole o JSON aqui ou selecione um arquivo..."
                        variant="outlined"
                        margin="dense"
                        error={!!importError}
                        helperText={importError}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setImportOpen(false)}>
                        Cancelar
                    </Button>
                    <Button
                        onClick={handleImportJson}
                        color="primary"
                        disabled={importLoading || !importData.trim()}
                    >
                        {importLoading ? (
                            <CircularProgress size={24} />
                        ) : (
                            'Importar'
                        )}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Dialog para adicionar novo menu */}
            <Dialog
                open={menuDialogOpen}
                onClose={() => setMenuDialogOpen(false)}
            >
                <DialogTitle>Novo Menu</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Nome do Menu"
                        fullWidth
                        value={newMenuName}
                        onChange={(e) => setNewMenuName(e.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setMenuDialogOpen(false)}>
                        Cancelar
                    </Button>
                    <Button
                        onClick={handleAddMenu}
                        color="primary"
                        disabled={!newMenuName.trim()}
                    >
                        Adicionar
                    </Button>
                </DialogActions>
            </Dialog>

            {/* New Dialog for confirming save after import */}
            <Dialog
                open={saveConfirmOpen}
                onClose={() => setSaveConfirmOpen(false)}
            >
                <DialogTitle>Salvar fluxo importado?</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Deseja salvar o fluxo importado no servidor? 
                        Isso substituirá o fluxo atual.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setSaveConfirmOpen(false)}>
                        Não
                    </Button>
                    <Button 
                        onClick={() => {
                            setSaveConfirmOpen(false);
                            onSave();
                        }} 
                        color="primary"
                    >
                        Sim, salvar
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default FlowToolbar;