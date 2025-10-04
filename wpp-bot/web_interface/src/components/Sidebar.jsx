import React from 'react';
import {
    Box,
    Typography,
    Divider,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Button,
    Tab,
    Tabs,
    Accordion,
    AccordionSummary,
    AccordionDetails,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TabPanel from './TabPanel';
import ButtonsEditor from './editors/ButtonsEditor';
import ListEditor from './editors/ListEditor';
import ExtraActionsEditor from './editors/ExtraActionsEditor';

function Sidebar({ selectedNode, updateNode, flowData, setFlowData }) {
    const [tabValue, setTabValue] = React.useState(0);

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
    };

    if (!selectedNode) {
        return (
            <Box
                sx={{
                    width: 300,
                    height: '100%',
                    borderLeft: '1px solid #e0e0e0',
                    p: 2,
                    backgroundColor: '#f5f5f5',
                }}
            >
                <Typography variant="h6" sx={{ mb: 2 }}>
                    Editor de Menu
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Selecione um nó no diagrama para editar seus detalhes.
                </Typography>
            </Box>
        );
    }

    const { menuId, menuData } = selectedNode.data;

    const handleInputChange = (field, value) => {
        // Criar uma cópia atualizada do nó
        const updatedNodeData = {
            ...selectedNode.data,
            menuData: {
                ...selectedNode.data.menuData,
                [field]: value,
            },
        };

        // Atualizar o nó
        updateNode({
            ...selectedNode,
            data: updatedNodeData,
        });

        // Atualizar o flowData
        if (flowData && flowData.menus && flowData.menus[menuId]) {
            const updatedFlowData = {
                ...flowData,
                menus: {
                    ...flowData.menus,
                    [menuId]: {
                        ...flowData.menus[menuId],
                        [field]: value,
                    },
                },
            };
            setFlowData(updatedFlowData);
        }
    };

    const handleMenuTypeChange = (event) => {
        const menuType = event.target.value;

        // Preparar as opções de acordo com o tipo de menu
        let options = {
            menu_type: menuType,
        };

        if (menuType === 'button') {
            options.buttons = menuData.options?.buttons || [];
        } else if (menuType === 'list') {
            options.header = menuData.options?.header || 'Cabeçalho';
            options.footer = menuData.options?.footer || 'Rodapé';
            options.button_text = menuData.options?.button_text || 'Ver opções';
            options.sections = menuData.options?.sections || [];
        }

        // Atualizar o nó
        const updatedNodeData = {
            ...selectedNode.data,
            menuData: {
                ...selectedNode.data.menuData,
                options: options,
            },
        };

        updateNode({
            ...selectedNode,
            data: updatedNodeData,
        });

        // Atualizar o flowData
        if (flowData && flowData.menus && flowData.menus[menuId]) {
            const updatedFlowData = {
                ...flowData,
                menus: {
                    ...flowData.menus,
                    [menuId]: {
                        ...flowData.menus[menuId],
                        options: options,
                    },
                },
            };
            setFlowData(updatedFlowData);
        }
    };

    const handleOptionsChange = (updatedOptions) => {
        // Atualizar o nó
        const updatedNodeData = {
            ...selectedNode.data,
            menuData: {
                ...selectedNode.data.menuData,
                options: updatedOptions,
            },
        };

        updateNode({
            ...selectedNode,
            data: updatedNodeData,
        });

        // Atualizar o flowData
        if (flowData && flowData.menus && flowData.menus[menuId]) {
            const updatedFlowData = {
                ...flowData,
                menus: {
                    ...flowData.menus,
                    [menuId]: {
                        ...flowData.menus[menuId],
                        options: updatedOptions,
                    },
                },
            };
            setFlowData(updatedFlowData);
        }
    };

    const handleExtraActionsChange = (updatedExtraActions) => {
        // Atualizar o nó
        const updatedNodeData = {
            ...selectedNode.data,
            menuData: {
                ...selectedNode.data.menuData,
                extra_actions: updatedExtraActions,
            },
        };

        updateNode({
            ...selectedNode,
            data: updatedNodeData,
        });

        // Atualizar o flowData
        if (flowData && flowData.menus && flowData.menus[menuId]) {
            const updatedFlowData = {
                ...flowData,
                menus: {
                    ...flowData.menus,
                    [menuId]: {
                        ...flowData.menus[menuId],
                        extra_actions: updatedExtraActions,
                    },
                },
            };
            setFlowData(updatedFlowData);
        }
    };

    return (
        <Box
            sx={{
                width: 350,
                height: '100%',
                borderLeft: '1px solid #e0e0e0',
                display: 'flex',
                flexDirection: 'column',
                backgroundColor: '#f9f9f9',
                overflow: 'auto',
            }}
        >
            <Box
                sx={{
                    p: 2,
                    backgroundColor: '#f0f0f0',
                    borderBottom: '1px solid #e0e0e0',
                }}
            >
                <Typography variant="h6">Editor de Menu: {menuId}</Typography>
            </Box>

            <Box sx={{ p: 2 }}>
                <Accordion defaultExpanded>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>Informações Básicas</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <TextField
                            label="Título"
                            fullWidth
                            margin="normal"
                            value={menuData.title || ''}
                            onChange={(e) =>
                                handleInputChange('title', e.target.value)
                            }
                        />

                        <TextField
                            label="Conteúdo"
                            fullWidth
                            margin="normal"
                            multiline
                            rows={4}
                            value={menuData.content || ''}
                            onChange={(e) =>
                                handleInputChange('content', e.target.value)
                            }
                        />

                        <FormControl fullWidth margin="normal">
                            <InputLabel>Tipo de Menu</InputLabel>
                            <Select
                                value={menuData.options?.menu_type || 'text'}
                                label="Tipo de Menu"
                                onChange={handleMenuTypeChange}
                            >
                                <MenuItem value="text">Texto</MenuItem>
                                <MenuItem value="button">Botões</MenuItem>
                                <MenuItem value="list">Lista</MenuItem>
                            </Select>
                        </FormControl>
                    </AccordionDetails>
                </Accordion>
            </Box>

            <Divider />

            <Box
                sx={{
                    p: 2,
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                <Tabs
                    value={tabValue}
                    onChange={handleTabChange}
                    variant="fullWidth"
                    sx={{ mb: 2 }}
                >
                    <Tab label="Opções" />
                    <Tab label="Ações Extras" />
                </Tabs>

                <TabPanel value={tabValue} index={0}>
                    {menuData.options?.menu_type === 'button' && (
                        <ButtonsEditor
                            buttons={menuData.options.buttons || []}
                            onChange={(buttons) =>
                                handleOptionsChange({
                                    ...menuData.options,
                                    buttons,
                                })
                            }
                        />
                    )}

                    {menuData.options?.menu_type === 'list' && (
                        <ListEditor
                            listOptions={menuData.options}
                            onChange={handleOptionsChange}
                        />
                    )}

                    {menuData.options?.menu_type === 'text' && (
                        <Typography variant="body2" color="text.secondary">
                            O menu do tipo texto não possui opções adicionais de
                            configuração.
                        </Typography>
                    )}
                </TabPanel>

                <TabPanel value={tabValue} index={1}>
                    <ExtraActionsEditor
                        extraActions={menuData.extra_actions || []}
                        onChange={handleExtraActionsChange}
                    />
                </TabPanel>
            </Box>
        </Box>
    );
}

export default Sidebar;
