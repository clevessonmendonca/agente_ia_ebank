// src/App.js
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
    Box,
    CssBaseline,
    Snackbar,
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogContentText,
    DialogActions,
    Button,
    TextField,
} from '@mui/material';
import ReactFlow, {
    ReactFlowProvider,
    Background,
    Controls,
    Panel,
    MiniMap,
    useNodesState,
    useEdgesState,
    addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

import MenuNode from './components/MenuNode';
import Sidebar from './components/Sidebar';
import FlowToolbar from './components/FlowToolbar';
import MenuPanel from './components/MenuPanel';
import JsonPreview from './components/JsonPreview';
import { fetchFlow, saveFlow, validateFlow } from './services/api';
import {
    generateNodesAndEdges,
    convertFlowToData,
    isFlowValid,
    generateUniqueMenuId,
} from './utils/flowUtils';

// Definir um tema personalizado para MUI
const theme = createTheme({
    palette: {
        primary: {
            main: '#1976d2',
        },
        secondary: {
            main: '#dc004e',
        },
    },
    typography: {
        fontSize: 14,
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                },
            },
        },
    },
});

// Definir os tipos de nós personalizados
const nodeTypes = {
    menuNode: MenuNode,
};

function App() {
    const reactFlowWrapper = useRef(null);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [reactFlowInstance, setReactFlowInstance] = useState(null);
    const [selectedNode, setSelectedNode] = useState(null);
    const [flowData, setFlowData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [notification, setNotification] = useState({
        open: false,
        message: '',
        severity: 'success',
    });
    const [confirmDialog, setConfirmDialog] = useState({
        open: false,
        title: '',
        message: '',
        onConfirm: null,
    });
    const [addMenuDialog, setAddMenuDialog] = useState(false);
    const [newMenuName, setNewMenuName] = useState('');
    // Novo estado para o diálogo de confirmação de salvar após importação
    const [saveAfterImportDialog, setSaveAfterImportDialog] = useState(false);

    // Carregar o fluxo quando a aplicação iniciar
    useEffect(() => {
        loadFlow();
    }, []);

    const loadFlow = async () => {
        try {
            setLoading(true);
            const data = await fetchFlow();
            setFlowData(data);

            const { nodes: flowNodes, edges: flowEdges } =
                generateNodesAndEdges(data);
            setNodes(flowNodes);
            setEdges(flowEdges);

            setNotification({
                open: true,
                message: 'Fluxo carregado com sucesso!',
                severity: 'success',
            });
        } catch (error) {
            console.error('Erro ao carregar o fluxo:', error);
            setNotification({
                open: true,
                message:
                    'Erro ao carregar o fluxo: ' + (error.message || error),
                severity: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    // Nova função para processar o fluxo importado
    const handleImportFlow = (importedFlowData) => {
        try {
            setLoading(true);
            
            // Atualizar o estado do fluxo
            setFlowData(importedFlowData);
            
            // Gerar nós e arestas a partir dos dados importados
            const { nodes: flowNodes, edges: flowEdges } = 
                generateNodesAndEdges(importedFlowData);
            
            // Atualizar o grafo
            setNodes(flowNodes);
            setEdges(flowEdges);
            
            // Auto-arranjar se necessário e ajustar a visualização
            if (reactFlowInstance) {
                // Pequeno atraso para permitir a renderização dos nós
                setTimeout(() => {
                    reactFlowInstance.fitView({ padding: 0.2 });
                }, 100);
            }
            
            setNotification({
                open: true,
                message: 'Fluxo importado com sucesso!',
                severity: 'success',
            });
            
            // Perguntar se deseja salvar no servidor
            setSaveAfterImportDialog(true);
        } catch (error) {
            console.error('Erro ao processar fluxo importado:', error);
            setNotification({
                open: true,
                message: 'Erro ao processar fluxo importado: ' + (error.message || error),
                severity: 'error',
            });
        } finally {
            setLoading(false);
        }
    };

    const onConnect = useCallback(
        (params) => {
            // Verificar se já existe uma conexão com a mesma origem e destino
            const existingEdge = edges.find(
                (edge) =>
                    edge.source === params.source &&
                    edge.target === params.target
            );

            if (existingEdge) {
                setNotification({
                    open: true,
                    message: 'Conexão já existe!',
                    severity: 'warning',
                });
                return;
            }

            // Adicionar nova conexão
            const newEdge = {
                ...params,
                id: `e-${params.source}-${params.target}`,
                animated: true,
                style: { stroke: '#1976d2' },
            };

            setEdges((eds) => addEdge(newEdge, eds));

            // Atualizar o fluxo de dados
            if (flowData && flowData.menus) {
                const sourceMenu = flowData.menus[params.source];
                if (sourceMenu && sourceMenu.options) {
                    // Dependendo do tipo de menu, atualizar as opções
                    if (
                        sourceMenu.options.menu_type === 'button' &&
                        sourceMenu.options.buttons
                    ) {
                        // Encontrar o primeiro botão sem próximo menu
                        const button = sourceMenu.options.buttons.find(
                            (b) => !b.next_menu
                        );
                        if (button) {
                            button.next_menu = params.target;
                            setFlowData({ ...flowData });
                        }
                    }
                }
            }
        },
        [edges, flowData, setEdges]
    );

    const onNodeClick = useCallback((event, node) => {
        setSelectedNode(node);
    }, []);

    const onPaneClick = useCallback(() => {
        setSelectedNode(null);
    }, []);

    const onSave = async () => {
        if (!reactFlowInstance || !flowData) return;

        try {
            setSaving(true);

            // Converter o fluxo visual para o formato do JSON
            const updatedFlowData = convertFlowToData(nodes, edges, flowData);

            // Validar o fluxo antes de salvar
            const validationResult = isFlowValid(updatedFlowData);

            if (!validationResult.valid) {
                setNotification({
                    open: true,
                    message: `Erro de validação: ${validationResult.error}`,
                    severity: 'error',
                });
                setSaving(false);
                return;
            }

            // Salvar o fluxo
            await saveFlow(updatedFlowData);

            setNotification({
                open: true,
                message: 'Fluxo salvo com sucesso!',
                severity: 'success',
            });

            // Atualizar o estado do fluxo
            setFlowData(updatedFlowData);
        } catch (error) {
            console.error('Erro ao salvar o fluxo:', error);
            setNotification({
                open: true,
                message: 'Erro ao salvar o fluxo: ' + (error.message || error),
                severity: 'error',
            });
        } finally {
            setSaving(false);
        }
    };

    const closeNotification = () => {
        setNotification({ ...notification, open: false });
    };

    const handleAddMenuOpen = () => {
        setNewMenuName('');
        setAddMenuDialog(true);
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

        // Criar novo menu
        const newMenu = {
            title: newMenuName,
            content: `Conteúdo do menu ${newMenuName}`,
            options: {
                menu_type: 'text',
            },
            extra_actions: [],
        };

        // Atualizar o flowData
        const updatedFlowData = {
            ...flowData,
            menus: {
                ...flowData.menus,
                [menuId]: newMenu,
            },
        };

        setFlowData(updatedFlowData);

        // Adicionar nó ao fluxo visual
        const position = reactFlowInstance
            ? reactFlowInstance.project({
                  x: Math.random() * 300 + 50,
                  y: Math.random() * 300 + 50,
              })
            : { x: 100, y: 100 };

        const newNode = {
            id: menuId,
            type: 'menuNode',
            position,
            data: {
                menuId,
                menuData: newMenu,
            },
        };

        setNodes((nds) => [...nds, newNode]);
        setAddMenuDialog(false);

        // Selecionar o novo nó
        setSelectedNode(newNode);
    };

    const handleSelectMenu = (menuId) => {
        // Encontrar o nó correspondente
        const node = nodes.find((n) => n.id === menuId);
        if (node) {
            setSelectedNode(node);

            // Centralizar o nó na tela
            if (reactFlowInstance) {
                reactFlowInstance.setCenter(node.position.x, node.position.y, {
                    duration: 800,
                });
            }
        }
    };

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100vh',
                }}
            >
                <ReactFlowProvider>
                    <Box
                        sx={{
                            display: 'flex',
                            flexGrow: 1,
                            height: 'calc(100% - 64px)',
                        }}
                    >
                        <MenuPanel
                            flowData={flowData}
                            onSelectMenu={handleSelectMenu}
                            onAddMenu={handleAddMenuOpen}
                            selectedMenuId={selectedNode?.id}
                        />

                        <Box
                            ref={reactFlowWrapper}
                            sx={{
                                flexGrow: 1,
                                height: '100%',
                                position: 'relative',
                            }}
                        >
                            <ReactFlow
                                nodes={nodes}
                                edges={edges}
                                onNodesChange={onNodesChange}
                                onEdgesChange={onEdgesChange}
                                onConnect={onConnect}
                                onNodeClick={onNodeClick}
                                onPaneClick={onPaneClick}
                                nodeTypes={nodeTypes}
                                onInit={setReactFlowInstance}
                                fitView
                                snapToGrid
                                snapGrid={[15, 15]}
                                defaultViewport={{ x: 0, y: 0, zoom: 1 }}
                            >
                                <Controls />
                                <MiniMap
                                    nodeStrokeWidth={3}
                                    nodeColor={(node) => {
                                        switch (
                                            node.data.menuData.options
                                                ?.menu_type
                                        ) {
                                            case 'button':
                                                return '#e8f5e9';
                                            case 'list':
                                                return '#fff8e1';
                                            default:
                                                return '#e3f2fd';
                                        }
                                    }}
                                />
                                <Background variant="dots" gap={12} size={1} />

                                <Panel position="top-center">
                                    <FlowToolbar
                                        flowData={flowData}
                                        setFlowData={setFlowData}
                                        onSave={onSave}
                                        onReload={loadFlow}
                                        onAddMenu={handleAddMenuOpen}
                                        onImportFlow={handleImportFlow} // Nova prop para lidar com importação
                                        saving={saving}
                                        loading={loading}
                                    />
                                </Panel>

                                <JsonPreview
                                    data={flowData}
                                    title="Fluxo JSON"
                                />
                            </ReactFlow>
                        </Box>

                        {selectedNode && (
                            <Sidebar
                                selectedNode={selectedNode}
                                updateNode={(updatedNode) => {
                                    setNodes((nds) =>
                                        nds.map((node) =>
                                            node.id === updatedNode.id
                                                ? updatedNode
                                                : node
                                        )
                                    );
                                }}
                                flowData={flowData}
                                setFlowData={setFlowData}
                            />
                        )}
                    </Box>
                </ReactFlowProvider>
            </Box>

            {/* Notificações */}
            <Snackbar
                open={notification.open}
                autoHideDuration={6000}
                onClose={closeNotification}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert
                    onClose={closeNotification}
                    severity={notification.severity}
                    sx={{ width: '100%' }}
                >
                    {notification.message}
                </Alert>
            </Snackbar>

            {/* Diálogo de confirmação */}
            <Dialog
                open={confirmDialog.open}
                onClose={() =>
                    setConfirmDialog({ ...confirmDialog, open: false })
                }
            >
                <DialogTitle>{confirmDialog.title}</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        {confirmDialog.message}
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button
                        onClick={() =>
                            setConfirmDialog({ ...confirmDialog, open: false })
                        }
                    >
                        Cancelar
                    </Button>
                    <Button
                        onClick={() => {
                            if (confirmDialog.onConfirm)
                                confirmDialog.onConfirm();
                            setConfirmDialog({ ...confirmDialog, open: false });
                        }}
                        color="primary"
                        autoFocus
                    >
                        Confirmar
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Novo diálogo para perguntar se deseja salvar após importação */}
            <Dialog
                open={saveAfterImportDialog}
                onClose={() => setSaveAfterImportDialog(false)}
            >
                <DialogTitle>Salvar fluxo importado?</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Deseja salvar o fluxo importado no servidor? 
                        Isso substituirá o fluxo atual.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setSaveAfterImportDialog(false)}>
                        Não
                    </Button>
                    <Button 
                        onClick={() => {
                            setSaveAfterImportDialog(false);
                            onSave();
                        }} 
                        color="primary"
                    >
                        Sim, salvar
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Diálogo para adicionar menu */}
            <Dialog
                open={addMenuDialog}
                onClose={() => setAddMenuDialog(false)}
            >
                <DialogTitle>Adicionar Novo Menu</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Digite um nome para o novo menu. O ID será gerado
                        automaticamente com base neste nome.
                    </DialogContentText>
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
                    <Button onClick={() => setAddMenuDialog(false)}>
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
        </ThemeProvider>
    );
}

export default App;